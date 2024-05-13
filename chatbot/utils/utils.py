from typing import List

from langchain.schema import Document
from json import dumps

from chatbot.utils.db_query import check_ai_session_for_ip_address, create_ai_session_for_ip_address


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
