-- Cindrela Sales Radar - PostgreSQL foundation
-- This schema is intentionally additive. Existing JSON files remain untouched.

create table if not exists events (
  id bigserial primary key,
  event_key text unique,
  title text not null,
  start_date date,
  end_date date,
  country text,
  city text,
  venue text,
  category text,
  source_url text,
  raw_data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists events_dates_idx on events (start_date, end_date);
create index if not exists events_title_idx on events (title);

create table if not exists public_lead_contacts (
  id bigserial primary key,
  lead_key text unique,
  event text,
  company text,
  country text,
  role text,
  contact_person text,
  business_email text,
  business_phone text,
  linkedin text,
  raw_data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists public_leads_event_idx on public_lead_contacts (event);
create index if not exists public_leads_company_idx on public_lead_contacts (company);
create index if not exists public_leads_country_idx on public_lead_contacts (country);
create index if not exists public_leads_email_idx on public_lead_contacts (business_email);

create table if not exists daily_intelligence (
  id bigserial primary key,
  item_key text unique,
  item_date date,
  title text,
  category text,
  raw_data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists intelligence_date_idx on daily_intelligence (item_date desc);
create index if not exists intelligence_category_idx on daily_intelligence (category);

create table if not exists lead_enrichment (
  id bigserial primary key,
  lead_key text unique,
  raw_data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists lead_enrichment_key_idx on lead_enrichment (lead_key);

create table if not exists event_candidates (
  id bigserial primary key,
  candidate_key text unique,
  event text,
  raw_data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists event_candidates_event_idx on event_candidates (event);
