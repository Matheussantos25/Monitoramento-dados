-- Run once in the SAME Supabase project as treinos and solem_items.
-- Private, authenticated progress photos. No public URLs, no service_role in clients.
begin;
create table public.solem_photos (
 id uuid primary key,
 owner_id uuid not null default auth.uid() references auth.users(id),
 day date not null check (day between date '1900-01-01' and date '2200-12-31'),
 kind text not null check (kind in ('face','body')),
 file_path text not null,
 created_at timestamptz not null default now(),
 unique(owner_id, day, kind),
 check (file_path = owner_id::text || '/' || id::text || '.jpg')
);
create index solem_photos_owner_day on public.solem_photos(owner_id, day desc);
alter table public.solem_photos enable row level security;
revoke all on public.solem_photos from anon, authenticated;
grant select, insert, delete on public.solem_photos to authenticated;
create policy solem_photos_read on public.solem_photos for select to authenticated
 using (owner_id = (select auth.uid()));
create policy solem_photos_insert on public.solem_photos for insert to authenticated
 with check (owner_id = (select auth.uid()));
create policy solem_photos_delete on public.solem_photos for delete to authenticated
 using (owner_id = (select auth.uid()));

insert into storage.buckets(id, name, public, file_size_limit, allowed_mime_types)
values ('solem-progress-photos', 'solem-progress-photos', false, 4194304, array['image/jpeg']);
create policy solem_photo_read on storage.objects for select to authenticated using (
 bucket_id = 'solem-progress-photos' and exists (
   select 1 from public.solem_photos p where p.file_path = name and p.owner_id = (select auth.uid()))
);
create policy solem_photo_insert on storage.objects for insert to authenticated with check (
 bucket_id = 'solem-progress-photos' and exists (
   select 1 from public.solem_photos p where p.file_path = name and p.owner_id = (select auth.uid()))
);
create policy solem_photo_delete on storage.objects for delete to authenticated using (
 bucket_id = 'solem-progress-photos' and exists (
   select 1 from public.solem_photos p where p.file_path = name and p.owner_id = (select auth.uid()))
);
-- Keep unrelated permissive Storage policies from opening this new bucket.
create policy solem_photo_guard_read on storage.objects as restrictive for select to authenticated using (
 bucket_id <> 'solem-progress-photos' or exists (
   select 1 from public.solem_photos p where p.file_path = name and p.owner_id = (select auth.uid()))
);
create policy solem_photo_guard_insert on storage.objects as restrictive for insert to authenticated with check (
 bucket_id <> 'solem-progress-photos' or exists (
   select 1 from public.solem_photos p where p.file_path = name and p.owner_id = (select auth.uid()))
);
create policy solem_photo_guard_delete on storage.objects as restrictive for delete to authenticated using (
 bucket_id <> 'solem-progress-photos' or exists (
   select 1 from public.solem_photos p where p.file_path = name and p.owner_id = (select auth.uid()))
);
create policy solem_photo_guard_update on storage.objects as restrictive for update to authenticated
 using (bucket_id <> 'solem-progress-photos') with check (bucket_id <> 'solem-progress-photos');
create policy solem_photo_guard_anon on storage.objects as restrictive for all to anon
 using (bucket_id <> 'solem-progress-photos') with check (bucket_id <> 'solem-progress-photos');
commit;
