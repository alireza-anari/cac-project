CREATE SCHEMA anchor AUTHORIZATION cac_anchor_guard;
SET LOCAL ROLE cac_anchor_guard;
CREATE TABLE anchor.instances(id uuid PRIMARY KEY,login name UNIQUE NOT NULL,cluster_sid text UNIQUE NOT NULL,secret bytea NOT NULL CHECK(octet_length(secret)=32));
CREATE TABLE anchor.state(singleton bool PRIMARY KEY CHECK(singleton),epoch bigint NOT NULL CHECK(epoch>=0),owner uuid REFERENCES anchor.instances,generation uuid,request uuid,phase text NOT NULL CHECK(phase IN ('empty','reserved','active')));
INSERT INTO anchor.state VALUES(true,0,NULL,NULL,NULL,'empty');
CREATE TABLE anchor.activations(request uuid PRIMARY KEY,instance uuid NOT NULL REFERENCES anchor.instances,epoch bigint UNIQUE NOT NULL,generation uuid NOT NULL);
CREATE TABLE anchor.operations(id bigserial PRIMARY KEY,ticket_hash text UNIQUE NOT NULL,instance uuid NOT NULL REFERENCES anchor.instances,epoch bigint NOT NULL,db_pid int NOT NULL,db_tx text NOT NULL,cluster_sid text NOT NULL,holder_pid int NOT NULL,holder_start timestamptz NOT NULL,phase text NOT NULL CHECK(phase IN ('open','done')));

CREATE FUNCTION anchor.actor() RETURNS anchor.instances LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,anchor AS $$
DECLARE i anchor.instances;BEGIN SELECT * INTO STRICT i FROM anchor.instances WHERE login=session_user;RETURN i;END $$;
CREATE FUNCTION anchor.status() RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,anchor AS $$
DECLARE s anchor.state;BEGIN
 PERFORM anchor.actor();
 IF pg_is_in_recovery() OR current_setting('transaction_read_only')::bool THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 SELECT * INTO STRICT s FROM anchor.state;
 RETURN to_jsonb(s)||jsonb_build_object('anchor_sid',(SELECT system_identifier::text FROM pg_control_system()));
END $$;
CREATE FUNCTION anchor.reserve(expected bigint,req uuid) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,anchor AS $$
DECLARE i anchor.instances;s anchor.state;g uuid;BEGIN
 i=anchor.actor();
 IF expected IS NULL OR req IS NULL OR pg_is_in_recovery() THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 SELECT * INTO STRICT s FROM anchor.state FOR UPDATE;
 IF s.request=req AND s.owner=i.id THEN RETURN anchor.status();END IF;
 IF s.epoch<>expected OR EXISTS(SELECT 1 FROM anchor.activations WHERE request=req) OR EXISTS(SELECT 1 FROM anchor.operations WHERE phase='open') THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 g=public.gen_random_uuid();
 UPDATE anchor.state SET epoch=epoch+1,owner=i.id,generation=g,request=req,phase='reserved';
 INSERT INTO anchor.activations VALUES(req,i.id,s.epoch+1,g);
 RETURN anchor.status();
END $$;
CREATE FUNCTION anchor.pack(p jsonb,k bytea) RETURNS text LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,anchor AS $$
 SELECT encode(convert_to(p::text,'UTF8'),'hex')||'.'||encode(public.hmac(convert_to(p::text,'UTF8'),k,'sha256'),'hex')
$$;
CREATE FUNCTION anchor.confirm(ack text) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,anchor AS $$
DECLARE i anchor.instances;s anchor.state;b bytea;p jsonb;BEGIN
 i=anchor.actor();
 IF ack IS NULL OR length(ack)>8000 OR ack!~'^[0-9a-f]+\.[0-9a-f]{64}$' THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 b=decode(split_part(ack,'.',1),'hex');p=convert_from(b,'UTF8')::jsonb;
 IF convert_to(p::text,'UTF8')<>b OR encode(public.hmac(b,i.secret,'sha256'),'hex')<>split_part(ack,'.',2) THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 SELECT * INTO STRICT s FROM anchor.state FOR UPDATE;
 IF p->>'kind' IS DISTINCT FROM 'committed_ack' OR p->>'instance' IS DISTINCT FROM i.id::text OR p->>'cluster_sid' IS DISTINCT FROM i.cluster_sid OR p->>'epoch' IS DISTINCT FROM s.epoch::text OR p->>'generation' IS DISTINCT FROM s.generation::text OR p->>'request' IS DISTINCT FROM s.request::text OR s.owner IS DISTINCT FROM i.id OR s.phase NOT IN ('reserved','active') THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 UPDATE anchor.state SET phase='active';RETURN anchor.status();
EXCEPTION WHEN OTHERS THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END $$;
CREATE FUNCTION anchor.live(g anchor.operations) RETURNS bool LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,anchor AS $$
 SELECT EXISTS(SELECT 1 FROM pg_stat_activity WHERE pid=(g).holder_pid AND backend_start=(g).holder_start)
$$;
CREATE FUNCTION anchor.locked(g anchor.operations) RETURNS bool LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,anchor AS $$
 SELECT anchor.live(g) AND EXISTS(SELECT 1 FROM pg_locks WHERE locktype='advisory' AND pid=(g).holder_pid AND classid=0 AND objid::bigint=(g).id AND objsubid=1 AND mode='ExclusiveLock' AND granted)
$$;
CREATE FUNCTION anchor.prepare(dbpid int,dbtx text,sid text) RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,anchor AS $$
DECLARE i anchor.instances;s anchor.state;t text;BEGIN
 i=anchor.actor();SELECT * INTO STRICT s FROM anchor.state FOR SHARE;
 IF sid IS DISTINCT FROM i.cluster_sid OR dbpid IS NULL OR dbtx IS NULL OR s.phase<>'active' OR s.owner IS DISTINCT FROM i.id OR EXISTS(SELECT 1 FROM anchor.operations o WHERE o.phase='open' AND NOT anchor.live(o)) THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 t=encode(public.gen_random_bytes(32),'hex');
 INSERT INTO anchor.operations(ticket_hash,instance,epoch,db_pid,db_tx,cluster_sid,holder_pid,holder_start,phase) VALUES(encode(public.digest(t,'sha256'),'hex'),i.id,s.epoch,dbpid,dbtx,sid,pg_backend_pid(),(SELECT backend_start FROM pg_stat_activity WHERE pid=pg_backend_pid()),'open');
 RETURN t;
END $$;
CREATE FUNCTION anchor.hold(t text) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,anchor AS $$
DECLARE i anchor.instances;s anchor.state;g anchor.operations;BEGIN
 i=anchor.actor();SELECT * INTO STRICT s FROM anchor.state FOR SHARE;
 SELECT * INTO STRICT g FROM anchor.operations WHERE ticket_hash=encode(public.digest(t,'sha256'),'hex') AND instance=i.id;
 IF s.phase<>'active' OR s.owner IS DISTINCT FROM i.id OR s.epoch<>g.epoch OR g.phase<>'open' OR g.holder_pid<>pg_backend_pid() OR NOT anchor.live(g) OR EXISTS(SELECT 1 FROM anchor.operations o WHERE o.phase='open' AND NOT anchor.live(o)) THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 PERFORM pg_advisory_xact_lock(g.id);
END $$;
CREATE FUNCTION anchor.finish(t text) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,anchor AS $$
DECLARE i anchor.instances;s anchor.state;g anchor.operations;BEGIN
 i=anchor.actor();SELECT * INTO STRICT s FROM anchor.state FOR SHARE;
 SELECT * INTO STRICT g FROM anchor.operations WHERE ticket_hash=encode(public.digest(t,'sha256'),'hex') AND instance=i.id;
 IF s.phase<>'active' OR s.owner IS DISTINCT FROM i.id OR s.epoch<>g.epoch OR g.phase<>'open' OR g.holder_pid<>pg_backend_pid() OR NOT anchor.locked(g) THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 UPDATE anchor.operations SET phase='done' WHERE id=g.id;
END $$;
CREATE FUNCTION anchor.attest(nonce text,mode_arg text,t text,sid text,dbpid int,dbtx text) RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,anchor AS $$
DECLARE i anchor.instances;s anchor.state;g anchor.operations;BEGIN
 i=anchor.actor();SELECT * INTO STRICT s FROM anchor.state FOR SHARE;
 IF nonce IS NULL OR nonce!~'^[0-9a-f]{64}$' OR sid IS DISTINCT FROM i.cluster_sid OR s.owner IS DISTINCT FROM i.id OR pg_is_in_recovery() OR current_setting('transaction_read_only')::bool OR EXISTS(SELECT 1 FROM anchor.operations o WHERE o.phase='open' AND NOT anchor.live(o)) THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 IF mode_arg='apply' THEN
  IF s.phase NOT IN ('reserved','active') THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 ELSIF mode_arg IN ('active','guard') THEN
  IF s.phase<>'active' THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 ELSE RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 IF mode_arg='guard' THEN
  SELECT * INTO STRICT g FROM anchor.operations WHERE ticket_hash=encode(public.digest(t,'sha256'),'hex') AND instance=i.id;
  IF g.phase<>'open' OR g.epoch<>s.epoch OR g.db_pid<>dbpid OR g.db_tx<>dbtx OR g.cluster_sid<>sid OR NOT anchor.locked(g) THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 END IF;
 RETURN anchor.pack(jsonb_build_object('nonce',nonce,'mode',mode_arg,'instance',i.id,'epoch',s.epoch,'generation',s.generation,'request',s.request,'anchor_sid',(SELECT system_identifier::text FROM pg_control_system()),'cluster_sid',sid,'ticket',coalesce(g.ticket_hash,''),'db_pid',dbpid,'db_tx',dbtx),i.secret);
EXCEPTION WHEN OTHERS THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END $$;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA anchor FROM PUBLIC;
ALTER DEFAULT PRIVILEGES REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
RESET ROLE;
GRANT USAGE ON SCHEMA anchor TO cac_anchor_a,cac_anchor_b;
GRANT EXECUTE ON FUNCTION anchor.status(),anchor.reserve(bigint,uuid),anchor.confirm(text),anchor.prepare(int,text,text),anchor.hold(text),anchor.finish(text),anchor.attest(text,text,text,text,int,text) TO cac_anchor_a,cac_anchor_b;
