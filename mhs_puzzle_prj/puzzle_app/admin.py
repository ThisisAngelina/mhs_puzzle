from django.contrib import admin
from .models import (
    SurveyCompletion,
    UserInteraction,
    Area,
    Category,
    Question,
    Answer,
    QuestionResult,
    CategoryResult,
)

# Registering models with the Django admin site
admin.site.register(SurveyCompletion)
admin.site.register(UserInteraction)
admin.site.register(Area)
admin.site.register(Category)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(QuestionResult)
admin.site.register(CategoryResult)