from typing import List

from langchain.schema import Document
from json import dumps

from chatbot.utils.db_query import check_ai_session_for_ip_address, create_ai_session_for_ip_address
from django.conf import settings
from evaluation.tools.vectorstores.redis_store import QuestionRedisStore


def getUserIpAddress(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def formatReference(context: List[Document]):
    reference = {"Rule": ""}
    for document in context:
        if "title" in document.metadata.keys():
            reference[document.metadata["title"]] = document.page_content
        else:
            reference["Rule"] = reference["Rule"] + document.page_content + "\n"
    
    return dumps(reference, ensure_ascii=False)


def is_not_logged_in_user(request):
    user_ip_address = getUserIpAddress(request)

    # ip 주소가 있는지 확인
    session_info = check_ai_session_for_ip_address(user_ip_address)

    # ip 주소가 없으면 세션을 생성
    if session_info == None:
        session_id = create_ai_session_for_ip_address(user_ip_address)
        session_info = check_ai_session_for_ip_address(user_ip_address)
    return session_info


def get_recommended_questions(q_content):
    """
    : 사용자가 입력한 모호한 질문에 대해 추천 질문을 반환하는 함수

    Args:
        q_content (str): 사용자가 입력한 질문 내용.
    Returns:
        recommended (list): 추천 질문 목록.
            사용자가 입력한 질문과 추천 질문의 유사도가 높은 경우, 모호하지 않은 질문으로 판별하여 빈 리스트 반환.
                높지 않은 경우, 사용자의 질문과 유사도가 높은 추천 질문 리스트 반환.
    """
    high_similarity_question_retriever = getattr(settings, "high_similarity_question_retriever", None)
    lower_similarity_question_retriever = getattr(settings, "lower_similarity_question_retriever", None)
    if not high_similarity_question_retriever or not lower_similarity_question_retriever:
        return []

    recommended = []
    ex_question = high_similarity_question_retriever.invoke(q_content)
    if ex_question:
        return recommended

    ex_question = lower_similarity_question_retriever.invoke(q_content)
    for Q in ex_question:
        recommended.append(Q.page_content)
    return recommended
