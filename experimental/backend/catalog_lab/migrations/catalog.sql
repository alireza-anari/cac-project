ALTER TABLE catalog_lab.product
 ADD CONSTRAINT product_store_scope_fk FOREIGN KEY (tenant_id, store_id)
 REFERENCES foundation.store(tenant_id, id);
CREATE TABLE cac_private.catalog_key (
 singleton boolean PRIMARY KEY CHECK (singleton),
 secret bytea NOT NULL CHECK (octet_length(secret) = 32)
);
REVOKE ALL ON cac_private.catalog_key FROM PUBLIC, cac_catalog;
REVOKE ALL ON SCHEMA catalog_lab FROM PUBLIC;
GRANT USAGE ON SCHEMA catalog_lab TO cac_catalog;

CREATE FUNCTION catalog_lab.allowed(row_tenant uuid, row_store uuid, write_required boolean)
RETURNS boolean LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = pg_catalog
AS $$
DECLARE
 token text := current_setting('cac.catalog_context', true);
 payload bytea;
 key bytea;
 claims jsonb;
 expires bigint;
 now_epoch numeric := extract(epoch FROM statement_timestamp());
BEGIN
 IF session_user <> 'cac_catalog' OR token IS NULL OR length(token) > 4096
    OR token !~ '^[0-9a-f]+\.[0-9a-f]{64}$' THEN
   RAISE EXCEPTION 'Invalid catalog context' USING ERRCODE = '42501';
 END IF;
 payload := decode(split_part(token,'.',1),'hex');
 SELECT secret INTO STRICT key FROM cac_private.catalog_key WHERE singleton;
 IF split_part(token,'.',2) <> encode(public.hmac(payload,key,'sha256'),'hex') THEN
   RAISE EXCEPTION 'Invalid catalog context' USING ERRCODE = '42501';
 END IF;
 claims := convert_from(payload,'UTF8')::jsonb;
 IF jsonb_typeof(claims) IS DISTINCT FROM 'object'
    OR claims->>'purpose' IS DISTINCT FROM 'cac.catalog.lab.v1'
    OR NOT coalesce(claims->>'scope' IN ('read','manage'),false)
    OR jsonb_typeof(claims->'principal') IS DISTINCT FROM 'string'
    OR jsonb_typeof(claims->'tenant') IS DISTINCT FROM 'string'
    OR jsonb_typeof(claims->'store') IS DISTINCT FROM 'string'
    OR jsonb_typeof(claims->'expires') IS DISTINCT FROM 'number'
    OR claims->>'tx' IS DISTINCT FROM txid_current()::text
    OR claims->'pid' IS DISTINCT FROM to_jsonb(pg_backend_pid()) THEN
   RAISE EXCEPTION 'Invalid catalog context' USING ERRCODE = '42501';
 END IF;
 PERFORM (claims->>'principal')::uuid;
 expires := (claims->>'expires')::bigint;
 IF expires < now_epoch OR expires > now_epoch + 60 THEN
   RAISE EXCEPTION 'Invalid catalog context' USING ERRCODE = '42501';
 END IF;
 RETURN row_tenant = (claims->>'tenant')::uuid AND row_store = (claims->>'store')::uuid
   AND (NOT write_required OR claims->>'scope' = 'manage');
EXCEPTION WHEN OTHERS THEN
 RAISE EXCEPTION 'Invalid catalog context' USING ERRCODE = '42501';
END;
$$;

REVOKE ALL ON FUNCTION catalog_lab.allowed(uuid, uuid, boolean) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION catalog_lab.allowed(uuid, uuid, boolean) TO cac_catalog;
ALTER TABLE catalog_lab.product ENABLE ROW LEVEL SECURITY;
ALTER TABLE catalog_lab.product FORCE ROW LEVEL SECURITY;
REVOKE ALL ON catalog_lab.product FROM PUBLIC, cac_runtime, cac_provisioner, cac_catalog;
GRANT SELECT, INSERT, DELETE ON catalog_lab.product TO cac_catalog;
GRANT UPDATE (sku, name) ON catalog_lab.product TO cac_catalog;

CREATE POLICY product_read ON catalog_lab.product FOR SELECT TO cac_catalog
 USING (catalog_lab.allowed(tenant_id, store_id, false));
CREATE POLICY product_insert ON catalog_lab.product FOR INSERT TO cac_catalog
 WITH CHECK (catalog_lab.allowed(tenant_id, store_id, true));
CREATE POLICY product_update ON catalog_lab.product FOR UPDATE TO cac_catalog
 USING (catalog_lab.allowed(tenant_id, store_id, true))
 WITH CHECK (catalog_lab.allowed(tenant_id, store_id, true));
CREATE POLICY product_delete ON catalog_lab.product FOR DELETE TO cac_catalog
 USING (catalog_lab.allowed(tenant_id, store_id, true));

