
from databases.users_db import get_users_connection
from databases.analysis_db import get_analysis_connection
from databases.reports_db import get_reports_connection
from databases.feedback_db import get_feedback_connection

connections = [
    ("Users", get_users_connection),
    ("Analysis", get_analysis_connection),
    ("Reports", get_reports_connection),
    ("Feedback", get_feedback_connection)
]

for name, get_connection in connections:
    try:
        connection = get_connection()
        print(f"{name} database: CONNECTED")
        connection.close()
    except Exception as error:
        print(f"{name} database: FAILED - {error}")
