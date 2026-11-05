"""Disposable SQL fault injection, with exact catalog restoration in finally."""
import contextlib
import hashlib
import json

from recovery_fencing.lab import require

MUTATIONS = {
    'cas': ('C', 'anchor.reserve(bigint,uuid)', 's.epoch<>expected OR ', ''),
    'sql_fence': (
        'A', 'fence_private.check_guard()',
        "PERFORM fence_private.attest('guard',s.epoch,s.generation,s.request,current_setting('cac.fence_ticket',true));",
        'NULL;'),
    'open': (
        'C', 'anchor.reserve(bigint,uuid)',
        " OR EXISTS(SELECT 1 FROM anchor.operations WHERE phase='open')", ''),
}


def catalog(lab, node, signature):
    with lab.connect(node) as c:
        return c.execute(
            "SELECT pg_get_functiondef(oid),proacl::text,proowner::regrole::text,"
            "prosecdef,proconfig FROM pg_proc WHERE oid=%s::regprocedure",
            (signature,)).fetchone()


@contextlib.contextmanager
def weaken(lab, kind):
    require()
    node, signature, needle, replacement = MUTATIONS[kind]
    before = catalog(lab, node, signature)
    assert before is not None
    definition = before[0]
    assert definition.count(needle) == 1, 'Mutation site drift'
    try:
        with lab.connect(node) as c:
            c.execute(definition.replace(needle, replacement, 1))
        assert catalog(lab, node, signature)[0] != definition
        yield
    finally:
        # Do not rely on the next fixture reset to remove a security mutation.
        with lab.connect(node) as c:
            c.execute(definition)
        assert catalog(lab, node, signature) == before, 'Mutation restoration drift'
        digest = hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest()
        print('S009D RESTORED', kind, 'definition/owner/ACL/SECURITY DEFINER/settings', digest, flush=True)
