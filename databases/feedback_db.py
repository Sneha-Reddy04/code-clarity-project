import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_feedback_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("FEEDBACK_DB"),
        connection_timeout=5,
    )


def save_feedback(user_id, rating, message):
    db = get_feedback_connection()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO feedback (user_id, rating, message) VALUES (%s,%s,%s)", (user_id, rating, message))
        db.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        db.close()
