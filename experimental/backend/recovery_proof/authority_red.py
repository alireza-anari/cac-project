"""Keep the fail-closed rollback assertion RED, not an approved recovery mode."""
from uuid import uuid4

from recovery_proof.authority_fixture import AuthorityFixture
from recovery_proof.authority_lab import dump_anchor, restore_anchor, authority_snapshot


class RollbackInvariant(AuthorityFixture):
    def test_anchor_rollback_must_not_revive_previous_owner(self):
        self.positive(self.a)
        old = dump_anchor(self.lab)
        self.restored_b()
        self.assertEqual(self.b.activate(1, str(uuid4()))['epoch'], 2)
        self.positive(self.b)
        self.assertFalse(self.a.ready())
        latest = dump_anchor(self.lab)
        before = authority_snapshot(self.lab)

        def restore_latest():
            restore_anchor(self.lab, latest)
            # Never include private snapshot values in assertion diagnostics.
            self.assertTrue(authority_snapshot(self.lab) == before,
                            'Current authority state/function/ACL restoration drift')
            self.assertFalse(self.a.ready())
            self.assertTrue(self.b.ready())
            print('S009D AUTHORITY ROLLBACK RESTORED latest epoch2/data/function/ACL/RLS state', flush=True)

        self.addCleanup(restore_latest)
        restore_anchor(self.lab, old)
        with self.lab.connect('C') as c:
            self.assertEqual(c.execute('SELECT epoch FROM anchor.state').fetchone(), (1,))
        revived = self.a.ready()
        if revived:
            self.positive(self.a)
        print('S009D SECURITY ROLLBACK WITNESS epoch2->1 old owner readiness',
              revived, 'new owner readiness', self.b.ready(), flush=True)
        self.assertFalse(revived, 'Rolled-back anchor revived previous-owner authority')
