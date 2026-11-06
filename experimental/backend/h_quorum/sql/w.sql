-- Q_SURVIVAL_ONLY. W stores public replay only, never Root tickets/keys or authority.
CREATE SCHEMA h_w AUTHORIZATION cac_anchor_guard;
SET LOCAL ROLE cac_anchor_guard;
CREATE TABLE h_w.cache(namespace uuid PRIMARY KEY,seq bigint NOT NULL CHECK(seq>=0),head text NOT NULL,body text NOT NULL);
CREATE TABLE h_w.journal(namespace uuid NOT NULL,seq bigint NOT NULL CHECK(seq>=0),entry_hash text NOT NULL CHECK(entry_hash~'^[0-9a-f]{64}$'),PRIMARY KEY(namespace,seq));
CREATE FUNCTION h_w.status(ns uuid) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,h_w AS $$
DECLARE r h_w.cache;p jsonb;j text;n bigint;sid text;BEGIN
 IF session_user NOT IN ('cac_anchor_a','cac_anchor_b') THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 SELECT * INTO STRICT r FROM h_w.cache WHERE namespace=ns;
 p=r.body::jsonb;
 SELECT count(*),encode(public.digest(coalesce(string_agg(entry_hash,E'\n' ORDER BY seq),''),'sha256'),'hex') INTO n,j FROM h_w.journal WHERE namespace=ns AND seq<=r.seq;
 SELECT system_identifier::text INTO sid FROM pg_control_system();
 RETURN jsonb_build_object('root_id',p->>'root_id','namespace',ns,'seq',r.seq,'head',r.head,'state_hash',encode(public.digest(r.body,'sha256'),'hex'),'journal_hash',j,'count',n,'wsid',sid);
END $$;
REVOKE ALL ON ALL TABLES IN SCHEMA h_w FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA h_w FROM PUBLIC;
RESET ROLE;
GRANT USAGE ON SCHEMA h_w TO cac_anchor_a,cac_anchor_b;
GRANT EXECUTE ON FUNCTION h_w.status(uuid) TO cac_anchor_a,cac_anchor_b;
