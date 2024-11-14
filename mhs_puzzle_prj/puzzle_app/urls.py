from django.urls import path
from . import views as v

urlpatterns = [
    path('quiz', v.quiz, name='quiz'),
]