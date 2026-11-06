-- Q_SURVIVAL_ONLY. Actual R is authority; legacy C supplies generation cache/readiness only.
CREATE SCHEMA h_guard AUTHORIZATION cac_ctx_guard;
GRANT USAGE ON SCHEMA h_guard TO cac_ctx_runtime,cac_ctx_issuer,cac_fence_activator;
SET LOCAL ROLE cac_ctx_guard;
CREATE TABLE h_guard.config(singleton bool PRIMARY KEY CHECK(singleton),root uuid NOT NULL,namespace uuid NOT NULL,policy bigint NOT NULL,node text NOT NULL,incarnation uuid NOT NULL,epoch bigint NOT NULL,checker_conn text NOT NULL);
CREATE FUNCTION h_guard.runtime_digest(st uuid,act text,target uuid,body_hash text) RETURNS text LANGUAGE sql IMMUTABLE SECURITY DEFINER SET search_path=pg_catalog AS $$
 SELECT encode(public.digest(jsonb_build_object('domain','cac-s009h-runtime','store',st,'action',act,'target',target,'body_digest',body_hash)::text,'sha256'),'hex')
$$;
CREATE FUNCTION h_guard.body_digest(body jsonb) RETURNS text LANGUAGE sql IMMUTABLE SECURITY DEFINER SET search_path=pg_catalog AS $$ SELECT encode(public.digest(body::text,'sha256'),'hex') $$;
CREATE FUNCTION h_guard.issuer_digest(h text,proof text,st uuid,act text,target uuid,body jsonb) RETURNS text LANGUAGE sql IMMUTABLE SECURITY DEFINER SET search_path=pg_catalog AS $$
 SELECT encode(public.digest(jsonb_build_object('domain','cac-s009h-issuer','challenge',h,'proof_hash',encode(public.digest(proof,'sha256'),'hex'),'store',st,'action',act,'target',target,'body',body)::text,'sha256'),'hex')
$$;
-- MEASUREMENT_FUNCTION
CREATE FUNCTION h_guard.rpc(action_arg text,args_arg jsonb) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,h_guard AS $$
DECLARE cfg h_guard.config;req jsonb;answer text;q text;BEGIN
 SELECT * INTO STRICT cfg FROM h_guard.config;
 req=jsonb_build_object('action',action_arg,'args',args_arg,'namespace',cfg.namespace);
 q=format('SELECT h_call(%L)',replace(encode(convert_to(req::text,'UTF8'),'base64'),E'\n',''));
 SELECT r INTO STRICT answer FROM public.dblink(cfg.checker_conn,q) AS response(r text);
 IF answer IS NULL OR length(answer)>16000 THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 RETURN answer::jsonb;
EXCEPTION WHEN OTHERS THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END $$;
CREATE FUNCTION h_guard.w_status() RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,h_guard AS $$
DECLARE cfg h_guard.config;conn text;s jsonb;BEGIN
 SELECT * INTO STRICT cfg FROM h_guard.config;SELECT anchor_conn INTO STRICT conn FROM fence_private.config;
 SELECT r INTO STRICT s FROM public.dblink(conn,format('SELECT h_w.status(%L::uuid)',cfg.namespace)) AS response(r jsonb);
 RETURN s;
EXCEPTION WHEN OTHERS THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END $$;
CREATE FUNCTION h_guard.require(mode_arg text DEFAULT 'guard',digest_arg text DEFAULT NULL) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,h_guard AS $$
DECLARE cfg h_guard.config;n text;sid text;pid int;tx text;man text;intent text;t text;a jsonb;r jsonb;p jsonb;answer text;k text;BEGIN
 SELECT * INTO STRICT cfg FROM h_guard.config;
 n=encode(public.gen_random_bytes(32),'hex');sid=fence.system_id();pid=pg_backend_pid();tx=txid_current()::text;man=h_guard.measure();
 intent=CASE WHEN mode_arg='active' THEN '' ELSE coalesce(digest_arg,current_setting('cac.h_intent',true),'') END;
 t=CASE WHEN mode_arg='active' THEN '' ELSE coalesce(current_setting('cac.h_ticket',true),'') END;
 k=CASE session_user WHEN 'cac_ctx_runtime' THEN 'runtime' WHEN 'cac_ctx_issuer' THEN 'issuer' WHEN 'cac_fence_activator' THEN 'activator' END;
 a=jsonb_build_object('root_id',cfg.root,'policy',cfg.policy,'epoch',cfg.epoch,'incarnation',cfg.incarnation,'manifest',man,'sid',sid,'pid',pid,'tx',tx,'nonce',n,'mode',mode_arg,'ticket',t,'digest',intent,'kind',k,'login',session_user);
 a=a||jsonb_build_object('projection',h_guard.w_status());
 r=h_guard.rpc('guard',a);answer=r->>'answer';
 IF answer IS NULL OR length(answer)>16000 OR answer!~'^[0-9a-f]+\.[0-9a-f]{64}$' THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 p=convert_from(decode(split_part(answer,'.',1),'hex'),'UTF8')::jsonb;
 IF p->>'v' IS DISTINCT FROM '1' OR p->>'domain' IS DISTINCT FROM 'cac-s009h-q-survival' OR p->>'root_id' IS DISTINCT FROM cfg.root::text OR p->>'namespace' IS DISTINCT FROM cfg.namespace::text OR p->>'node' IS DISTINCT FROM cfg.node OR p->>'policy' IS DISTINCT FROM cfg.policy::text OR p->>'epoch' IS DISTINCT FROM cfg.epoch::text OR p->>'incarnation' IS DISTINCT FROM cfg.incarnation::text OR p->>'manifest' IS DISTINCT FROM man OR p->>'sid' IS DISTINCT FROM sid OR p->>'pid' IS DISTINCT FROM pid::text OR p->>'tx' IS DISTINCT FROM tx OR p->>'nonce' IS DISTINCT FROM n OR p->>'mode' IS DISTINCT FROM mode_arg OR p->>'digest' IS DISTINCT FROM intent OR p->>'kind' IS DISTINCT FROM k OR p->>'login' IS DISTINCT FROM session_user OR p->>'ticket_hash' IS DISTINCT FROM encode(public.digest(t,'sha256'),'hex') THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 r=h_guard.rpc('verify',a||jsonb_build_object('answer',answer));
 IF r->'valid' IS DISTINCT FROM 'true'::jsonb THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
EXCEPTION WHEN OTHERS THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END $$;
CREATE FUNCTION h_guard.set_epoch(ep bigint) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,h_guard AS $$
DECLARE cfg h_guard.config;s jsonb;BEGIN
 IF session_user<>'cac_fence_activator' THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 SELECT * INTO STRICT cfg FROM h_guard.config;s=h_guard.rpc('status','{}'::jsonb);
 IF ep IS NULL OR s->>'epoch' IS DISTINCT FROM ep::text OR s->>'owner' IS DISTINCT FROM cfg.node OR s->>'phase' IS DISTINCT FROM 'RESERVED' OR s->>'root_id' IS DISTINCT FROM cfg.root::text OR s->>'namespace' IS DISTINCT FROM cfg.namespace::text OR s->>'policy' IS DISTINCT FROM cfg.policy::text THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 UPDATE h_guard.config SET epoch=ep;
END $$;
CREATE FUNCTION h_guard.final_check() RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ BEGIN PERFORM h_guard.require();END $$;
RESET ROLE;
ALTER FUNCTION fence_private.check_guard() RENAME TO check_guard_c;
ALTER FUNCTION fence.is_ready() SET SCHEMA h_guard;
ALTER FUNCTION h_guard.is_ready() RENAME TO c_is_ready;
ALTER FUNCTION poc.issue(text,text,uuid,text,uuid,jsonb) SET SCHEMA h_guard;
ALTER FUNCTION h_guard.issue(text,text,uuid,text,uuid,jsonb) RENAME TO issue_c;
ALTER FUNCTION poc.verify() SET SCHEMA h_guard;
ALTER FUNCTION h_guard.verify() RENAME TO verify_c;
REVOKE ALL ON FUNCTION fence_private.check_guard_c() FROM PUBLIC,cac_ctx_runtime,cac_ctx_issuer,cac_fence_activator;
REVOKE ALL ON FUNCTION h_guard.c_is_ready() FROM PUBLIC,cac_ctx_runtime,cac_ctx_issuer,cac_fence_activator;
REVOKE ALL ON FUNCTION h_guard.issue_c(text,text,uuid,text,uuid,jsonb) FROM PUBLIC,cac_ctx_issuer,cac_ctx_runtime;
REVOKE ALL ON FUNCTION h_guard.verify_c() FROM PUBLIC,cac_ctx_runtime,cac_ctx_issuer;
CREATE FUNCTION fence_private.check_guard() RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ BEGIN PERFORM h_guard.require();END $$;
CREATE FUNCTION fence.is_ready() RETURNS bool LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ BEGIN PERFORM h_guard.require('active','');RETURN h_guard.c_is_ready();EXCEPTION WHEN OTHERS THEN RETURN false;END $$;
CREATE FUNCTION poc.issue(h text,proof text,st uuid,act text,target uuid,body jsonb) RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE d text;r text;BEGIN d=h_guard.issuer_digest(h,proof,st,act,target,body);PERFORM h_guard.require('guard',d);r=h_guard.issue_c(h,proof,st,act,target,body);PERFORM h_guard.require('guard',d);RETURN r;END $$;
CREATE FUNCTION poc.verify() RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE r jsonb;BEGIN PERFORM h_guard.require();r=h_guard.verify_c();PERFORM h_guard.require('guard',h_guard.runtime_digest((r->>'store')::uuid,r->>'action',(r->>'target')::uuid,r->>'digest'));RETURN r;END $$;
ALTER FUNCTION fence_private.check_guard() OWNER TO cac_ctx_guard;
ALTER FUNCTION fence.is_ready() OWNER TO cac_ctx_guard;
ALTER FUNCTION poc.issue(text,text,uuid,text,uuid,jsonb) OWNER TO cac_ctx_guard;
ALTER FUNCTION poc.verify() OWNER TO cac_ctx_guard;
SET LOCAL ROLE cac_ctx_guard;
CREATE FUNCTION h_guard.scope() RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE c jsonb;BEGIN c=poc.verify();IF c->>'action' NOT IN ('read','probe') OR (c->>'action'='read' AND c->>'digest' IS DISTINCT FROM encode(public.digest('{}'::jsonb::text,'sha256'),'hex')) THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;RETURN (c->>'store')::uuid;END $$;
CREATE FUNCTION h_guard.is_probe() RETURNS bool LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ BEGIN RETURN poc.verify()->>'action'='probe';END $$;
CREATE FUNCTION h_guard.write_body(body text) RETURNS bool LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE c jsonb;BEGIN c=poc.verify();RETURN poc.authorize('probe',(c->>'target')::uuid,jsonb_build_object('body',body));END $$;
RESET ROLE;
ALTER POLICY scoped_read ON poc.records USING(store=h_guard.scope());
GRANT UPDATE(body) ON poc.records TO cac_ctx_runtime;
CREATE POLICY scoped_write ON poc.records FOR UPDATE TO cac_ctx_runtime USING(store=h_guard.scope() AND h_guard.is_probe()) WITH CHECK(store=h_guard.scope() AND h_guard.write_body(body));
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA h_guard FROM PUBLIC;
REVOKE ALL ON FUNCTION fence_private.check_guard(),fence.is_ready(),poc.issue(text,text,uuid,text,uuid,jsonb),poc.verify() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION h_guard.runtime_digest(uuid,text,uuid,text) TO cac_ctx_runtime;
GRANT EXECUTE ON FUNCTION h_guard.issuer_digest(text,text,uuid,text,uuid,jsonb) TO cac_ctx_issuer;
GRANT EXECUTE ON FUNCTION h_guard.final_check() TO cac_ctx_runtime,cac_ctx_issuer;
GRANT EXECUTE ON FUNCTION h_guard.scope(),h_guard.is_probe(),h_guard.write_body(text) TO cac_ctx_runtime;
GRANT EXECUTE ON FUNCTION fence.is_ready() TO cac_ctx_runtime,cac_ctx_issuer,cac_fence_activator;
GRANT EXECUTE ON FUNCTION poc.issue(text,text,uuid,text,uuid,jsonb) TO cac_ctx_issuer;
GRANT EXECUTE ON FUNCTION poc.verify() TO cac_ctx_runtime;

GRANT EXECUTE ON FUNCTION h_guard.body_digest(jsonb) TO cac_ctx_runtime;
GRANT EXECUTE ON FUNCTION h_guard.set_epoch(bigint) TO cac_fence_activator;
