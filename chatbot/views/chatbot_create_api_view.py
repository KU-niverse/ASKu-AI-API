from rest_framework.generics import ListCreateAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import APIException


from chatbot.serializers.chatbot_qna_serializer import ChatbotQnaSerializer
from chatbot.models import Chatbot
from chatbot.utils.utils import getRelatedDocs, getCompletion
from chatbot.utils.db_query import insert_ai_history, check_ai_session, ai_session_start, ai_session_end

class DatabaseError(APIException):
    status_code = 500
    default_detail = '데이터베이스 오류가 발생했습니다.'
    default_code = 'database_error'

class ChatbotCreateAPIView(ListCreateAPIView):
    serializer_class = ChatbotQnaSerializer
    queryset = Chatbot.objects.all()

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save()

    def post(self, request, *args, **kwargs):
        #TODO: 아래 전체 코드에 대해(한 번에 묶어서) try except구문을 적용하여 에러 처리만 하면 됨 except code는 카톡으로 보냄
        serializer = ChatbotQnaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_id = request.data['user_id']
        session_info = check_ai_session(user_id)
        session_id = session_info[0]
        is_questioning = session_info[1]
        processing_q = session_info[2]
        user_question = request.data['q_content']
        #현재 진행중인지 확인-is_questioning
        if is_questioning:
            response_data = {
                "success": False,
                "message": "잘못된 요청, 진행 중인 질문이 있습니다, 해당 api를 호출할 수 없습니다.",
                "data": {"processing_q": processing_q}
            }
            return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)
        #TODO: false일때 DB에러 처리 해야함, 처리함
        #현재 진행중이 아니라면 진행중으로 변경
        start_result = ai_session_start(session_id, user_question)
        #쿼리가 성공적으로 수행되지 못한 경우
        if not start_result:
            raise DatabaseError
        

        raw_data = getRelatedDocs(user_question, database="Redis")
        completion = getCompletion(user_question, raw_data)
        assistant_content = completion[-1]['content']['choices'][0]['message']['content']
        reference = '\n\n'.join(raw_data)
        chat_answer = serializer.save(
            session_id=session_id,
            q_content=user_question,
            a_content=assistant_content,
            reference=reference
        )
        serializer = ChatbotQnaSerializer(chat_answer)
        #TODO: false일때 DB에러 처리 해야함, 처리함
        end_result = ai_session_end(session_id)
        if not end_result:
            raise DatabaseError
        #INFO: response에 success항목을 추가 및 기존에 body에 들어가던 데이터를 body.data로 전달, 이를 프론트에게 알려줘야함
        return Response({
            "success": True,
            "data": serializer.data,
            "message": "성공적으로 질문 답변이 이루어졌습니다!"
        }, status=status.HTTP_201_CREATED)
