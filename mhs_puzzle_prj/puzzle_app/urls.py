from django.urls import path
from django.contrib.auth import views as auth_views
from django.views import defaults
from . import views as v

urlpatterns = [
    path('', v.home, name='home'),
    path('quiz', v.quiz, name='quiz'),
    path('results', v.display_results, name='results'),
    path('logout', v.CustomLogoutView.as_view(), name='logout'),
    path('login', v.CustomLoginView.as_view(), name='login'),
    path('register', v.register, name='register'),
    path('password_reset', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password_change', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('password_change/done', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    path("help/", v.help, name="help"),

]

