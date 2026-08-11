"""
Streamlit UI components module.
Handles rendering for Add Record, View Records, and Search Records.
"""
import streamlit as st
from supabase import Client
from src.validation import validate_name, validate_nric, validate_unit_number
from src.database import add_record, get_all_records, search_records, delete_record, import_records_from_excel, export_records_to_excel

def render_add_record_tab(supabase: Client):
    st.header("➕ Add Resident Record")
    st.markdown("Enter resident details below. Unit numbers must be unique.")

    with st.form("add_record_form", clear_on_submit=True):
        name = st.text_input("Name", placeholder="e.g., John Tan")
        nric = st.text_input("NRIC (Last 3 digits + letter)", placeholder="e.g., 123A")
        unit_number = st.text_input("Unit Number", placeholder="e.g., #12-345")
        
        submitted = st.form_submit_button("Submit Record")
        
        if submitted:
            # Validation
            errors = []
            if not validate_name(name):
                errors.append("Name cannot be empty.")
            if not validate_nric(nric):
                errors.append("Invalid NRIC format. Expected last 3 digits and alphabet (e.g., 123A).")
            if not validate_unit_number(unit_number):
                errors.append("Invalid unit number format. Expected format like #12-345 or 12-345.")
                
            if errors:
                for err in errors:
                    st.error(err)
            else:
                success, message = add_record(supabase, name, nric, unit_number)
                if success:
                    st.success(message)
                else:
                    st.error(message)

def render_import_export_tab(supabase: Client):
    st.header("📂 Import / Export Records")
    st.markdown("Manage batch data operations using Excel files.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📥 Import from Excel")
        st.markdown("Upload an Excel file (.xlsx, .xls) containing columns: **Name**, **NRIC**, **Unit Number**.")
        uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx", "xls"])
        if uploaded_file is not None:
            if st.button("Process & Import Excel"):
                with st.spinner("Importing records..."):
                    success_count, failure_count, errors = import_records_from_excel(supabase, uploaded_file)
                    if success_count > 0:
                        st.success(f"Successfully imported {success_count} record(s).")
                    if failure_count > 0:
                        st.warning(f"Failed to import {failure_count} record(s):")
                        for err in errors:
                            st.error(err)
                    if success_count == 0 and failure_count == 0:
                        st.info("No records found in file.")
                        
    with col2:
        st.subheader("📤 Export to Excel")
        st.markdown("Download all current resident records as an Excel spreadsheet.")
        if st.button("Generate Excel Export"):
            with st.spinner("Preparing export..."):
                excel_bytes = export_records_to_excel(supabase)
                st.download_button(
                    label="📥 Download Excel File",
                    data=excel_bytes,
                    file_name="hdb_resident_records.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

def render_view_records_tab(supabase: Client):
    st.header("📋 Distribution Records List")
    st.markdown("Displaying all registered distribution tickets with sequential numbering. When an entry is deleted, subsequent ticket numbers automatically re-index.")
    
    records = get_all_records(supabase)
    
    if not records:
        st.info("No records found in the database.")
        return
        
    # Render table header
    hcol1, hcol2, hcol3, hcol4, hcol5, hcol6 = st.columns([1, 2, 2, 2, 2, 1])
    with hcol1:
        st.markdown("**Ticket**")
    with hcol2:
        st.markdown("**Name**")
    with hcol3:
        st.markdown("**NRIC**")
    with hcol4:
        st.markdown("**Unit Number**")
    with hcol5:
        st.markdown("**Date**")
    with hcol6:
        st.markdown("**Action**")
    st.divider()

    for idx, r in enumerate(records, start=1):
        col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 2, 2, 2, 1])
        with col1:
            st.write(f"#{idx}")
        with col2:
            st.write(r.get("name"))
        with col3:
            st.write(r.get("nric_masked"))
        with col4:
            st.write(r.get("unit_number"))
        with col5:
            created_at = r.get("created_at")
            st.write(created_at[:10] if created_at else "")
        with col6:
            record_id = r.get("id")
            if st.button("🗑️ Delete", key=f"del_{record_id}"):
                success, message = delete_record(supabase, record_id)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
        st.divider()

def render_search_records_tab(supabase: Client):
    st.header("🔍 Search Records")
    st.markdown("Search existing records by Name or Unit Number.")
    
    query = st.text_input("Search query", placeholder="Enter name or unit number (e.g., John or #12-345)")
    
    if st.button("Search") or query:
        results = search_records(supabase, query)
        if not results:
            st.warning("No matching records found.")
        else:
            st.success(f"Found {len(results)} matching record(s):")
            display_data = []
            for r in results:
                display_data.append({
                    "Name": r.get("name"),
                    "Masked NRIC": r.get("nric_masked"),
                    "Unit Number": r.get("unit_number"),
                    "Created Date": r.get("created_at")[:10] if r.get("created_at") else ""
                })
            st.dataframe(display_data, use_container_width=True)
