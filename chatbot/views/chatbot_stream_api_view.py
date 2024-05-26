import os
import json
from datetime import datetime

from django.conf import settings
from django.http import StreamingHttpResponse
from rest_framework.exceptions import APIException
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from langfuse.callback import CallbackHandler
from chatbot.serializers.chatbot_qna_serializer import ChatbotQnaSerializer
from chatbot.models import Chatbot
from chatbot.utils.utils import formatReference
from chatbot.utils.db_query import check_ai_session, ai_session_start, ai_session_end


class DatabaseError(APIException):
    status_code = 500
    default_detail = '데이터베이스 오류가 발생했습니다.'
    default_code = 'database_error'


class ChatbotStreamAPIView(APIView):
    serializer_class = ChatbotQnaSerializer
    queryset = Chatbot.objects.all()
    is_limit = False


    def post(self, request, *args, **kwargs):
        serializer = ChatbotQnaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_id = request.data['user_id']
        session_info = check_ai_session(user_id)
        session_id, user_id, is_questioning, processing_q, question_limit = session_info[:5]
        user_question = request.data['q_content']

        if is_questioning:
            response_data = {
                "success": False,
                "message": "잘못된 요청, 진행 중인 질문이 있습니다, 해당 api를 호출할 수 없습니다.",
                "data": {"processing_q": processing_q}
            }
            return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

        try:
            start_result = ai_session_start(session_id, user_question)
            if not start_result:
                raise DatabaseError

            query_chain = getattr(settings, "QueryChain", "localhost")

            langfuse_handler = CallbackHandler(
                secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                host=os.getenv("LANGFUSE_HOST"),
                user_id=str(user_id),
            )

            def event_stream(serializer):
                try:
                    answers = []
                    contexts = []
                    requested_at = datetime.now()
                    for chunk in query_chain.stream({"input": user_question}, config={"callbacks": [langfuse_handler]}):
                        if 'context' in chunk:
                            contexts.extend(chunk['context'])
                        if 'answer' in chunk:
                            answers.append(chunk['answer'])
                            yield f'data: {chunk}\n\n'
                    responsed_at = datetime.now()
                    latency = responsed_at - requested_at
                    latency_time = latency.total_seconds()

                    chat_answer = serializer.save(
                        session_id=session_id,
                        q_content=user_question,
                        a_content=''.join(answers),
                        reference=formatReference(contexts),
                        requested_at=requested_at,
                        responsed_at=responsed_at,
                        latency_time=latency_time
                    )
                    serializer = ChatbotQnaSerializer(chat_answer)
                    yield f'data: {json.dumps({"complete": True, "data": serializer.data})}\n\n'
                    ai_session_end(session_id, self.is_limit, user_id == 0)

                except Exception as e:
                    ai_session_end(session_id, self.is_limit, user_id == 0)
                    yield f'data: {json.dumps({"error": "An error occurred"})}\n\n'

            response = StreamingHttpResponse(event_stream(serializer), content_type='text/event-stream')
            response['Cache-Control'] = 'no-cache'
            return response

        except Exception as e:
            ai_session_end(session_id, self.is_limit, user_id == 0)
            return Response({"error": "An error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
