-- Additive private creator workspace. Existing activities/health/XP are untouched.
begin;
create table if not exists public.solem_journey_settings (
  owner_id uuid primary key default auth.uid() references auth.users(id) on delete cascade,
  preferences jsonb not null check (jsonb_typeof(preferences) = 'object' and octet_length(preferences::text) <= 20000),
  revision integer not null default 1,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create table if not exists public.solem_creator_items (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  kind text not null check (kind in ('channel','video')),
  title text not null check (length(trim(title)) between 1 and 160),
  body text not null default '' check (length(body) <= 10000),
  channel_id uuid references public.solem_creator_items(id),
  stage text check (stage in ('Ideia','Roteiro','Gravação','Edição','Pronto','Publicado')),
  produced_on date,
  published_on date,
  url text not null default '' check (length(url) <= 2000 and (url='' or url ~ '^https?://')),
  archived boolean not null default false,
  revision integer not null default 1,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint creator_dates_valid check (
    (kind='channel' and channel_id is null and stage is null and produced_on is null and published_on is null)
    or (kind='video' and channel_id is not null and stage is not null
      and ((stage in ('Pronto','Publicado')) = (produced_on is not null))
      and ((stage='Publicado') = (published_on is not null))
      and (published_on is null or published_on >= produced_on))
  )
);
create index if not exists creator_owner_created on public.solem_creator_items(owner_id,created_at,id);
alter table public.solem_journey_settings enable row level security;
alter table public.solem_creator_items enable row level security;
revoke all on public.solem_journey_settings, public.solem_creator_items from anon, authenticated;
grant select, insert, update on public.solem_journey_settings, public.solem_creator_items to authenticated;
do $$
declare t text;
begin
  foreach t in array array['solem_journey_settings','solem_creator_items'] loop
    if not exists (select 1 from pg_policies where schemaname='public' and tablename=t and policyname='owner_read') then
      execute format('create policy owner_read on public.%I for select to authenticated using (owner_id = (select auth.uid()))',t);
      execute format('create policy owner_insert on public.%I for insert to authenticated with check (owner_id = (select auth.uid()))',t);
      execute format('create policy owner_update on public.%I for update to authenticated using (owner_id = (select auth.uid())) with check (owner_id = (select auth.uid()))',t);
    end if;
  end loop;
end $$;
create or replace function public.solem_journey_revision() returns trigger
language plpgsql set search_path = '' as $$
begin
  if new.owner_id is distinct from old.owner_id then raise exception 'Owner is immutable'; end if;
  new.created_at := old.created_at;
  new.revision := old.revision + 1;
  new.updated_at := now();
  return new;
end $$;
create or replace function public.solem_creator_guard() returns trigger
language plpgsql set search_path = '' as $$
begin
  if tg_op = 'UPDATE' then
    if new.id <> old.id or new.kind <> old.kind then raise exception 'Identity is immutable'; end if;
  end if;
  if new.kind='video' and not exists (
    select 1 from public.solem_creator_items c where c.id=new.channel_id and c.owner_id=new.owner_id and c.kind='channel'
  ) then raise exception 'Channel must belong to the same account'; end if;
  return new;
end $$;
create or replace trigger journey_settings_revision before update on public.solem_journey_settings
for each row execute function public.solem_journey_revision();
create or replace trigger journey_item_revision before update on public.solem_creator_items
for each row execute function public.solem_journey_revision();
create or replace trigger journey_item_guard before insert or update on public.solem_creator_items
for each row execute function public.solem_creator_guard();
revoke all on function public.solem_journey_revision(), public.solem_creator_guard() from public;
-- Seed only the specifically requested personal channel, without touching history.
insert into public.solem_creator_items(owner_id,kind,title,body)
select u.id,'channel','Canal principal · Gacha','Meu canal principal de vídeos Gacha.'
from auth.users u where lower(u.email)='msdof25@gmail.com'
and not exists (select 1 from public.solem_creator_items i where i.owner_id=u.id and i.kind='channel');
notify pgrst, 'reload schema';
commit;
