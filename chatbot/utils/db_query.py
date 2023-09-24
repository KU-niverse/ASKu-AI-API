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


def check_ai_session(user_id):
    with connection.cursor() as cursor:
        sql = """
            SELECT id,user_id, is_questioning, processing_q, question_limit FROM ai_session WHERE user_id = %s
        """
        cursor.execute(sql, [user_id])
        session_info = cursor.fetchall()
    if session_info:
        return session_info[0]
    return None

def check_ai_session_for_ip_address(user_ip_address):
    with connection.cursor() as cursor:
        sql = """
            SELECT id, user_id, is_questioning, processing_q, question_limit FROM ai_session WHERE ip_address = %s
        """
        cursor.execute(sql, [user_ip_address])
        session_info = cursor.fetchall()
    if session_info:
        return session_info[0]
    return None
def create_ai_session_for_ip_address(user_ip_address):
    with connection.cursor() as cursor:
        sql = """
            INSERT INTO ai_session (user_id, ip_address) VALUES (%s, %s)
        """
        cursor.execute(sql, [0, user_ip_address])
        session_id = cursor.lastrowid
    return session_id


def check_question_limit(user_id):
    """ user가 질문을 할 수 있는지 여부를 판단하는 함수.
    question_limit의 기본값은 5이며, question_limit가 0보다 클 경우 user가 질문할 수 있음.
    """
    with connection.cursor() as cursor:
        sql = """
            SELECT question_limit FROM ai_session WHERE user_id = %s
        """
        cursor.execute(sql, [user_id])
        session_info = cursor.fetchall()
        print(session_info)
    if session_info[0][0] > 0:
        return False
    return True


def ai_session_start(session_id, q_content):
    """ ai_session을 시작할때 실행, 실제로 업데이트가 이루어지지 않으면 False를 반환 """
    with connection.cursor() as cursor:
        sql = """
            UPDATE ai_session SET is_questioning = 1, processing_q = %s WHERE id = %s
        """
        cursor.execute(sql, [q_content, session_id])
        session_info = cursor.rowcount
    if session_info:
        return True
    return False


def ai_session_end(session_id, is_limit, is_ip_based):
    """ ai_session을 끝낼 때 실행, 실제로 업데이트가 이루어지지 않으면 False를 반환 """
    with connection.cursor() as cursor:
        if is_limit or is_ip_based:
            sql = """
                UPDATE ai_session SET is_questioning = 0, processing_q = NULL, question_limit = question_limit - 1 
                WHERE id = %s
            """
        else:
            sql = """
                UPDATE ai_session SET is_questioning = 0, processing_q = NULL WHERE id = %s
            """
        cursor.execute(sql, [session_id])
        session_info = cursor.rowcount
    if session_info:
        return True
    return False


def select_ai_history(session_id):
    with connection.cursor() as cursor:
        sql = """
            SELECT id, q_content, a_content, reference, created_at FROM ai_history 
            WHERE session_id = %s AND is_deleted = 0
        """
        cursor.execute(sql, [session_id])
        chatbot_list = cursor.fetchall()
    if chatbot_list:
        return chatbot_list
    return None


def get_ai_session(user_id):
    with connection.cursor() as cursor:
        sql = """
            SELECT is_questioning, processing_q FROM ai_session WHERE user_id = %s
        """
        cursor.execute(sql, [user_id])
        session = cursor.fetchall()
    if session:
        return session
    return None


def update_is_delete(session_id):
    with connection.cursor() as cursor:
        sql = """
            UPDATE ai_history SET is_deleted = 1 WHERE session_id = %s
        """
        cursor.execute(sql, [session_id])
        history = cursor.rowcount
    if history:
        return True
    return False


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
