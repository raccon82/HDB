"""
Streamlit UI components module.
Handles rendering for Add Record, View Records, and Search Records.
"""
import streamlit as st
import streamlit.components.v1 as components
from supabase import Client
from src.validation import validate_name, validate_nric, validate_unit_number
from src.database import add_record, get_all_records, search_records, delete_record, import_records_from_excel, export_records_to_excel

@st.dialog("Registration Successful!")
def show_registration_success_dialog(details: dict):
    st.write(f"**Ticket Number:** #{details.get('ticket_no')}")
    st.write(f"**Name:** {details.get('name')}")
    st.write(f"**NRIC:** {details.get('nric_masked')}")
    st.write(f"**Unit Number:** {details.get('unit_number')}")
    blk = details.get('block_number')
    st.write(f"**Block Number:** {blk if blk else 'N/A'}")
    
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Register Another Resident", type="primary", use_container_width=True):
            st.session_state["reg_name"] = ""
            st.session_state["reg_nric"] = ""
            st.session_state["reg_unit"] = ""
            st.session_state["reg_block"] = ""
            st.session_state["success_details"] = None
            st.rerun()
    with col2:
        if st.button("Close", use_container_width=True):
            st.session_state["success_details"] = None
            st.rerun()

def render_add_record_tab(supabase: Client):
    st.header("➕ Add Resident Record")
    st.markdown("Enter resident details below. Unit numbers must be unique.")

    if "reg_name" not in st.session_state:
        st.session_state["reg_name"] = ""
    if "reg_nric" not in st.session_state:
        st.session_state["reg_nric"] = ""
    if "reg_unit" not in st.session_state:
        st.session_state["reg_unit"] = ""
    if "reg_block" not in st.session_state:
        st.session_state["reg_block"] = ""
    if "success_details" not in st.session_state:
        st.session_state["success_details"] = None

    if st.session_state.get("success_details"):
        show_registration_success_dialog(st.session_state["success_details"])

    with st.form("add_record_form"):
        name = st.text_input("Name", key="reg_name", placeholder="e.g., John Tan")
        nric = st.text_input("NRIC (Last 3 digits + letter)", key="reg_nric", placeholder="e.g., 123A")
        unit_number = st.text_input("Unit Number", key="reg_unit", placeholder="e.g., #12-345")
        block_number = st.text_input("Block Number (Optional)", key="reg_block", placeholder="e.g., 123")
        
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
                success, message, record_details = add_record(supabase, name, nric, unit_number, block_number)
                if success and record_details:
                    st.session_state["success_details"] = record_details
                    st.rerun()
                else:
                    st.error(message)

def render_import_export_tab(supabase: Client):
    st.header("📂 Import / Export Records")
    st.markdown("Manage batch data operations using Excel files.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📥 Import from Excel")
        st.markdown("Upload an Excel file (.xlsx, .xls) containing columns: **Name**, **NRIC**, **Unit Number**, and optionally **Block Number**.")
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
    hcol1, hcol2, hcol3, hcol4, hcol5, hcol6, hcol7 = st.columns([1, 2, 2, 2, 2, 2, 1])
    with hcol1:
        st.markdown("**Ticket**")
    with hcol2:
        st.markdown("**Name**")
    with hcol3:
        st.markdown("**NRIC**")
    with hcol4:
        st.markdown("**Unit Number**")
    with hcol5:
        st.markdown("**Block Number**")
    with hcol6:
        st.markdown("**Date**")
    with hcol7:
        st.markdown("**Action**")
    st.divider()

    for idx, r in enumerate(records, start=1):
        col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 2, 2, 2, 2, 2, 1])
        with col1:
            st.write(f"#{idx}")
        with col2:
            st.write(r.get("name"))
        with col3:
            st.write(r.get("nric_masked"))
        with col4:
            st.write(r.get("unit_number"))
        with col5:
            st.write(r.get("block_number") or "-")
        with col6:
            created_at = r.get("created_at")
            st.write(created_at[:10] if created_at else "")
        with col7:
            record_id = r.get("id")
            if st.button("🗑️ Delete", key=f"del_{record_id}"):
                success, message = delete_record(supabase, record_id)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
        st.divider()

    # Inject Floating Back to Top Button into parent document
    components.html(
        """
        <script>
        (function() {
            const parentDoc = window.parent.document;
            let btn = parentDoc.getElementById('st-back-to-top-btn');
            if (!btn) {
                btn = parentDoc.createElement('button');
                btn.id = 'st-back-to-top-btn';
                btn.innerHTML = '↑ Back to Top';
                btn.style.cssText = `
                    position: fixed;
                    bottom: 24px;
                    right: 24px;
                    z-index: 999999;
                    background-color: #262730;
                    color: #FAFAFA;
                    border: 1px solid #4A4D5A;
                    border-radius: 8px;
                    padding: 10px 16px;
                    font-size: 14px;
                    font-weight: 500;
                    font-family: Source Sans Pro, -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
                    cursor: pointer;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
                    transition: all 0.2s ease-in-out;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                `;
                
                btn.onmouseover = function() {
                    btn.style.backgroundColor = '#31333F';
                    btn.style.borderColor = '#FF4B4B';
                    btn.style.color = '#FFFFFF';
                    btn.style.transform = 'translateY(-2px)';
                    btn.style.boxShadow = '0 6px 16px rgba(0, 0, 0, 0.6)';
                };
                btn.onmouseout = function() {
                    btn.style.backgroundColor = '#262730';
                    btn.style.borderColor = '#4A4D5A';
                    btn.style.color = '#FAFAFA';
                    btn.style.transform = 'translateY(0)';
                    btn.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.4)';
                };

                parentDoc.body.appendChild(btn);
            }

            btn.style.display = 'flex';
            btn.onclick = function(e) {
                if (e) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                const doc = window.parent ? window.parent.document : document;
                const scrollables = [
                    doc.querySelector('[data-testid="stAppViewContainer"]'),
                    doc.querySelector('[data-testid="stMain"]'),
                    doc.querySelector('section.main'),
                    doc.querySelector('.main'),
                    doc.querySelector('.stMain'),
                    doc.querySelector('[data-testid="stMainBlockContainer"]'),
                    doc.documentElement,
                    doc.body,
                    window.parent,
                    window
                ];
                for (let el of scrollables) {
                    if (el) {
                        if (typeof el.scrollTo === 'function') {
                            try {
                                el.scrollTo({ top: 0, behavior: 'smooth' });
                            } catch(err) {}
                        }
                        try {
                            el.scrollTop = 0;
                        } catch(err) {}
                    }
                }
            };
        })();
        </script>
        """,
        height=0
    )

def render_search_records_tab(supabase: Client):
    st.header("🔍 Search Records")
    st.markdown("Search existing records by Name, Unit Number, or Block Number.")
    
    query = st.text_input("Search query", placeholder="Enter name, unit number, or block number (e.g., John, #12-345, or 123)")
    
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
                    "Block Number": r.get("block_number") or "-",
                    "Created Date": r.get("created_at")[:10] if r.get("created_at") else ""
                })
            st.dataframe(display_data, use_container_width=True)
