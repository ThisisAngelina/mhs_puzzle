from django.shortcuts import render
from .models import Question, Answer, Category, Area


from django.shortcuts import render, redirect

def question_view(request):
    # Get the current question index from the session or start with the first question
    current_index = request.session.get('current_question_index', 0)
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
                    "title": nutrition_question.content,
                    "answer_choices": [{"answer_text": answer.answer_text, "score": answer.score} for answer in answers]
                }
                nutrition_questions_to_present.append(question_to_present)
            
            # Move index forward by the count of nutrition questions
            request.session['current_question_index'] = current_index + nutrition_questions.count()
        
        else:  # For all other categories, display a single question
            answers = Answer.objects.filter(question=question)
            question_to_present = {
                "title": question.content,
                "answer_choices": [{"answer_text": answer.answer_text, "score": answer.score} for answer in answers]
            }
            # Move index forward by 1 for non-nutrition questions
            request.session['current_question_index'] = current_index + 1

    else:
        # Reset the session index if all questions have been answered
        request.session['current_question_index'] = 0

    return render(request, "puzzle_app/question.html", {
        "question": question_to_present,
        "nutrition_questions": nutrition_questions_to_present,
        "progress": str(progress),
        "category": category_to_display,
        "group_text": group_text
    })

#TODO allow the user to select only one button! Enforce the choice of at least one asnwer.
def calculate_score(request):
    pass