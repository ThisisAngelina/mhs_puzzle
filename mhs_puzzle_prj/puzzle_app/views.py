from django.shortcuts import render, redirect
from django.utils.timezone import now
from django.contrib import messages
from django.db.models import Prefetch

from .models import Question, Answer, Category, Area, QuestionResult, SurveyCompletion
from . import services


# Prefetch the querysets globally
def load_questions(): #TODO store it in Redis later
    global questions, question_count, nutrition_questions
    questions = Question.objects.select_related('category', 'category__area').prefetch_related(
        Prefetch('answer_set', queryset=Answer.objects.all())
    )
    question_count = questions.count()
    nutrition_questions = questions.filter(category__name="Nutrition")  # Questions in the "Nutrition" category


load_questions()


# Main quiz function
def quiz(request):
    current_index = request.session.get('current_question_index', 0)
    user_answers = request.session.get('user_answers', {}) #storing the dictionary with the answers in the session 

    # Display the questions
    if request.method != "POST":
        user = request.user
        progress = round(current_index / question_count * 100) if question_count > 0 else 0

        # Initialize variables to pass to the template
        nutrition_questions_to_present = []  # Render Nutrition questions as a group
        question_to_present = None
        group_text = None  # Pertinent only to Nutrition questions
        category_to_display = None  # Display category name

        if current_index < question_count:
            question = questions[current_index]  # Get the question object
            category = question.category.name

            if question.category.area.name != "Esthetic":
                category_to_display = category
            else:
                category_to_display = question.category.area.name  # Display area name for "Esthetic" questions

            # If the category is "Nutrition," group multiple questions
            if category == "Nutrition":
                group_text = "In the last three days, did you consume any of the following foods:"
                for nutrition_question in nutrition_questions:
                    answers = nutrition_question.answer_set.all()
                    question_to_present = {
                        "id": nutrition_question.id,
                        "title": nutrition_question.content,
                        "answer_choices": [{"answer_text": answer.answer_text, "score": answer.score} for answer in answers]
                    }
                    nutrition_questions_to_present.append(question_to_present)

                # Move index forward by the count of Nutrition questions
                request.session['current_question_index'] = current_index + len(nutrition_questions)

            else:  # For all other categories, display a single question
                answers = question.answer_set.all()
                question_to_present = {
                    "id": question.id,
                    "title": question.content,
                    "answer_choices": [{"answer_text": answer.answer_text, "score": answer.score} for answer in answers]
                }
                # Move index forward by 1 for non-Nutrition questions
                request.session['current_question_index'] = current_index + 1

        else:
            # Reset session index if all questions are answered
            request.session['current_question_index'] = 0
            category_to_display = ""

            # Record quiz completion in the SurveyCompletion model
            completion_time = now()
            new_quiz_submission = SurveyCompletion.objects.create(user=user, completion_time=completion_time)
            new_quiz_submission.save()
            print("the submitted answers to pass are ", user_answers)

            # Process the data to calculate the scores and produce the graphs
            #create the dictionary needed for the processing:
            
            services.process_answers(user, user_answers)
            request.session.pop('user_answers', None)  # Clear answers after processing

        return render(request, "puzzle_app/question.html", {
            "question": question_to_present,
            "nutrition_questions": nutrition_questions_to_present,
            "progress": str(progress),
            "category": category_to_display,
            "group_text": group_text
        })

    # Handle form submission (Next button click) #if the user is POSTing the answers
    else:
        user = request.user
        answers_processed = False #TODO how are we using this variable?

        for key, value in request.POST.items():
            if key.startswith("selected_score_"):
                question_id = key.split("_")[-1]
                question_score = value  # The selected score for the question
                user_answers[question_id] = question_score #this dictionary will then be passed to the process_answers function

                if value:
                    question = next((q for q in questions if q.id == int(question_id)), None)
                    if question is None:
                        raise ValueError(f"Question with id {question_id} not found in the prefetched queryset") #TODO log this error

                    # Save the answer to the database
                    new_score = QuestionResult.objects.create(user=user, question=question, score=question_score)
                    new_score.save()
                    print("the submitted answers to pass are ", user_answers)
                    answers_processed = True
                else:
                    # If no answer was selected
                    messages.warning(request, "Oops, please select an answer!")
                    request.session['current_question_index'] = max(0, current_index - 1)  # Prevent negative index
                    return redirect('quiz')

        request.session['user_answers'] = user_answers  # Save updated answers in the session
        return redirect('quiz')  # Allow the user to continue with the quiz