-- Q_SURVIVAL_ONLY. Only under external committed NOLOGIN and verified drain.
DROP POLICY scoped_write ON poc.records;
REVOKE UPDATE(body) ON poc.records FROM cac_ctx_runtime;
ALTER POLICY scoped_read ON poc.records USING(store=poc.read_scope());
DROP FUNCTION fence_private.check_guard(),fence.is_ready(),poc.issue(text,text,uuid,text,uuid,jsonb),poc.verify();
ALTER FUNCTION fence_private.check_guard_c() RENAME TO check_guard;
ALTER FUNCTION h_guard.c_is_ready() RENAME TO is_ready;
ALTER FUNCTION h_guard.is_ready() SET SCHEMA fence;
ALTER FUNCTION h_guard.issue_c(text,text,uuid,text,uuid,jsonb) RENAME TO issue;
ALTER FUNCTION h_guard.issue(text,text,uuid,text,uuid,jsonb) SET SCHEMA poc;
ALTER FUNCTION h_guard.verify_c() RENAME TO verify;
ALTER FUNCTION h_guard.verify() SET SCHEMA poc;
GRANT EXECUTE ON FUNCTION fence.is_ready() TO cac_ctx_runtime,cac_ctx_issuer,cac_fence_activator;
GRANT EXECUTE ON FUNCTION poc.issue(text,text,uuid,text,uuid,jsonb) TO cac_ctx_issuer;
GRANT EXECUTE ON FUNCTION poc.verify() TO cac_ctx_runtime;
DROP SCHEMA h_guard CASCADE;
