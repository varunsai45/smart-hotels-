import streamlit as st
import pandas as pd
from datetime import date, datetime
from database import init_db, get_db
from auth import create_default_admin, authenticate

st.set_page_config(page_title="Smart Hostel", page_icon="🏠", layout="wide")
init_db()
create_default_admin()

st.markdown("""
<style>
.block-container {padding-top: 1.6rem; max-width: 1400px;}
[data-testid="stSidebar"] {background: #10233f;}
[data-testid="stSidebar"] * {color: white;}
div[data-testid="stMetric"] {background: white; border: 1px solid #e5eaf1;
  padding: 15px; border-radius: 12px;}
</style>
""", unsafe_allow_html=True)

def query_df(sql, params=()):
    with get_db() as conn:
        return pd.read_sql_query(sql, conn, params=params)

def run_sql(sql, params=()):
    with get_db() as conn:
        conn.execute(sql, params)

def login_screen():
    st.title("🏠 Smart Hostel Management")
    st.caption("Hostel administration, made simpler.")
    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", use_container_width=True)
    if submitted:
        if authenticate(username, password):
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.rerun()
        else:
            st.error("Incorrect username or password.")
    st.info("First-time demo login: admin / admin123. Change this password in Settings.")

if not st.session_state.get("logged_in"):
    login_screen()
    st.stop()

st.sidebar.title("🏠 SMART HOSTEL")
st.sidebar.caption("Administration portal")
menu = st.sidebar.radio("NAVIGATION", [
    "Dashboard", "Students", "Rooms", "Fees",
    "Complaints", "Visitors", "Reports", "Settings"
])
st.sidebar.divider()
st.sidebar.write(f"Signed in: **{st.session_state.get('username','admin')}**")
if st.sidebar.button("Log out", use_container_width=True):
    st.session_state.clear()
    st.rerun()

st.title(menu)

if menu == "Dashboard":
    students = query_df("SELECT COUNT(*) n FROM students WHERE active=1").iloc[0]["n"]
    rooms = query_df("SELECT COUNT(*) n FROM rooms").iloc[0]["n"]
    occupied = query_df("SELECT COUNT(*) n FROM students WHERE room_id IS NOT NULL AND active=1").iloc[0]["n"]
    open_complaints = query_df("SELECT COUNT(*) n FROM complaints WHERE status!='Resolved'").iloc[0]["n"]
    total_paid = query_df("SELECT COALESCE(SUM(amount),0) n FROM payments").iloc[0]["n"]
    capacity = query_df("SELECT COALESCE(SUM(capacity),0) n FROM rooms").iloc[0]["n"]
    a,b,c,d,e = st.columns(5)
    a.metric("Active students", int(students))
    b.metric("Total rooms", int(rooms))
    c.metric("Occupied beds", f"{int(occupied)} / {int(capacity)}")
    d.metric("Open complaints", int(open_complaints))
    e.metric("Fees collected", f"₹{total_paid:,.0f}")
    left, right = st.columns(2)
    with left:
        st.subheader("Room occupancy")
        occ = query_df("""SELECT r.room_number, r.capacity,
            COUNT(s.student_id) occupied FROM rooms r
            LEFT JOIN students s ON s.room_id=r.room_id AND s.active=1
            GROUP BY r.room_id ORDER BY r.room_number""")
        if not occ.empty:
            st.bar_chart(occ.set_index("room_number")[["occupied","capacity"]])
        else:
            st.info("Add rooms to see occupancy.")
    with right:
        st.subheader("Complaint status")
        comp = query_df("SELECT status, COUNT(*) count FROM complaints GROUP BY status")
        if not comp.empty:
            st.bar_chart(comp.set_index("status"))
        else:
            st.info("No complaints recorded yet.")
    st.subheader("Recent students")
    st.dataframe(query_df("""SELECT student_id,name,email,course,room_id,joining_date
        FROM students WHERE active=1 ORDER BY student_id DESC LIMIT 8"""),
        use_container_width=True, hide_index=True)

elif menu == "Students":
    tab1, tab2, tab3 = st.tabs(["Register student", "Student records", "Room allocation"])
    with tab1:
        with st.form("student_form", clear_on_submit=True):
            name = st.text_input("Full name *")
            email = st.text_input("Email *")
            phone = st.text_input("Phone")
            course = st.text_input("Course / department")
            guardian = st.text_input("Guardian name")
            guardian_phone = st.text_input("Guardian phone")
            joining = st.date_input("Joining date", value=date.today())
            submit = st.form_submit_button("Register student")
        if submit:
            if not name.strip() or not email.strip() or "@" not in email:
                st.error("Enter a name and valid email address.")
            else:
                try:
                    from services import add_student
                    add_student(name,email,phone,course,guardian,guardian_phone,joining)
                    st.success("Student registered.")
                except Exception as ex:
                    st.error(f"Could not register student: {ex}")
    with tab2:
        search = st.text_input("Search by name, email or student ID")
        data = query_df("""SELECT s.student_id,s.name,s.email,s.phone,s.course,
            r.room_number,s.joining_date FROM students s
            LEFT JOIN rooms r ON r.room_id=s.room_id
            WHERE s.active=1 AND (s.name LIKE ? OR s.email LIKE ? OR CAST(s.student_id AS TEXT) LIKE ?)
            ORDER BY s.student_id DESC""", (f"%{search}%",)*3)
        st.dataframe(data, use_container_width=True, hide_index=True)
        if not data.empty:
            chosen = st.selectbox("Select student to deactivate", data["student_id"].tolist())
            if st.button("Deactivate selected student"):
                from services import deactivate_student
                deactivate_student(chosen)
                st.success("Student deactivated and room vacated.")
                st.rerun()
    with tab3:
        active = query_df("SELECT student_id,name FROM students WHERE active=1 ORDER BY name")
        rooms_df = query_df("""SELECT r.room_id,r.room_number,r.capacity,
            COUNT(s.student_id) occupied FROM rooms r
            LEFT JOIN students s ON s.room_id=r.room_id AND s.active=1
            GROUP BY r.room_id ORDER BY r.room_number""")
        if active.empty or rooms_df.empty:
            st.info("Add at least one active student and one room first.")
        else:
            sid = st.selectbox("Student", active["student_id"].tolist(),
                               format_func=lambda x: f'{x} - {active.loc[active.student_id==x,"name"].iloc[0]}')
            available = rooms_df[rooms_df.occupied < rooms_df.capacity]
            if not available.empty:
                rid = st.selectbox("Available room", available["room_id"].tolist(),
                    format_func=lambda x: f'{available.loc[available.room_id==x,"room_number"].iloc[0]} ({int(available.loc[available.room_id==x,"occupied"].iloc[0])}/{int(available.loc[available.room_id==x,"capacity"].iloc[0])})')
                if st.button("Allocate room"):
                    try:
                        from services import allocate_room
                        allocate_room(sid,rid)
                        st.success("Room allocated.")
                        st.rerun()
                    except Exception as ex: st.error(str(ex))
            else: st.warning("No rooms currently have available capacity.")
            assigned = query_df("""SELECT student_id,name,room_id FROM students
                WHERE active=1 AND room_id IS NOT NULL""")
            if not assigned.empty:
                vacate_id = st.selectbox("Student to vacate", assigned.student_id.tolist(),
                    format_func=lambda x: f'{x} - {assigned.loc[assigned.student_id==x,"name"].iloc[0]}')
                if st.button("Vacate room"):
                    from services import vacate_room
                    vacate_room(vacate_id)
                    st.success("Room vacated.")
                    st.rerun()

elif menu == "Rooms":
    with st.expander("Add new room", expanded=True):
        with st.form("room_form", clear_on_submit=True):
            number = st.text_input("Room number")
            capacity = st.number_input("Bed capacity", min_value=1, max_value=20, value=2)
            fee = st.number_input("Monthly fee (₹)", min_value=0.0, value=8000.0, step=500.0)
            room_type = st.selectbox("Room type", ["Standard","Deluxe","Shared","Single"])
            submit = st.form_submit_button("Add room")
        if submit:
            if not number.strip(): st.error("Room number is required.")
            else:
                try:
                    from services import add_room
                    add_room(number,capacity,fee,room_type)
                    st.success("Room added.")
                    st.rerun()
                except Exception as ex: st.error(f"Could not add room: {ex}")
    room_data = query_df("""SELECT r.room_id,r.room_number,r.room_type,r.capacity,
        COUNT(s.student_id) occupied,r.monthly_fee,
        (r.capacity-COUNT(s.student_id)) available
        FROM rooms r LEFT JOIN students s ON s.room_id=r.room_id AND s.active=1
        GROUP BY r.room_id ORDER BY r.room_number""")
    st.dataframe(room_data, use_container_width=True, hide_index=True)
    if not room_data.empty:
        st.caption("Occupied and available bed counts are calculated from active student allocations.")

elif menu == "Fees":
    students = query_df("SELECT student_id,name FROM students WHERE active=1 ORDER BY name")
    if students.empty:
        st.info("Register students before recording payments.")
    else:
        with st.form("payment_form", clear_on_submit=True):
            sid = st.selectbox("Student", students.student_id.tolist(),
                format_func=lambda x: f'{x} - {students.loc[students.student_id==x,"name"].iloc[0]}')
            amount = st.number_input("Amount paid (₹)", min_value=1.0, value=8000.0)
            month = st.text_input("Payment month", value=date.today().strftime("%Y-%m"))
            pdate = st.date_input("Payment date", value=date.today())
            method = st.selectbox("Payment method", ["Cash","UPI","Bank transfer","Card","Other"])
            reference = st.text_input("Transaction reference (optional)")
            notes = st.text_input("Notes")
            submit = st.form_submit_button("Record payment")
        if submit:
            try:
                from services import record_payment
                record_payment(sid,amount,month,pdate,method,reference,notes)
                st.success("Payment recorded.")
            except Exception as ex: st.error(str(ex))
    st.subheader("Payment history")
    payments = query_df("""SELECT p.payment_id,s.name,p.amount,p.payment_month,
        p.payment_date,p.method,p.reference FROM payments p
        JOIN students s ON s.student_id=p.student_id ORDER BY p.payment_id DESC""")
    st.dataframe(payments, use_container_width=True, hide_index=True)
    st.subheader("Collected by month")
    monthly = query_df("SELECT payment_month, SUM(amount) total FROM payments GROUP BY payment_month ORDER BY payment_month")
    if not monthly.empty: st.bar_chart(monthly.set_index("payment_month"))
    st.download_button("Download payment CSV", payments.to_csv(index=False).encode("utf-8"),
                       "hostel_payments.csv","text/csv")

elif menu == "Complaints":
    students = query_df("SELECT student_id,name FROM students WHERE active=1 ORDER BY name")
    if students.empty: st.info("Register students before adding complaints.")
    else:
        with st.form("complaint_form", clear_on_submit=True):
            sid = st.selectbox("Student", students.student_id.tolist(),
                format_func=lambda x: f'{x} - {students.loc[students.student_id==x,"name"].iloc[0]}')
            category = st.selectbox("Category", ["Electrical","Plumbing","Cleaning","Wi-Fi","Furniture","Other"])
            description = st.text_area("Describe the issue")
            submit = st.form_submit_button("Submit complaint")
        if submit:
            if not description.strip(): st.error("Please describe the issue.")
            else:
                from services import add_complaint
                add_complaint(sid,category,description)
                st.success("Complaint submitted.")
    complaints = query_df("""SELECT c.complaint_id,s.name,c.category,c.description,
        c.status,c.created_at FROM complaints c JOIN students s ON s.student_id=c.student_id
        ORDER BY c.complaint_id DESC""")
    st.subheader("Complaint register")
    st.dataframe(complaints, use_container_width=True, hide_index=True)
    if not complaints.empty:
        cid = st.selectbox("Complaint ID", complaints.complaint_id.tolist())
        status = st.selectbox("Update status", ["Pending","In Progress","Resolved"])
        if st.button("Update complaint"):
            from services import update_complaint
            update_complaint(cid,status)
            st.success("Complaint updated.")
            st.rerun()
    st.download_button("Download complaints CSV", complaints.to_csv(index=False).encode("utf-8"),
                       "hostel_complaints.csv","text/csv")

elif menu == "Visitors":
    students = query_df("SELECT student_id,name FROM students WHERE active=1 ORDER BY name")
    if students.empty: st.info("Register students before recording visitors.")
    else:
        with st.form("visitor_form", clear_on_submit=True):
            sid = st.selectbox("Student being visited", students.student_id.tolist(),
                format_func=lambda x: f'{x} - {students.loc[students.student_id==x,"name"].iloc[0]}')
            visitor = st.text_input("Visitor name")
            phone = st.text_input("Visitor phone")
            purpose = st.text_input("Purpose of visit")
            entry = st.datetime_input("Entry time", value=datetime.now()) if hasattr(st, "datetime_input") else st.text_input("Entry time (YYYY-MM-DD HH:MM:SS)", value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            submit = st.form_submit_button("Record visitor entry")
        if submit:
            if not visitor.strip(): st.error("Visitor name is required.")
            else:
                from services import add_visitor
                add_visitor(sid,visitor,phone,purpose,entry)
                st.success("Visitor entry recorded.")
                st.rerun()
    visitors = query_df("""SELECT v.visitor_id,v.visitor_name,s.name AS student,
        v.visitor_phone,v.purpose,v.entry_time,v.exit_time FROM visitors v
        JOIN students s ON s.student_id=v.student_id ORDER BY v.visitor_id DESC""")
    st.dataframe(visitors, use_container_width=True, hide_index=True)
    pending = visitors[visitors.exit_time.isna()] if not visitors.empty else visitors
    if not pending.empty:
        vid = st.selectbox("Visitor checkout ID", pending.visitor_id.tolist())
        exit_time = st.text_input("Exit time (YYYY-MM-DD HH:MM:SS)", value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        if st.button("Record visitor exit"):
            try:
                from services import checkout_visitor
                checkout_visitor(vid,exit_time)
                st.success("Visitor checked out.")
                st.rerun()
            except Exception as ex: st.error(str(ex))
    st.download_button("Download visitors CSV", visitors.to_csv(index=False).encode("utf-8"),
                       "hostel_visitors.csv","text/csv")

elif menu == "Reports":
    st.subheader("Hostel occupancy report")
    occupancy = query_df("""SELECT r.room_number,r.capacity,COUNT(s.student_id) occupied,
        r.monthly_fee FROM rooms r LEFT JOIN students s
        ON s.room_id=r.room_id AND s.active=1 GROUP BY r.room_id""")
    st.dataframe(occupancy, use_container_width=True, hide_index=True)
    st.download_button("Download occupancy CSV", occupancy.to_csv(index=False).encode("utf-8"),
                       "room_occupancy.csv","text/csv")
    st.subheader("Student directory")
    directory = query_df("""SELECT s.student_id,s.name,s.email,s.phone,s.course,
        r.room_number,s.joining_date FROM students s LEFT JOIN rooms r ON r.room_id=s.room_id
        WHERE s.active=1 ORDER BY s.name""")
    st.dataframe(directory, use_container_width=True, hide_index=True)
    st.download_button("Download student CSV", directory.to_csv(index=False).encode("utf-8"),
                       "hostel_students.csv","text/csv")

elif menu == "Settings":
    st.subheader("Change administrator password")
    from auth import change_password
    with st.form("password_form"):
        old = st.text_input("Current password", type="password")
        new = st.text_input("New password", type="password")
        confirm = st.text_input("Confirm new password", type="password")
        submit = st.form_submit_button("Change password")
    if submit:
        if new != confirm: st.error("New passwords do not match.")
        else:
            try:
                if change_password(st.session_state["username"],old,new):
                    st.success("Password changed successfully.")
                else: st.error("Current password is incorrect.")
            except Exception as ex: st.error(str(ex))
    st.warning("This is an educational prototype. Back up the database file before making major changes.")
