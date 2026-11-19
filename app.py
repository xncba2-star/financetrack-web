import streamlit as st
from supabase_client import get_supabase
from data_service import get_workspaces, get_transactions, add_transaction, get_debts, add_debt, add_payment

st.set_page_config(page_title="RuangUang", page_icon="💰", layout="wide")
st.title("RuangUang")
st.caption("One platform. Personal and family finance.")

sb = get_supabase()
if not sb:
    st.info("Configure Supabase URL and key in Streamlit Secrets to start.")
    st.stop()

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    tab1, tab2 = st.tabs(["Login", "Register"])
    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pw")
        if st.button("Login"):
            try:
                res = sb.auth.sign_in_with_password({"email":email, "password":password})
                st.session_state.user = res.user
                st.rerun()
            except Exception as e: st.error(f"Login failed: {e}")
    with tab2:
        email2 = st.text_input("Email", key="reg_email")
        password2 = st.text_input("Password", type="password", key="reg_pw")
        if st.button("Create account"):
            try:
                res = sb.auth.sign_up({"email":email2, "password":password2})
                st.success("Account created. Check email if confirmation is required.")
            except Exception as e: st.error(f"Registration failed: {e}")
    st.stop()

user=st.session_state.user
st.sidebar.write(f"Signed in: {user.email}")
if st.sidebar.button("Logout"):
    sb.auth.sign_out()
    st.session_state.user=None
    st.rerun()

workspaces=get_workspaces(sb,user.id)
if not workspaces:
    st.warning("No workspace found. Run supabase/schema.sql in your Supabase SQL Editor.")
    st.stop()
ws_options={w["name"]:w["id"] for w in workspaces}
selected=st.sidebar.selectbox("Workspace",list(ws_options))
workspace_id=ws_options[selected]

pages=["Dashboard","Transactions","Debt & Receivables"]
page=st.sidebar.radio("Navigate",pages)

if page=="Dashboard":
    st.subheader(selected)
    tx=get_transactions(sb,workspace_id)
    income=sum(float(t["amount"]) for t in tx if t["kind"]=="income")
    expenses=sum(float(t["amount"]) for t in tx if t["kind"]=="expense")
    c1,c2,c3=st.columns(3)
    c1.metric("Income",f"Rp {income:,.0f}")
    c2.metric("Expense",f"Rp {expenses:,.0f}")
    c3.metric("Net",f"Rp {income-expenses:,.0f}")
    st.dataframe(tx, use_container_width=True)
elif page=="Transactions":
    st.subheader("Transactions")
    with st.form("transaction_form"):
        kind=st.selectbox("Type",["income","expense","transfer"])
        amount=st.number_input("Amount (Rp)",min_value=0.0,step=1000.0)
        description=st.text_input("Description")
        date=st.date_input("Date")
        submitted=st.form_submit_button("Save transaction")
    if submitted:
        try:
            add_transaction(sb,workspace_id,user.id,kind,amount,description,date.isoformat())
            st.success("Saved")
            st.rerun()
        except Exception as e: st.error(str(e))
    st.dataframe(get_transactions(sb,workspace_id),use_container_width=True)
else:
    st.subheader("Debt & Receivables")
    st.caption("Debt means you owe money; receivable means someone owes you. Payments are recorded separately.")
    with st.form("debt_form"):
        debt_type=st.selectbox("Record type",["debt","receivable"])
        person=st.text_input("Person / creditor / debtor")
        amount=st.number_input("Original amount (Rp)",min_value=0.0,step=1000.0)
        due=st.date_input("Due date")
        note=st.text_input("Notes")
        create=st.form_submit_button("Add record")
    if create:
        try:
            add_debt(sb,workspace_id,user.id,debt_type,person,amount,due.isoformat(),note)
            st.success("Record created")
            st.rerun()
        except Exception as e: st.error(str(e))
    records=get_debts(sb,workspace_id)
    for r in records:
        original=float(r["amount"])
        paid=float(r.get("paid_amount") or 0)
        remaining=max(original-paid,0)
        status="Paid" if remaining==0 else ("Partially paid" if paid>0 else "Unpaid")
        with st.expander(f'{r["record_type"].title()} · {r["person"]} · Remaining Rp {remaining:,.0f} · {status}'):
            st.write(f'Original: Rp {original:,.0f} | Paid: Rp {paid:,.0f} | Remaining: Rp {remaining:,.0f}')
            st.write(f'Due date: {r.get("due_date") or "—"}')
            st.write(r.get("note") or "")
            with st.form(f'pay_{r["id"]}'):
                payment=st.number_input("Payment amount (Rp)",min_value=0.0,max_value=remaining if remaining>0 else 0.0,step=1000.0,key=f'p_{r["id"]}')
                paydate=st.date_input("Payment date",key=f'd_{r["id"]}')
                paybutton=st.form_submit_button("Record payment")
            if paybutton and payment>0:
                try:
                    add_payment(sb,r["id"],user.id,payment,paydate.isoformat())
                    st.success("Payment recorded")
                    st.rerun()
                except Exception as e: st.error(str(e))
    st.divider()
    st.write("All debt/receivable records")
    st.dataframe(records,use_container_width=True)
