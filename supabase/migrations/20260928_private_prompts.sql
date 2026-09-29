-- Apply once in the existing Solem Supabase project after 20260927_finance.sql.
-- Personal prompt copies inherit solem_items owner-scoped RLS and recoverable archive.
begin;
alter table public.solem_items drop constraint solem_items_kind_check;
alter table public.solem_items add constraint solem_items_kind_check
  check (kind in ('note','summary','mindmap','pdf','plan','investment','salary','subscription','prompt'));
commit;
