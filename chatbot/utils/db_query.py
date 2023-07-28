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


def select_user_id(user_id):
    with connection.cursor() as cursor:
        sql = """
            SELECT id FROM ai_session WHERE user_id = %s
        """
        cursor.execute(sql, [user_id])
        session_id = cursor.fetchall()
    if session_id:
        return session_id[0][0]
    return None


def is_feedback(qna_id):
    """ feedback Table에 qna_id의 값이 존재 여부를 확인하는 함수
    qna_id가 이미 존재할 경우 True, 존재하지 않을 경우 False를 반환
    """
    with connection.cursor() as cursor:
        sql = """
            SELECT id FROM feedback WHERE qna_id = %s
        """
        cursor.execute(sql, [qna_id])
        feedback = cursor.fetchall()
    if feedback:
        return True
    return False


def is_not_qna_id(qna_id):
    """ ai_history Table에 qna_id의 FK값이 존재 여부를 확인하는 함수
    id가 존재하지 않을 경우 True, 존재할 경우 False를 반환
    """
    with connection.cursor() as cursor:
        sql = """
            SELECT id FROM ai_history WHERE id = %s
        """
        cursor.execute(sql, [qna_id])
        qna = cursor.fetchall()
    if qna:
        return False
    return True


def is_not_feedback_id(feedback_id):
    """ feedback Table에 feedback_id의 FK값이 존재 여부를 확인하는 함수
    id가 존재하지 않을 경우 True, 존재할 경우 False를 반환
    """
    with connection.cursor() as cursor:
        sql = """
            SELECT id FROM feedback WHERE id = %s
        """
        cursor.execute(sql, [feedback_id])
        feedback = cursor.fetchall()
    if feedback:
        return False
    return True


def is_feedback_content(feedback_id):
    """ feedback_content Table에 feedback_id의 값이 존재 여부를 확인하는 함수
    feedback_id가 이미 존재할 경우 True, 존재하지 않을 경우 False를 반환
    """
    with connection.cursor() as cursor:
        sql = """
            SELECT id FROM feedback_content WHERE feedback_id = %s
        """
        cursor.execute(sql, [feedback_id])
        comment = cursor.fetchall()
    if comment:
        return True
    return False
