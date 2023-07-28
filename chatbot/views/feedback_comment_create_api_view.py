from rest_framework.generics import CreateAPIView
from rest_framework import generics, status
from rest_framework.response import Response

from chatbot.serializers import FeedbackSerializer
from chatbot.serializers.feedback_comment_serializer import FeedbackCommentSerializer
from chatbot.utils.db_query import is_feedback, is_not_qna_id, is_not_feedback_id, is_feedback_content


class FeedbackCommentCreateAPIView(CreateAPIView):
    """FeedbackCommentCreateView
    POST: api/chatbot/feedback/{int:feedback_id}
    """
    serializer_class = FeedbackCommentSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        feedback_id = request.data['feedback_id']
        content = request.data['content']

        if is_not_feedback_id(feedback_id):
            return Response(status=status.HTTP_404_NOT_FOUND)
        if is_feedback_content(feedback_id):
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer.save(
            feedback_id=feedback_id,
            content=content,
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
