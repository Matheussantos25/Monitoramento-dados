-- Run once in the same Supabase project as solem_items.
-- New health entries are private by account. Existing public treinos rows are not copied.
begin;
create table public.solem_health_entries (
 id uuid primary key default gen_random_uuid(),
 owner_id uuid not null default auth.uid() references auth.users(id),
 day date not null check (day between date '1900-01-01' and date '2200-12-31'),
 logged_at time not null,
 kind text not null check (kind in ('meal','water','weight','sleep')),
 details jsonb not null default '{}'::jsonb
   check (jsonb_typeof(details) = 'object' and octet_length(details::text) <= 4096),
 created_at timestamptz not null default now()
);
create index solem_health_entries_owner_day on public.solem_health_entries(owner_id, day desc, logged_at desc);
create unique index solem_health_entries_daily_once on public.solem_health_entries(owner_id, day, kind)
 where kind in ('weight', 'sleep');
alter table public.solem_health_entries enable row level security;
revoke all on public.solem_health_entries from anon, authenticated;
grant select, insert, update, delete on public.solem_health_entries to authenticated;
create policy solem_health_read on public.solem_health_entries for select to authenticated
 using (owner_id = (select auth.uid()));
create policy solem_health_insert on public.solem_health_entries for insert to authenticated
 with check (owner_id = (select auth.uid()));
create policy solem_health_update on public.solem_health_entries for update to authenticated
 using (owner_id = (select auth.uid())) with check (owner_id = (select auth.uid()));
create policy solem_health_delete on public.solem_health_entries for delete to authenticated
 using (owner_id = (select auth.uid()));
commit;
