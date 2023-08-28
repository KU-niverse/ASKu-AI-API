from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from chatbot.serializers import ChatbotCheckSerializer
from chatbot.utils.db_query import get_ai_session


class ChatbotCheckAPIView(APIView):
    serializer_class = ChatbotCheckSerializer

    def get(self, request, user_id, *args, **kwargs):
        session = get_ai_session(user_id)
        if session is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = ChatbotCheckSerializer(
            data={
                'is_questioning': session[0][0],
                'processing_q': session[0][1],
            })
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
