-- ONLY a fresh disposable cac_s007_test database. Never run on an existing product DB.
CREATE ROLE cac_owner LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS;
CREATE ROLE cac_runtime LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS;
CREATE ROLE cac_provisioner LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS;
REVOKE ALL ON DATABASE cac_s007_test FROM PUBLIC;
GRANT CONNECT ON DATABASE cac_s007_test TO cac_owner, cac_runtime, cac_provisioner;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO cac_owner;
CREATE EXTENSION pgcrypto WITH SCHEMA public;
CREATE SCHEMA foundation AUTHORIZATION cac_owner;
CREATE SCHEMA cac_private AUTHORIZATION cac_owner;
GRANT USAGE ON SCHEMA foundation TO cac_runtime,cac_provisioner;
CREATE TABLE cac_private.context_key (singleton boolean PRIMARY KEY CHECK (singleton), secret bytea NOT NULL);
ALTER TABLE cac_private.context_key OWNER TO cac_owner;
REVOKE ALL ON SCHEMA cac_private FROM PUBLIC,cac_runtime,cac_provisioner;
REVOKE ALL ON TABLE cac_private.context_key FROM PUBLIC,cac_runtime,cac_provisioner;
ALTER DEFAULT PRIVILEGES FOR ROLE cac_owner IN SCHEMA foundation REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
