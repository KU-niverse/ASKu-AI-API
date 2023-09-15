from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from chatbot.serializers import ChatbotAbstractSerializer
from chatbot.serializers.chatbot_qna_serializer import ChatbotQnaSerializer
from chatbot.utils.db_query import select_user_id, update_is_delete, select_ai_history


class ChatbotListUpdateAPIView(APIView):
    serializer_class = ChatbotQnaSerializer

    def get(self, request, user_id, *args, **kwargs):
        session_id = select_user_id(user_id)
        if session_id is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        history = select_ai_history(session_id)
        if history is None:
            return Response(status=status.HTTP_204_NO_CONTENT)

        serialized_data = []
        for tuple_data in history:
            serializer = ChatbotAbstractSerializer(
                data={
                    'id': tuple_data[0],
                    'q_content': tuple_data[1],
                    'a_content': tuple_data[2],
                    'reference': tuple_data[3],
                    'created_at': tuple_data[4],
                })
            if serializer.is_valid():
                serialized_data.append(serializer.data)
        return Response(serialized_data, status=status.HTTP_200_OK)


    def patch(self, request, user_id, *args, **kwargs):
        session_id = select_user_id(user_id)
        if session_id is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        update_is_delete(session_id)
        return Response(status=status.HTTP_200_OK)
