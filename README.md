# RuangUang Multi-User v3 (foundation)

Streamlit + Supabase Auth + PostgreSQL RLS foundation, with personal/family workspace membership, transactions, debt/receivables and payment history.

## Setup
1. Create a Supabase project.
2. Run `supabase/schema.sql` in the Supabase SQL Editor.
3. Push this folder to GitHub.
4. Deploy on Streamlit Community Cloud.
5. Add Streamlit secrets: `SUPABASE_URL` and `SUPABASE_ANON_KEY`.
6. Register in the app. A trigger creates a personal workspace for new users.

## Important
This is a foundation, not a production-audited financial application. Family-workspace creation/invitations, fine-grained roles, account/wallet transfers, receipt OCR, advanced reports, reminders, and security testing remain to be implemented. Verify RLS and Auth settings before inviting real users or storing sensitive financial data.
