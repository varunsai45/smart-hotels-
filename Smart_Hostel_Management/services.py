from database import get_db

def add_room(number, capacity, monthly_fee, room_type):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO rooms(room_number,capacity,monthly_fee,room_type) VALUES(?,?,?,?)",
            (number.strip(), int(capacity), float(monthly_fee), room_type)
        )

def add_student(name, email, phone, course, guardian_name, guardian_phone, joining_date):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO students(name,email,phone,course,guardian_name,guardian_phone,joining_date)
            VALUES(?,?,?,?,?,?,?)
        """, (name.strip(), email.strip().lower(), phone, course, guardian_name,
              guardian_phone, str(joining_date)))

def update_student(student_id, name, email, phone, course, guardian_name, guardian_phone):
    with get_db() as conn:
        conn.execute("""
            UPDATE students SET name=?, email=?, phone=?, course=?,
            guardian_name=?, guardian_phone=? WHERE student_id=?
        """, (name.strip(), email.strip().lower(), phone, course, guardian_name,
              guardian_phone, int(student_id)))

def allocate_room(student_id, room_id):
    with get_db() as conn:
        student = conn.execute(
            "SELECT room_id, active FROM students WHERE student_id=?", (student_id,)
        ).fetchone()
        room = conn.execute(
            "SELECT capacity FROM rooms WHERE room_id=?", (room_id,)
        ).fetchone()
        if not student or not student["active"]:
            raise ValueError("Active student not found.")
        if not room:
            raise ValueError("Room not found.")
        if student["room_id"] == room_id:
            raise ValueError("Student is already assigned to this room.")
        occupied = conn.execute(
            "SELECT COUNT(*) AS n FROM students WHERE room_id=? AND active=1",
            (room_id,)
        ).fetchone()["n"]
        if occupied >= room["capacity"]:
            raise ValueError("This room is full.")
        conn.execute("UPDATE students SET room_id=? WHERE student_id=?",
                     (room_id, student_id))

def vacate_room(student_id):
    with get_db() as conn:
        cur = conn.execute(
            "UPDATE students SET room_id=NULL WHERE student_id=? AND active=1",
            (student_id,)
        )
        if cur.rowcount == 0:
            raise ValueError("Active student not found.")

def deactivate_student(student_id):
    with get_db() as conn:
        conn.execute("UPDATE students SET active=0, room_id=NULL WHERE student_id=?",
                     (student_id,))

def record_payment(student_id, amount, payment_month, payment_date, method, reference, notes):
    if float(amount) <= 0:
        raise ValueError("Payment amount must be greater than zero.")
    with get_db() as conn:
        conn.execute("""
            INSERT INTO payments(student_id,amount,payment_month,payment_date,method,reference,notes)
            VALUES(?,?,?,?,?,?,?)
        """, (int(student_id), float(amount), payment_month, str(payment_date),
              method, reference, notes))

def add_complaint(student_id, category, description):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO complaints(student_id,category,description) VALUES(?,?,?)",
            (int(student_id), category, description.strip())
        )

def update_complaint(complaint_id, status):
    with get_db() as conn:
        conn.execute(
            "UPDATE complaints SET status=?, updated_at=CURRENT_TIMESTAMP WHERE complaint_id=?",
            (status, int(complaint_id))
        )

def add_visitor(student_id, name, phone, purpose, entry_time):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO visitors(student_id,visitor_name,visitor_phone,purpose,entry_time)
            VALUES(?,?,?,?,?)
        """, (int(student_id), name.strip(), phone, purpose, str(entry_time)))

def checkout_visitor(visitor_id, exit_time):
    with get_db() as conn:
        row = conn.execute("SELECT entry_time FROM visitors WHERE visitor_id=?",
                           (int(visitor_id),)).fetchone()
        if not row:
            raise ValueError("Visitor record not found.")
        if str(exit_time) < row["entry_time"]:
            raise ValueError("Exit time cannot be earlier than entry time.")
        conn.execute("UPDATE visitors SET exit_time=? WHERE visitor_id=?",
                     (str(exit_time), int(visitor_id)))
