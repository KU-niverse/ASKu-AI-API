import os
from datetime import datetime

from django.conf import settings
from langfuse.callback import CallbackHandler
from rest_framework.generics import ListCreateAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import APIException

from chatbot.serializers.chatbot_qna_serializer import ChatbotQnaSerializer
from chatbot.models import Chatbot
from chatbot.utils.utils import formatReference, get_recommended_questions
from chatbot.utils.db_query import check_ai_session, ai_session_start, ai_session_end


class DatabaseError(APIException):
    status_code = 500
    default_detail = '데이터베이스 오류가 발생했습니다.'
    default_code = 'database_error'


class ChatbotCreateAPIView(ListCreateAPIView):
    serializer_class = ChatbotQnaSerializer
    queryset = Chatbot.objects.all()
    is_limit = False

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save()

    def post(self, request, *args, **kwargs):
        serializer = ChatbotQnaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_id = request.data['user_id']
        session_info = check_ai_session(user_id)
        session_id, user_id, is_questioning, processing_q, question_limit = session_info[:5]
        user_question = request.data['q_content']

        if is_questioning:
            """ 현재 진행중일 경우 오류 반환 """
            response_data = {
                "success": False,
                "message": "잘못된 요청, 진행 중인 질문이 있습니다, 해당 api를 호출할 수 없습니다.",
                "data": {"processing_q": processing_q}
            }
            return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

        try:
            start_result = ai_session_start(session_id, user_question)
            if not start_result:
                """ 쿼리가 성공적으로 수행되지 못한 경우 오류 처리 """
                raise DatabaseError

            query_chain = getattr(settings, "query_chain", "localhost")

            langfuse_handler = CallbackHandler(
                secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                host=os.getenv("LANGFUSE_HOST"),
                user_id=str(user_id),
            )

            requested_at = datetime.now()
            query_response = query_chain.invoke({"input": user_question}, config={"callbacks": [langfuse_handler]})
            responsed_at = datetime.now()
            latency = responsed_at - requested_at
            latency_time = latency.total_seconds()

            chat_answer = serializer.save(
                session_id=session_id,
                q_content=user_question,
                a_content=query_response["answer"],
                reference=formatReference(query_response["context"]),
                recommended_questions=get_recommended_questions(user_question),
                requested_at=requested_at,
                responsed_at=responsed_at,
                latency_time=latency_time
            )
            serializer = ChatbotQnaSerializer(chat_answer)
            end_result = ai_session_end(session_id, self.is_limit, user_id == 0)
            if not end_result:
                raise DatabaseError
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(e)
            end_result = ai_session_end(session_id, self.is_limit, user_id == 0)
            if not end_result:
                raise DatabaseError
            return Response(serializer.data, status=status.HTTP_408_REQUEST_TIMEOUT)
