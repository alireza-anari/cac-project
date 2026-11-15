"""S0-09N: qualify a fresh learner after an observed old-byte native fail-stop."""
import copy
import json
import os
import signal
from pathlib import Path
from uuid import uuid4

from h_quorum.authority import Root
from h_quorum.broker import Broker
from h_quorum.cluster import Cluster
from h_quorum.common import BANNER, Denied
from h_quorum.etcd import b64, unb64
from h_quorum.l_physical.m_triage import (
    ObservedPhysical,
    PROGRESS_PUTS,
    clean_stop_receipt,
    observe,
    state_summary,
)
from h_quorum.retirement import adopt_policy
from h_quorum.rpc import Client
from recovery_fencing.lab import S1


CASES = {
    "N_PROGRESS_OLD_CLEAN_OPEN": {"kill": False, "operation": "OPEN"},
    "N_PROGRESS_OLD_KILL_UNKNOWN": {"kill": True, "operation": "UNKNOWN"},
}
REPETITIONS = (1, 2)


def emit_n(kind, value):
    print(BANNER, "N " + kind, json.dumps(value, sort_keys=True), flush=True)


def read_full(lab):
    return Root(lab.rootcfg).read(lab.namespace, True)


def retire_policy(lab):
    result = Client(lab.rootcfg, "control", lab.namespace).call(
        "retire_policy", dict(expected=1, new=2, request=str(uuid4()))
    )
    if result.get("policy") != 2:
        raise AssertionError("N policy retirement did not commit")
    lab.replay()
    return result


def progress_and_stop(test, physical, kill):
    physical.phase = "resume-progress"
    child, log = physical.spawn()
    physical.caught_up()
    archive_status = physical.status("N-resumed-before-progress")
    prefix = "/cac-n-progress/" + uuid4().hex + "/"
    for index in range(PROGRESS_PUTS):
        physical.q.etcd.call(
            "/v3/kv/put",
            dict(key=b64(prefix + str(index)), value=b64(str(index))),
        )

    def applied():
        rows = physical.q.etcd.range(
            prefix + str(PROGRESS_PUTS - 1),
            serializable=True,
            endpoint=physical.q.cfg["members"]["r4"]["endpoint"],
        ).get("kvs", [])
        return len(rows) == 1 and unb64(rows[0]["value"]) == str(PROGRESS_PUTS - 1).encode()

    physical.q._wait(applied)
    progress_status = physical.status("N-fixed-progress-locally-applied")
    test.assertGreaterEqual(
        int(progress_status["raftAppliedIndex"]),
        int(archive_status["raftAppliedIndex"]) + PROGRESS_PUTS,
        "N progress did not exceed the archived local applied index",
    )
    physical.phase = "final-stop"
    if kill:
        record = copy.deepcopy(physical.q.cfg["members"]["r4"])
        os.kill(record["pid"], signal.SIGSTOP)
        physical.frozen = True
        physical.q = Cluster()  # Exercise the inherited non-child stop path.
        test.assertFalse(physical.q.children)
        physical.stop()
        physical.frozen = False
        test.assertFalse(physical.q._owned(record), "N old executable remains before byte selection")
        test.assertEqual(child.wait(timeout=5), -signal.SIGKILL)
        stop = dict(kind="SIGSTOP_NONCHILD_SIGKILL", exit=-signal.SIGKILL,
                    executable_absent=True, member=str(record["id"]))
    else:
        physical.stop()
        clean = clean_stop_receipt(test, *physical.last_native)
        stop = dict(kind="CLEAN_SIGTERM", exit=clean["exit_code"],
                    received_sigterm=clean["received_sigterm"],
                    closed_server=clean["closed_server"])
    return dict(archive_status=archive_status, progress_status=progress_status, stop=stop)


def replay_old_and_require_panic(test, lab, physical, expected_state):
    target, revision, history = expected_state
    physical.majority_current("N-before-old-byte-replay")
    data = physical.path(physical.q.cfg["members"]["r4"]["data_dir"])
    current_files = physical.inventory(data)
    test.assertNotEqual(current_files, physical.manifest, "N progressed current bytes unexpectedly equal archive")
    sealed = physical.private / ("sealed-current-before-N-" + uuid4().hex)
    data.rename(sealed)
    physical.copy_archive(data)
    imported = physical.inventory(data)
    test.assertEqual(imported, physical.manifest, "N imported bytes differ from the exact old archive")
    physical.phase = "observation"
    physical.spawn()
    native = observe(physical, target, revision, history)
    if native.get("outcome") != "NATIVE_FAIL_STOP_EXIT2":
        emit_n("PRECONDITION_NOT_REPRODUCED", dict(native=native, expected="NATIVE_FAIL_STOP_EXIT2"))
        raise AssertionError("N_PRECONDITION_NOT_REPRODUCED: exact M native panic was not observed")
    test.assertTrue(native.get("native_id_confirmed"), "N native panic lacks old member identity")
    panic = native.get("panic", {})
    test.assertGreater(panic.get("tocommit", 0), panic.get("last_index", 0))
    test.assertEqual(native.get("exit_code"), 2)
    return dict(native=native, archive_files=physical.manifest,
                sealed_current_files=current_files, imported_files=imported,
                highest_observed_index=physical.highest_index)


def repair_with_receipt(test, physical, old_id):
    """Run the existing real remove -> fresh learner -> catch-up -> promote path."""
    q = physical.q
    old_member = copy.deepcopy(q.cfg["members"]["r4"])
    old_data_dir = old_member["data_dir"]
    old_cert, old_key = old_member["cert"], old_member["key"]
    if q._owned(old_member):
        raise AssertionError("N old native member is still running; replacement forbidden")

    receipt = {
        "old_member_id": str(old_id),
        "old_process_absent": True,
        "fresh_data_dir_absent_before_spawn": False,
        "fresh_identity_distinct": False,
        "fresh_certificate_distinct": False,
        "learner_observed_before_promotion": False,
        "current_log_catchup_verified": False,
        "server_accepted_promotion": False,
        "membership_calls": [],
    }

    original_call = q.etcd.call
    original_spawn = q._spawn
    original_promote = q.promote
    original_caught_up = physical.caught_up

    def traced_call(path, *args, **kwargs):
        result = original_call(path, *args, **kwargs)
        if path in (
            "/v3/cluster/member/remove",
            "/v3/cluster/member/add",
            "/v3/cluster/member/promote",
        ):
            receipt["membership_calls"].append(
                dict(path=path, response_keys=sorted(result.keys()) if isinstance(result, dict) else [])
            )
        return result

    def guarded_spawn(name, state="existing", initial=None):
        if name == "r4":
            member = q.cfg["members"][name]
            data_dir = Path(member["data_dir"])
            test.assertNotEqual(str(member["id"]), str(old_id), "N replacement reused old member ID")
            test.assertNotEqual(str(data_dir), str(old_data_dir), "N replacement reused old data directory")
            test.assertFalse(data_dir.exists(), "N fresh learner data directory was not empty before bootstrap")
            test.assertNotEqual(member["cert"], old_cert, "N replacement reused old certificate")
            test.assertNotEqual(member["key"], old_key, "N replacement reused old private key")
            receipt.update(
                fresh_data_dir_absent_before_spawn=True,
                fresh_identity_distinct=True,
                fresh_certificate_distinct=True,
                new_member_id=str(member["id"]),
                new_data_dir_is_distinct=True,
            )
        return original_spawn(name, state=state, initial=initial)

    def guarded_caught_up():
        result = original_caught_up()
        member_id = str(q.cfg["members"]["r4"]["id"])
        if member_id != str(old_id):
            members = q.etcd.call("/v3/cluster/member/list", {}).get("members", [])
            matches = [m for m in members if str(m["ID"]) == member_id]
            test.assertEqual(len(matches), 1, "N fresh learner membership is ambiguous")
            test.assertTrue(matches[0].get("isLearner"), "N fresh member voted before promotion")
            test.assertFalse(any(str(m["ID"]) == str(old_id) for m in members),
                             "N removed old identity remains in authoritative membership")
            receipt["learner_observed_before_promotion"] = True
            receipt["current_log_catchup_verified"] = True
            receipt["learner_status"] = physical.status("N-fresh-learner-caught-up")
        return result

    def guarded_promote(name):
        member_id = str(q.cfg["members"][name]["id"])
        members = q.etcd.call("/v3/cluster/member/list", {}).get("members", [])
        matches = [m for m in members if str(m["ID"]) == member_id]
        test.assertEqual(len(matches), 1, "N promotion target is not uniquely present")
        test.assertTrue(matches[0].get("isLearner"), "N promotion attempted after learner already voted")
        test.assertTrue(receipt["current_log_catchup_verified"],
                        "N promotion attempted before current Root/journal catch-up")
        result = original_promote(name)
        receipt["server_accepted_promotion"] = True
        return result

    q.etcd.call = traced_call
    q._spawn = guarded_spawn
    q.promote = guarded_promote
    physical.caught_up = guarded_caught_up
    try:
        physical.repair_fresh_after_native_refusal()
    finally:
        q.etcd.call = original_call
        q._spawn = original_spawn
        q.promote = original_promote
        physical.caught_up = original_caught_up

    membership = q.etcd.call("/v3/cluster/member/list", {})
    members = membership.get("members", [])
    cluster_id = str(membership.get("header", {}).get("cluster_id"))
    new_id = str(q.cfg["members"]["r4"]["id"])
    voters = [m for m in members if not m.get("isLearner")]
    learners = [m for m in members if m.get("isLearner")]
    test.assertEqual(cluster_id, str(q.cfg["cluster_id"]), "N cluster ID changed during repair")
    test.assertEqual(len(members), 5, "N expected five total members after replacement")
    test.assertEqual(len(voters), 5, "N expected five voters after explicit promotion")
    test.assertEqual(len(learners), 0, "N learner remained after promotion")
    test.assertTrue(any(str(m["ID"]) == new_id for m in voters), "N fresh identity is not a voter")
    test.assertFalse(any(str(m["ID"]) == str(old_id) for m in members), "N old identity remains admitted")
    test.assertTrue(receipt["fresh_data_dir_absent_before_spawn"])
    test.assertTrue(receipt["fresh_identity_distinct"])
    test.assertTrue(receipt["fresh_certificate_distinct"])
    test.assertTrue(receipt["learner_observed_before_promotion"])
    test.assertTrue(receipt["current_log_catchup_verified"])
    test.assertTrue(receipt["server_accepted_promotion"])
    required = {
        "/v3/cluster/member/remove",
        "/v3/cluster/member/add",
        "/v3/cluster/member/promote",
    }
    test.assertTrue(required.issubset({v["path"] for v in receipt["membership_calls"]}),
                    "N actual consensus membership operations are incomplete")
    receipt.update(
        new_member_id=new_id,
        cluster_id=cluster_id,
        total_members=len(members),
        voter_count=len(voters),
        learner_count=len(learners),
        old_member_absent=True,
        new_member_is_voter=True,
        original_majority_ids={name: str(m["id"]) for name, m in physical.majority.items()},
    )
    return receipt


def run_open_case(test, lab, broker, repetition):
    physical = ObservedPhysical(lab)
    test.addCleanup(physical.close)
    physical.archive_current()
    body = {"body": "synthetic-N-open-" + str(repetition)}
    successor = Broker(lab, "B")
    row = dict(case="N_PROGRESS_OLD_CLEAN_OPEN", repetition=repetition,
               status="N_TEST_HARNESS_FAILURE", member_repair="NOT_RUN")
    try:
        with broker.runtime(action="probe", body=body) as gate:
            gate.install(broker.issue(gate.challenge(), action="probe", body=body))
            test.assertEqual(gate.records(), [S1])
            test.assertEqual(
                gate.c.execute("UPDATE poc.records SET body=%s WHERE store=%s",
                               (body["body"], S1)).rowcount,
                1,
            )
            row["pregrant"] = dict(pid=gate.pid, fullxid=gate.tx, system_id=gate.sid,
                                   operation=gate.operation)
            progress = progress_and_stop(test, physical, kill=False)
            row["progress"] = progress
            retire_policy(lab)
            before = read_full(lab)
            summary = state_summary(*before)
            test.assertGreaterEqual(summary["open"], 1, "N pre-granted operation is not OPEN")
            test.assertEqual(summary["unknown"], 0, "N OPEN scenario unexpectedly has UNKNOWN")
            row["before_native"] = summary
            replay = replay_old_and_require_panic(test, lab, physical, before)
            row["native_replay"] = replay
            physical.majority_current("N-after-native-panic-before-repair")
            test.assertEqual(read_full(lab), before, "N native panic changed current Root/journal")
            test.assertFalse(broker.ready(), "N retired policy unexpectedly remains ready")
            with test.assertRaises(Denied):
                with broker.runtime():
                    test.fail("N old policy admitted after native panic")
            with test.assertRaises(Denied):
                successor.activate(1, str(uuid4()))
            repair = repair_with_receipt(test, physical, physical.original["id"])
            row["repair"] = repair
            row["member_repair"] = "OBSERVED_FRESH_ID_LEARNER"
            after_repair = read_full(lab)
            test.assertEqual(after_repair, before, "N repair changed current Root/journal/OPEN")
            held = state_summary(*after_repair)
            test.assertGreaterEqual(held["open"], 1, "N repair cleared the pre-granted OPEN")
            test.assertEqual(held["unknown"], 0)
            row["after_repair"] = held
            with test.assertRaises(Denied):
                successor.activate(1, str(uuid4()))
            test.assertEqual(gate.records(), [S1])
        final_state = Root(lab.rootcfg).read(lab.namespace)[0]
        test.assertEqual(final_state["ops"][gate.operation]["phase"], "CLOSED_COMMIT",
                         "N OPEN did not close after the actual local COMMIT ACK")
        row["after_authoritative_close"] = dict(
            phase=final_state["ops"][gate.operation]["phase"],
            open=sum(op["phase"] == "OPEN" for op in final_state["ops"].values()),
            unknown=sum(op["phase"] == "UNKNOWN" for op in final_state["ops"].values()),
        )
        adopt_policy(lab)
        test.assertTrue(broker.ready(), "N current policy2 SQL path did not recover after known CLOSE")
        with broker.runtime() as current:
            test.assertEqual(current.binding["policy"], 2)
            with test.assertRaises(Denied):
                broker.command(
                    "admit",
                    dict(current.binding, policy=1, request=str(uuid4()), operation=str(uuid4())),
                )
            current.install(broker.issue(current.challenge()))
            test.assertEqual(current.records(), [S1])
            test.assertEqual(
                current.c.execute("SELECT body FROM poc.records WHERE store=%s", (S1,)).fetchone(),
                (body["body"],),
            )
            row["healthy_current_sql"] = dict(policy=2, scoped_read=True, committed_body=True,
                                               pid=current.pid, fullxid=current.tx, system_id=current.sid)
        physical.majority_current("N-after-open-close-current-SQL-and-repair")
        row["status"] = "OBSERVED"
        emit_n("OBSERVATION", row)
        return row
    except BaseException as error:
        row["status"] = (
            "N_SUPPORTED_SECURITY_FAIL"
            if any(term in str(error) for term in (
                "N_SUPPORTED_SECURITY_FAIL", "Root/journal", "cleared the pre-granted",
                "old identity remains", "cluster ID changed", "not a voter",
            ))
            else "N_TEST_HARNESS_FAILURE"
        )
        row["failure_type"] = type(error).__name__
        emit_n("OBSERVATION", row)
        raise


def run_unknown_case(test, lab, broker, repetition):
    physical = ObservedPhysical(lab)
    test.addCleanup(physical.close)
    physical.archive_current()
    successor = Broker(lab, "B")
    row = dict(case="N_PROGRESS_OLD_KILL_UNKNOWN", repetition=repetition,
               status="N_TEST_HARNESS_FAILURE", member_repair="NOT_RUN")
    gate = broker.runtime(action="probe", body={"body": "synthetic-N-unknown-" + str(repetition)})

    def retire_after_open(label):
        if label == "after_durable_open":
            retire_policy(lab)

    broker.hook = retire_after_open
    try:
        with test.assertRaises(Denied):
            with gate:
                test.fail("N retired ungranted operation reached protected SQL")
        broker.hook = lambda _: None
        test.assertIsNotNone(gate.ticket, "N UNKNOWN lacks its durable ticket")
        test.assertIsNotNone(gate.binding, "N UNKNOWN lacks its authoritative binding")
        progress = progress_and_stop(test, physical, kill=True)
        row["progress"] = progress
        before = read_full(lab)
        summary = state_summary(*before)
        test.assertEqual(summary["unknown"], 1, "N genuine UNKNOWN was not recorded")
        row["before_native"] = summary
        replay = replay_old_and_require_panic(test, lab, physical, before)
        row["native_replay"] = replay
        physical.majority_current("N-unknown-after-native-panic-before-repair")
        test.assertEqual(read_full(lab), before, "N native panic changed UNKNOWN/Root/journal")
        test.assertFalse(broker.ready(), "N UNKNOWN scenario unexpectedly made old policy ready")
        repair = repair_with_receipt(test, physical, physical.original["id"])
        row["repair"] = repair
        row["member_repair"] = "OBSERVED_FRESH_ID_LEARNER"
        after_repair = read_full(lab)
        test.assertEqual(after_repair, before, "N repair changed current Root/journal/UNKNOWN")
        held = state_summary(*after_repair)
        test.assertEqual(held["unknown"], 1, "N fresh learner repair cleared genuine UNKNOWN")
        row["after_repair"] = held
        with test.assertRaises(Denied):
            successor.activate(1, str(uuid4()))
        with test.assertRaises(Denied):
            adopt_policy(lab)
        with test.assertRaises(Denied):
            broker.command(
                "close",
                dict(gate.binding, ticket=gate.ticket, outcome="abort"),
            )
        test.assertEqual(read_full(lab), before, "N denied UNKNOWN resolution changed Root/journal")
        test.assertEqual(broker.inspect()["unknown"], 1)
        row["resolution"] = dict(
            successor_denied=True,
            policy_adoption_denied=True,
            inferred_abort_denied=True,
            unknown_retained=True,
            healthy_policy2_sql="BLOCKED_BY_DESIGN_WHILE_UNKNOWN",
        )
        physical.majority_current("N-after-unknown-fresh-learner-repair")
        row["status"] = "OBSERVED"
        emit_n("OBSERVATION", row)
        return row
    except BaseException as error:
        row["status"] = (
            "N_SUPPORTED_SECURITY_FAIL"
            if any(term in str(error) for term in (
                "cleared genuine UNKNOWN", "UNKNOWN/Root/journal", "Root/journal",
                "old identity remains", "cluster ID changed", "not a voter",
            ))
            else "N_TEST_HARNESS_FAILURE"
        )
        row["failure_type"] = type(error).__name__
        emit_n("OBSERVATION", row)
        raise
    finally:
        broker.hook = lambda _: None


def run_sample(test, lab, broker, case, repetition):
    if case not in CASES or repetition not in REPETITIONS:
        raise AssertionError("N_TEST_HARNESS_FAILURE case/repetition outside frozen matrix")
    emit_n("FROZEN_SAMPLE", dict(case=case, repetition=repetition, specification=CASES[case]))
    if case == "N_PROGRESS_OLD_CLEAN_OPEN":
        return run_open_case(test, lab, broker, repetition)
    return run_unknown_case(test, lab, broker, repetition)


# N uses the one-shot, quarantine-hash-verified repair observer; parent L/M stay immutable.
from h_quorum.l_physical.n_recovery import repair_with_receipt as repair_with_receipt
