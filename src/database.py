"""
Supabase database connection and operations module.
Uses Streamlit secrets for credentials and parameterized queries.
"""
import streamlit as st
from supabase import create_client, Client
from src.masking import mask_nric
from src.validation import normalize_unit_number

@st.cache_resource
def init_supabase_client() -> Client:
    """
    Initializes and returns the Supabase client using Streamlit secrets.
    Safely handles missing keys with appropriate fallbacks or error messages.
    """
    if "SUPABASE_URL" not in st.secrets or "SUPABASE_KEY" not in st.secrets:
        raise KeyError("Supabase credentials (`SUPABASE_URL` and `SUPABASE_KEY`) are missing from Streamlit secrets.")
    
    supabase_url = st.secrets["SUPABASE_URL"]
    supabase_key = st.secrets["SUPABASE_KEY"]
    return create_client(supabase_url, supabase_key)

def check_unit_exists(supabase: Client, unit_number_normalized: str) -> bool:
    """
    Checks whether a normalized unit number already exists in the database.
    """
    try:
        response = supabase.table("records") \
            .select("id") \
            .eq("unit_number_normalized", unit_number_normalized) \
            .execute()
        data = response.data
        return len(data) > 0
    except Exception as e:
        # Log error details for debugging RLS or query issues
        print(f"Database error in check_unit_exists: {e}")
        st.error(f"Database error while checking duplicate unit: {e}")
        return False

def add_record(supabase: Client, name: str, nric: str, unit_number: str, block_number: str = "") -> tuple[bool, str, dict | None]:
    """
    Adds a new record to Supabase after checking for duplicate normalized unit numbers.
    Returns (success: bool, message: str, record_details: dict | None).
    """
    normalized_unit = normalize_unit_number(unit_number)
    
    # Check duplicate
    if check_unit_exists(supabase, normalized_unit):
        return False, "❌ This unit number already exists.", None
    
    masked = mask_nric(nric)
    clean_block = block_number.strip() if block_number else ""
    
    payload = {
        "name": name.strip(),
        "nric": nric.strip().upper(),
        "nric_masked": masked,
        "unit_number": unit_number.strip(),
        "unit_number_normalized": normalized_unit,
        "block_number": clean_block
    }
    
    try:
        response = supabase.table("records").insert(payload).execute()
        if response.data:
            inserted_item = response.data[0] if isinstance(response.data, list) and len(response.data) > 0 else response.data
            records = get_all_records(supabase)
            ticket_no = len(records)
            if isinstance(inserted_item, dict) and "id" in inserted_item:
                target_id = inserted_item["id"]
                for idx, rec in enumerate(records, start=1):
                    if rec.get("id") == target_id:
                        ticket_no = idx
                        break
            
            record_details = {
                "ticket_no": ticket_no,
                "name": name.strip(),
                "nric_masked": masked,
                "unit_number": unit_number.strip(),
                "block_number": clean_block
            }
            return True, "✅ Record added successfully.", record_details
        else:
            return False, "❌ Failed to insert record.", None
    except Exception as e:
        # Check if error is due to unique violation
        err_msg = str(e)
        print(f"Database error in add_record: {err_msg}")
        if "unique" in err_msg.lower() or "duplicate" in err_msg.lower():
            return False, "❌ This unit number already exists.", None
        return False, f"❌ Database insertion failed: {e}", None

def get_all_records(supabase: Client) -> list:
    """
    Fetches all records from the database, ordering by creation date ascending (so ticket #1 is oldest/first).
    """
    try:
        response = supabase.table("records") \
            .select("id, name, nric_masked, unit_number, block_number, created_at") \
            .order("created_at", desc=False) \
            .execute()
        return response.data or []
    except Exception as e:
        st.error("Failed to fetch records from database.")
        return []

def delete_record(supabase: Client, record_id: str) -> tuple[bool, str]:
    """
    Deletes a record by its unique ID.
    Returns (success: bool, message: str).
    """
    try:
        response = supabase.table("records").delete().eq("id", record_id).execute()
        return True, "✅ Record deleted successfully."
    except Exception as e:
        err_msg = str(e)
        print(f"Database error in delete_record: {err_msg}")
        return False, f"❌ Failed to delete record: {e}"

def delete_all_records(supabase: Client) -> tuple[bool, str]:
    """
    Deletes all records from the records table without deleting the table itself.
    Returns (success: bool, message: str).
    """
    try:
        response = supabase.table("records").delete().not_.is_("id", "null").execute()
        return True, "✅ All records deleted successfully."
    except Exception as e:
        try:
            response = supabase.table("records").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            return True, "✅ All records deleted successfully."
        except Exception as e2:
            err_msg = str(e2)
            print(f"Database error in delete_all_records: {err_msg}")
            return False, f"❌ Failed to delete all records: {e2}"

def search_records(supabase: Client, query: str) -> list:
    """
    Searches records by name, unit number (normalized or raw), or block number.
    """
    if not query:
        return get_all_records(supabase)
    
    q = query.strip()
    norm_q = normalize_unit_number(q)
    
    try:
        # Search by name (ilike), unit_number_normalized (eq/ilike), or block_number (ilike)
        response = supabase.table("records") \
            .select("id, name, nric_masked, unit_number, block_number, created_at") \
            .or_(f"name.ilike.%{q}%,unit_number_normalized.ilike.%{norm_q}%,block_number.ilike.%{q}%") \
            .order("created_at", desc=True) \
            .execute()
        return response.data or []
    except Exception as e:
        st.error("Search query failed.")
        return []

def import_records_from_excel(supabase: Client, uploaded_file) -> tuple[int, int, list]:
    """
    Imports records from an uploaded Excel file using pandas.
    Expected columns: Name, NRIC (or FIN), Unit Number, Block Number (Optional).
    Returns (success_count: int, failure_count: int, errors: list).
    """
    import pandas as pd
    from src.validation import validate_name, validate_nric, validate_unit_number
    
    try:
        df = pd.read_excel(uploaded_file)
    except Exception as e:
        return 0, 0, [f"Failed to read Excel file: {e}"]
        
    # Standardize column names (strip whitespace and lowercase)
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    # Map common column name variations
    name_col = next((c for c in df.columns if 'name' in c), None)
    nric_col = next((c for c in df.columns if 'nric' in c or 'fin' in c), None)
    unit_col = next((c for c in df.columns if 'unit' in c), None)
    block_col = next((c for c in df.columns if 'block' in c or 'blk' in c), None)
    
    if not name_col or not nric_col or not unit_col:
        return 0, len(df), [f"Excel file must contain Name, NRIC/FIN, and Unit Number columns. Found columns: {list(df.columns)}"]
        
    success_count = 0
    failure_count = 0
    errors = []
    
    for idx, row in df.iterrows():
        name = str(row[name_col]) if pd.notna(row[name_col]) else ""
        nric = str(row[nric_col]) if pd.notna(row[nric_col]) else ""
        unit_number = str(row[unit_col]) if pd.notna(row[unit_col]) else ""
        block_number = str(row[block_col]).strip() if (block_col and pd.notna(row[block_col])) else ""
        
        # Validate fields
        row_errors = []
        if not validate_name(name):
            row_errors.append("Invalid name")
        if not validate_nric(nric):
            row_errors.append("Invalid NRIC")
        if not validate_unit_number(unit_number):
            row_errors.append("Invalid unit number")
            
        if row_errors:
            failure_count += 1
            errors.append(f"Row {idx + 2}: {', '.join(row_errors)} (Name: {name}, Unit: {unit_number})")
            continue
            
        success, msg, _ = add_record(supabase, name, nric, unit_number, block_number)
        if success:
            success_count += 1
        else:
            failure_count += 1
            errors.append(f"Row {idx + 2}: {msg} (Unit: {unit_number})")
            
    return success_count, failure_count, errors

def export_records_to_excel(supabase: Client) -> bytes:
    """
    Exports all records from Supabase to an Excel file bytes buffer using pandas, including Ticket Numbers and Block Numbers.
    """
    import pandas as pd
    import io
    
    records = get_all_records(supabase)
    if not records:
        df = pd.DataFrame(columns=["Ticket No.", "Name", "NRIC", "Unit Number", "Block Number", "Created Date"])
    else:
        data = []
        for idx, r in enumerate(records, start=1):
            data.append({
                "Ticket No.": idx,
                "Name": r.get("name"),
                "NRIC": r.get("nric_masked"),
                "Unit Number": r.get("unit_number"),
                "Block Number": r.get("block_number") or "",
                "Created Date": r.get("created_at")[:10] if r.get("created_at") else ""
            })
        df = pd.DataFrame(data)
        
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Distribution Records")
    processed_data = output.getvalue()
    return processed_data
