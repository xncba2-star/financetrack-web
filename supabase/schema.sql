-- RuangUang baseline schema. Execute in Supabase SQL Editor.
create extension if not exists pgcrypto;

create table if not exists public.workspaces (
 id uuid primary key default gen_random_uuid(),
 name text not null,
 kind text not null check (kind in ('personal','family')),
 created_by uuid not null references auth.users(id) on delete cascade,
 created_at timestamptz not null default now()
);

create table if not exists public.workspace_members (
 workspace_id uuid not null references public.workspaces(id) on delete cascade,
 user_id uuid not null references auth.users(id) on delete cascade,
 role text not null default 'owner' check (role in ('owner','member')),
 created_at timestamptz not null default now(),
 primary key(workspace_id,user_id)
);

create table if not exists public.transactions (
 id uuid primary key default gen_random_uuid(),
 workspace_id uuid not null references public.workspaces(id) on delete cascade,
 created_by uuid not null references auth.users(id) on delete cascade,
 kind text not null check (kind in ('income','expense','transfer')),
 amount numeric(14,2) not null check (amount>0),
 description text,
 transaction_date date not null default current_date,
 created_at timestamptz not null default now()
);

create table if not exists public.debt_records (
 id uuid primary key default gen_random_uuid(),
 workspace_id uuid not null references public.workspaces(id) on delete cascade,
 created_by uuid not null references auth.users(id) on delete cascade,
 record_type text not null check (record_type in ('debt','receivable')),
 person text not null,
 amount numeric(14,2) not null check (amount>0),
 due_date date,
 note text,
 created_at timestamptz not null default now()
);

create table if not exists public.debt_payments (
 id uuid primary key default gen_random_uuid(),
 debt_record_id uuid not null references public.debt_records(id) on delete cascade,
 created_by uuid not null references auth.users(id) on delete cascade,
 amount numeric(14,2) not null check (amount>0),
 payment_date date not null default current_date,
 created_at timestamptz not null default now()
);

create or replace function public.create_personal_workspace()
returns trigger language plpgsql security definer set search_path=public as $$
declare wid uuid;
begin
 insert into public.workspaces(name,kind,created_by)
 values ('Personal Finance','personal',new.id) returning id into wid;
 insert into public.workspace_members(workspace_id,user_id,role)
 values (wid,new.id,'owner');
 return new;
end; $$;

drop trigger if exists on_auth_user_created_workspace on auth.users;
create trigger on_auth_user_created_workspace
 after insert on auth.users for each row execute procedure public.create_personal_workspace();

alter table public.workspaces enable row level security;
alter table public.workspace_members enable row level security;
alter table public.transactions enable row level security;
alter table public.debt_records enable row level security;
alter table public.debt_payments enable row level security;

-- Membership helper. Security definer avoids recursive membership-policy evaluation.
create or replace function public.is_workspace_member(wid uuid)
returns boolean language sql stable security definer set search_path=public as $$
 select exists(select 1 from public.workspace_members m
 where m.workspace_id=wid and m.user_id=auth.uid());
$$;

create policy "members read workspaces" on public.workspaces for select
 using (public.is_workspace_member(id));
create policy "members read membership" on public.workspace_members for select
 using (user_id=auth.uid() or public.is_workspace_member(workspace_id));
create policy "members read transactions" on public.transactions for select
 using (public.is_workspace_member(workspace_id));
create policy "members insert transactions" on public.transactions for insert
 with check (public.is_workspace_member(workspace_id) and created_by=auth.uid());
create policy "members read debts" on public.debt_records for select
 using (public.is_workspace_member(workspace_id));
create policy "members insert debts" on public.debt_records for insert
 with check (public.is_workspace_member(workspace_id) and created_by=auth.uid());
create policy "members read payments" on public.debt_payments for select
 using (exists(select 1 from public.debt_records d where d.id=debt_record_id and public.is_workspace_member(d.workspace_id)));
create policy "members insert payments" on public.debt_payments for insert
 with check (created_by=auth.uid() and exists(select 1 from public.debt_records d where d.id=debt_record_id and public.is_workspace_member(d.workspace_id)));

-- Personal workspace auto-created on signup. Workspace sharing/invitation is not yet implemented.
