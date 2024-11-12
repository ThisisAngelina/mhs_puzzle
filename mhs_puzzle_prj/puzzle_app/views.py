from django.shortcuts import render
from .models import Question, Answer, Category


#Display nutrition questions as a group
def question_view(request):
    # Get the current question index from the session or start with the first question
    current_index = request.session.get('current_question_index', 0)
    questions = Question.objects.all() #queryset of all the questions
    question_count = questions.count()
    progress = round(current_index/question_count*100) #calculation to update the progress bar
    print("the progress is", progress)
    print("the question count is", question_count)

    if current_index < question_count:
        question = questions[current_index] #question object
        category = Category.objects.filter(question=question).first().name
        answers = Answer.objects.filter(question=question)
        
        question_to_present = {
            "title": question.content,
            "answer_choices": [{"answer_text": answer.answer_text, "score": answer.score} for answer in answers]
        } #the object that will be passed to the template

        
        # Save the next question index in the session
        request.session['current_question_index'] = current_index + 1
        print("the current index is", current_index)

    else:
        # Reset the session index if all questions have been answered
        request.session['current_question_index'] = 0
        question_to_present = None

    return render(request, "puzzle_app/question.html", {"question": question_to_present, "progress": str(progress), "category": category})

#TODO allow the user to select only one button!
def calculate_score(request):
    pass