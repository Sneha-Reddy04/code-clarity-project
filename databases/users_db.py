
import os
import json
import mysql.connector
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()


def get_users_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("USERS_DB")
    )


def register_user(full_name, email, password):
    db = None
    cursor = None

    try:
        db = get_users_connection()
        cursor = db.cursor()

        password_hash = generate_password_hash(password)

        cursor.execute(
            """
            INSERT INTO users (full_name, email, password_hash)
            VALUES (%s, %s, %s)
            """,
            (full_name, email, password_hash)
        )

        db.commit()
        return {"success": True}

    except mysql.connector.IntegrityError:
        return {
            "success": False,
            "error": "Email already registered"
        }

    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


def get_user_by_email(email):
    db = None
    cursor = None

    try:
        db = get_users_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE email = %s",
            (email,)
        )

        return cursor.fetchone()

    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


def get_user_by_id(user_id):
    db = None
    cursor = None

    try:
        db = get_users_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, full_name, email, plan,
                   premium_expires_at, created_at,
                   preferred_languages
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if user and user.get("preferred_languages"):
            try:
                user["preferred_languages"] = json.loads(
                    user["preferred_languages"]
                )
            except (ValueError, TypeError):
                user["preferred_languages"] = []

        elif user:
            user["preferred_languages"] = []

        return user

    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


def verify_user(email, password):
    user = get_user_by_email(email)

    if user and check_password_hash(
        user["password_hash"], password
    ):
        return user

    return None


def update_user_profile(user_id, full_name, email):
    db = None
    cursor = None

    try:
        db = get_users_connection()
        cursor = db.cursor()

        cursor.execute(
            """
            UPDATE users
            SET full_name = %s, email = %s
            WHERE id = %s
            """,
            (full_name, email, user_id)
        )

        db.commit()

        return {"success": True}

    except mysql.connector.IntegrityError:
        return {
            "success": False,
            "error": "This email address is already registered."
        }

    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


def update_user_preferences(user_id, preferred_languages):
    db = None
    cursor = None

    try:
        db = get_users_connection()
        cursor = db.cursor()

        cursor.execute(
            """
            UPDATE users
            SET preferred_languages = %s
            WHERE id = %s
            """,
            (
                json.dumps(preferred_languages),
                user_id
            )
        )

        db.commit()

        return {"success": True}

    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


def change_user_password(user_id, current_password, new_password):

    db = None
    cursor = None

    try:
        db = get_users_connection()
        cursor = db.cursor()

        cursor.execute(
            "SELECT password_hash FROM users WHERE id = %s",
            (user_id,)
        )

        user = cursor.fetchone()

        if not user:
            return {
                "success": False,
                "error": "User not found."
            }

        if not check_password_hash(user[0], current_password):
            return {
                "success": False,
                "error": "Current password is incorrect."
            }

        new_password_hash = generate_password_hash(new_password)

        cursor.execute(
            """
            UPDATE users
            SET password_hash = %s
            WHERE id = %s
            """,
            (new_password_hash, user_id)
        )

        db.commit()

        return {"success": True}

    finally:
        if cursor:
            cursor.close()

        if db:
            db.close()

