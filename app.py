from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.secret_key = "hospital_secret_key_123"

DATABASE = "hospital.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def initialize_database():

    db = get_db()

    # Patients table
    db.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL
        )
    """)

    # Doctors table
    db.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            phone TEXT NOT NULL
        )
    """)

    # Appointments table
    db.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient TEXT NOT NULL,
            doctor TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending'
        )
    """)

    # Users table
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            name TEXT NOT NULL
        )
    """)

    # -----------------------------------------------------
    # Default Admin
    # -----------------------------------------------------

    admin = db.execute(
        "SELECT * FROM users WHERE username = ?",
        ("admin",)
    ).fetchone()

    if admin is None:

        db.execute(
            """
            INSERT INTO users
            (username, password, role, name)
            VALUES (?, ?, ?, ?)
            """,
            (
                "admin",
                generate_password_hash("admin123"),
                "admin",
                "Hospital Admin"
            )
        )

    # -----------------------------------------------------
    # Default Doctor
    # -----------------------------------------------------

    doctor_user = db.execute(
        "SELECT * FROM users WHERE username = ?",
        ("doctor",)
    ).fetchone()

    if doctor_user is None:

        db.execute(
            """
            INSERT INTO users
            (username, password, role, name)
            VALUES (?, ?, ?, ?)
            """,
            (
                "doctor",
                generate_password_hash("doctor123"),
                "doctor",
                "John Smith"
            )
        )

    # -----------------------------------------------------
    # Default Patient
    # -----------------------------------------------------

    patient_user = db.execute(
        "SELECT * FROM users WHERE username = ?",
        ("patient",)
    ).fetchone()

    if patient_user is None:

        db.execute(
            """
            INSERT INTO users
            (username, password, role, name)
            VALUES (?, ?, ?, ?)
            """,
            (
                "patient",
                generate_password_hash("patient123"),
                "patient",
                "Rahul Kumar"
            )
        )

    # -----------------------------------------------------
    # Default Doctors
    # -----------------------------------------------------

    doctor_count = db.execute(
        "SELECT COUNT(*) AS count FROM doctors"
    ).fetchone()["count"]

    if doctor_count == 0:

        db.execute(
            """
            INSERT INTO doctors
            (name, specialization, phone)
            VALUES (?, ?, ?)
            """,
            (
                "John Smith",
                "Cardiologist",
                "9876500000"
            )
        )

        db.execute(
            """
            INSERT INTO doctors
            (name, specialization, phone)
            VALUES (?, ?, ?)
            """,
            (
                "Sarah",
                "Dermatologist",
                "9876511111"
            )
        )

    # -----------------------------------------------------
    # Default Patient
    # -----------------------------------------------------

    patient_count = db.execute(
        "SELECT COUNT(*) AS count FROM patients"
    ).fetchone()["count"]

    if patient_count == 0:

        db.execute(
            """
            INSERT INTO patients
            (name, age, gender, phone, email)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "Rahul Kumar",
                25,
                "Male",
                "9876543210",
                "rahul@gmail.com"
            )
        )

    db.commit()
    db.close()


# =========================================================
# LOGIN REQUIRED
# =========================================================

def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "username" not in session:

            return redirect(url_for("login"))

        return f(*args, **kwargs)

    return decorated_function


# =========================================================
# ADMIN / DOCTOR REQUIRED
# =========================================================

def staff_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "username" not in session:

            return redirect(url_for("login"))

        if session.get("role") not in ["admin", "doctor"]:

            flash(
                "You do not have permission to access this page.",
                "error"
            )

            return redirect(url_for("dashboard"))

        return f(*args, **kwargs)

    return decorated_function


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template("index.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if not username or not password:

            flash(
                "Please enter username and password.",
                "error"
            )

            return render_template("login.html")

        db = get_db()

        user = db.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

        db.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["username"] = user["username"]

            session["role"] = user["role"]

            session["name"] = user["name"]

            flash(
                "Login successful!",
                "success"
            )

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid username or password.",
            "error"
        )

    return render_template("login.html")


# =========================================================
# PATIENT REGISTRATION
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        age = request.form.get(
            "age",
            ""
        ).strip()

        gender = request.form.get(
            "gender",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if not all([
            name,
            age,
            gender,
            phone,
            email,
            username,
            password
        ]):

            flash(
                "Please fill all fields.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        db = get_db()

        existing_user = db.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

        if existing_user:

            db.close()

            flash(
                "Username already exists. Please choose another username.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        hashed_password = generate_password_hash(
            password
        )

        db.execute(
            """
            INSERT INTO users
            (username, password, role, name)
            VALUES (?, ?, ?, ?)
            """,
            (
                username,
                hashed_password,
                "patient",
                name
            )
        )

        db.execute(
            """
            INSERT INTO patients
            (name, age, gender, phone, email)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                name,
                age,
                gender,
                phone,
                email
            )
        )

        db.commit()

        db.close()

        flash(
            "Patient account created successfully. Please login.",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
@login_required
def dashboard():

    db = get_db()

    patients = db.execute(
        "SELECT * FROM patients ORDER BY id DESC"
    ).fetchall()

    doctors = db.execute(
        "SELECT * FROM doctors ORDER BY id DESC"
    ).fetchall()

    appointments = db.execute(
        "SELECT * FROM appointments ORDER BY id DESC"
    ).fetchall()

    db.close()

    if session.get("role") == "patient":

        patient_name = session.get("name")

        appointments = [
            appointment
            for appointment in appointments
            if appointment["patient"] == patient_name
        ]

    return render_template(
        "dashboard.html",
        patients=patients,
        doctors=doctors,
        appointments=appointments
    )


# =========================================================
# PATIENT MANAGEMENT
# ADMIN + DOCTOR ONLY
# =========================================================

@app.route("/patients", methods=["GET", "POST"])
@staff_required
def patients():

    db = get_db()

    if request.method == "POST":

        name = request.form.get("name")

        age = request.form.get("age")

        gender = request.form.get("gender")

        phone = request.form.get("phone")

        email = request.form.get("email")

        db.execute(
            """
            INSERT INTO patients
            (name, age, gender, phone, email)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                name,
                age,
                gender,
                phone,
                email
            )
        )

        db.commit()

        db.close()

        flash(
            "Patient added successfully!",
            "success"
        )

        return redirect(
            url_for("patients")
        )

    patients_data = db.execute(
        "SELECT * FROM patients ORDER BY id DESC"
    ).fetchall()

    db.close()

    return render_template(
        "patients.html",
        patients=patients_data
    )


# =========================================================
# EDIT PATIENT
# ADMIN + DOCTOR ONLY
# =========================================================

@app.route(
    "/patients/edit/<int:patient_id>",
    methods=["GET", "POST"]
)
@staff_required
def edit_patient(patient_id):

    db = get_db()

    patient = db.execute(
        """
        SELECT *
        FROM patients
        WHERE id = ?
        """,
        (patient_id,)
    ).fetchone()

    if patient is None:

        db.close()

        flash(
            "Patient not found.",
            "error"
        )

        return redirect(
            url_for("patients")
        )

    if request.method == "POST":

        name = request.form.get("name")

        age = request.form.get("age")

        gender = request.form.get("gender")

        phone = request.form.get("phone")

        email = request.form.get("email")

        db.execute(
            """
            UPDATE patients
            SET name = ?,
                age = ?,
                gender = ?,
                phone = ?,
                email = ?
            WHERE id = ?
            """,
            (
                name,
                age,
                gender,
                phone,
                email,
                patient_id
            )
        )

        db.commit()

        db.close()

        flash(
            "Patient information updated successfully!",
            "success"
        )

        return redirect(
            url_for("patients")
        )

    db.close()

    return render_template(
        "edit_patient.html",
        patient=patient
    )


# =========================================================
# DELETE PATIENT
# ADMIN + DOCTOR ONLY
# =========================================================

@app.route(
    "/patients/delete/<int:patient_id>"
)
@staff_required
def delete_patient(patient_id):

    db = get_db()

    db.execute(
        """
        DELETE FROM patients
        WHERE id = ?
        """,
        (patient_id,)
    )

    db.commit()

    db.close()

    flash(
        "Patient deleted successfully!",
        "success"
    )

    return redirect(
        url_for("patients")
    )


# =========================================================
# DOCTOR MANAGEMENT
# ADMIN + DOCTOR ONLY
# =========================================================

@app.route("/doctors", methods=["GET", "POST"])
@login_required
def doctors():

    db = get_db()

    if request.method == "POST":

        if session.get("role") not in ["admin", "doctor"]:

            db.close()

            flash(
                "You do not have permission to add doctors.",
                "error"
            )

            return redirect(
                url_for("doctors")
            )

        name = request.form.get("name")

        specialization = request.form.get(
            "specialization"
        )

        phone = request.form.get("phone")

        db.execute(
            """
            INSERT INTO doctors
            (name, specialization, phone)
            VALUES (?, ?, ?)
            """,
            (
                name,
                specialization,
                phone
            )
        )

        db.commit()

        db.close()

        flash(
            "Doctor added successfully!",
            "success"
        )

        return redirect(
            url_for("doctors")
        )

    doctors_data = db.execute(
        "SELECT * FROM doctors ORDER BY id DESC"
    ).fetchall()

    db.close()

    return render_template(
        "doctors.html",
        doctors=doctors_data
    )


# =========================================================
# EDIT DOCTOR
# ADMIN + DOCTOR ONLY
# =========================================================

@app.route(
    "/doctors/edit/<int:doctor_id>",
    methods=["GET", "POST"]
)
@staff_required
def edit_doctor(doctor_id):

    db = get_db()

    doctor = db.execute(
        """
        SELECT *
        FROM doctors
        WHERE id = ?
        """,
        (doctor_id,)
    ).fetchone()

    if doctor is None:

        db.close()

        flash(
            "Doctor not found.",
            "error"
        )

        return redirect(
            url_for("doctors")
        )

    if request.method == "POST":

        name = request.form.get("name")

        specialization = request.form.get(
            "specialization"
        )

        phone = request.form.get("phone")

        db.execute(
            """
            UPDATE doctors
            SET name = ?,
                specialization = ?,
                phone = ?
            WHERE id = ?
            """,
            (
                name,
                specialization,
                phone,
                doctor_id
            )
        )

        db.commit()

        db.close()

        flash(
            "Doctor information updated successfully!",
            "success"
        )

        return redirect(
            url_for("doctors")
        )

    db.close()

    return render_template(
        "edit_doctor.html",
        doctor=doctor
    )


# =========================================================
# DELETE DOCTOR
# ADMIN + DOCTOR ONLY
# =========================================================

@app.route(
    "/doctors/delete/<int:doctor_id>"
)
@staff_required
def delete_doctor(doctor_id):

    db = get_db()

    db.execute(
        """
        DELETE FROM doctors
        WHERE id = ?
        """,
        (doctor_id,)
    )

    db.commit()

    db.close()

    flash(
        "Doctor deleted successfully!",
        "success"
    )

    return redirect(
        url_for("doctors")
    )


# =========================================================
# BOOK APPOINTMENT
# ALL LOGGED-IN USERS
# =========================================================

@app.route(
    "/appointment",
    methods=["GET", "POST"]
)
@login_required
def appointment():

    db = get_db()

    if request.method == "POST":

        doctor = request.form.get("doctor")

        date = request.form.get("date")

        time = request.form.get("time")

        reason = request.form.get("reason")

        # Patient automatically uses their own name
        if session.get("role") == "patient":

            patient = session.get("name")

        else:

            patient = request.form.get("patient")

        db.execute(
            """
            INSERT INTO appointments
            (patient, doctor, date, time, reason, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                patient,
                doctor,
                date,
                time,
                reason,
                "Pending"
            )
        )

        db.commit()

        db.close()

        flash(
            "Appointment booked successfully!",
            "success"
        )

        return redirect(
            url_for("appointments")
        )

    doctors_data = db.execute(
        "SELECT * FROM doctors ORDER BY name"
    ).fetchall()

    patients_data = db.execute(
        "SELECT * FROM patients ORDER BY name"
    ).fetchall()

    db.close()

    return render_template(
        "appointment.html",
        doctors=doctors_data,
        patients=patients_data
    )


# =========================================================
# APPOINTMENTS
# =========================================================

@app.route("/appointments")
@login_required
def appointments():

    db = get_db()

    appointments_data = db.execute(
        """
        SELECT *
        FROM appointments
        ORDER BY id DESC
        """
    ).fetchall()

    db.close()

    # Patients can see only their own appointments
    if session.get("role") == "patient":

        patient_name = session.get("name")

        appointments_data = [
            appointment
            for appointment in appointments_data
            if appointment["patient"] == patient_name
        ]

    return render_template(
        "appointments.html",
        appointments=appointments_data
    )


# =========================================================
# UPDATE APPOINTMENT STATUS
# ADMIN + DOCTOR ONLY
# =========================================================

@app.route(
    "/appointment/status/<int:appointment_id>/<status>"
)
@staff_required
def update_appointment_status(
    appointment_id,
    status
):

    allowed_statuses = [
        "Pending",
        "Approved",
        "Completed",
        "Cancelled"
    ]

    if status not in allowed_statuses:

        flash(
            "Invalid appointment status.",
            "error"
        )

        return redirect(
            url_for("appointments")
        )

    db = get_db()

    db.execute(
        """
        UPDATE appointments
        SET status = ?
        WHERE id = ?
        """,
        (
            status,
            appointment_id
        )
    )

    db.commit()

    db.close()

    flash(
        "Appointment status updated successfully!",
        "success"
    )

    return redirect(
        url_for("appointments")
    )


# =========================================================
# USER MANAGEMENT
# ADMIN ONLY
# =========================================================

@app.route("/users", methods=["GET", "POST"])
@login_required
def users():

    if session.get("role") != "admin":

        flash(
            "Only admin can manage users.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )

    db = get_db()

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        role = request.form.get(
            "role",
            ""
        ).strip()

        name = request.form.get(
            "name",
            ""
        ).strip()

        if role not in [
            "admin",
            "doctor",
            "patient"
        ]:

            db.close()

            flash(
                "Invalid role.",
                "error"
            )

            return redirect(
                url_for("users")
            )

        existing_user = db.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

        if existing_user:

            db.close()

            flash(
                "Username already exists.",
                "error"
            )

            return redirect(
                url_for("users")
            )

        hashed_password = generate_password_hash(
            password
        )

        db.execute(
            """
            INSERT INTO users
            (username, password, role, name)
            VALUES (?, ?, ?, ?)
            """,
            (
                username,
                hashed_password,
                role,
                name
            )
        )

        db.commit()

        db.close()

        flash(
            "User created successfully!",
            "success"
        )

        return redirect(
            url_for("users")
        )

    users_data = db.execute(
        """
        SELECT id, username, role, name
        FROM users
        ORDER BY id DESC
        """
    ).fetchall()

    db.close()

    return render_template(
        "users.html",
        users=users_data
    )


# =========================================================
# DELETE USER
# ADMIN ONLY
# =========================================================

@app.route(
    "/users/delete/<int:user_id>"
)
@login_required
def delete_user(user_id):

    if session.get("role") != "admin":

        flash(
            "Only admin can delete users.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )

    db = get_db()

    user = db.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    if user is None:

        db.close()

        flash(
            "User not found.",
            "error"
        )

        return redirect(
            url_for("users")
        )

    # Admin cannot delete their own account
    if user["username"] == session.get("username"):

        db.close()

        flash(
            "You cannot delete your own account.",
            "error"
        )

        return redirect(
            url_for("users")
        )

    db.execute(
        """
        DELETE FROM users
        WHERE id = ?
        """,
        (user_id,)
    )

    db.commit()

    db.close()

    flash(
        "User deleted successfully!",
        "success"
    )

    return redirect(
        url_for("users")
    )


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    initialize_database()

    app.run(
        debug=True
    )