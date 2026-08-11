# 🏢 HDB Resident Records Management System

A secure Python/Streamlit web application for managing residential/unit records with Supabase PostgreSQL persistent storage, NRIC privacy masking, and strict duplicate unit checking.

## 🔒 Security & Privacy Features
- **NRIC Privacy Masking**: Full NRIC numbers are masked (e.g., `***567A`) across all UI lists, tables, and search results. Full NRICs are never exposed in logs or URLs.
- **Duplicate Unit Protection**: Prevents duplicate unit registrations through both application-level validation and database-level unique constraints (`unit_number_normalized`).
- **Secure Credentials**: Uses Streamlit Secrets (`st.secrets`) for Supabase credentials. No API keys or passwords are hardcoded.

---

## 🚀 Deployment & Setup Instructions

### 1. Supabase Database Setup
1. Log in to your [Supabase Dashboard](https://supabase.com) and create a new project.
2. Navigate to the **SQL Editor** and run the following script to create the `records` table and indexes:

```sql
CREATE TABLE records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    nric TEXT NOT NULL,
    nric_masked TEXT NOT NULL,
    unit_number TEXT NOT NULL,
    unit_number_normalized TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance and uniqueness
CREATE INDEX idx_records_unit_normalized ON records(unit_number_normalized);
CREATE INDEX idx_records_name ON records(name);
```

### 2. Local Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/hdb-resident-app.git
   cd hdb-resident-app
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure Streamlit Secrets:
   Create a directory named `.streamlit` and a file named `secrets.toml`:
   ```bash
   mkdir .streamlit
   ```
   Add your Supabase URL and API Key to `.streamlit/secrets.toml`:
   ```toml
   SUPABASE_URL = "https://your-supabase-project.supabase.co"
   SUPABASE_KEY = "your-supabase-anon-key"
   ```

4. Run the Streamlit application:
   ```bash
   streamlit run app.py
   ```

---

## ☁️ Deployment on Streamlit Community Cloud

1. Push your source code to a public or private GitHub repository (Ensure `.streamlit/secrets.toml` is **NOT** committed and is added to your `.gitignore`).
2. Log in to [Streamlit Community Cloud](https://share.streamlit.io/).
3. Click **New app** and select your GitHub repository, branch (`main`), and main file path (`app.py`).
4. Expand **Advanced settings** and add your Supabase secrets under **Secrets**:
   ```toml
   SUPABASE_URL = "https://your-supabase-project.supabase.co"
   SUPABASE_KEY = "your-supabase-anon-key"
   ```
5. Click **Deploy!**

---

## ✅ Testing Checklist

- **Test 1 (Successful Insertion)**:
  - Name: `John Tan`
  - NRIC: `S1234567A`
  - Unit: `#12-345`
  - *Expected*: Successful insertion (`✅ Record added successfully.`).
- **Test 2 (Duplicate Unit Rejection)**:
  - Name: `Mary Tan`
  - NRIC: `S7654321B`
  - Unit: `#12-345` (or variant like `12-345`)
  - *Expected*: Rejected with error (`❌ This unit number already exists.`).
- **Test 3 (NRIC Masking)**:
  - View records list.
  - *Expected*: NRIC appears as `***567A`. Full NRIC is never displayed.
- **Test 4 (Search)**:
  - Search by unit number or name.
  - *Expected*: Records are returned without exposing full NRICs.
- **Test 5 (Persistence)**:
  - Restart the Streamlit application.
  - *Expected*: Previously saved records remain accessible from Supabase.
