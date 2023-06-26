from django.db import connection
from datetime import datetime


def insert_ai_history(session_id, content):
    created_at = datetime.now()
    with connection.cursor() as cursor:
        sql = """
            INSERT INTO ai_history (session_id, content, type, created_at)
            VALUES (%s, %s, %s, %s)
        """
        values = [
            session_id,
            content,
            False,
            created_at,
        ]
        cursor.execute(sql, values)
