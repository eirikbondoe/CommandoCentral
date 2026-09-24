create table if not exists public.notion_pages (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users (id) on delete cascade,
  notion_page_id text not null,
  notion_database_id text not null,
  title text,
  status text,
  tags text[] not null default '{}',
  notion_url text,
  created_time timestamptz,
  last_edited_time timestamptz,
  raw_properties jsonb not null default '{}'::jsonb,
  raw_page jsonb not null default '{}'::jsonb,
  synced_at timestamptz not null default timezone('utc', now()),
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  unique (owner_id, notion_page_id)
);

create index if not exists idx_notion_pages_database on public.notion_pages (owner_id, notion_database_id);
create index if not exists idx_notion_pages_last_edited on public.notion_pages (last_edited_time desc nulls last);
create index if not exists idx_notion_pages_tags on public.notion_pages using gin (tags);
create index if not exists idx_notion_pages_raw_properties on public.notion_pages using gin (raw_properties);

alter table public.notion_pages enable row level security;

do $$
begin
  if not exists (
    select 1 from pg_policies where schemaname = 'public' and tablename = 'notion_pages' and policyname = 'notion_pages_owner_access'
  ) then
    create policy notion_pages_owner_access on public.notion_pages
      for all
      using (auth.uid() = owner_id)
      with check (auth.uid() = owner_id);
  end if;
end;
$$;

do $$
begin
  if not exists (
    select 1 from pg_trigger where tgname = 'notion_pages_set_updated_at'
  ) then
    create trigger notion_pages_set_updated_at
      before update on public.notion_pages
      for each row execute function public.set_updated_at();
  end if;
end;
$$;

create table if not exists public.backup_runs (
  id uuid primary key default gen_random_uuid(),
  initiated_by uuid references auth.users (id) on delete set null,
  trigger_source text not null default 'external',
  status text not null default 'queued' check (status in ('queued', 'running', 'succeeded', 'failed', 'partial')),
  started_at timestamptz not null default timezone('utc', now()),
  completed_at timestamptz,
  object_path text,
  object_checksum text,
  object_size_bytes bigint check (object_size_bytes is null or object_size_bytes >= 0),
  retention_class text not null default 'daily' check (retention_class in ('daily', 'weekly', 'monthly', 'manual', 'pitr')),
  provider text not null default 'external',
  error_message text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create index if not exists idx_backup_runs_status_started_at on public.backup_runs (status, started_at desc);
create index if not exists idx_backup_runs_retention_completed_at on public.backup_runs (retention_class, completed_at desc nulls last);

alter table public.backup_runs enable row level security;

comment on table public.backup_runs is 'Backup audit log. Populate from external backup infrastructure (GitHub Actions, managed backup tooling, or PITR reconciliation jobs).';

do $$
begin
  if not exists (
    select 1 from pg_trigger where tgname = 'backup_runs_set_updated_at'
  ) then
    create trigger backup_runs_set_updated_at
      before update on public.backup_runs
      for each row execute function public.set_updated_at();
  end if;
end;
$$;
