-- W_ORACLE_ASSUMED. Disposable rollback, always under external quarantine.
DROP FUNCTION fence_private.check_guard(),fence.is_ready(),poc.issue(text,text,uuid,text,uuid,jsonb),poc.verify();
ALTER FUNCTION fence_private.check_guard_c() RENAME TO check_guard;
ALTER FUNCTION w_guard.c_is_ready() RENAME TO is_ready;
ALTER FUNCTION w_guard.is_ready() SET SCHEMA fence;
ALTER FUNCTION w_guard.issue_c(text,text,uuid,text,uuid,jsonb) RENAME TO issue;
ALTER FUNCTION w_guard.issue(text,text,uuid,text,uuid,jsonb) SET SCHEMA poc;
ALTER FUNCTION w_guard.verify_c() RENAME TO verify;
ALTER FUNCTION w_guard.verify() SET SCHEMA poc;
GRANT EXECUTE ON FUNCTION fence.is_ready() TO cac_ctx_runtime,cac_ctx_issuer,cac_fence_activator;
GRANT EXECUTE ON FUNCTION poc.issue(text,text,uuid,text,uuid,jsonb) TO cac_ctx_issuer;
GRANT EXECUTE ON FUNCTION poc.verify() TO cac_ctx_runtime;
DROP SCHEMA w_guard CASCADE;
