-- Administrator-only diagnostic. No records, users or policies are modified.
-- SET ROLE ensures SELECT runs with application privileges, not postgres bypass.
begin;
select set_config('solem.audit_owner', (select id::text from auth.users where lower(email)='msdof25@gmail.com'), true);
select set_config('solem.audit_others', (select coalesce(jsonb_agg(id), '[]'::jsonb)::text from auth.users where lower(email)<>'msdof25@gmail.com'), true);
select set_config('solem.audit_total', (select count(*)::text from public.treinos), true);
set local role authenticated;
do $$
declare account_id text; owner_rows bigint; tested integer := 0;
begin
    for account_id in select jsonb_array_elements_text(current_setting('solem.audit_others')::jsonb) loop
        perform set_config('request.jwt.claims', jsonb_build_object('sub',account_id,'role','authenticated')::text, true);
        perform set_config('request.jwt.claim.sub',account_id,true);
        if exists(select 1 from public.treinos) then raise exception 'Other account can read legacy history'; end if;
        if exists(select 1 from public.solem_activities where user_id::text <> account_id) then raise exception 'Cross-account activities'; end if;
        if exists(select 1 from public.solem_health_entries where owner_id::text <> account_id) then raise exception 'Cross-account health'; end if;
        tested := tested + 1;
    end loop;
    account_id := current_setting('solem.audit_owner');
    perform set_config('request.jwt.claims', jsonb_build_object('sub',account_id,'role','authenticated')::text,true);
    perform set_config('request.jwt.claim.sub',account_id,true);
    select count(*) into owner_rows from public.treinos;
    if owner_rows <> current_setting('solem.audit_total')::bigint then raise exception 'Owner history changed'; end if;
    perform set_config('solem.audit_result',jsonb_build_object('owner_rows',owner_rows,'other_accounts_tested',tested,'other_accounts_legacy_rows',0,'cross_account_private_rows',0)::text,true);
end $$;
set local role anon;
select set_config('request.jwt.claim.sub','',true), set_config('request.jwt.claims','{}',true);
do $$ begin
    if exists(select 1 from public.treinos) then raise exception 'Anonymous legacy access'; end if;
end $$;
reset role;
select current_setting('solem.audit_result')::jsonb || jsonb_build_object('anonymous_legacy_rows',0,'result','PASS') as isolation_audit;
commit;
