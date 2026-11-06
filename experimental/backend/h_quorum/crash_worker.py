"""Q_SURVIVAL_ONLY. Owned disposable PG worker: real SIGKILL, no exception cleanup."""
import json
import os
import signal
import sys
from recovery_fencing.lab import S1
from h_quorum.broker import Broker
from h_quorum.integration_lab import IntegrationLab
from h_quorum.common import BANNER

def main():
    request=json.load(sys.stdin);lab=IntegrationLab();lab.namespace=request['namespace'];lab.actors=request['actors']
    broker=Broker(lab);body={'body':'synthetic-crash-commit'};phase='runtime'
    gate=broker.runtime(action='probe',body=body)
    def hook(label):
        if phase=='runtime' and label==request['cut']:
            print(BANNER,'ACTUAL WORKER SIGKILL',label,'pid',gate.pid,'fullxid',gate.tx,'PG SID',gate.sid,flush=True)
            os.kill(os.getpid(),signal.SIGKILL)
    broker.hook=hook
    with gate as g:
        phase='issuer';token=broker.issue(g.challenge(),action='probe',body=body);phase='runtime'
        g.install(token)
        if g.records()!=[S1]:raise AssertionError('Worker scope not established')
        if g.c.execute('UPDATE poc.records SET body=%s WHERE store=%s',(body['body'],S1)).rowcount!=1:raise AssertionError('Worker protected write absent')
        if request.get('abort'):raise ValueError('synthetic exact abort')
    raise AssertionError('Requested actual crash cut was not reached')

if __name__=='__main__':main()
