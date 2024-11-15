# handle Category score calculation and graph creation 

from .models import Category, Area, QuestionResult, CategoryResult, SurveyCompletion 
from django.contrib.auth.models import User


def calculate_category_scores(user):
    
    # pull out the set of categories and the set of areas to prepare the results for
    # for each category, obtain the score calculation formula
    # plug stuff into the formula
    #evaluate nutrition questions separately


    # pull out the questions submitted
    print("the user is ", user.username)
    
    answers = QuestionResult.objects.filter(user=user)
    print("the user's answers are ", answers)
    # pull out the set of categories and the set of areas to prepare the results for:
    categories = Category.objects.all() #returns category objects
    print("the categories are ", categories)

    if answers: # if the user submitted answers
    # for each category, obtain the score calculation formula
        for category in categories:
            if category.name != "Nutrition": #Nutrition is scored differently
                formula = category.formula #string
                values = {} #set up a dictionary (to pass into the eval function later) that holds questions' alphabetic id's as keys and the relative answer scores as values
                questions = answers.filter(question__category=category) #the user's answers to that category of questions
                for question in questions:
                    question_alphabetic_id = question.question.alphabetic_id
                    score = question.score
                    values[question_alphabetic_id] = score

                print(f"Values for category '{category.name}':", values)

                try: 
                    category_score = eval(formula, {}, values)
                    print(f"the score for the {category.name} category is ", category_score)
                    category_result = CategoryResult.objects.create(user=user, category=category, score=category_score)
                    category_result.save()
                
                except Exception as e:
                    print(f"Error evaluating formula for category '{category.name}':", e)

            else: #scoring the Nutrition category
                pass
    else:
        print("oops there are no answers to evaluate!")
        #log the exception to the logbook
        '''
            ncdp = whole_grains + legumes + nuts_seeds + vitamin_a_rich_orange_veg + dark_green_leafy_vegetables + other_vegetables + vitamin_a_rich_fruits + citrus + other_fruit

            ncdr = soda + max(baked1, baked2, baked3) + other_sweets + processed_meat + max(unprocessed_red_meat_ruminant, unprocessed_red_meat_non_ruminant) + deep_fried_foods + max(instant_noodles,fast_food) + salty_snacks

            gdr_raw = (ncdp - ncdr + 9)
            gdr = (gdr_raw/18)*100 #the gdr score expressed as a percentage

            category_score = eval(formula, [{}], values)
            print("the score for the {category_name} category is ", category_score)
            category_result = CategoryResult.objects.create(user=user, category=category, score=category_score)
'''

#def build_wheel_of_life_graph: