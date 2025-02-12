import json

from django.db.models import Prefetch
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.core.mail import send_mail
from django.contrib import messages
from django.utils.timezone import now
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib.auth.views import LogoutView, LoginView
from django.conf import settings

from .models import Question, Category, Answer, QuestionResult, SurveyCompletion
from .forms import HelpForm
from django.contrib.auth.models import User
from .services.main_quiz_services import _load_questions, _process_scores, _display_graphs, _display_priority_category, _display_recommendation

#display the home page
def home(request):
    ''' The home page just displays a welcome image and a button to start the quiz'''
    return render(request, 'puzzle_app/home.html')



# Serve quiz questions, collect answers, call the answer-processing function
@login_required
def quiz(request):
    user = request.user

    current_index = request.session.get('current_question_index', 0)
    user_answers = request.session.get('user_answers', {}) #storing the dictionary with the answers in the session 

    # Fetch cached questions from Redis
    cached_questions, question_count = _load_questions() # Grab quiz questions from the cache
    
    # Deserialize cached questions
    questions_dict = json.loads(cached_questions)
    question_ids = list(questions_dict.keys())  # Extract all question IDs

    # Display the questions
    if request.method == "GET":
        if current_index >= question_count:
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
            #request.session['current_question_index'] = current_index + 1

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
                
        request.session['current_question_index'] = current_index + 1 # increment the q index by 1 after the user has submitted a response
        
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
    context = {"priority_category": priority_category, "recommendation": recommendation}
    context = graphs | context

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
    
def custom_error_view(request, exception):
    return render(request, 'puzzle_app/404.html', status=404)


def help(request):
    if request.method == "POST":
        form = HelpForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            email = form.cleaned_data["email"]
            subject = form.cleaned_data["subject"]
            message = form.cleaned_data["message"]

            # Compose the email
            full_message = f"Message from {name} ({email}):\n\n{message}"

            try:
                send_mail(
                    subject=f"MHS puzzle app help: {subject}",
                    message=full_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.EMAIL_HOST_USER],  # Replace with your email
                    fail_silently=False,
                )
                messages.success(request, "Your message has been sent successfully!")
                return redirect("help")  # Redirect back to the help page
            except Exception as e:
                messages.error(request, f"Error sending email: {e}")

    else:
        form = HelpForm()

    return render(request, "puzzle_app/help.html", {"form": form})