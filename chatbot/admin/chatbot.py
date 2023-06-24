from django.contrib import admin
from chatbot.models import Chatbot


@admin.register(Chatbot)
class ChatbotAdmin(admin.ModelAdmin):
    """Admin View for Chatbot"""

    list_display = (
            "id",
            "session_id",
            "content",
            "type",
            "reference",
            "created_at",
    )
    readonly_fields = (
        "created_at",
    )
    search_fields = ("session_id",)
    ordering = (
        "created_at",
    )

# admin.site.register(Chatbot)
