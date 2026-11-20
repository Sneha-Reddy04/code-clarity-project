import json
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_analysis_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("ANALYSIS_DB"),
        connection_timeout=5,
    )


def save_analysis(user_id, language, code, result):
    db = get_analysis_connection()
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO analysis_history (user_id, language, code_text, result_json, status) VALUES (%s,%s,%s,%s,%s)",
            (user_id, language, code, json.dumps(result, ensure_ascii=False), result.get("execution", {}).get("status", "completed")),
        )
        analysis_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO analysis_usage (user_id, usage_date, analysis_count) VALUES (%s, CURDATE(), 1) ON DUPLICATE KEY UPDATE analysis_count = analysis_count + 1",
            (user_id,),
        )
        db.commit()
        return analysis_id
    finally:
        cursor.close()
        db.close()


def list_analyses(user_id, limit=50):
    db = get_analysis_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, language, LEFT(code_text, 180) AS code_preview, status, created_at FROM analysis_history WHERE user_id=%s ORDER BY created_at DESC LIMIT %s",
            (user_id, limit),
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        db.close()


def get_analysis(user_id, analysis_id):
    db = get_analysis_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM analysis_history WHERE id=%s AND user_id=%s",
            (analysis_id, user_id),
        )
        row = cursor.fetchone()
        if row and row.get("result_json"):
            row["result_json"] = json.loads(row["result_json"]) if isinstance(row["result_json"], (str, bytes, bytearray)) else row["result_json"]
        return row
    finally:
        cursor.close()
        db.close()


def delete_analysis(user_id, analysis_id):
    db = get_analysis_connection()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM analysis_history WHERE id=%s AND user_id=%s", (analysis_id, user_id))
        db.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        db.close()
