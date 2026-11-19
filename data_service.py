def get_workspaces(sb,user_id):
    # Workspace membership policies in schema.sql restrict rows to the signed-in user.
    return sb.table("workspace_members").select("workspace_id,workspaces(id,name,kind)").eq("user_id",user_id).execute().data and [
        {"id":row["workspace_id"],"name":row["workspaces"]["name"],"kind":row["workspaces"]["kind"]}
        for row in sb.table("workspace_members").select("workspace_id,workspaces(id,name,kind)").eq("user_id",user_id).execute().data
        if row.get("workspaces")
    ] or []

def get_transactions(sb,workspace_id):
    return sb.table("transactions").select("*").eq("workspace_id",workspace_id).order("transaction_date",desc=True).execute().data

def add_transaction(sb,workspace_id,user_id,kind,amount,description,date):
    if amount<=0: raise ValueError("Amount must be greater than zero.")
    sb.table("transactions").insert({"workspace_id":workspace_id,"created_by":user_id,"kind":kind,"amount":amount,"description":description,"transaction_date":date}).execute()

def get_debts(sb,workspace_id):
    rows=sb.table("debt_records").select("*,debt_payments(amount)").eq("workspace_id",workspace_id).order("created_at",desc=True).execute().data
    for row in rows:
        row["paid_amount"]=sum(float(p["amount"]) for p in row.get("debt_payments",[]))
    return rows

def add_debt(sb,workspace_id,user_id,record_type,person,amount,due_date,note):
    if amount<=0: raise ValueError("Amount must be greater than zero.")
    if not person.strip(): raise ValueError("Please enter a person or institution.")
    sb.table("debt_records").insert({"workspace_id":workspace_id,"created_by":user_id,"record_type":record_type,"person":person,"amount":amount,"due_date":due_date,"note":note}).execute()

def add_payment(sb,record_id,user_id,amount,payment_date):
    if amount<=0: raise ValueError("Payment must be greater than zero.")
    record=sb.table("debt_records").select("amount,debt_payments(amount)").eq("id",record_id).single().execute().data
    paid=sum(float(p["amount"]) for p in record.get("debt_payments",[]))
    remaining=float(record["amount"])-paid
    if amount>remaining: raise ValueError("Payment exceeds remaining balance.")
    sb.table("debt_payments").insert({"debt_record_id":record_id,"created_by":user_id,"amount":amount,"payment_date":payment_date}).execute()
