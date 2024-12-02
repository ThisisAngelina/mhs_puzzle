#TODO Install Selenium. Make Wheel of life graph - https://matplotlib.org/stable/gallery/pie_and_polar_chart.
#TODO make unit tests for all the functions
from django.db.models import Prefetch
from django.core.cache import cache
import json
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils.timezone import now
import base64

from .models import Question, Category, Answer, QuestionResult, SurveyCompletion
from . import services

#display the home page
def home(request):
    return render(request, 'puzzle_app/home.html')




# Get quiz questions form cache - Prefetch questions and answers, serialize them, and store in Redis.
def load_questions():
    global question_count #the number of quiz questions

    questions_cache_key = "quiz_questions"

    # Check if questions are already cached
    cached_questions = cache.get(questions_cache_key)

    if not cached_questions:
        # Prefetch questions and answers
        questions = Question.objects.select_related('category', 'category__area').prefetch_related(
            Prefetch('answer_set', queryset=Answer.objects.all())
        )
        print("questions got fetched from the db")

        # Serialize all questions into JSON-like structures
        questions_dict = {
            question.id: {
                "content": question.content,
                "category": question.category.name,
                "area": question.category.area.name,
                "answers": [
                    {"answer_text": answer.answer_text, "score": answer.score} for answer in question.answer_set.all()
                ],
            }
            for question in questions
        }

        # Cache serialized data
        cache.set(questions_cache_key, json.dumps(questions_dict), timeout=60 * 60 * 24 * 30)  # Cache for 30 days
        print("Questions cached in Redis.")

    else:
        print("Questions loaded from Redis.")

    # Set question count
    question_count = len(json.loads(cached_questions) if cached_questions else questions_dict)


load_questions() # Grab quiz questions from the cache

# Serve quiz questions, collect answers, call the answer-processing function
def quiz(request):
    user = request.user

    current_index = request.session.get('current_question_index', 0)
    user_answers = request.session.get('user_answers', {}) #storing the dictionary with the answers in the session 

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
            print("the submitted answers to pass are ", user_answers)
            print("the completion time is ", completion_time)

            # Process the data to calculate the scores and produce the graphs
            services.process_scores(user, user_answers)
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
                    print("new score recorded in db")
                else:
                    # If no answer was selected
                    messages.warning(request, "Oops, please select an answer!")
                    request.session['current_question_index'] = max(0, current_index - 1)  # Prevent negative index
                    return redirect('quiz')
        
        # Update session with user answers       
        request.session['user_answers'] = user_answers  # Save updated answers in the session
        return redirect('quiz')  # Allow the user to continue with the quiz
    

#TODO don't display Esthetic area graphs
#TODO check what happens if the same user submits the quiz twice
#TODO check how the graphs are displayed on a small phone screen
def display_results(request):
    # Retrieve cached images using the user ID
    cache_key = f"user_{request.user.id}_gauge_graphs"
    print("the key with which to search the cache is ", cache_key)
    gauge_graphs = cache.get(cache_key)

    if not gauge_graphs:
        # If no graphs are found in the cache, return an error or handle accordingly
        return render(request, "puzzle_app/error.html", {"message": "No results found. Please complete the quiz first."})

    # Prepare data for the template
    images_data = []  # List to hold image and label pairs
    for label, graph_bytes in gauge_graphs.items():
        # Convert byte data to a base64 string
        img_base64 = base64.b64encode(graph_bytes).decode('utf-8')
        # Append the label and base64 data
        images_data.append({"label": label, "image": f"data:image/jpeg;base64,{img_base64}"})

    # Render the results template
    return render(request, "puzzle_app/results.html", {"images_data": images_data})

