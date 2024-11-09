from django.shortcuts import render
from .models import Question, Answer

def question_view(request):
    # Get the current question index from the session or start with the first question
    current_index = request.session.get('current_question_index', 0)
    questions = Question.objects.all()
    question_count = questions.count()
    progress = round(((question_count - current_index)/question_count)*100) #calculation to update the progress bar

    if current_index < question_count:
        question = questions[current_index]
        answers = Answer.objects.filter(question=question)
        
        question_to_present = {
            "title": question.content,
            "answer_choices": [{"answer_text": answer.answer_text, "score": answer.score} for answer in answers]
        }
        
        # Save the next question index in the session
        request.session['current_question_index'] = current_index + 1
    else:
        # Reset the session index if all questions have been answered
        request.session['current_question_index'] = 0
        question_to_present = None

    return render(request, "puzzle_app/question.html", {"question": question_to_present, "progress": progress})