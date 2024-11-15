from django.shortcuts import render
from django.utils.timezone import now
from django.contrib import messages
from django.contrib.auth.models import User

from .models import Question, Answer, Category, Area, QuestionResult, SurveyCompletion

from . import services


from django.shortcuts import render, redirect

#TODO add the "go back" logic
#@login_required
def quiz(request):
    current_index = request.session.get('current_question_index', 0)
    if request.method != "POST":
        user = request.user 
        #display the questions
        # Get the current question index from the session or start with the first question
        
        questions = Question.objects.all()  # Queryset of all questions
        question_count = questions.count()
        progress = round(current_index / question_count * 100) if question_count > 0 else 0

        # Initialize variables to pass to the template
        nutrition_questions_to_present = [] #render only the nutrition questions as a group: render all other questions individually
        question_to_present = None
        group_text = None # pertinent only to nutrition questions
        category = None # needed to display the category name on the quiz page 
        category_to_display = None # needed because we are not displaying category name for esthetic questions

        if current_index < question_count:
            question = questions[current_index]  # Get the question object
            category = question.category.name 
            if question.category.area.name != "Esthetic":
                category_to_display = category  # Get the category name
            else:
                category_to_display = question.category.area.name # don't display the category name for esthetic questions

            # If category is "Nutrition", group multiple questions
            if category == "Nutrition":
                nutrition_questions = Question.objects.filter(category__name="Nutrition")  # Filter Nutrition questions
                group_text = "In the last three days, did you consume any of the following foods:"
                for nutrition_question in nutrition_questions:
                    answers = Answer.objects.filter(question=nutrition_question)
                    question_to_present = {
                        "id": nutrition_question.id,
                        "title": nutrition_question.content,
                        "answer_choices": [{"answer_text": answer.answer_text, "score": answer.score} for answer in answers]
                    }
                    nutrition_questions_to_present.append(question_to_present)
            
                # Move index forward by the count of nutrition questions
                request.session['current_question_index'] = current_index + nutrition_questions.count()
        
            else:  # For all other categories, display a single question
                answers = Answer.objects.filter(question=question)
                question_to_present = {
                    "id": question.id,
                    "title": question.content,
                    "answer_choices": [{"answer_text": answer.answer_text, "score": answer.score} for answer in answers]
             }
                # Move index forward by 1 for non-nutrition questions
                request.session['current_question_index'] = current_index + 1

        else:
            # Reset the session index if all questions have been answered
            request.session['current_question_index'] = 0
            category_to_display = ""
            #record the fact of the questionnaire completion in the SurveyCompeltion model
            completion_time = now()
            new_quiz_submission = SurveyCompletion.objects.create(user=user, completion_time=completion_time)
            new_quiz_submission.save()
            #calculate the cateogry scores for the user
            services.calculate_category_scores(user, completion_time)

        return render(request, "puzzle_app/question.html", {
            "question": question_to_present,
            "nutrition_questions": nutrition_questions_to_present,
            "progress": str(progress),
            "category": category_to_display,
            "group_text": group_text
        })

    else: #if the user is sending in their responses (the user has clicked on the "next button"):
        #identify the question
        print("form submitted")
        # Loop through POST data to find question scores
        for key, value in request.POST.items():
            if key.startswith("selected_score_"):
                # Extract question_id from the key name
                question_id = key.split("_")[-1]
                question_score = value  # This is the selected score for this question

                if value:
                    #identify the relevant question object
                    question = Question.objects.get(id=question_id)
                    #TODO indentify the user correctly
                    #save the answer to the db
                    temp_user = User.objects.get(username="test_user") #temporarily saving the scores under Angelina's account
                    new_score = QuestionResult.objects.create(user=temp_user, question=question, score=question_score)
                    new_score.save()
                    print("the new score recorded is ", new_score)
                    answers_processed = True
                else: #if no answer was selected
                    messages.warning(request, "Ooops, please select an answer!")
                    request.session['current_question_index'] = current_index - 1
                    return redirect('quiz')
                
        if answers_processed:
            return redirect('quiz') #allow the user to continue with the quiz




