from django.conf import settings
from langfuse.callback import CallbackHandler
from rest_framework.generics import ListCreateAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import APIException

from chatbot.serializers.chatbot_qna_serializer import ChatbotQnaSerializer
from chatbot.models import Chatbot
from chatbot.utils.utils import getUserIpAddress, formatReference
from chatbot.utils.db_query import check_ai_session, ai_session_start, ai_session_end, check_question_limit, check_ai_session_for_ip_address, create_ai_session_for_ip_address


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
        #비로그인 유저일 경우
        if user_id == 0:
            user_ip_address = getUserIpAddress(request)
            #ip주소가 있는지 확인
            session_info = check_ai_session_for_ip_address(user_ip_address)
            #ip주소가 없으면 세션을 생성
            if session_info == None:
                session_id = create_ai_session_for_ip_address(user_ip_address)
                session_info = check_ai_session_for_ip_address(user_ip_address)
        else:
            session_info = check_ai_session(user_id)

        session_id, user_id, is_questioning, processing_q, question_limit = session_info[:5]
        user_question = request.data['q_content']

        if question_limit <= 0:
            """ user가 1일 질문 횟수(5회)를 넘겼을 경우 오류 반환 """
            return Response(status=status.HTTP_403_FORBIDDEN)

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
            
            QueryChain = getattr(settings, "QueryChain", "localhost")


            langfuse_handler = CallbackHandler(
                secret_key= "",
                public_key= "",
                host="https://cloud.langfuse.com", # 🇪🇺 EU region
              # host="https://us.cloud.langfuse.com", # 🇺🇸 US region
            )
            
            QueryResponse = QueryChain.invoke({"input": user_question}, config={"callbacks": [langfuse_handler]})
            assistant_content = QueryResponse["answer"]
            reference = formatReference(QueryResponse["context"])

            chat_answer = serializer.save(
                session_id=session_id,
                q_content=user_question,
                a_content=assistant_content,
                reference=reference
            )
            serializer = ChatbotQnaSerializer(chat_answer)
            end_result = ai_session_end(session_id, self.is_limit, user_id == 0)
            if not end_result:
                raise DatabaseError
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            end_result = ai_session_end(session_id, self.is_limit, user_id == 0)
            if not end_result:
                raise DatabaseError
            return Response(serializer.data, status=status.HTTP_408_REQUEST_TIMEOUT)
