from ..models import Category, Area, QuestionResult, SurveyCompletion 
from django.contrib.auth.models import User
from ..services.main_quiz_services import calculate_category_scores


def run():

    test_user = User.objects.get(username="test_user")
    print("the user object is ", test_user.username)
    #check_time = SurveyCompletion.objects.filter(user=test_user).first().completion_time

    calculate_category_scores(test_user)
    print("last line executed")