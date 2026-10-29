ALTER TABLE foundation.membership ADD CONSTRAINT membership_store_scope_fk
 FOREIGN KEY (tenant_id,store_id) REFERENCES foundation.store(tenant_id,id);
ALTER TABLE foundation.scoped_grant ADD CONSTRAINT grant_store_scope_fk
 FOREIGN KEY (tenant_id,store_id) REFERENCES foundation.store(tenant_id,id);
ALTER TABLE foundation.scoped_grant ADD CONSTRAINT grant_membership_scope_fk
 FOREIGN KEY (tenant_id,store_id,membership_id) REFERENCES foundation.membership(tenant_id,store_id,id);

CREATE FUNCTION foundation.verified_context() RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = pg_catalog, cac_private
AS $function$
DECLARE token text; payload bytea; signature text; key bytea; claims jsonb;
BEGIN
 token := current_setting('cac.context',true);
 IF token IS NULL OR length(token)>4096 OR token !~ '^[0-9a-f]+\.[0-9a-f]{64}$' THEN
   RAISE EXCEPTION 'Invalid request context' USING ERRCODE='42501';
 END IF;
 payload := decode(split_part(token,'.',1),'hex');
 signature := split_part(token,'.',2);
 SELECT secret INTO STRICT key FROM cac_private.context_key WHERE singleton;
 IF signature <> encode(public.hmac(payload,key,'sha256'),'hex') THEN
   RAISE EXCEPTION 'Invalid request context' USING ERRCODE='42501';
 END IF;
 claims := convert_from(payload,'UTF8')::jsonb;
 -- All mandatory fields validated before policies cast/use them. Unknown fields ignored.
 IF claims->>'tenant' IS NULL OR claims->>'store' IS NULL OR claims->>'principal' IS NULL THEN
   RAISE EXCEPTION 'Invalid request context' USING ERRCODE='42501';
 END IF;
 PERFORM (claims->>'tenant')::uuid, (claims->>'store')::uuid, (claims->>'principal')::uuid;
 IF (claims->>'expires')::bigint IS NULL OR (claims->>'expires')::bigint < extract(epoch FROM statement_timestamp())
    OR (claims->>'expires')::bigint > extract(epoch FROM statement_timestamp())+300
    OR (claims->>'tx') IS DISTINCT FROM txid_current()::text
    OR (claims->>'pid')::integer IS DISTINCT FROM pg_backend_pid()
    OR session_user NOT IN ('cac_runtime','cac_provisioner')
    OR NOT COALESCE((session_user='cac_runtime' AND claims->>'purpose'='runtime')
         OR (session_user='cac_provisioner' AND claims->>'purpose'='provision'), false) THEN
   RAISE EXCEPTION 'Invalid request context' USING ERRCODE='42501';
 END IF;
 RETURN claims;
EXCEPTION WHEN OTHERS THEN
 RAISE EXCEPTION 'Invalid request context' USING ERRCODE='42501';
END
$function$;
REVOKE ALL ON FUNCTION foundation.verified_context() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION foundation.verified_context() TO cac_runtime,cac_provisioner;

ALTER TABLE foundation.tenant ENABLE ROW LEVEL SECURITY;
ALTER TABLE foundation.tenant FORCE ROW LEVEL SECURITY;
ALTER TABLE foundation.store ENABLE ROW LEVEL SECURITY;
ALTER TABLE foundation.store FORCE ROW LEVEL SECURITY;
ALTER TABLE foundation.membership ENABLE ROW LEVEL SECURITY;
ALTER TABLE foundation.membership FORCE ROW LEVEL SECURITY;
ALTER TABLE foundation.scoped_grant ENABLE ROW LEVEL SECURITY;
ALTER TABLE foundation.scoped_grant FORCE ROW LEVEL SECURITY;
REVOKE ALL ON foundation.tenant,foundation.store,foundation.membership,foundation.scoped_grant FROM PUBLIC,cac_runtime,cac_provisioner;
GRANT SELECT ON foundation.tenant,foundation.store,foundation.membership,foundation.scoped_grant TO cac_runtime,cac_provisioner;
GRANT INSERT ON foundation.tenant,foundation.store,foundation.membership,foundation.scoped_grant TO cac_provisioner;

CREATE POLICY member_read ON foundation.membership FOR SELECT TO cac_runtime,cac_provisioner USING (
 tenant_id=(foundation.verified_context()->>'tenant')::uuid
 AND store_id=(foundation.verified_context()->>'store')::uuid
 AND principal_id=(foundation.verified_context()->>'principal')::uuid AND active);
CREATE POLICY member_insert ON foundation.membership FOR INSERT TO cac_provisioner WITH CHECK (
 tenant_id=(foundation.verified_context()->>'tenant')::uuid
 AND store_id=(foundation.verified_context()->>'store')::uuid
 AND principal_id=(foundation.verified_context()->>'principal')::uuid AND active);
CREATE POLICY grant_read ON foundation.scoped_grant FOR SELECT TO cac_runtime,cac_provisioner USING (
 tenant_id=(foundation.verified_context()->>'tenant')::uuid
 AND store_id=(foundation.verified_context()->>'store')::uuid
 AND EXISTS (SELECT 1 FROM foundation.membership m WHERE m.id=membership_id AND m.tenant_id=scoped_grant.tenant_id AND m.store_id=scoped_grant.store_id));
CREATE POLICY grant_insert ON foundation.scoped_grant FOR INSERT TO cac_provisioner WITH CHECK (
 tenant_id=(foundation.verified_context()->>'tenant')::uuid
 AND store_id=(foundation.verified_context()->>'store')::uuid
 AND EXISTS (SELECT 1 FROM foundation.membership m WHERE m.id=membership_id AND m.tenant_id=scoped_grant.tenant_id AND m.store_id=scoped_grant.store_id));
CREATE POLICY store_runtime_read ON foundation.store FOR SELECT TO cac_runtime USING (
 tenant_id=(foundation.verified_context()->>'tenant')::uuid AND id=(foundation.verified_context()->>'store')::uuid
 AND EXISTS (SELECT 1 FROM foundation.scoped_grant g WHERE g.tenant_id=store.tenant_id AND g.store_id=store.id AND g.capability='store.view'));
CREATE POLICY tenant_runtime_read ON foundation.tenant FOR SELECT TO cac_runtime USING (
 id=(foundation.verified_context()->>'tenant')::uuid
 AND EXISTS (SELECT 1 FROM foundation.scoped_grant g WHERE g.tenant_id=tenant.id AND g.capability='store.view'));
CREATE POLICY store_provision_read ON foundation.store FOR SELECT TO cac_provisioner USING (
 tenant_id=(foundation.verified_context()->>'tenant')::uuid AND id=(foundation.verified_context()->>'store')::uuid);
CREATE POLICY store_insert ON foundation.store FOR INSERT TO cac_provisioner WITH CHECK (
 tenant_id=(foundation.verified_context()->>'tenant')::uuid AND id=(foundation.verified_context()->>'store')::uuid);
CREATE POLICY tenant_provision_read ON foundation.tenant FOR SELECT TO cac_provisioner USING (id=(foundation.verified_context()->>'tenant')::uuid);
CREATE POLICY tenant_insert ON foundation.tenant FOR INSERT TO cac_provisioner WITH CHECK (id=(foundation.verified_context()->>'tenant')::uuid);
