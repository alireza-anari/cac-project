ALTER TABLE catalog_lab.private_assistant
 ADD CONSTRAINT assistant_store_scope_fk FOREIGN KEY (tenant_id, store_id)
 REFERENCES foundation.store(tenant_id, id);

ALTER TABLE catalog_lab.private_assistant ENABLE ROW LEVEL SECURITY;
ALTER TABLE catalog_lab.private_assistant FORCE ROW LEVEL SECURITY;
REVOKE ALL ON catalog_lab.private_assistant FROM PUBLIC, cac_runtime, cac_provisioner, cac_catalog;
GRANT SELECT, INSERT ON catalog_lab.private_assistant TO cac_catalog;
GRANT UPDATE (display_name, greeting) ON catalog_lab.private_assistant TO cac_catalog;

CREATE POLICY assistant_read ON catalog_lab.private_assistant FOR SELECT TO cac_catalog
 USING (catalog_lab.allowed(tenant_id, store_id, false));
CREATE POLICY assistant_insert ON catalog_lab.private_assistant FOR INSERT TO cac_catalog
 WITH CHECK (catalog_lab.allowed(tenant_id, store_id, true));
CREATE POLICY assistant_update ON catalog_lab.private_assistant FOR UPDATE TO cac_catalog
 USING (catalog_lab.allowed(tenant_id, store_id, true))
 WITH CHECK (catalog_lab.allowed(tenant_id, store_id, true));
