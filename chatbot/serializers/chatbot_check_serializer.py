from rest_framework import serializers


class ChatbotCheckSerializer(serializers.Serializer):
    """Serializer definition for Chatbot Check API."""

    is_questioning = serializers.IntegerField(required=False)
    processing_q = serializers.CharField(required=False, allow_null=True)

    class Meta:
        """Meta definition for ChatbotListSerializer."""

        fields = [
            "is_questioning",
            "processing_q",
        ]

    def create(self, validated_data):
        is_questioning = validated_data['is_questioning']
        processing_q = validated_data['processing_q']
        return validated_data
