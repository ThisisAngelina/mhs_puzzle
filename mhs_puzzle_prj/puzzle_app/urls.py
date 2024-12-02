from django.urls import path
from . import views as v

urlpatterns = [
    path('', v.home, name='home'),
    path('quiz', v.quiz, name='quiz'),
    path('results', v.display_results, name='results'),
]