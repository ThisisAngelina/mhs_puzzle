from django.urls import path
from . import views as v

urlpatterns = [
    path('quiz', v.question_view, name='quiz'),
    path('quiz', v.save_answers, name='save_answers'),
]