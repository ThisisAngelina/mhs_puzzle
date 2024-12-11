#TODO Figure out how to simulate a user with Selenium - https://www.djangotricks.com/tricks/3bNUzYpfpCRR/
#TODO make unit tests for all the functions

import json

from django.db.models import Prefetch
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils.timezone import now
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib.auth.views import LogoutView, LoginView

from .models import Question, Category, Answer, QuestionResult, SurveyCompletion
from django.contrib.auth.models import User
from .services.main_quiz_services import _load_questions, _process_scores, _display_graphs, _display_priority_category, _display_recommendation

#display the home page
def home(request):
    ''' The home page just displays a welcome image and a button to start the quiz'''
    return render(request, 'puzzle_app/home.html')

_load_questions() # Grab quiz questions from the cache

# Serve quiz questions, collect answers, call the answer-processing function
@login_required
def quiz(request):
    user = request.user

    current_index = request.session.get('current_question_index', 0)
    user_answers = request.session.get('user_answers', {}) #storing the dictionary with the answers in the session 
    #TODO use the _load_questions() function instead
    # Fetch cached questions from Redis
    questions_cache_key = "quiz_questions"
    cached_questions = cache.get(questions_cache_key)

    if not cached_questions:
        # Handle missing cached questions
        print("there are no questions in the cache")
        return render(request, "puzzle_app/error.html", {"message": "Questions not available. Please reload."})

    # Deserialize cached questions
    questions_dict = json.loads(cached_questions)
    question_ids = list(questions_dict.keys())  # Extract all question IDs
    
    # Display the questions
    if request.method == "GET":
        if current_index >= len(question_ids):
            # Handle end of quiz
            request.session['current_question_index'] = 0  # Reset index for future sessions
            # Record quiz completion in the SurveyCompletion model
            completion_time = now()
            new_quiz_submission = SurveyCompletion.objects.create(user=user, completion_time=completion_time)
            new_quiz_submission.save()
       
            # Process the data to calculate the scores and produce the graphs
            _process_scores(user, user_answers)
            request.session.pop('user_answers', None)  # Clear answers after processing

            # Redirect the user to the results page
            return redirect('results')

        # Retrieve the current question
        current_question_id = question_ids[current_index]
        current_question = questions_dict[current_question_id]

        # Nutrition questions handling
        if current_question["category"] == "Nutrition":
            group_text = "In the last three days, did you consume any of the following foods:"
            nutrition_questions_to_present = [
                {
                    "id": qid,
                    "title": qdata["content"],
                    "answer_choices": qdata["answers"]
                }
                for qid, qdata in questions_dict.items() if qdata["category"] == "Nutrition"
            ]
            # Update the session index
            request.session['current_question_index'] = current_index + len(nutrition_questions_to_present)
        else:
            # Non-Nutrition questions
            group_text = None
            nutrition_questions_to_present = []
            request.session['current_question_index'] = current_index + 1

        return render(request, "puzzle_app/quiz.html", {
            "question": {
                "id": current_question_id,
                "title": current_question["content"],
                "answer_choices": current_question["answers"]
            } if not nutrition_questions_to_present else None,
            "nutrition_questions": nutrition_questions_to_present,
            "progress": round((current_index + 1) / len(question_ids) * 100),
            "group_text": group_text,
        })
        
        
    # Handle form submission (Next button click) #if the user is POSTing the answers
    elif request.method == "POST":
        
        for key, value in request.POST.items():
            if key.startswith("selected_score_"):
                question_id = key.split("_")[-1]
                question_score = value  # The selected score for the question
                user_answers[question_id] = question_score #this dictionary will then be passed to the process_answers function

                if value:
                    # Validate question existence in cached questions
                    if question_id not in questions_dict:
                        raise ValueError(f"Question with id {question_id} not found in cached questions.")  # Log this error

                    # Save the answer to the database
                    new_score = QuestionResult.objects.create(
                        user=user,
                        question_id=int(question_id),  # Directly save using the ID
                        score=question_score
                    )
                    new_score.save()
                    
                else:
                    # If no answer was selected
                    messages.warning(request, "Oops, please select an answer!")
                    request.session['current_question_index'] = max(0, current_index - 1)  # Prevent negative index
                    return redirect('quiz')
        
        # Update session with user answers       
        request.session['user_answers'] = user_answers  # Save updated answers in the session
        return redirect('quiz')  # Allow the user to continue with the quiz
    

@login_required   
def display_results(request):
    '''Display graphs, priority category and recomemendations'''

    # Graphs
    graphs = _display_graphs(request.user.id)
    
    if not graphs:
        # if there are no graphs to display
        return render(request, "puzzle_app/error.html", {"message": "No results found. Please complete the quiz first."})
    
    # Priority category (text)
    priority_category = _display_priority_category(request.user.id)
    if priority_category == None:
        priority_category = ""
    print("the priority category is ", priority_category)

    recommendation = _display_recommendation(request.user.id)
    if recommendation == None:
        recommendation = ""
    print("the recommendation is ", recommendation)

    
    # Combine the graphs, the priority category and the recommendation dictionaries
    context = graphs | priority_category| recommendation

    # Render the results template
    return render(request, "puzzle_app/results.html", context)

def register(request):
    ''' Create a new user account. '''
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration successful! You can now log in.")
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'puzzle_app/register.html', {'form': form})

class CustomLoginView(LoginView):
    template_name = 'puzzle_app/login.html'  
    #redirect_authenticated_user = True  

    def form_valid(self, form):
        # Add a success message
        messages.success(self.request, "Logged in successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('quiz')

class CustomLogoutView(LogoutView):
    ''' Customize Django's built-in LogoutView class with custom rerouting and message'''
    next_page = reverse_lazy('home')  # Redirect to home after logout

    def dispatch(self, request, *args, **kwargs):
        messages.success(request, "Logged out successfully.")
        return super().dispatch(request, *args, **kwargs)