-- W_ORACLE_ASSUMED. Test-first schema; operation API intentionally not implemented yet.
CREATE SCHEMA w AUTHORIZATION cac_w_guard;
SET LOCAL ROLE cac_w_guard;
CREATE TABLE w.control(singleton bool PRIMARY KEY CHECK(singleton),root uuid NOT NULL,namespace uuid NOT NULL,policy bigint NOT NULL,continuity bool NOT NULL,secret bytea NOT NULL);
CREATE TABLE w.actors(node text PRIMARY KEY,coord name UNIQUE NOT NULL,checker name UNIQUE NOT NULL,sid text NOT NULL,incarnation uuid NOT NULL,manifest text NOT NULL,admitted bool NOT NULL);
CREATE TABLE w.state(singleton bool PRIMARY KEY CHECK(singleton),epoch bigint NOT NULL,owner text,request uuid,phase text NOT NULL);
INSERT INTO w.state VALUES(true,0,NULL,NULL,'empty');
RESET ROLE;
GRANT USAGE ON SCHEMA w TO cac_w_a_coord,cac_w_b_coord,cac_w_a_check,cac_w_b_check;
