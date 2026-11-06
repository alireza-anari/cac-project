"""W_ORACLE_ASSUMED. External controller measures this catalog query itself."""

# Deliberately excludes configuration rows, credentials and fixture data. A local
# verifier cannot self-certify: admission uses this controller-owned query too.
MEASURE = """
SELECT encode(public.digest(jsonb_build_object(
 'functions',(SELECT jsonb_agg(jsonb_build_array(n.nspname,p.proname,
   pg_get_function_identity_arguments(p.oid),pg_get_functiondef(p.oid),
   p.proowner::regrole::text,p.proacl::text,p.prosecdef,p.proconfig)
   ORDER BY n.nspname,p.proname,pg_get_function_identity_arguments(p.oid))
   FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
   WHERE n.nspname IN ('poc','poc_private','fence','fence_private','w_guard')),
 'relations',(SELECT jsonb_agg(jsonb_build_array(n.nspname,r.relname,
   r.relowner::regrole::text,r.relacl::text,r.relrowsecurity,r.relforcerowsecurity)
   ORDER BY n.nspname,r.relname) FROM pg_class r JOIN pg_namespace n ON n.oid=r.relnamespace
   WHERE n.nspname IN ('poc','poc_private','fence','fence_private','w_guard') AND r.relkind IN ('r','S')),
 'schemas',(SELECT jsonb_agg(jsonb_build_array(nspname,nspowner::regrole::text,nspacl::text)
   ORDER BY nspname) FROM pg_namespace WHERE nspname IN ('poc','poc_private','fence','fence_private','w_guard')),
 'policies',(SELECT jsonb_agg(to_jsonb(p) ORDER BY policyname) FROM pg_policies p WHERE schemaname='poc'),
 'roles',(SELECT jsonb_agg(jsonb_build_array(rolname,rolsuper,rolcreaterole,rolcreatedb,
   rolreplication,rolbypassrls,rolinherit) ORDER BY rolname) FROM pg_roles
   WHERE rolname IN ('cac_ctx_runtime','cac_ctx_issuer','cac_ctx_guard','cac_fence_activator')),
 'membership',(SELECT coalesce(jsonb_agg(jsonb_build_array(roleid::regrole::text,
   member::regrole::text,admin_option,inherit_option,set_option) ORDER BY roleid::regrole::text,member::regrole::text),'[]'::jsonb)
   FROM pg_auth_members WHERE member IN ('cac_ctx_runtime'::regrole,'cac_ctx_issuer'::regrole,'cac_fence_activator'::regrole))
)::text,'sha256'),'hex')
"""
