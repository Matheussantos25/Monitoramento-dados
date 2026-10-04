-- Same Supabase project. No changes to health entries or legacy treinos.
begin;
create table if not exists public.solem_meal_analysis_budget (
 scope text not null,
 day date not null,
 used integer not null default 0 check (used >= 0),
 last_request timestamptz not null default now(),
 primary key (scope, day)
);
alter table public.solem_meal_analysis_budget enable row level security;
revoke all on public.solem_meal_analysis_budget from public, anon, authenticated;

create or replace function public.solem_reserve_meal_analysis() returns boolean
language plpgsql security definer set search_path = '' as $$
declare
 caller uuid := auth.uid();
 utc_day date := (clock_timestamp() at time zone 'UTC')::date;
 stamp timestamptz := clock_timestamp();
 global_used integer;
 user_used integer;
 previous_request timestamptz;
begin
 if caller is null then raise insufficient_privilege; end if;
 -- One lock for all reservations: concurrent calls cannot race past the cap.
 perform pg_advisory_xact_lock(610042026);
 -- Keep only aggregate counters, never image/prompt/result/history.
 delete from public.solem_meal_analysis_budget where day < utc_day - 2;
 select used into global_used from public.solem_meal_analysis_budget where scope = 'global' and day = utc_day;
 select used, last_request into user_used, previous_request from public.solem_meal_analysis_budget
  where scope = caller::text and day = utc_day;
 -- Conservative application limits; Google project quotas can be lower.
 if coalesce(global_used, 0) >= 20 or coalesce(user_used, 0) >= 6
  or previous_request > stamp - interval '30 seconds' then return false; end if;
 insert into public.solem_meal_analysis_budget(scope, day, used, last_request)
 values ('global', utc_day, 1, stamp), (caller::text, utc_day, 1, stamp)
 on conflict (scope, day) do update set used = solem_meal_analysis_budget.used + 1, last_request = excluded.last_request;
 return true;
end;
$$;
revoke all on function public.solem_reserve_meal_analysis() from public, anon;
grant execute on function public.solem_reserve_meal_analysis() to authenticated;
commit;
