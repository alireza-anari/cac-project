-- W_ORACLE_ASSUMED. Deny-only overlay. No W signing key or coordinator login here.
CREATE SCHEMA w_guard AUTHORIZATION cac_ctx_guard;
GRANT USAGE ON SCHEMA w_guard TO cac_ctx_runtime,cac_ctx_issuer,cac_fence_activator;
SET LOCAL ROLE cac_ctx_guard;
CREATE TABLE w_guard.config(singleton bool PRIMARY KEY CHECK(singleton),root uuid NOT NULL,namespace uuid NOT NULL,policy bigint NOT NULL,node text NOT NULL,incarnation uuid NOT NULL,epoch bigint NOT NULL,checker_conn text NOT NULL);
CREATE FUNCTION w_guard.runtime_digest(store_arg uuid) RETURNS text LANGUAGE sql IMMUTABLE SECURITY DEFINER SET search_path=pg_catalog AS $$
 SELECT encode(public.digest(jsonb_build_object('domain','cac-s009f-runtime','store',store_arg,'action','read')::text,'sha256'),'hex')
$$;
CREATE FUNCTION w_guard.issuer_digest(h text,proof text,st uuid,act text,target uuid,body jsonb) RETURNS text LANGUAGE sql IMMUTABLE SECURITY DEFINER SET search_path=pg_catalog AS $$
 SELECT encode(public.digest(jsonb_build_object('domain','cac-s009f-issuer','challenge',h,'proof_hash',encode(public.digest(proof,'sha256'),'hex'),'store',st,'action',act,'target',target,'body',body)::text,'sha256'),'hex')
$$;
-- Controller injects its independently held query as the function body below.
-- MEASUREMENT_FUNCTION
CREATE FUNCTION w_guard.require(mode_arg text DEFAULT 'guard',digest_arg text DEFAULT NULL) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,w_guard AS $$
DECLARE cfg w_guard.config;nonce text;sid text;pid int;tx text;man text;intent text;t text;answer text;good bool;p jsonb;BEGIN
 SELECT * INTO STRICT cfg FROM w_guard.config;
 man=w_guard.measure();sid=fence.system_id();pid=pg_backend_pid();tx=txid_current()::text;
 intent=coalesce(digest_arg,current_setting('cac.w_intent',true),'');
 t=coalesce(current_setting('cac.w_ticket',true),'');nonce=encode(public.gen_random_bytes(32),'hex');
 SELECT r INTO STRICT answer FROM public.dblink(cfg.checker_conn,format('SELECT w.attest(%L,%L,%L,%L,%L::int,%L,%L,%L,%L)',nonce,mode_arg,t,sid,pid,tx,man,intent,session_user)) AS response(r text);
 IF answer IS NULL OR length(answer)>8000 OR answer!~'^[0-9a-f]+\.[0-9a-f]{64}$' THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 p=convert_from(decode(split_part(answer,'.',1),'hex'),'UTF8')::jsonb;
 IF p->>'v' IS DISTINCT FROM '1' OR p->>'domain' IS DISTINCT FROM 'cac-s009f-assumed' OR p->>'root' IS DISTINCT FROM cfg.root::text OR p->>'namespace' IS DISTINCT FROM cfg.namespace::text OR p->>'policy' IS DISTINCT FROM cfg.policy::text OR p->>'owner' IS DISTINCT FROM cfg.node OR p->>'incarnation' IS DISTINCT FROM cfg.incarnation::text OR p->>'epoch' IS DISTINCT FROM cfg.epoch::text OR p->>'nonce' IS DISTINCT FROM nonce OR p->>'mode' IS DISTINCT FROM mode_arg OR p->>'sid' IS DISTINCT FROM sid OR p->>'pid' IS DISTINCT FROM pid::text OR p->>'tx' IS DISTINCT FROM tx OR p->>'manifest' IS DISTINCT FROM man OR p->>'login' IS DISTINCT FROM session_user THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 IF mode_arg='guard' AND (p->>'digest' IS DISTINCT FROM intent OR p->>'ticket_hash' IS DISTINCT FROM encode(public.digest(t,'sha256'),'hex') OR p->>'kind' IS DISTINCT FROM (CASE session_user WHEN 'cac_ctx_runtime' THEN 'runtime' WHEN 'cac_ctx_issuer' THEN 'issuer' END)) THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 -- The W return channel and W root are assumed. Reverification stays online in W.
 SELECT r INTO STRICT good FROM public.dblink(cfg.checker_conn,format('SELECT w.verify(%L,%L,%L,%L,%L,%L::int,%L,%L,%L,%L)',answer,nonce,mode_arg,t,sid,pid,tx,man,intent,session_user)) AS response(r bool);
 IF good IS DISTINCT FROM true THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
EXCEPTION WHEN OTHERS THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END $$;
CREATE FUNCTION w_guard.set_epoch(ep bigint) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,w_guard AS $$
DECLARE cfg w_guard.config;s jsonb;BEGIN
 IF session_user<>'cac_fence_activator' THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 SELECT * INTO STRICT cfg FROM w_guard.config;
 SELECT r INTO STRICT s FROM public.dblink(cfg.checker_conn,'SELECT w.status()') AS response(r jsonb);
 IF ep IS NULL OR s->>'epoch' IS DISTINCT FROM ep::text OR s->>'owner' IS DISTINCT FROM cfg.node OR s->>'phase' IS DISTINCT FROM 'reserved' OR s->>'root' IS DISTINCT FROM cfg.root::text OR s->>'namespace' IS DISTINCT FROM cfg.namespace::text OR s->>'policy' IS DISTINCT FROM cfg.policy::text OR s->>'incarnation' IS DISTINCT FROM cfg.incarnation::text OR s->>'manifest' IS DISTINCT FROM w_guard.measure() THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 UPDATE w_guard.config SET epoch=ep;
END $$;
CREATE FUNCTION w_guard.final_check() RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
BEGIN PERFORM w_guard.require();END $$;
RESET ROLE;
ALTER FUNCTION fence_private.check_guard() RENAME TO check_guard_c;
ALTER FUNCTION fence.is_ready() SET SCHEMA w_guard;
ALTER FUNCTION w_guard.is_ready() RENAME TO c_is_ready;
ALTER FUNCTION poc.issue(text,text,uuid,text,uuid,jsonb) SET SCHEMA w_guard;
ALTER FUNCTION w_guard.issue(text,text,uuid,text,uuid,jsonb) RENAME TO issue_c;
ALTER FUNCTION poc.verify() SET SCHEMA w_guard;
ALTER FUNCTION w_guard.verify() RENAME TO verify_c;
REVOKE ALL ON FUNCTION w_guard.c_is_ready() FROM cac_ctx_runtime,cac_ctx_issuer,cac_fence_activator;
REVOKE ALL ON FUNCTION w_guard.issue_c(text,text,uuid,text,uuid,jsonb) FROM cac_ctx_issuer;
REVOKE ALL ON FUNCTION w_guard.verify_c() FROM cac_ctx_runtime;
RESET ROLE;
CREATE FUNCTION fence_private.check_guard() RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,fence_private AS $$
BEGIN PERFORM w_guard.require();PERFORM fence_private.check_guard_c();END $$;
CREATE FUNCTION fence.is_ready() RETURNS bool LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
BEGIN PERFORM w_guard.require('active','');RETURN w_guard.c_is_ready();EXCEPTION WHEN OTHERS THEN RETURN false;END $$;
CREATE FUNCTION poc.issue(h text,proof text,st uuid,act text,target uuid,body jsonb) RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE r text;d text;BEGIN
 d=w_guard.issuer_digest(h,proof,st,act,target,body);PERFORM w_guard.require('guard',d);
 r=w_guard.issue_c(h,proof,st,act,target,body);PERFORM w_guard.require('guard',d);RETURN r;
END $$;
CREATE FUNCTION poc.verify() RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE r jsonb;BEGIN
 PERFORM w_guard.require();r=w_guard.verify_c();PERFORM w_guard.require('guard',w_guard.runtime_digest((r->>'store')::uuid));RETURN r;
END $$;
ALTER FUNCTION fence_private.check_guard() OWNER TO cac_ctx_guard;
ALTER FUNCTION fence.is_ready() OWNER TO cac_ctx_guard;
ALTER FUNCTION poc.issue(text,text,uuid,text,uuid,jsonb) OWNER TO cac_ctx_guard;
ALTER FUNCTION poc.verify() OWNER TO cac_ctx_guard;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA w_guard FROM PUBLIC;
REVOKE ALL ON FUNCTION fence_private.check_guard(),fence.is_ready(),poc.issue(text,text,uuid,text,uuid,jsonb),poc.verify() FROM PUBLIC;
RESET ROLE;
GRANT EXECUTE ON FUNCTION w_guard.runtime_digest(uuid) TO cac_ctx_runtime;
GRANT EXECUTE ON FUNCTION w_guard.issuer_digest(text,text,uuid,text,uuid,jsonb) TO cac_ctx_issuer;
GRANT EXECUTE ON FUNCTION w_guard.set_epoch(bigint) TO cac_fence_activator;
GRANT EXECUTE ON FUNCTION w_guard.final_check() TO cac_ctx_runtime,cac_ctx_issuer;
GRANT EXECUTE ON FUNCTION fence.is_ready() TO cac_ctx_runtime,cac_ctx_issuer,cac_fence_activator;
GRANT EXECUTE ON FUNCTION poc.issue(text,text,uuid,text,uuid,jsonb) TO cac_ctx_issuer;
GRANT EXECUTE ON FUNCTION poc.verify() TO cac_ctx_runtime;
