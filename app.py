"""
Main Streamlit application entry point for Rivervale Food Distribution.
"""
import streamlit as st
from src.database import init_supabase_client
from src.ui import render_add_record_tab, render_view_records_tab, render_search_records_tab, render_import_export_tab

# Page configuration
st.set_page_config(
    page_title="Rivervale Food Distribution",
    page_icon="📦",
    layout="centered"
)

def main():
    st.title("📦 Rivervale Food Distribution")
    st.markdown("Manage food distribution records with secure privacy protection and sequential ticket numbering.")
    
    # Check if secrets are configured
    if "SUPABASE_URL" not in st.secrets or "SUPABASE_KEY" not in st.secrets:
        st.error("❌ Supabase credentials (`SUPABASE_URL` and `SUPABASE_KEY`) are missing from Streamlit secrets (`.streamlit/secrets.toml`). Please configure them to continue.")
        st.stop()
        
    try:
        supabase = init_supabase_client()
    except Exception as e:
        st.error("❌ Failed to connect to Supabase. Please check your credentials and network connection.")
        st.stop()
        
    # Navigation tabs
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Add Record", "📋 View Records", "🔍 Search Records", "📂 Import / Export"])
    
    with tab1:
        render_add_record_tab(supabase)
        
    with tab2:
        render_view_records_tab(supabase)
        
    with tab3:
        render_search_records_tab(supabase)
        
    with tab4:
        render_import_export_tab(supabase)

if __name__ == "__main__":
    main()
