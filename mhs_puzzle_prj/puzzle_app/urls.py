from django.urls import path
from . import views as v

urlpatterns = [
    path('', v.home, name='home'),
    path('quiz', v.quiz, name='quiz'),
    path('results', v.display_results, name='results'),
    path("login", v.login_view, name="login"),
    path("logout", v.logout_view, name="logout"),
    path("register", v.register, name="register"),

]