"""Q_SURVIVAL_ONLY. External disposable admission starts with committed denial."""
import time
from recovery_fencing.lab import Lab
from h_quorum.common import BANNER

class IntegrationLab:
    def __init__(self):self.parent=Lab();self.cfg=self.parent.cfg
    def connect(self,node='A',role='postgres'):return self.parent.connect(node,role)
    def quarantine(self,node):
        with self.connect(node) as c:c.execute('ALTER ROLE cac_ctx_runtime NOLOGIN;ALTER ROLE cac_ctx_issuer NOLOGIN')
        with self.connect(node) as c:
            c.autocommit=True;deadline=time.monotonic()+5
            while True:
                rows=c.execute("SELECT pid FROM pg_stat_activity WHERE usename IN ('cac_ctx_runtime','cac_ctx_issuer')").fetchall()
                if not rows:break
                for (pid,) in rows:c.execute('SELECT pg_terminate_backend(%s,1000)',(pid,))
                if time.monotonic()>deadline:raise AssertionError('Quarantine drain incomplete')
        print(BANNER,'QUARANTINE',node,'committed NOLOGIN and zero observed live app sessions',flush=True)
    def reset(self):
        for node in ('A','B'):self.quarantine(node)
        self.parent.reset()
        # Test-first preflight: absence never enables LOGIN or data scope.
        return False
    def close(self):self.parent.close()
