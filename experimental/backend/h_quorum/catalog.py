"""Q_SURVIVAL_ONLY. Controller-owned catalog closure, no configuration row data."""
MEASURE="""
WITH ns AS (SELECT oid,nspname,nspowner,nspacl FROM pg_namespace WHERE nspname !~ '^pg_' AND nspname<>'information_schema')
SELECT encode(public.digest(jsonb_build_object(
 'functions',(SELECT jsonb_agg(jsonb_build_array(n.nspname,p.proname,pg_get_function_identity_arguments(p.oid),pg_get_functiondef(p.oid),p.proowner::regrole::text,p.proacl::text,p.prosecdef,p.proconfig) ORDER BY n.nspname,p.proname,pg_get_function_identity_arguments(p.oid)) FROM pg_proc p JOIN ns n ON n.oid=p.pronamespace WHERE p.prokind IN ('f','p')),
 'relations',(SELECT jsonb_agg(jsonb_build_array(n.nspname,r.relname,r.relkind,r.relowner::regrole::text,r.relacl::text,r.relrowsecurity,r.relforcerowsecurity,r.reloptions) ORDER BY n.nspname,r.relname) FROM pg_class r JOIN ns n ON n.oid=r.relnamespace WHERE r.relkind IN ('r','p','v','m','f','S')),
 'columns',(SELECT jsonb_agg(jsonb_build_array(n.nspname,r.relname,a.attname,format_type(a.atttypid,a.atttypmod),a.attnotnull,a.attacl::text,pg_get_expr(d.adbin,d.adrelid)) ORDER BY n.nspname,r.relname,a.attnum) FROM pg_class r JOIN ns n ON n.oid=r.relnamespace JOIN pg_attribute a ON a.attrelid=r.oid AND a.attnum>0 AND NOT a.attisdropped LEFT JOIN pg_attrdef d ON d.adrelid=r.oid AND d.adnum=a.attnum WHERE r.relkind IN ('r','p','v','m','f')),
 'constraints',(SELECT jsonb_agg(jsonb_build_array(n.nspname,r.relname,c.conname,pg_get_constraintdef(c.oid),c.convalidated) ORDER BY n.nspname,r.relname,c.conname) FROM pg_constraint c JOIN pg_class r ON r.oid=c.conrelid JOIN ns n ON n.oid=r.relnamespace),
 'triggers',(SELECT jsonb_agg(jsonb_build_array(n.nspname,r.relname,t.tgname,t.tgenabled,pg_get_triggerdef(t.oid)) ORDER BY n.nspname,r.relname,t.tgname) FROM pg_trigger t JOIN pg_class r ON r.oid=t.tgrelid JOIN ns n ON n.oid=r.relnamespace WHERE NOT t.tgisinternal),
 'rewrite_rules',(SELECT jsonb_agg(jsonb_build_array(n.nspname,r.relname,w.rulename,w.ev_enabled,pg_get_ruledef(w.oid)) ORDER BY n.nspname,r.relname,w.rulename) FROM pg_rewrite w JOIN pg_class r ON r.oid=w.ev_class JOIN ns n ON n.oid=r.relnamespace),
 'views',(SELECT jsonb_agg(jsonb_build_array(n.nspname,r.relname,pg_get_viewdef(r.oid)) ORDER BY n.nspname,r.relname) FROM pg_class r JOIN ns n ON n.oid=r.relnamespace WHERE r.relkind IN ('v','m')),
 'policies',(SELECT jsonb_agg(to_jsonb(p) ORDER BY schemaname,tablename,policyname) FROM pg_policies p WHERE schemaname !~ '^pg_'),
 'schemas',(SELECT jsonb_agg(jsonb_build_array(nspname,nspowner::regrole::text,nspacl::text) ORDER BY nspname) FROM ns),
 'extensions',(SELECT jsonb_agg(jsonb_build_array(e.extname,e.extversion,e.extowner::regrole::text,n.nspname) ORDER BY e.extname) FROM pg_extension e JOIN pg_namespace n ON n.oid=e.extnamespace),
 'database',(SELECT jsonb_build_array(datname,datdba::regrole::text,datacl::text) FROM pg_database WHERE datname=current_database()),
 'roles',(SELECT jsonb_agg(jsonb_build_array(rolname,rolsuper,rolcreaterole,rolcreatedb,rolreplication,rolbypassrls,rolinherit,rolconfig) ORDER BY rolname) FROM pg_roles),
 'memberships',(SELECT jsonb_agg(jsonb_build_array(roleid::regrole::text,member::regrole::text,admin_option,inherit_option,set_option) ORDER BY roleid::regrole::text,member::regrole::text) FROM pg_auth_members)
)::text,'sha256'),'hex')
"""
