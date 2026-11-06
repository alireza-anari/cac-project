"""W_ORACLE_ASSUMED. Intended assertion RED, exact restore, same probe GREEN."""
import contextlib
import hashlib
import json
import re
import unittest

from w_oracle.lab import BANNER
from w_oracle.tests.test_oracle import OracleContractTests
from w_oracle.tests.test_integration import IntegrationTests


CASES={
 'W_CAS':(OracleContractTests,'test_initial_activation_and_stale_cas_denial','w.reserve(bigint,uuid)','expected<>s.epoch OR ',''),
 'W_OPEN':(OracleContractTests,'test_orphan_open_blocks_takeover_after_disconnect','w.reserve(bigint,uuid)'," OR EXISTS(SELECT 1 FROM w.ops WHERE phase IN ('open','unknown'))",''),
 'W_SQL_ENFORCEMENT':(IntegrationTests,'test_current_w_blocks_old_owner_after_real_c_rollback','w_guard.require(text,text)',None,None),
}

def connect(lab,kind):return lab.connect('A') if kind=='W_SQL_ENFORCEMENT' else lab.connect()

def catalog(lab,kind,signature):
    with connect(lab,kind) as c:
        return c.execute('SELECT pg_get_functiondef(oid),proacl::text,proowner::regrole::text,prosecdef,proconfig FROM pg_proc WHERE oid=%s::regprocedure',(signature,)).fetchone()

@contextlib.contextmanager
def weaken(lab,kind):
    _,_,signature,needle,replacement=CASES[kind];before=catalog(lab,kind,signature)
    definition=before[0]
    if needle is not None:
        assert definition.count(needle)==1,'Mutation site drift'
        mutant=definition.replace(needle,replacement,1)
    else:
        mutant,count=re.subn(r'AS \$function\$.*\$function\$',r'AS $function$BEGIN NULL;END$function$',definition,flags=re.S)
        assert count==1,'SQL guard body mutation site drift'
    try:
        with connect(lab,kind) as c:c.execute(mutant)
        assert catalog(lab,kind,signature)[0]!=definition,'Mutation not installed'
        yield
    finally:
        with connect(lab,kind) as c:c.execute(definition)
        assert catalog(lab,kind,signature)==before,'Mutation restoration drift'
        print(BANNER,'EXACT RESTORE',kind,'definition/owner/ACL/SECURITY DEFINER/search_path',
              hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest(),flush=True)

def probe(cls,method):
    return unittest.TextTestRunner(verbosity=2,failfast=True).run(unittest.TestSuite([cls(method)]))

if __name__=='__main__':
    print(BANNER,flush=True)
    for kind,(base,method,_,_,_) in CASES.items():
        def install(case,kind=kind):
            context=weaken(case.lab,kind);context.__enter__()
            case.addCleanup(context.__exit__,None,None,None)
        if kind=='W_SQL_ENFORCEMENT':
            mutant=type('InjectedWEnforcement',(base,),{'after_c_rollback':install})
        else:
            def setup(case,base=base,install=install):
                base.setUp(case);install(case)
            mutant=type('Injected'+kind,(base,),{'setUp':setup})
        result=probe(mutant,method)
        expected='Rolled-back anchor revived previous-owner authority' if kind=='W_SQL_ENFORCEMENT' else 'InsufficientPrivilege not raised'
        assert result.testsRun==1 and len(result.failures)==1 and not result.errors and not result.skipped,'Not intended one-assertion security RED'
        assert expected in result.failures[0][1],'Wrong RED assertion'
        print(BANNER,'EXPECTED_MUTATION_RED',kind,method,'one assertion failure; zero errors/skips',flush=True)
        restored=probe(base,method)
        assert restored.wasSuccessful() and not restored.skipped,'Restored probe not GREEN'
        print(BANNER,'RESTORED GREEN',kind,method,flush=True)
