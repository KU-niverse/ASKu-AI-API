from rest_framework.generics import ListCreateAPIView
from rest_framework.response import Response
from rest_framework import status

from drf_yasg.utils import swagger_auto_schema

from chatbot.serializers.chatbot_qna_serializer import ChatbotQnaSerializer
from chatbot.models import Chatbot
from chatbot.utils import getRelatedDocs, getCompletion

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
        # Encoding 문제: 한국어 쿼리를 못 받음
        serializer = ChatbotQnaSerializer(data=request.data)

        user_question = request.data['content']
        row_data = getRelatedDocs(user_question, database="Redis")
        completion = getCompletion(user_question, row_data)

        assistant_content = completion[-1]['content']['choices'][0]['message']['content']
        reference = '\n\n'.join(row_data)

        if serializer.is_valid():
            Chatbot.objects.create(content=user_question)
            chat_answer = serializer.save(
                content=assistant_content,
                type=True,
                reference=reference
            )
            serializer = ChatbotQnaSerializer(chat_answer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    