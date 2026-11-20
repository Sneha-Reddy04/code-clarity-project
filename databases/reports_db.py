import json
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_reports_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("REPORTS_DB"),
        connection_timeout=5,
    )


def create_report(user_id, title, report, analysis_id=None):
    db = get_reports_connection()
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO reports (user_id, analysis_id, title, report_json) VALUES (%s,%s,%s,%s)",
            (user_id, analysis_id, title[:255], json.dumps(report, ensure_ascii=False)),
        )
        db.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        db.close()


def list_reports(user_id):
    db = get_reports_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, analysis_id, title, created_at FROM reports WHERE user_id=%s ORDER BY created_at DESC LIMIT 100", (user_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        db.close()


def get_report(user_id, report_id):
    db = get_reports_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM reports WHERE id=%s AND user_id=%s", (report_id, user_id))
        row = cursor.fetchone()
        if row:
            row["report_json"] = json.loads(row["report_json"]) if isinstance(row["report_json"], (str, bytes, bytearray)) else row["report_json"]
        return row
    finally:
        cursor.close()
        db.close()
