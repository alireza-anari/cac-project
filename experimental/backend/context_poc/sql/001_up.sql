CREATE SCHEMA poc AUTHORIZATION cac_ctx_owner;
CREATE SCHEMA poc_private AUTHORIZATION cac_ctx_guard;
GRANT USAGE ON SCHEMA poc TO cac_ctx_runtime,cac_ctx_issuer,cac_ctx_identity,cac_ctx_guard;
GRANT USAGE ON SCHEMA public TO cac_ctx_guard;
CREATE TABLE poc_private.config(singleton bool PRIMARY KEY CHECK(singleton), generation uuid NOT NULL);
CREATE TABLE poc_private.keys(kind text,kid text,secret bytea NOT NULL,state text NOT NULL CHECK(state IN ('active','verify','revoked')),PRIMARY KEY(kind,kid));
CREATE UNIQUE INDEX one_signer ON poc_private.keys(kind) WHERE state='active';
CREATE TABLE poc_private.principals(id uuid PRIMARY KEY,active bool NOT NULL,epoch int NOT NULL);
CREATE TABLE poc_private.sessions(id uuid PRIMARY KEY,principal uuid REFERENCES poc_private.principals,proof bytea UNIQUE NOT NULL,active bool NOT NULL,epoch int NOT NULL,expires timestamptz NOT NULL,mfa timestamptz NOT NULL);
CREATE TABLE poc_private.stores(id uuid PRIMARY KEY,tenant uuid NOT NULL,epoch int NOT NULL);
CREATE TABLE poc_private.access(principal uuid REFERENCES poc_private.principals,store uuid REFERENCES poc_private.stores,PRIMARY KEY(principal,store));
CREATE TABLE poc_private.ledger(generation uuid,tx text,pid int,tuple jsonb NOT NULL,token text NOT NULL,started timestamptz NOT NULL,PRIMARY KEY(generation,tx,pid));
CREATE TABLE poc.records(id uuid PRIMARY KEY,tenant uuid NOT NULL,store uuid NOT NULL,body text NOT NULL,UNIQUE(tenant,store,id));
ALTER TABLE poc_private.stores ADD CONSTRAINT scope_unique UNIQUE(tenant,id);
ALTER TABLE poc.records ADD CONSTRAINT record_scope_fk FOREIGN KEY(tenant,store) REFERENCES poc_private.stores(tenant,id);
ALTER TABLE poc.records OWNER TO cac_ctx_owner;
ALTER TABLE poc.records ENABLE ROW LEVEL SECURITY;
ALTER TABLE poc.records FORCE ROW LEVEL SECURITY;
GRANT SELECT ON poc.records TO cac_ctx_runtime;

CREATE FUNCTION poc_private.pack(p jsonb,kind_arg text) RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,poc_private AS $$
DECLARE k record;b bytea;
BEGIN
 SELECT * INTO STRICT k FROM poc_private.keys WHERE kind=kind_arg AND state='active';
 p=p||jsonb_build_object('kid',k.kid,'kind',kind_arg);
 b=convert_to(p::text,'UTF8');
 RETURN encode(b,'hex')||'.'||encode(public.hmac(b,k.secret,'sha256'),'hex');
END $$;
CREATE FUNCTION poc_private.unpack(token text,kind_arg text) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,poc_private AS $$
DECLARE b bytea;j json;p jsonb;k bytea;
BEGIN
 IF token IS NULL OR length(token)>16000 OR token !~ '^[0-9a-f]+\.[0-9a-f]{64}$' THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501'; END IF;
 b=decode(split_part(token,'.',1),'hex');j=convert_from(b,'UTF8')::json;p=j::jsonb;
 IF json_typeof(j)<>'object' OR (SELECT count(*)<>count(DISTINCT key) FROM json_each(j)) OR convert_to(p::text,'UTF8')<>b THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501'; END IF;
 SELECT secret INTO STRICT k FROM poc_private.keys WHERE kind=kind_arg AND kid=p->>'kid' AND state IN ('active','verify');
 IF p->>'kind' IS DISTINCT FROM kind_arg OR encode(public.hmac(b,k,'sha256'),'hex')<>split_part(token,'.',2) THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501'; END IF;
 RETURN p;
EXCEPTION WHEN OTHERS THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';
END $$;
CREATE FUNCTION poc.challenge() RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,poc_private AS $$
BEGIN
 IF session_user<>'cac_ctx_runtime' THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 RETURN poc_private.pack(jsonb_build_object('v',2,'aud','cac-s009-disposable','generation',(SELECT generation FROM poc_private.config),'login',session_user,'tx',txid_current()::text,'pid',pg_backend_pid(),'nonce',encode(public.gen_random_bytes(32),'hex'),'started',extract(epoch FROM transaction_timestamp())),'challenge');
END $$;
CREATE FUNCTION poc.issue(challenge_arg text,proof_arg text,store_arg uuid,action_arg text,target_arg uuid,body_arg jsonb) RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,poc_private AS $$
DECLARE h jsonb;s record;p record;st record;claims jsonb;result text;existing record;now_s numeric;
BEGIN
 IF session_user<>'cac_ctx_issuer' THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 IF proof_arg IS NULL OR store_arg IS NULL OR target_arg IS NULL OR action_arg IS NULL OR body_arg IS NULL THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 h=poc_private.unpack(challenge_arg,'challenge'); now_s=extract(epoch FROM clock_timestamp());
 IF h->>'v'<>'2' OR h->>'aud'<>'cac-s009-disposable' OR h->>'login'<>'cac_ctx_runtime' OR (h->>'generation')::uuid<>(SELECT generation FROM poc_private.config) OR now_s-(h->>'started')::numeric NOT BETWEEN 0 AND 5 THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 SELECT * INTO STRICT s FROM poc_private.sessions WHERE proof=public.digest(proof_arg,'sha256');
 SELECT * INTO STRICT p FROM poc_private.principals WHERE id=s.principal FOR SHARE;
 SELECT * INTO STRICT s FROM poc_private.sessions WHERE id=s.id FOR SHARE;
 SELECT * INTO STRICT st FROM poc_private.stores WHERE id=store_arg FOR SHARE;
 IF NOT p.active OR NOT s.active OR s.expires<=clock_timestamp() OR s.mfa<clock_timestamp()-interval '5 minutes' OR s.mfa>clock_timestamp() OR target_arg<>p.id OR action_arg NOT IN ('read','probe') OR NOT EXISTS(SELECT 1 FROM poc_private.access WHERE principal=p.id AND store=st.id) THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 claims=jsonb_build_object('v',2,'aud','cac-s009-disposable','generation',h->>'generation','login',h->>'login','tx',h->>'tx','pid',h->'pid','nonce',h->>'nonce','challenge',challenge_arg,'principal',p.id,'pe',p.epoch,'session',s.id,'se',s.epoch,'tenant',st.tenant,'store',st.id,'ae',st.epoch,'action',action_arg,'target',target_arg,'digest',encode(public.digest(body_arg::text,'sha256'),'hex'));
 SELECT * INTO existing FROM poc_private.ledger WHERE generation=(h->>'generation')::uuid AND tx=h->>'tx' AND pid=(h->>'pid')::int;
 IF FOUND THEN
  IF existing.tuple<>claims THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501'; END IF;
  RETURN existing.token;
 END IF;
 result=poc_private.pack(claims||jsonb_build_object('exp',now_s+60,'iat',now_s),'context');
 INSERT INTO poc_private.ledger VALUES((h->>'generation')::uuid,h->>'tx',(h->>'pid')::int,claims,result,to_timestamp((h->>'started')::double precision)) ON CONFLICT DO NOTHING;
 SELECT * INTO STRICT existing FROM poc_private.ledger WHERE generation=(h->>'generation')::uuid AND tx=h->>'tx' AND pid=(h->>'pid')::int;
 IF existing.tuple<>claims THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 RETURN existing.token;
EXCEPTION WHEN OTHERS THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';
END $$;
CREATE FUNCTION poc.verify() RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,poc_private AS $$
DECLARE c jsonb;h jsonb;p record;s record;st record;field text;
BEGIN
 c=poc_private.unpack(current_setting('cac.poc_context',true),'context');
 FOREACH field IN ARRAY ARRAY['aud','generation','login','tx','nonce','challenge','principal','session','tenant','store','action','target','digest','kid','kind'] LOOP
  IF jsonb_typeof(c->field) IS DISTINCT FROM 'string' THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 END LOOP;
 FOREACH field IN ARRAY ARRAY['v','pid','pe','se','ae','iat','exp'] LOOP
  IF jsonb_typeof(c->field) IS DISTINCT FROM 'number' THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 END LOOP;
 IF (SELECT count(*) FROM jsonb_object_keys(c))<>22 OR c->>'v'<>'2' OR c->>'aud'<>'cac-s009-disposable' OR c->>'login'<>session_user OR session_user<>'cac_ctx_runtime' OR (c->>'generation')::uuid<>(SELECT generation FROM poc_private.config) OR c->>'tx'<>txid_current()::text OR c->>'pid'<>pg_backend_pid()::text OR (c->>'exp')::numeric<=extract(epoch FROM clock_timestamp()) OR (c->>'exp')::numeric>(c->>'iat')::numeric+60 OR (c->>'iat')::numeric>extract(epoch FROM clock_timestamp())+5 THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 h=poc_private.unpack(c->>'challenge','challenge');
 IF h->>'generation'<>c->>'generation' OR h->>'tx'<>c->>'tx' OR h->>'pid'<>c->>'pid' OR h->>'nonce'<>c->>'nonce' OR h->>'login'<>c->>'login' THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501'; END IF;
 IF NOT EXISTS(SELECT 1 FROM poc_private.ledger WHERE generation=(c->>'generation')::uuid AND tx=c->>'tx' AND pid=(c->>'pid')::int AND tuple=c-ARRAY['iat','exp','kid','kind']) THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 SELECT * INTO STRICT p FROM poc_private.principals WHERE id=(c->>'principal')::uuid FOR SHARE;
 SELECT * INTO STRICT s FROM poc_private.sessions WHERE id=(c->>'session')::uuid FOR SHARE;
 SELECT * INTO STRICT st FROM poc_private.stores WHERE id=(c->>'store')::uuid FOR SHARE;
 IF NOT p.active OR NOT s.active OR s.principal<>p.id OR p.epoch<>(c->>'pe')::int OR s.epoch<>(c->>'se')::int OR s.expires<=clock_timestamp() OR s.mfa<clock_timestamp()-interval '5 minutes' OR s.mfa>clock_timestamp() OR st.tenant<>(c->>'tenant')::uuid OR c->>'target'<>p.id::text OR NOT EXISTS(SELECT 1 FROM poc_private.access WHERE principal=p.id AND store=st.id) THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 IF st.epoch<>(c->>'ae')::int THEN RAISE EXCEPTION 'snapshot stale' USING ERRCODE='PZ001';END IF;
 RETURN c;
EXCEPTION WHEN SQLSTATE 'PZ001' THEN RAISE; WHEN OTHERS THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';
END $$;
CREATE FUNCTION poc.authorize(action_arg text,target_arg uuid,body_arg jsonb) RETURNS bool LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,poc_private AS $$
DECLARE c jsonb;
BEGIN c=poc.verify();IF action_arg IS NULL OR target_arg IS NULL OR body_arg IS NULL OR c->>'action'<>action_arg OR c->>'target'<>target_arg::text OR c->>'digest'<>encode(public.digest(body_arg::text,'sha256'),'hex') THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;RETURN true;END $$;
CREATE FUNCTION poc.read_scope() RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,poc_private AS $$
DECLARE c jsonb;
BEGIN c=poc.verify();IF c->>'action'<>'read' OR c->>'digest'<>encode(public.digest('{}'::jsonb::text,'sha256'),'hex') THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;RETURN (c->>'store')::uuid;END $$;
CREATE POLICY scoped_read ON poc.records FOR SELECT TO cac_ctx_runtime USING(store=poc.read_scope());
CREATE FUNCTION poc.revoke(kind_arg text,id_arg uuid) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,poc_private AS $$
BEGIN
 IF session_user<>'cac_ctx_identity' THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 IF kind_arg='principal' THEN UPDATE poc_private.principals SET active=false,epoch=epoch+1 WHERE id=id_arg;
 ELSIF kind_arg='session' THEN UPDATE poc_private.sessions SET active=false,epoch=epoch+1 WHERE id=id_arg;
 ELSIF kind_arg='store' THEN UPDATE poc_private.stores SET epoch=epoch+1 WHERE id=id_arg;
 ELSE RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
END $$;
CREATE FUNCTION poc.purge_ledger() RETURNS int LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,poc_private AS $$
DECLARE n int;
BEGIN IF session_user<>'cac_ctx_issuer' THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;DELETE FROM poc_private.ledger WHERE started<clock_timestamp()-interval '120 seconds';GET DIAGNOSTICS n=ROW_COUNT;RETURN n;END $$;
DO $$ DECLARE r record;BEGIN
 FOR r IN SELECT oid::regprocedure AS f FROM pg_proc WHERE pronamespace IN ('poc'::regnamespace,'poc_private'::regnamespace) LOOP
 EXECUTE format('ALTER FUNCTION %s OWNER TO cac_ctx_guard',r.f);EXECUTE format('REVOKE ALL ON FUNCTION %s FROM PUBLIC',r.f);END LOOP;
 FOR r IN SELECT tablename FROM pg_tables WHERE schemaname='poc_private' LOOP EXECUTE format('ALTER TABLE poc_private.%I OWNER TO cac_ctx_guard',r.tablename);END LOOP;
END $$;
ALTER DEFAULT PRIVILEGES FOR ROLE cac_ctx_guard REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
GRANT EXECUTE ON FUNCTION poc.challenge(),poc.verify(),poc.read_scope(),poc.authorize(text,uuid,jsonb) TO cac_ctx_runtime;
GRANT EXECUTE ON FUNCTION poc.issue(text,text,uuid,text,uuid,jsonb),poc.purge_ledger() TO cac_ctx_issuer;
GRANT EXECUTE ON FUNCTION poc.revoke(text,uuid) TO cac_ctx_identity;
