-- Same project. Additive only: no INSERT/UPDATE/DELETE/ALTER on legacy treinos.
begin;
create table if not exists public.solem_activities (
    like public.treinos including defaults including identity including constraints including indexes,
    user_id uuid not null default auth.uid() references auth.users(id)
);
alter table public.solem_activities enable row level security;
revoke all on public.solem_activities from anon;
grant select, insert, update, delete on public.solem_activities to authenticated;
do $$
begin
    if not exists (select 1 from pg_policies where schemaname='public'
                   and tablename='solem_activities' and policyname='Own activities') then
        create policy "Own activities" on public.solem_activities
        for all to authenticated using (user_id = auth.uid())
        with check (user_id = auth.uid());
    end if;
    if exists (select 1 from pg_publication where pubname='supabase_realtime')
       and not exists (select 1 from pg_publication_tables
                       where pubname='supabase_realtime' and schemaname='public'
                       and tablename='solem_activities') then
        alter publication supabase_realtime add table public.solem_activities;
    end if;
end $$;
commit;
