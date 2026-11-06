-- W_ORACLE_ASSUMED / Lane1 fixture, NOT real root recovery or orphan reconciliation.
CREATE SCHEMA w AUTHORIZATION cac_w_guard;
SET LOCAL ROLE cac_w_guard;
CREATE TABLE w.control(singleton bool PRIMARY KEY CHECK(singleton),root uuid NOT NULL,namespace uuid NOT NULL,policy bigint NOT NULL,continuity bool NOT NULL,secret bytea NOT NULL CHECK(octet_length(secret)=32));
CREATE TABLE w.actors(node text PRIMARY KEY,coord name UNIQUE NOT NULL,checker name UNIQUE NOT NULL,sid text NOT NULL,incarnation uuid NOT NULL,manifest text NOT NULL,admitted bool NOT NULL);
CREATE TABLE w.state(singleton bool PRIMARY KEY CHECK(singleton),epoch bigint NOT NULL CHECK(epoch>=0),owner text REFERENCES w.actors,request uuid,phase text NOT NULL CHECK(phase IN ('empty','reserved','active','revoking')));
CREATE TABLE w.activations(request uuid PRIMARY KEY,node text NOT NULL,epoch bigint UNIQUE NOT NULL);
CREATE TABLE w.ops(lockid bigserial UNIQUE,id uuid PRIMARY KEY,node text NOT NULL REFERENCES w.actors,request uuid NOT NULL,digest text NOT NULL,epoch bigint NOT NULL,incarnation uuid NOT NULL,namespace uuid NOT NULL,policy bigint NOT NULL,manifest text NOT NULL,sid text NOT NULL,dbpid int NOT NULL,dbtx text NOT NULL,kind text NOT NULL,login text NOT NULL,ticket text UNIQUE NOT NULL,holder int NOT NULL,holder_start timestamptz NOT NULL,phase text NOT NULL CHECK(phase IN ('open','unknown','closed_commit','closed_abort')),outcome jsonb,UNIQUE(node,request));
INSERT INTO w.state VALUES(true,0,NULL,NULL,'empty');
CREATE FUNCTION w.identity(coord_only bool DEFAULT false) RETURNS w.actors LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,w AS $$
DECLARE a w.actors;BEGIN
 SELECT * INTO STRICT a FROM w.actors WHERE coord=session_user OR (NOT coord_only AND checker=session_user);
 IF NOT a.admitted OR NOT (SELECT continuity FROM w.control) OR pg_is_in_recovery() OR current_setting('transaction_read_only')::bool THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 RETURN a;
EXCEPTION WHEN OTHERS THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END $$;
CREATE FUNCTION w.status() RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,w AS $$
DECLARE a w.actors;s w.state;c w.control;BEGIN
 a=w.identity();SELECT * INTO STRICT c FROM w.control;SELECT * INTO STRICT s FROM w.state;
 RETURN to_jsonb(s)||jsonb_build_object('root',c.root,'namespace',c.namespace,'policy',c.policy,'incarnation',a.incarnation,'manifest',a.manifest);
END $$;
CREATE FUNCTION w.reserve(expected bigint,req uuid) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,w AS $$
DECLARE a w.actors;s w.state;BEGIN
 a=w.identity(true);SELECT * INTO STRICT s FROM w.state FOR UPDATE;
 IF s.request=req AND s.owner=a.node THEN RETURN w.status();END IF;
 IF expected IS NULL OR req IS NULL OR expected<>s.epoch OR EXISTS(SELECT 1 FROM w.activations WHERE request=req) OR EXISTS(SELECT 1 FROM w.ops WHERE phase IN ('open','unknown')) THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 UPDATE w.state SET epoch=epoch+1,owner=a.node,request=req,phase='reserved';
 INSERT INTO w.activations VALUES(req,a.node,s.epoch+1);RETURN w.status();
END $$;
CREATE FUNCTION w.activate(req uuid) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,w AS $$
DECLARE a w.actors;s w.state;BEGIN
 a=w.identity(true);SELECT * INTO STRICT s FROM w.state FOR UPDATE;
 IF s.owner IS DISTINCT FROM a.node OR s.request IS DISTINCT FROM req OR s.phase NOT IN ('reserved','active') OR EXISTS(SELECT 1 FROM w.ops WHERE phase IN ('open','unknown')) THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 UPDATE w.state SET phase='active';RETURN w.status();
END $$;
CREATE FUNCTION w.revoke(expected bigint) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,w AS $$
DECLARE s w.state;BEGIN
 PERFORM w.identity(true);SELECT * INTO STRICT s FROM w.state FOR UPDATE;
 IF expected IS DISTINCT FROM s.epoch OR s.phase NOT IN ('active','revoking') THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 UPDATE w.state SET phase='revoking';
END $$;
CREATE FUNCTION w.live(g w.ops) RETURNS bool LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,w AS $$
 SELECT EXISTS(SELECT 1 FROM pg_stat_activity WHERE pid=(g).holder AND backend_start=(g).holder_start)
$$;
CREATE FUNCTION w.locked(g w.ops) RETURNS bool LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,w AS $$
 SELECT w.live(g) AND EXISTS(SELECT 1 FROM pg_locks WHERE locktype='advisory' AND pid=(g).holder AND classid=0 AND objid::bigint=(g).lockid AND objsubid=1 AND mode='ExclusiveLock' AND granted)
$$;
CREATE FUNCTION w.admit(req uuid,op uuid,d text,sid_arg text,pid_arg int,tx_arg text,kind_arg text,login_arg text,ns uuid,pol bigint,inc uuid,man text) RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,w AS $$
DECLARE a w.actors;s w.state;c w.control;g w.ops;t text;BEGIN
 a=w.identity(true);SELECT * INTO STRICT s FROM w.state FOR UPDATE;SELECT * INTO STRICT c FROM w.control;
 IF req IS NULL OR op IS NULL OR d IS NULL OR d!~'^[0-9a-f]{64}$' OR sid_arg IS DISTINCT FROM a.sid OR pid_arg IS NULL OR pid_arg<=0 OR tx_arg IS NULL OR tx_arg!~'^[0-9]+$' OR ns IS DISTINCT FROM c.namespace OR pol IS DISTINCT FROM c.policy OR inc IS DISTINCT FROM a.incarnation OR man IS DISTINCT FROM a.manifest OR kind_arg IS NULL OR kind_arg NOT IN ('runtime','issuer') OR login_arg IS DISTINCT FROM (CASE kind_arg WHEN 'runtime' THEN 'cac_ctx_runtime' ELSE 'cac_ctx_issuer' END) THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 SELECT * INTO g FROM w.ops WHERE node=a.node AND request=req;
 IF FOUND THEN
  IF (g.id,g.digest,g.sid,g.dbpid,g.dbtx,g.kind,g.login,g.namespace,g.policy,g.incarnation,g.manifest) IS DISTINCT FROM (op,d,sid_arg,pid_arg,tx_arg,kind_arg,login_arg,ns,pol,inc,man) THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
  RETURN g.ticket;
 END IF;
 IF s.phase<>'active' OR s.owner IS DISTINCT FROM a.node OR EXISTS(SELECT 1 FROM w.ops o WHERE o.phase='unknown' OR (o.phase='open' AND NOT w.live(o))) THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 t=encode(public.gen_random_bytes(32),'hex');
 INSERT INTO w.ops(id,node,request,digest,epoch,incarnation,namespace,policy,manifest,sid,dbpid,dbtx,kind,login,ticket,holder,holder_start,phase) VALUES(op,a.node,req,d,s.epoch,inc,ns,pol,man,sid_arg,pid_arg,tx_arg,kind_arg,login_arg,t,pg_backend_pid(),(SELECT backend_start FROM pg_stat_activity WHERE pid=pg_backend_pid()),'open');
 RETURN t;
END $$;
CREATE FUNCTION w.hold(t text) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,w AS $$
DECLARE a w.actors;s w.state;g w.ops;BEGIN
 a=w.identity(true);SELECT * INTO STRICT s FROM w.state;SELECT * INTO STRICT g FROM w.ops WHERE ticket=t AND node=a.node;
 IF s.phase<>'active' OR s.owner IS DISTINCT FROM a.node OR s.epoch<>g.epoch OR g.phase<>'open' OR g.holder<>pg_backend_pid() OR NOT w.live(g) THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 PERFORM pg_advisory_xact_lock(g.lockid);
END $$;
CREATE FUNCTION w.close(t text,result text,pid_arg int,tx_arg text,sid_arg text) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,w AS $$
DECLARE a w.actors;g w.ops;s w.state;BEGIN
 -- Outcome authority is the trusted synthetic coordinator, never app/checker.
 a=w.identity(true);SELECT * INTO STRICT s FROM w.state;SELECT * INTO STRICT g FROM w.ops WHERE ticket=t AND node=a.node;
 IF result IS NULL OR result NOT IN ('commit','abort') OR g.phase<>'open' OR g.holder<>pg_backend_pid() OR NOT w.locked(g) OR (g.dbpid,g.dbtx,g.sid) IS DISTINCT FROM (pid_arg,tx_arg,sid_arg) OR s.owner IS DISTINCT FROM a.node OR s.epoch<>g.epoch THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 UPDATE w.ops SET phase='closed_'||result,outcome=jsonb_build_object('kind','trusted_local_ack','result',result,'dbpid',pid_arg,'dbtx',tx_arg,'sid',sid_arg) WHERE id=g.id;
END $$;
CREATE FUNCTION w.unknown(t text) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,w AS $$
DECLARE a w.actors;BEGIN
 a=w.identity(true);UPDATE w.ops SET phase='unknown' WHERE ticket=t AND node=a.node AND phase='open';
END $$;
CREATE FUNCTION w.attest(n text,mode_arg text,t text,sid_arg text,pid_arg int,tx_arg text,man text,d text,login_arg text) RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,w AS $$
DECLARE a w.actors;s w.state;c w.control;g w.ops;p jsonb;b bytea;BEGIN
 a=w.identity();SELECT * INTO STRICT s FROM w.state;SELECT * INTO STRICT c FROM w.control;
 IF n IS NULL OR n!~'^[0-9a-f]{64}$' OR mode_arg IS NULL OR d IS NULL OR sid_arg IS DISTINCT FROM a.sid OR man IS DISTINCT FROM a.manifest OR s.phase<>'active' OR s.owner IS DISTINCT FROM a.node OR EXISTS(SELECT 1 FROM w.ops o WHERE o.phase='unknown' OR (o.phase='open' AND NOT w.live(o))) THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 IF mode_arg='guard' THEN
  SELECT * INTO STRICT g FROM w.ops WHERE ticket=t AND node=a.node;
  IF g.phase<>'open' OR g.epoch<>s.epoch OR g.incarnation<>a.incarnation OR (g.sid,g.dbpid,g.dbtx,g.login) IS DISTINCT FROM (sid_arg,pid_arg,tx_arg,login_arg) OR NOT w.locked(g) OR (d<>'' AND d IS DISTINCT FROM g.digest) THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 ELSIF mode_arg<>'active' THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END IF;
 p=jsonb_build_object('v',1,'domain','cac-s009f-assumed','root',c.root,'namespace',c.namespace,'policy',c.policy,'owner',a.node,'incarnation',a.incarnation,'epoch',s.epoch,'nonce',n,'mode',mode_arg,'sid',sid_arg,'pid',pid_arg,'tx',tx_arg,'manifest',man,'login',login_arg,'op',g.id,'request',g.request,'digest',g.digest,'kind',g.kind,'ticket_hash',encode(public.digest(coalesce(t,''),'sha256'),'hex'));
 b=convert_to(p::text,'UTF8');RETURN encode(b,'hex')||'.'||encode(public.hmac(b,c.secret,'sha256'),'hex');
EXCEPTION WHEN OTHERS THEN RAISE EXCEPTION 'denied' USING ERRCODE='42501';END $$;
CREATE FUNCTION w.verify(proof text,n text,mode_arg text,t text,sid_arg text,pid_arg int,tx_arg text,man text,d text,login_arg text) RETURNS bool LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,w AS $$
BEGIN
 -- Online verification root stays in W; authenticated return channel ASSUMED.
 RETURN proof IS NOT NULL AND proof=w.attest(n,mode_arg,t,sid_arg,pid_arg,tx_arg,man,d,login_arg);
EXCEPTION WHEN OTHERS THEN RETURN false;END $$;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA w FROM PUBLIC;
RESET ROLE;
GRANT USAGE ON SCHEMA w TO cac_w_a_coord,cac_w_b_coord,cac_w_a_check,cac_w_b_check;
GRANT EXECUTE ON FUNCTION w.status(),w.attest(text,text,text,text,int,text,text,text,text),w.verify(text,text,text,text,text,int,text,text,text,text) TO cac_w_a_coord,cac_w_b_coord,cac_w_a_check,cac_w_b_check;
GRANT EXECUTE ON FUNCTION w.reserve(bigint,uuid),w.activate(uuid),w.revoke(bigint),w.admit(uuid,uuid,text,text,int,text,text,text,uuid,bigint,uuid,text),w.hold(text),w.close(text,text,int,text,text),w.unknown(text) TO cac_w_a_coord,cac_w_b_coord;
