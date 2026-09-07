-- Run once in the SAME Supabase project's SQL Editor as an administrator.
-- Does not modify treinos or its permissions. No public access to personal data.
begin;
create table public.solem_items (
 id uuid primary key,
 owner_id uuid not null default auth.uid() references auth.users(id),
 kind text not null check (kind in ('note','summary','mindmap','pdf','plan','investment')),
 title text not null check (length(btrim(title)) between 1 and 160),
 body text not null default '' check (length(body) <= 50000),
 event_date date,
 event_time text not null default '' check (event_time = '' or event_time ~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'),
 duration_minutes integer not null default 0 check (duration_minutes between 0 and 1440),
 done boolean not null default false,
 invested_cents bigint not null default 0 check (invested_cents between 0 and 999999999999),
 value_cents bigint not null default 0 check (value_cents between 0 and 999999999999),
 file_path text,
 archived boolean not null default false,
 revision integer not null default 1,
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(),
 check (kind not in ('plan','investment') or event_date is not null),
 check (kind <> 'plan' or duration_minutes > 0),
 check (event_date is null or event_date between date '1900-01-01' and date '2200-12-31'),
 check ((kind = 'pdf' and file_path = owner_id::text || '/' || id::text || '.pdf') or (kind <> 'pdf' and file_path is null))
);
create index solem_items_owner_date on public.solem_items(owner_id, created_at, id);
alter table public.solem_items enable row level security;
revoke all on public.solem_items from anon, authenticated;
grant select, insert, update on public.solem_items to authenticated;
create policy solem_items_read on public.solem_items for select to authenticated using (owner_id = (select auth.uid()));
create policy solem_items_insert on public.solem_items for insert to authenticated with check (owner_id = (select auth.uid()));
create policy solem_items_update on public.solem_items for update to authenticated using (owner_id = (select auth.uid())) with check (owner_id = (select auth.uid()));

create function public.solem_items_validate() returns trigger language plpgsql set search_path = '' as $$
declare line text; depth integer; previous_depth integer := -1; nodes integer := 0;
begin
 if TG_OP = 'UPDATE' then
   if new.id <> old.id or new.owner_id <> old.owner_id or new.kind <> old.kind or new.file_path is distinct from old.file_path then
     raise exception 'Identity and file path are immutable';
   end if;
   new.revision := old.revision + 1;
   new.created_at := old.created_at;
 else
   new.revision := 1;
   if new.kind = 'pdf' then new.file_path := new.owner_id::text || '/' || new.id::text || '.pdf'; end if;
 end if;
 new.updated_at := now();
 if new.kind = 'mindmap' then
   foreach line in array string_to_array(replace(new.body, E'\r', ''), E'\n') loop
     if btrim(line) = '' then continue; end if;
     nodes := nodes + 1;
     depth := length(line) - length(ltrim(line, ' '));
     if position(E'\t' in line) > 0 or depth % 2 <> 0 or depth > 10 or length(btrim(line)) > 160 then raise exception 'Invalid mind map indentation or label'; end if;
     depth := depth / 2;
     if (nodes = 1 and depth <> 0) or (nodes > 1 and depth = 0) or depth > previous_depth + 1 then raise exception 'Mind map needs one root and consecutive levels'; end if;
     previous_depth := depth;
   end loop;
   if nodes < 1 or nodes > 80 then raise exception 'Mind map needs 1 to 80 nodes'; end if;
 end if;
 return new;
end $$;
create trigger solem_items_validate before insert or update on public.solem_items for each row execute function public.solem_items_validate();
revoke all on function public.solem_items_validate() from public;

-- Private PDFs only, up to 10 MiB. Existing files cannot be overwritten by clients.
insert into storage.buckets(id, name, public, file_size_limit, allowed_mime_types)
values ('solem-documents', 'solem-documents', false, 10485760, array['application/pdf']);
create policy solem_pdf_read on storage.objects for select to authenticated using (
 bucket_id = 'solem-documents' and exists (select 1 from public.solem_items i where i.file_path = name and i.owner_id = (select auth.uid()) and not i.archived)
);
create policy solem_pdf_insert on storage.objects for insert to authenticated with check (
 bucket_id = 'solem-documents' and exists (select 1 from public.solem_items i where i.file_path = name and i.owner_id = (select auth.uid()) and not i.archived)
);
-- Restrictive guards prevent unrelated permissive Storage policies from opening
-- this NEW bucket. Other buckets keep their current behavior.
create policy solem_pdf_guard_read on storage.objects as restrictive for select to authenticated using (
 bucket_id <> 'solem-documents' or exists (select 1 from public.solem_items i where i.file_path = name and i.owner_id = (select auth.uid()) and not i.archived)
);
create policy solem_pdf_guard_insert on storage.objects as restrictive for insert to authenticated with check (
 bucket_id <> 'solem-documents' or exists (select 1 from public.solem_items i where i.file_path = name and i.owner_id = (select auth.uid()) and not i.archived)
);
create policy solem_pdf_guard_update on storage.objects as restrictive for update to authenticated using (bucket_id <> 'solem-documents') with check (bucket_id <> 'solem-documents');
create policy solem_pdf_guard_delete on storage.objects as restrictive for delete to authenticated using (bucket_id <> 'solem-documents');
create policy solem_pdf_guard_anon on storage.objects as restrictive for all to anon using (bucket_id <> 'solem-documents') with check (bucket_id <> 'solem-documents');
commit;
