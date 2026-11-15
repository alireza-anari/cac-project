"""S0-09N: instrument the existing consensus-governed fresh-identity replacement."""
import copy
import json
from pathlib import Path

from h_quorum.authority import Root
from h_quorum.common import BANNER


def repair_with_receipt(test, physical, old_id):
    """Remove the failed ID, add a fresh learner, verify catch-up, then promote once."""
    lab = physical.lab
    q = physical.q
    old_id = str(old_id)
    root_before = Root(lab.rootcfg).read(lab.namespace, True)
    physical.majority_current("N-immediately-before-quarantine-and-remove")

    old_member = copy.deepcopy(q.cfg["members"]["r4"])
    if str(old_member["id"]) != old_id:
        raise AssertionError("N configured old member identity changed before repair")
    if q._owned(old_member):
        raise AssertionError("N old native member is still running; replacement forbidden")
    old_data_dir = Path(old_member["data_dir"])
    old_files = physical.inventory(old_data_dir)
    old_cert, old_key = old_member["cert"], old_member["key"]

    before = q.etcd.call("/v3/cluster/member/list", {})["members"]
    before_by_id = {str(member["ID"]): member for member in before}
    test.assertEqual(len(before), 5, "N pre-repair membership is not the expected five members")
    test.assertIn(old_id, before_by_id)
    test.assertFalse(before_by_id[old_id].get("isLearner", False))
    for name in ("r1", "r2", "r3"):
        voter_id = str(q.cfg["members"][name]["id"])
        test.assertIn(voter_id, before_by_id)
        test.assertFalse(before_by_id[voter_id].get("isLearner", False))
    test.assertFalse(any(member.get("isLearner") for member in before),
                     "N sequential recovery requires no pre-existing learner")

    receipt = {
        "old_member_id": old_id,
        "old_process_absent": True,
        "old_data_dir_quarantined": False,
        "quarantine_hashes_match": False,
        "old_id_absent_before_add": False,
        "fresh_data_dir_absent_before_spawn": False,
        "fresh_identity_distinct": False,
        "fresh_certificate_distinct": False,
        "learner_observed_before_promotion": False,
        "current_log_catchup_verified": False,
        "server_accepted_promotion": False,
        "membership_calls": [],
        "membership_attempts": [],
        "promotion_attempts": 0,
    }

    original_call = q.etcd.call
    original_spawn = q._spawn
    original_promote = q.promote

    def traced_call(path, *args, **kwargs):
        tracked = path in (
            "/v3/cluster/member/remove",
            "/v3/cluster/member/add",
            "/v3/cluster/member/promote",
        )
        attempt = {"path": path, "outcome": "REQUESTED"} if tracked else None
        if attempt is not None:
            receipt["membership_attempts"].append(attempt)
        if path == "/v3/cluster/member/add" and not receipt["old_id_absent_before_add"]:
            if attempt is not None:
                attempt["outcome"] = "REJECTED_ORDER"
            raise AssertionError("N learner add attempted before old ID removal was verified")
        try:
            result = original_call(path, *args, **kwargs)
        except Exception as error:
            if attempt is not None:
                attempt["outcome"] = "ERROR"
                attempt["error_type"] = type(error).__name__
            raise
        if path == "/v3/cluster/member/remove":
            # A fresh authoritative membership read proves removal before add.
            members = original_call("/v3/cluster/member/list", {})["members"]
            if any(str(member["ID"]) == old_id for member in members):
                if attempt is not None:
                    attempt["outcome"] = "POSTCONDITION_FAILED"
                raise AssertionError("N old member ID remains after consensus remove")
            receipt["old_id_absent_before_add"] = True
        if attempt is not None:
            attempt["outcome"] = "COMMITTED_RESPONSE"
            receipt["membership_calls"].append(
                {"path": path, "response_keys": sorted(result.keys())}
            )
        return result

    def guarded_spawn(name, state="existing", initial=None):
        if name == "r4":
            member = q.cfg["members"][name]
            data_dir = Path(member["data_dir"])
            test.assertNotEqual(str(member["id"]), old_id, "N replacement reused old member ID")
            test.assertNotEqual(data_dir.resolve(), old_data_dir.resolve(),
                                "N replacement reused old data directory")
            test.assertFalse(data_dir.exists(),
                             "N fresh learner data directory was not absent before bootstrap")
            test.assertNotEqual(member["cert"], old_cert, "N replacement reused old certificate")
            test.assertNotEqual(member["key"], old_key, "N replacement reused old private key")
            test.assertTrue(Path(member["cert"]).is_file(), "N new peer certificate is missing")
            test.assertTrue(Path(member["key"]).is_file(), "N new peer private key is missing")
            receipt.update(
                fresh_data_dir_absent_before_spawn=True,
                fresh_identity_distinct=True,
                fresh_certificate_distinct=True,
                new_member_id=str(member["id"]),
                new_data_dir_is_distinct=True,
            )
        return original_spawn(name, state=state, initial=initial)

    def guarded_promote(name):
        member_id = str(q.cfg["members"][name]["id"])
        members = original_call("/v3/cluster/member/list", {})["members"]
        matches = [member for member in members if str(member["ID"]) == member_id]
        test.assertEqual(len(matches), 1, "N promotion target is not uniquely present")
        test.assertTrue(matches[0].get("isLearner", False),
                        "N promotion attempted after learner already became a voter")
        test.assertTrue(receipt["current_log_catchup_verified"],
                        "N promotion attempted before current Root/journal catch-up")
        # Exactly one promotion request; no retry loop around a destructive membership change.
        receipt["promotion_attempts"] += 1
        test.assertEqual(receipt["promotion_attempts"], 1,
                         "N attempted more than one learner promotion")
        result = original_promote(name)
        receipt["server_accepted_promotion"] = True
        return result

    q.etcd.call = traced_call
    q._spawn = guarded_spawn
    q.promote = guarded_promote
    try:
        # Reap the already failed child and prove its executable is absent.
        physical.stop()
        if q._owned(old_member):
            raise AssertionError("N old process survived stop proof; membership change forbidden")

        # Existing L consensus replacement: remove exact old ID, add one empty learner.
        fresh_id = str(q.replace("r4"))
        test.assertNotEqual(fresh_id, old_id)

        member_cfg = q.cfg["members"]["r4"]
        archives = [
            item for item in member_cfg.get("archives", [])
            if str(item.get("id")) == old_id
        ]
        test.assertTrue(archives, "N old native directory was not retained in quarantine")
        quarantine = Path(archives[-1]["data_dir"])
        test.assertTrue(quarantine.exists(), "N old member quarantine path is missing")
        test.assertFalse(old_data_dir.exists(), "N old data path was reused instead of quarantined")
        quarantine_files = physical.inventory(quarantine)
        test.assertEqual(quarantine_files, old_files,
                         "N quarantined old native WAL/snapshot/db hashes changed")
        receipt.update(
            old_data_dir_quarantined=True,
            quarantine_hashes_match=True,
            quarantine_file_count=len(quarantine_files),
        )

        after_add = q.etcd.call("/v3/cluster/member/list", {})["members"]
        after_add_by_id = {str(member["ID"]): member for member in after_add}
        test.assertNotIn(old_id, after_add_by_id)
        test.assertIn(fresh_id, after_add_by_id)
        test.assertTrue(after_add_by_id[fresh_id].get("isLearner", False),
                        "N replacement must remain a non-voting learner before catch-up")
        test.assertEqual(len(after_add), len(before),
                         "N membership count changed while replacing voter with learner")
        test.assertEqual(Root(lab.rootcfg).read(lab.namespace, True), root_before,
                         "N membership change altered application Root/journal")

        # Full local Root + ordered-journal catch-up is required before promotion.
        caught = physical.caught_up()
        test.assertEqual(str(caught["member"]), fresh_id)
        test.assertEqual(Root(lab.rootcfg).read(lab.namespace, True), root_before)
        learner_status = physical.status("N-fresh-learner-caught-up")
        receipt["learner_observed_before_promotion"] = True
        receipt["current_log_catchup_verified"] = True
        receipt["learner_status"] = learner_status
        physical.majority_current("N-fresh-learner-caught-up-before-promotion")

        # Promote once, only after the authenticated learner and current majority checks.
        q.promote("r4")
        after_promote = q.etcd.call("/v3/cluster/member/list", {})["members"]
        promoted = {str(member["ID"]): member for member in after_promote}
        test.assertNotIn(old_id, promoted)
        test.assertIn(fresh_id, promoted)
        test.assertFalse(promoted[fresh_id].get("isLearner", False))
        test.assertEqual(len(after_promote), 5)
        voters = [member for member in after_promote if not member.get("isLearner")]
        learners = [member for member in after_promote if member.get("isLearner")]
        test.assertEqual(len(voters), 5)
        test.assertEqual(len(learners), 0)
        test.assertEqual(Root(lab.rootcfg).read(lab.namespace, True), root_before,
                         "N promotion altered application Root/journal")
        physical.majority_current("N-after-explicit-fresh-learner-promotion")
    finally:
        q.etcd.call = original_call
        q._spawn = original_spawn
        q.promote = original_promote

    membership = original_call("/v3/cluster/member/list", {})
    members = membership.get("members", [])
    cluster_id = str(membership.get("header", {}).get("cluster_id"))
    new_id = str(q.cfg["members"]["r4"]["id"])
    voters = [member for member in members if not member.get("isLearner")]
    learners = [member for member in members if member.get("isLearner")]
    test.assertEqual(cluster_id, str(q.cfg["cluster_id"]), "N cluster ID changed during repair")
    test.assertEqual(len(members), 5)
    test.assertEqual(len(voters), 5)
    test.assertEqual(len(learners), 0)
    test.assertTrue(any(str(member["ID"]) == new_id for member in voters))
    test.assertFalse(any(str(member["ID"]) == old_id for member in members))
    for key in (
        "old_id_absent_before_add",
        "old_data_dir_quarantined",
        "quarantine_hashes_match",
        "fresh_data_dir_absent_before_spawn",
        "fresh_identity_distinct",
        "fresh_certificate_distinct",
        "learner_observed_before_promotion",
        "current_log_catchup_verified",
        "server_accepted_promotion",
    ):
        test.assertTrue(receipt[key], "N recovery receipt missing " + key)
    expected_attempt_order = [
        "/v3/cluster/member/remove",
        "/v3/cluster/member/add",
        "/v3/cluster/member/promote",
    ]
    actual_attempt_order = [item["path"] for item in receipt["membership_attempts"]]
    test.assertEqual(actual_attempt_order, expected_attempt_order,
                     "N membership operations retried or executed out of order")
    test.assertEqual(receipt["promotion_attempts"], 1,
                     "N promotion was not exactly one explicit request")
    receipt.update(
        new_member_id=new_id,
        cluster_id=cluster_id,
        total_members=len(members),
        voter_count=len(voters),
        learner_count=len(learners),
        old_member_absent=True,
        new_member_is_voter=True,
        original_majority_ids={name: str(member["id"]) for name, member in physical.majority.items()},
        root_unchanged=True,
        old_quarantine_hashes_match=True,
    )
    print(BANNER, "N RECOVERY", json.dumps(receipt, sort_keys=True), flush=True)
    return receipt
