from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from chatbot.serializers.chatbot_qna_serializer import ChatbotQnaSerializer
from chatbot.utils.db_query import select_user_id, update_is_delete


class ChatbotUpdateAPIView(APIView):
    serializer_class = ChatbotQnaSerializer

    def patch(self, request, user_id, *args, **kwargs):
        session_id = select_user_id(user_id)
        if session_id is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        update_is_delete(session_id)
        return Response(status=status.HTTP_200_OK)
