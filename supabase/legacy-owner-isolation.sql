-- Apply AFTER deploying clients that authenticate legacy requests.
-- No records are changed or deleted. Additional restrictive policy closes the
-- existing public ALL policy without replacing unrelated policies.
begin;
do $$
declare owner_uuid uuid;
begin
    select id into strict owner_uuid from auth.users where lower(email) = 'msdof25@gmail.com';
    if not exists (select 1 from pg_policies where schemaname='public' and tablename='treinos'
                   and policyname='Legacy history owner only') then
        execute format('create policy "Legacy history owner only" on public.treinos as restrictive for all to public using ((select auth.uid()) = %L::uuid) with check ((select auth.uid()) = %L::uuid)', owner_uuid, owner_uuid);
    end if;
end $$;
alter table public.treinos enable row level security;
commit;
