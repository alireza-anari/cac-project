CREATE SCHEMA fence AUTHORIZATION cac_ctx_guard;
CREATE SCHEMA fence_private AUTHORIZATION cac_ctx_guard;
GRANT USAGE ON SCHEMA fence TO cac_ctx_runtime,cac_ctx_issuer,cac_fence_activator,cac_fence_ack;
SET LOCAL ROLE cac_ctx_guard;
CREATE TABLE fence_private.config(singleton bool PRIMARY KEY CHECK(singleton),instance uuid NOT NULL,cluster_sid text NOT NULL,anchor_sid text NOT NULL,anchor_conn text NOT NULL,ack_conn text NOT NULL,secret bytea NOT NULL CHECK(octet_length(secret)=32));
CREATE TABLE fence_private.state(singleton bool PRIMARY KEY CHECK(singleton),epoch bigint NOT NULL,generation uuid,request uuid,ready bool NOT NULL);
INSERT INTO fence_private.state VALUES(true,0,NULL,NULL,false);
CREATE FUNCTION fence.system_id() RETURNS text LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,fence_private AS $$ SELECT system_identifier::text FROM pg_control_system() $$;
CREATE FUNCTION fence_private.attest(mode_arg text,ep bigint,gen uuid,req uuid,ticket text DEFAULT '') RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,fence_private AS $$
DECLARE cfg fence_private.config;sid text;n text;answer text;b bytea;p jsonb;pid int;tx text;BEGIN
 SELECT * INTO STRICT cfg FROM fence_private.config;
 sid=fence.system_id();pid=pg_backend_pid();tx=txid_current()::text;
 IF cfg.cluster_sid<>sid OR ep IS NULL OR gen IS NULL OR req IS NULL THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 n=encode(public.gen_random_bytes(32),'hex');
 SELECT r INTO STRICT answer FROM public.dblink(cfg.anchor_conn,format('SELECT anchor.attest(%L,%L,%L,%L,%L::int,%L)',n,mode_arg,ticket,sid,pid,tx)) AS response(r text);
 IF answer IS NULL OR length(answer)>8000 OR answer!~'^[0-9a-f]+\.[0-9a-f]{64}$' THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 b=decode(split_part(answer,'.',1),'hex');p=convert_from(b,'UTF8')::jsonb;
 IF convert_to(p::text,'UTF8')<>b OR encode(public.hmac(b,cfg.secret,'sha256'),'hex')<>split_part(answer,'.',2) OR p->>'nonce' IS DISTINCT FROM n OR p->>'mode' IS DISTINCT FROM mode_arg OR p->>'instance' IS DISTINCT FROM cfg.instance::text OR p->>'epoch' IS DISTINCT FROM ep::text OR p->>'generation' IS DISTINCT FROM gen::text OR p->>'request' IS DISTINCT FROM req::text OR p->>'cluster_sid' IS DISTINCT FROM sid OR p->>'anchor_sid' IS DISTINCT FROM cfg.anchor_sid OR p->>'db_pid' IS DISTINCT FROM pid::text OR p->>'db_tx' IS DISTINCT FROM tx THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 IF mode_arg='guard' AND p->>'ticket' IS DISTINCT FROM encode(public.digest(ticket,'sha256'),'hex') THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 RETURN p;
EXCEPTION WHEN OTHERS THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END $$;
CREATE FUNCTION fence_private.bootstrap_ok() RETURNS bool LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,fence_private AS $$
 BEGIN RETURN (SELECT (SELECT count(*)=2 FROM pg_extension WHERE extname IN ('dblink','pgcrypto'))
 AND NOT has_function_privilege('cac_ctx_runtime','poc_private.verify_unfenced()','EXECUTE')
 AND NOT has_function_privilege('cac_ctx_issuer','poc_private.issue_unfenced(text,text,uuid,text,uuid,jsonb)','EXECUTE')
 AND (SELECT count(*)=3 FROM pg_proc WHERE oid IN ('poc.challenge()'::regprocedure,'poc.verify()'::regprocedure,'poc.issue(text,text,uuid,text,uuid,jsonb)'::regprocedure) AND prosecdef AND proowner='cac_ctx_guard'::regrole)); END $$;
CREATE FUNCTION fence_private.check_guard() RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,fence_private AS $$
DECLARE s fence_private.state;BEGIN
 SELECT * INTO STRICT s FROM fence_private.state;
 IF NOT s.ready OR NOT fence_private.bootstrap_ok() OR s.generation IS DISTINCT FROM (SELECT generation FROM poc_private.config) THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 PERFORM fence_private.attest('guard',s.epoch,s.generation,s.request,current_setting('cac.fence_ticket',true));
END $$;
CREATE FUNCTION fence.is_ready() RETURNS bool LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,fence_private AS $$
DECLARE s fence_private.state;BEGIN
 SELECT * INTO STRICT s FROM fence_private.state;
 IF NOT s.ready OR NOT fence_private.bootstrap_ok() OR s.generation IS DISTINCT FROM (SELECT generation FROM poc_private.config) THEN RETURN false;END IF;
 PERFORM fence_private.attest('active',s.epoch,s.generation,s.request);RETURN true;
EXCEPTION WHEN OTHERS THEN RETURN false;END $$;
CREATE FUNCTION fence.apply(ep bigint,gen uuid,req uuid) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,fence_private AS $$
BEGIN
 IF session_user<>'cac_fence_activator' OR NOT fence_private.bootstrap_ok() THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 PERFORM 1 FROM fence_private.state FOR UPDATE;
 PERFORM fence_private.attest('apply',ep,gen,req);
 UPDATE poc_private.config SET generation=gen;
 UPDATE fence_private.state SET epoch=ep,generation=gen,request=req,ready=false;
END $$;
CREATE FUNCTION fence.committed_state() RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,fence_private AS $$
DECLARE s fence_private.state;cfg fence_private.config;BEGIN
 SELECT * INTO STRICT s FROM fence_private.state;SELECT * INTO STRICT cfg FROM fence_private.config;
 IF session_user<>'cac_fence_ack' OR cfg.cluster_sid<>fence.system_id() OR s.epoch<=0 OR s.generation IS DISTINCT FROM (SELECT generation FROM poc_private.config) OR NOT fence_private.bootstrap_ok() THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 RETURN jsonb_build_object('kind','committed_ack','instance',cfg.instance,'cluster_sid',fence.system_id(),'epoch',s.epoch,'generation',s.generation,'request',s.request);
END $$;
CREATE FUNCTION fence.ack(ep bigint,req uuid) RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,fence_private AS $$
DECLARE cfg fence_private.config;p jsonb;b bytea;BEGIN
 IF session_user<>'cac_fence_activator' THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 SELECT * INTO STRICT cfg FROM fence_private.config;
 -- This fresh loopback connection can only see committed state, even if caller
 -- invokes ACK inside the same transaction as an uncommitted apply.
 SELECT r INTO STRICT p FROM public.dblink(cfg.ack_conn,'SELECT fence.committed_state()') AS response(r jsonb);
 IF p->>'epoch' IS DISTINCT FROM ep::text OR p->>'request' IS DISTINCT FROM req::text OR p->>'instance' IS DISTINCT FROM cfg.instance::text OR p->>'cluster_sid' IS DISTINCT FROM fence.system_id() THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 b=convert_to(p::text,'UTF8');RETURN encode(b,'hex')||'.'||encode(public.hmac(b,cfg.secret,'sha256'),'hex');
EXCEPTION WHEN OTHERS THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END $$;
CREATE FUNCTION fence.mark_ready() RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,fence_private AS $$
DECLARE s fence_private.state;BEGIN
 IF session_user<>'cac_fence_activator' OR NOT fence_private.bootstrap_ok() THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 SELECT * INTO STRICT s FROM fence_private.state FOR UPDATE;
 PERFORM fence_private.attest('active',s.epoch,s.generation,s.request);
 UPDATE fence_private.state SET ready=true;
END $$;
RESET ROLE;
ALTER FUNCTION poc.challenge() SET SCHEMA poc_private;
ALTER FUNCTION poc_private.challenge() RENAME TO challenge_unfenced;
ALTER FUNCTION poc.issue(text,text,uuid,text,uuid,jsonb) SET SCHEMA poc_private;
ALTER FUNCTION poc_private.issue(text,text,uuid,text,uuid,jsonb) RENAME TO issue_unfenced;
ALTER FUNCTION poc.verify() SET SCHEMA poc_private;
ALTER FUNCTION poc_private.verify() RENAME TO verify_unfenced;
REVOKE ALL ON FUNCTION poc_private.challenge_unfenced(),poc_private.verify_unfenced() FROM cac_ctx_runtime;
REVOKE ALL ON FUNCTION poc_private.issue_unfenced(text,text,uuid,text,uuid,jsonb) FROM cac_ctx_issuer;
CREATE FUNCTION poc.challenge() RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,poc_private,fence_private AS $$
DECLARE r text;BEGIN PERFORM fence_private.check_guard();r=poc_private.challenge_unfenced();PERFORM fence_private.check_guard();RETURN r;END $$;
CREATE FUNCTION poc.issue(h text,proof text,store_arg uuid,action_arg text,target_arg uuid,body_arg jsonb) RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,poc_private,fence_private AS $$
DECLARE r text;BEGIN PERFORM fence_private.check_guard();r=poc_private.issue_unfenced(h,proof,store_arg,action_arg,target_arg,body_arg);PERFORM fence_private.check_guard();RETURN r;END $$;
CREATE FUNCTION poc.verify() RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,poc_private,fence_private AS $$
DECLARE r jsonb;BEGIN PERFORM fence_private.check_guard();r=poc_private.verify_unfenced();PERFORM fence_private.check_guard();RETURN r;END $$;
ALTER FUNCTION poc.challenge() OWNER TO cac_ctx_guard;
ALTER FUNCTION poc.issue(text,text,uuid,text,uuid,jsonb) OWNER TO cac_ctx_guard;
ALTER FUNCTION poc.verify() OWNER TO cac_ctx_guard;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA fence,fence_private FROM PUBLIC;
REVOKE ALL ON FUNCTION poc.challenge(),poc.issue(text,text,uuid,text,uuid,jsonb),poc.verify() FROM PUBLIC;
RESET ROLE;
GRANT EXECUTE ON FUNCTION poc.challenge(),poc.verify() TO cac_ctx_runtime;
GRANT EXECUTE ON FUNCTION poc.issue(text,text,uuid,text,uuid,jsonb) TO cac_ctx_issuer;
GRANT EXECUTE ON FUNCTION fence.system_id(),fence.is_ready() TO cac_ctx_runtime,cac_ctx_issuer,cac_fence_activator;
GRANT EXECUTE ON FUNCTION fence.apply(bigint,uuid,uuid),fence.ack(bigint,uuid),fence.mark_ready() TO cac_fence_activator;
GRANT EXECUTE ON FUNCTION fence.committed_state() TO cac_fence_ack;
