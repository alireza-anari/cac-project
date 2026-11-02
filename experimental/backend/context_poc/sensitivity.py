"""Synthetic adversarial controls must fail when deliberately weakened, then restore."""
import os
import subprocess
import sys
from context_poc.harness import CFG,connect
if os.environ.get('CAC_EXPERIMENTAL_DISPOSABLE')!='1' or CFG['connection']['dbname']!='cac_s007_test':raise SystemExit('Disposable only')
mutations=[
 ('poc.issue(text,text,uuid,text,uuid,jsonb)',"h=poc_private.unpack(challenge_arg,'challenge');", "DELETE FROM poc_private.ledger; h=poc_private.unpack(challenge_arg,'challenge');", 'test_savepoint_ledger_survives'),
 ('poc_private.unpack(text,text)',"encode(public.hmac(b,k,'sha256'),'hex')<>split_part(token,'.',2)",'false','test_challenge_forgery_and_revocation'),
 ('poc.issue(text,text,uuid,text,uuid,jsonb)',"s.mfa<clock_timestamp()-interval '5 minutes'",'false','test_stale_mfa_denied')]
for name,old,new,test in mutations:
 with connect('postgres') as c:definition=c.execute('SELECT pg_get_functiondef(%s::regprocedure)',(name,)).fetchone()[0]
 assert old in definition, 'Mutation must match actual code'
 try:
  with connect('postgres') as c:c.execute(definition.replace(old,new))
  run=subprocess.run([sys.executable,'-m','unittest','context_poc.tests.test_context.ContextTests.'+test,'-v'],capture_output=True,text=True)
  print(run.stdout+run.stderr,flush=True)
  assert run.returncode==1 and 'FAIL:' in run.stderr and 'ERROR:' not in run.stderr, test
  print('POC EXPECTED RED:',test,'exit1; weakened control detected',flush=True)
 finally:
  with connect('postgres') as c:c.execute(definition)
print('POC controls restored; complete green suite required')
