create extension if not exists pgcrypto;

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

create table if not exists public.ideas (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users (id) on delete cascade,
  title text not null check (length(trim(title)) > 0),
  description text not null default '',
  status text not null default 'draft' check (status in ('draft', 'active', 'completed', 'archived')),
  source text not null default 'manual',
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create index if not exists idx_ideas_owner_status on public.ideas (owner_id, status);
create index if not exists idx_ideas_created_at on public.ideas (created_at desc);

create table if not exists public.products (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users (id) on delete cascade,
  slug text not null check (length(trim(slug)) > 0),
  name text not null check (length(trim(name)) > 0),
  description text not null default '',
  status text not null default 'active' check (status in ('active', 'paused', 'archived')),
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  unique (owner_id, slug)
);

create index if not exists idx_products_owner_status on public.products (owner_id, status);

create table if not exists public.decisions (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users (id) on delete cascade,
  idea_id uuid references public.ideas (id) on delete set null,
  product_id uuid references public.products (id) on delete set null,
  decision_text text not null check (length(trim(decision_text)) > 0),
  rationale text not null default '',
  decided_at timestamptz not null default timezone('utc', now()),
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create index if not exists idx_decisions_owner_decided_at on public.decisions (owner_id, decided_at desc);
create index if not exists idx_decisions_idea on public.decisions (idea_id);
create index if not exists idx_decisions_product on public.decisions (product_id);

create table if not exists public.translations (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users (id) on delete cascade,
  entity_type text not null check (entity_type in ('idea', 'decision', 'product', 'ui')),
  entity_id uuid,
  locale text not null,
  content_key text not null check (length(trim(content_key)) > 0),
  content_value text not null default '',
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists uq_translations_scope
  on public.translations (
    owner_id,
    entity_type,
    coalesce(entity_id, '00000000-0000-0000-0000-000000000000'::uuid),
    locale,
    content_key
  );

create index if not exists idx_translations_owner_locale on public.translations (owner_id, locale);

alter table public.ideas enable row level security;
alter table public.products enable row level security;
alter table public.decisions enable row level security;
alter table public.translations enable row level security;

do $$
begin
  if not exists (
    select 1 from pg_policies where schemaname = 'public' and tablename = 'ideas' and policyname = 'ideas_owner_access'
  ) then
    create policy ideas_owner_access on public.ideas
      for all
      using (auth.uid() = owner_id)
      with check (auth.uid() = owner_id);
  end if;
end;
$$;

do $$
begin
  if not exists (
    select 1 from pg_policies where schemaname = 'public' and tablename = 'products' and policyname = 'products_owner_access'
  ) then
    create policy products_owner_access on public.products
      for all
      using (auth.uid() = owner_id)
      with check (auth.uid() = owner_id);
  end if;
end;
$$;

do $$
begin
  if not exists (
    select 1 from pg_policies where schemaname = 'public' and tablename = 'decisions' and policyname = 'decisions_owner_access'
  ) then
    create policy decisions_owner_access on public.decisions
      for all
      using (auth.uid() = owner_id)
      with check (auth.uid() = owner_id);
  end if;
end;
$$;

do $$
begin
  if not exists (
    select 1 from pg_policies where schemaname = 'public' and tablename = 'translations' and policyname = 'translations_owner_access'
  ) then
    create policy translations_owner_access on public.translations
      for all
      using (auth.uid() = owner_id)
      with check (auth.uid() = owner_id);
  end if;
end;
$$;

do $$
begin
  if not exists (
    select 1 from pg_trigger where tgname = 'ideas_set_updated_at'
  ) then
    create trigger ideas_set_updated_at
      before update on public.ideas
      for each row execute function public.set_updated_at();
  end if;

  if not exists (
    select 1 from pg_trigger where tgname = 'products_set_updated_at'
  ) then
    create trigger products_set_updated_at
      before update on public.products
      for each row execute function public.set_updated_at();
  end if;

  if not exists (
    select 1 from pg_trigger where tgname = 'decisions_set_updated_at'
  ) then
    create trigger decisions_set_updated_at
      before update on public.decisions
      for each row execute function public.set_updated_at();
  end if;

  if not exists (
    select 1 from pg_trigger where tgname = 'translations_set_updated_at'
  ) then
    create trigger translations_set_updated_at
      before update on public.translations
      for each row execute function public.set_updated_at();
  end if;
end;
$$;
