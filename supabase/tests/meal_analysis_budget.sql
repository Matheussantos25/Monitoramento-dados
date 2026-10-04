-- Administrator-only diagnostic. All synthetic counters and claims are rolled back.
begin;
select pg_advisory_xact_lock(610042026);
do $$
declare
 stamp date := (clock_timestamp() at time zone 'UTC')::date;
 counter integer;
begin
 if has_table_privilege('authenticated','public.solem_meal_analysis_budget','SELECT')
  or has_table_privilege('anon','public.solem_meal_analysis_budget','SELECT')
  or has_function_privilege('anon','public.solem_reserve_meal_analysis()','EXECUTE') then
  raise exception 'Counter access must be private';
 end if;
 if not (select relrowsecurity from pg_class where oid='public.solem_meal_analysis_budget'::regclass) then
  raise exception 'RLS missing';
 end if;
 perform set_config('request.jwt.claim.sub','61111111-1111-1111-1111-111111111111',true);
 insert into public.solem_meal_analysis_budget(scope,day,used,last_request)
 values ('global',stamp,0,clock_timestamp()-interval '1 minute')
 on conflict(scope,day) do update set used=0;
 for counter in 1..6 loop
  if not public.solem_reserve_meal_analysis() then raise exception 'Allowed reservation failed'; end if;
  if public.solem_reserve_meal_analysis() then raise exception 'Cooldown bypassed'; end if;
  update public.solem_meal_analysis_budget set last_request=clock_timestamp()-interval '1 minute'
   where scope='61111111-1111-1111-1111-111111111111' and day=stamp;
 end loop;
 if public.solem_reserve_meal_analysis() then raise exception 'Daily per-user cap bypassed'; end if;
 perform set_config('request.jwt.claim.sub','62222222-2222-2222-2222-222222222222',true);
 update public.solem_meal_analysis_budget set used=20 where scope='global' and day=stamp;
 if public.solem_reserve_meal_analysis() then raise exception 'Shared cap bypassed'; end if;
 perform set_config('request.jwt.claim.sub','',true);
 begin
  perform public.solem_reserve_meal_analysis();
  raise exception 'No user allowed';
 exception when insufficient_privilege then null;
 end;
end;
$$;
rollback;
select 'PASS: RLS/private counters, cooldown, 6/user/day, 20/app/day, missing user denied; synthetic writes rolled back.' as result;
