# Smart Hostel Management System

A Python + Streamlit + SQLite application for hostel administration.

## Features
- Admin login with PBKDF2 password hashing
- Dashboard statistics and charts
- Student CRUD and room allocation/vacating
- Room management and occupancy validation
- Fee payments, balances and CSV export
- Complaint tracking
- Visitor entry/exit log
- CSV exports

## Run locally
1. Install Python 3.10 or newer.
2. Create and activate a virtual environment:
   - Windows: `py -m venv .venv` then `.venv\\Scripts\\activate`
   - macOS/Linux: `python3 -m venv .venv` then `source .venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Start: `streamlit run app.py`
5. First run creates `data/hostel.db` and a default admin account:
   - Username: `admin`
   - Password: `admin123`
6. Change the default password immediately from the Settings page.

## Team development
- Member 1: app shell, authentication, integration and testing
- Member 2: student management
- Member 3: room management and allocation
- Member 4: payments and fee reporting
- Member 5: complaints, visitors and documentation

## Important
This is an educational prototype. Do not store real student identity documents,
bank details, or sensitive personal information. Add backups, HTTPS, stronger
authorization, audit logs and deployment security before real-world use.
