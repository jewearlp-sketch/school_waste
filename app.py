from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

DATABASE = "incident.db"


# =========================
# CREATE DATABASE
# =========================

def create_database():

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    # Incident reports table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            incident_type TEXT NOT NULL,
            location TEXT NOT NULL,
            description TEXT NOT NULL,
            risk_level TEXT NOT NULL,
            report_time TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)

    # Emergency alarms table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alarms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            location TEXT NOT NULL,
            alarm_time TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


# =========================
# STUDENT HOME PAGE
# =========================

@app.route("/")
def home():
    return render_template("index.html")


# =========================
# SUBMIT INCIDENT REPORT
# =========================

@app.route("/report", methods=["POST"])
def report():

    student_name = request.form["student_name"]
    incident_type = request.form["incident_type"]
    location = request.form["location"]
    description = request.form["description"]
    risk_level = request.form["risk_level"]

    report_time = datetime.now().strftime("%Y-%m-%d %I:%M %p")

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO incidents (
            student_name,
            incident_type,
            location,
            description,
            risk_level,
            report_time,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        student_name,
        incident_type,
        location,
        description,
        risk_level,
        report_time,
        "Pending"
    ))

    connection.commit()
    connection.close()

    return redirect(url_for("home"))


# =========================
# EMERGENCY ALARM
# =========================

@app.route("/alarm", methods=["POST"])
def alarm():

    student_name = request.form["student_name"]
    location = request.form["location"]

    alarm_time = datetime.now().strftime("%Y-%m-%d %I:%M %p")

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO alarms (
            student_name,
            location,
            alarm_time,
            status
        )
        VALUES (?, ?, ?, ?)
    """, (
        student_name,
        location,
        alarm_time,
        "ACTIVE"
    ))

    connection.commit()
    connection.close()

    return redirect(url_for("home"))


# =========================
# PERSONNEL DASHBOARD
# =========================

@app.route("/personnel")
def personnel():

    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    # Get emergency alarms
    cursor.execute("""
        SELECT *
        FROM alarms
        ORDER BY id DESC
    """)

    alarms = cursor.fetchall()

    # Get incident reports
    # High Risk appears first
    cursor.execute("""
        SELECT *
        FROM incidents
        ORDER BY
            CASE
                WHEN risk_level = 'High Risk' THEN 1
                WHEN risk_level = 'Moderate Risk' THEN 2
                ELSE 3
            END,
            id DESC
    """)

    incidents = cursor.fetchall()

    connection.close()

    return render_template(
        "personnel.html",
        alarms=alarms,
        incidents=incidents
    )


# =========================
# CHECK FOR NEW ALARM
# =========================

@app.route("/check_alarm")
def check_alarm():

    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM alarms
        ORDER BY id DESC
        LIMIT 1
    """)

    alarm = cursor.fetchone()

    connection.close()

    if alarm:

        return jsonify({
            "id": alarm["id"],
            "student_name": alarm["student_name"],
            "location": alarm["location"],
            "alarm_time": alarm["alarm_time"],
            "status": alarm["status"]
        })

    return jsonify({
        "id": 0
    })


# =========================
# UPDATE ALARM STATUS
# =========================

@app.route("/update_alarm/<int:alarm_id>", methods=["POST"])
def update_alarm(alarm_id):

    new_status = request.form["status"]

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE alarms
        SET status = ?
        WHERE id = ?
    """, (
        new_status,
        alarm_id
    ))

    connection.commit()
    connection.close()

    return redirect(url_for("personnel"))


# =========================
# UPDATE INCIDENT STATUS
# =========================

@app.route("/update_incident/<int:incident_id>", methods=["POST"])
def update_incident(incident_id):

    new_status = request.form["status"]

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE incidents
        SET status = ?
        WHERE id = ?
    """, (
        new_status,
        incident_id
    ))

    connection.commit()
    connection.close()

    return redirect(url_for("personnel"))


# =========================
# START SYSTEM
# =========================

if __name__ == "__main__":

    create_database()

    app.run(debug=True)