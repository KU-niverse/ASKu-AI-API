from rest_framework.generics import ListCreateAPIView
from rest_framework.response import Response
from rest_framework import status

from chatbot.serializers.chatbot_qna_serializer import ChatbotQnaSerializer
from chatbot.models import Chatbot
from chatbot.utils.utils import getRelatedDocs, getCompletion
from chatbot.utils.db_query import insert_ai_history, select_user_id


class ChatbotListCreateAPIView(ListCreateAPIView):
    serializer_class = ChatbotQnaSerializer
    queryset = Chatbot.objects.all()

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save()

    def post(self, request, *args, **kwargs):
        serializer = ChatbotQnaSerializer(data=request.data)

        user_id = request.data['user_id']
        session_id = select_user_id(user_id)
        user_question = request.data['content']
        raw_data = getRelatedDocs(user_question, database="Redis")
        completion = getCompletion(user_question, raw_data)

        assistant_content = completion[-1]['content']['choices'][0]['message']['content']
        reference = '\n\n'.join(raw_data)
        if serializer.is_valid():
            insert_ai_history(session_id=session_id, content=user_question)
            chat_answer = serializer.save(
                session_id=session_id,
                content=assistant_content,
                type=True,
                reference=reference
            )
            serializer = ChatbotQnaSerializer(chat_answer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
