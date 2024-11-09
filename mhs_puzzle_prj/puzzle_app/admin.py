from django.contrib import admin
from .models import (
    User,
    SurveyCompletion,
    UserInteraction,
    Area,
    Category,
    Question,
    Answer,
    QuestionResult,
    CategoryResult,
    AreaResult,
    Focus,
    Recommendation,
    Prompt,
)

# Registering models with the Django admin site
admin.site.register(User)
admin.site.register(SurveyCompletion)
admin.site.register(UserInteraction)
admin.site.register(Area)
admin.site.register(Category)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(QuestionResult)
admin.site.register(CategoryResult)
admin.site.register(AreaResult)
admin.site.register(Focus)
admin.site.register(Recommendation)
admin.site.register(Prompt)