from rest_framework.generics import CreateAPIView
from rest_framework import generics, status
from rest_framework.response import Response

from chatbot.serializers import FeedbackSerializer
from chatbot.utils.db_query import is_feedback, is_not_qna_id


class FeedbackCreateAPIView(CreateAPIView):
    """FeedbackCreateView
    POST: api/chatbot/feedback/
    """
    serializer_class = FeedbackSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        qna_id = request.data['qna_id']
        feedback = request.data['feedback']

        if is_not_qna_id(qna_id):
            return Response(status=status.HTTP_404_NOT_FOUND)
        if is_feedback(qna_id):
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer.save(
            qna_id=qna_id,
            feedback=feedback,
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
