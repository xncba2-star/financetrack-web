import streamlit as st
from supabase import create_client

def get_supabase():
    try:
        url=st.secrets["SUPABASE_URL"]
        key=st.secrets["SUPABASE_ANON_KEY"]
        return create_client(url,key)
    except Exception:
        return None
