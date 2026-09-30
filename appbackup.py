from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps

app = Flask(__name__)
app.secret_key = "hospital_secret_key_123"


# =========================================================
# TEMPORARY DATA
# =========================================================

users = [
    {
        "username": "admin",
        "password": "admin123",
        "role": "admin",
        "name": "Hospital Admin"
    },
    {
        "username": "doctor",
        "password": "doctor123",
        "role": "doctor",
        "name": "Dr. John Smith"
    },
    {
        "username": "patient",
        "password": "patient123",
        "role": "patient",
        "name": "Rahul Kumar"
    }
]


patients_list = [
    {
        "id": 1,
        "name": "Rahul Kumar",
        "age": 25,
        "gender": "Male",
        "phone": "9876543210",
        "email": "rahul@gmail.com"
    }
]


doctors_list = [
    {
        "id": 1,
        "name": "Dr. John Smith",
        "specialization": "Cardiologist",
        "phone": "9876500000"
    },
    {
        "id": 2,
        "name": "Dr. Sarah",
        "specialization": "Dermatologist",
        "phone": "9876511111"
    }
]


appointments_list = []

next_patient_id = 2
next_appointment_id = 1


# =========================================================
# LOGIN REQUIRED DECORATOR
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
            flash("You do not have permission to access this page.", "error")
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

        username = request.form.get("username")
        password = request.form.get("password")

        for user in users:

            if user["username"] == username and user["password"] == password:

                session["username"] = user["username"]
                session["role"] = user["role"]
                session["name"] = user["name"]

                return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "error")

    return render_template("login.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
@login_required
def dashboard():

    return render_template(
        "dashboard.html",
        patients=patients_list,
        doctors=doctors_list,
        appointments=appointments_list
    )


# =========================================================
# PATIENT MANAGEMENT
# DOCTOR + ADMIN
# =========================================================

@app.route("/patients", methods=["GET", "POST"])
@staff_required
def patients():

    global next_patient_id

    if request.method == "POST":

        name = request.form.get("name")
        age = request.form.get("age")
        gender = request.form.get("gender")
        phone = request.form.get("phone")
        email = request.form.get("email")

        new_patient = {
            "id": next_patient_id,
            "name": name,
            "age": age,
            "gender": gender,
            "phone": phone,
            "email": email
        }

        patients_list.append(new_patient)

        next_patient_id += 1

        flash("Patient added successfully!", "success")

        return redirect(url_for("patients"))

    return render_template(
        "patients.html",
        patients=patients_list
    )


# =========================================================
# EDIT PATIENT
# =========================================================

@app.route("/patients/edit/<int:patient_id>", methods=["GET", "POST"])
@staff_required
def edit_patient(patient_id):

    patient = None

    for p in patients_list:

        if p["id"] == patient_id:
            patient = p
            break

    if patient is None:
        flash("Patient not found.", "error")
        return redirect(url_for("patients"))

    if request.method == "POST":

        patient["name"] = request.form.get("name")
        patient["age"] = request.form.get("age")
        patient["gender"] = request.form.get("gender")
        patient["phone"] = request.form.get("phone")
        patient["email"] = request.form.get("email")

        flash("Patient information updated successfully!", "success")

        return redirect(url_for("patients"))

    return render_template(
        "edit_patient.html",
        patient=patient
    )


# =========================================================
# DELETE PATIENT
# =========================================================

@app.route("/patients/delete/<int:patient_id>")
@staff_required
def delete_patient(patient_id):

    global patients_list

    patients_list = [
        p for p in patients_list
        if p["id"] != patient_id
    ]

    flash("Patient deleted successfully!", "success")

    return redirect(url_for("patients"))


# =========================================================
# APPOINTMENT BOOKING
# PATIENT / USER
# =========================================================

@app.route("/appointment", methods=["GET", "POST"])
@login_required
def appointment():

    global next_appointment_id

    if request.method == "POST":

        patient = request.form.get("patient")
        doctor = request.form.get("doctor")
        date = request.form.get("date")
        time = request.form.get("time")
        reason = request.form.get("reason")

        appointment_data = {
            "id": next_appointment_id,
            "patient": patient,
            "doctor": doctor,
            "date": date,
            "time": time,
            "reason": reason,
            "status": "Pending"
        }

        appointments_list.append(appointment_data)

        next_appointment_id += 1

        flash("Appointment booked successfully!", "success")

        return redirect(url_for("appointments"))

    return render_template(
        "appointment.html",
        doctors=doctors_list
    )


# =========================================================
# APPOINTMENT LIST
# =========================================================

@app.route("/appointments")
@login_required
def appointments():

    # Patient sees their own appointments
    if session.get("role") == "patient":

        patient_name = session.get("name")

        user_appointments = [
            a for a in appointments_list
            if a["patient"] == patient_name
        ]

        return render_template(
            "appointments.html",
            appointments=user_appointments
        )

    # Admin and doctor see all appointments
    return render_template(
        "appointments.html",
        appointments=appointments_list
    )


# =========================================================
# UPDATE APPOINTMENT STATUS
# ADMIN / DOCTOR
# =========================================================

@app.route("/appointment/status/<int:appointment_id>/<status>")
@staff_required
def update_appointment_status(appointment_id, status):

    for appointment in appointments_list:

        if appointment["id"] == appointment_id:

            if status in ["Approved", "Rejected", "Completed"]:

                appointment["status"] = status

            break

    return redirect(url_for("appointments"))


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)