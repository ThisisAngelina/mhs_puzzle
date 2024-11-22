# handle Category score calculation and graph creation 
from django.db.models import Prefetch

from .models import Question, Category, CategoryResult, Answer
from django.contrib.auth.models import User

#prep

# Prefetch the querysets globally
def load_questions(): #TODO store it in Redis later
    global questions, question_count, nutrition_questions, categories
    questions = Question.objects.select_related('category', 'category__area').prefetch_related(
        Prefetch('answer_set', queryset=Answer.objects.all())
    )
    categories = Category.objects.all()
    question_count = questions.count()
    nutrition_questions = questions.filter(category__name="Nutrition")  # Questions in the "Nutrition" category


load_questions()
   #prefetch quiz question categories

#executing the functions 
#user is the user object, user_answers is the dictionary {queston id: question score}
def process_answers(user, user_answers):
    calculate_category_scores(user, user_answers)
    #make_graphs(user, user_answers)

# Pass `user_answers` as a dictionary {question_id: score}
def calculate_category_scores(user, user_answers):
    # Iterate over categories to calculate scores
    for category in categories:
        if category.name != "Nutrition":  # Process non-Nutrition categories
            formula = category.formula  # The formula is a string
            values = {}  # Dictionary to hold question alphabetic IDs and their scores
            
            # Collect relevant questions and their scores
            questions_in_category = [q for q in questions if q.category == category]
            for question in questions_in_category:
                question_id_str = str(question.id)
                if question_id_str in user_answers:
                    question_alphabetic_id = question.alphabetic_id
                    score = float(user_answers[question_id_str])  # Convert score to float
                    values[question_alphabetic_id] = score
            
            print(f"Values for category '{category.name}':", values)

            try:
                # Evaluate the formula
                category_score = eval(formula, {}, values)
                print(f"Score for the {category.name} category:", category_score)
                
                # Save the category score to the database
                category_result = CategoryResult.objects.create(user=user, category=category, score=category_score)
                category_result.save()
            
            except Exception as e:
                print(f"Error evaluating formula for category '{category.name}':", e)
                # Log this error in a logging system 

        else:  # Process Nutrition category separately
            formula = "(((whole_grains + legumes + nuts_seeds + vitamin_a_rich_orange_veg + dark_green_leafy_vegetables + other_vegetables + vitamin_a_rich_fruits + citrus + other_fruit) - (soda + max(baked1, baked2, baked3) + other_sweets + processed_meat + max(unprocessed_red_meat_ruminant, unprocessed_red_meat_non_ruminant) + deep_fried_foods + max(instant_noodles,fast_food) + salty_snacks) + 9)/18)*100"
            values = {}

            nutrition_questions = [q for q in questions if q.category == category] #questions is the queryset of all the quesstions, obitained with the load_questions function

            for question in nutrition_questions:
                question_id_str = str(question.id)
                if question_id_str in user_answers:
                    question_alphabetic_id = question.alphabetic_id
                    score = float(user_answers[question_id_str])  # Convert score to float
                    values[question_alphabetic_id] = score

            print(f"Values for Nutrition category:", values)

            try:
                # Evaluate the Nutrition formula
                category_score = eval(formula, {}, values)
                print(f"Score for the Nutrition category:", category_score)
                
                # Save the category score to the database
                category_result = CategoryResult.objects.create(user=user, category=category, score=category_score)
                category_result.save()
            
            except Exception as e:
                print(f"Error evaluating formula for Nutrition category:", e)
                # Log this error in a logging system 
    else:
        print("oops there are no answers to evaluate!")
        #log the exception to the logbook


def make_graphs(user, user_answers): #TODO
    print("the make_graphs() function was called")
