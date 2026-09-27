-- Run once in the SAME Supabase project as solem_items, as a database administrator.
-- Existing investment records and the per-user RLS policies are preserved.
begin;
alter table public.solem_items drop constraint solem_items_kind_check;
alter table public.solem_items add constraint solem_items_kind_check
  check (kind in ('note','summary','mindmap','pdf','plan','investment','salary','subscription'));
alter table public.solem_items add column billing_cycle text not null default ''
  check (billing_cycle in ('','monthly','annual'));
alter table public.solem_items add constraint solem_finance_fields_check check (
  (kind not in ('salary','subscription') or (event_date is not null and value_cents > 0))
  and (kind <> 'subscription' or billing_cycle in ('monthly','annual'))
  and (kind = 'subscription' or billing_cycle = '')
);
commit;
