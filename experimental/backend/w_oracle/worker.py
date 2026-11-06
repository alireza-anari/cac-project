"""W_ORACLE_ASSUMED. Crash only disposable coordinator process, fixed exit77."""
import os
import sys
from w_oracle.lab import BANNER
from w_oracle.integration_lab import IntegrationLab
from w_oracle.broker import Broker

stage=sys.argv[1]
def hook(observed):
    if observed==stage:
        print(BANNER,'CRASH_CUT',stage,flush=True);os._exit(77)
lab=IntegrationLab();broker=Broker(lab,hook=hook)
with broker.runtime() as gate:
    gate.challenge();hook('after_first_use')
    if stage=='after_local_abort_before_close':raise ValueError('synthetic known abort')
raise SystemExit('Requested crash cut was not reached')
