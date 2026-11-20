from databases.users_db import get_users_connection
from databases.analysis_db import get_analysis_connection
from databases.reports_db import get_reports_connection
from databases.feedback_db import get_feedback_connection


schemas = {
    "Users": (
        get_users_connection,
        [
            """
            CREATE TABLE IF NOT EXISTS users (
                id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                full_name VARCHAR(150) NOT NULL,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                plan ENUM('free', 'premium') DEFAULT 'free',
                premium_expires_at DATETIME NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS subscriptions (
                id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT UNSIGNED NOT NULL,
                plan VARCHAR(30) NOT NULL DEFAULT 'premium',
                amount DECIMAL(10,2) NOT NULL,
                status VARCHAR(30) NOT NULL DEFAULT 'pending',
                payment_reference VARCHAR(255) NULL,
                starts_at DATETIME NULL,
                expires_at DATETIME NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
    ),

    "Analysis": (
        get_analysis_connection,
        [
            """
            CREATE TABLE IF NOT EXISTS analysis_usage (
                id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT UNSIGNED NOT NULL,
                usage_date DATE NOT NULL,
                analysis_count INT NOT NULL DEFAULT 0,
                UNIQUE KEY unique_daily_usage (user_id, usage_date)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS analysis_history (
                id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT UNSIGNED NOT NULL,
                language VARCHAR(30) NOT NULL,
                code_text LONGTEXT NOT NULL,
                result_json JSON NULL,
                status VARCHAR(30) DEFAULT 'completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
    ),

    "Reports": (
        get_reports_connection,
        [
            """
            CREATE TABLE IF NOT EXISTS reports (
                id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT UNSIGNED NOT NULL,
                analysis_id BIGINT UNSIGNED NULL,
                title VARCHAR(255) NOT NULL,
                report_json JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
    ),

    "Feedback": (
        get_feedback_connection,
        [
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT UNSIGNED NULL,
                rating TINYINT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
    )
}


def initialize_databases():
    for name, (connect, queries) in schemas.items():
        db = None
        cursor = None

        try:
            db = connect()
            cursor = db.cursor()

            for query in queries:
                cursor.execute(query)

            db.commit()
            print(f"{name} database: TABLES CREATED")

        except Exception as error:
            if db:
                db.rollback()
            print(f"{name} database: FAILED - {error}")

        finally:
            if cursor:
                cursor.close()
            if db:
                db.close()


if __name__ == "__main__":
    initialize_databases()
