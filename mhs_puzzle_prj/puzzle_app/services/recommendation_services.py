import openai 

#TODO to move to environ variables before deploying/publishing on GitHub
openai.api_key = "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"

def _generate_recommendation(user_data):
  '''Pass the user data (priority category, category scores, exact answers to each question of the priority cateogry) to Chat GPT to generate recomnendations'''
  ''' The user_data is a dictionary that looks like:
  {"priority_category" : priority_category,
  "category_scores": {"sleep": 100.0, "stress": 60.0, etc.},
  "answers_of_priority_category": {"question1 content": "user's answer to question1 content","question2 content": "user's answer to question2 content", etc.}
  }'''

  priority_category = user_data["priority_category"]
  answers_of_priority_category = user_data["answers_of_priority_category"]
  category_scores = user_data["category_scores"]

  prompt = (

  f"Act as a medical doctor (a dermatologist) and a health coach to suggest simple, easy-to-implement, sustainable lifestyle changes"
  f"to a person that wants to improve their health and the look for their skin and who knows that health impacts the skin."
  f"This person struggles the most with {priority_category} "
  f"and the scores for the other areas of their life are the following (with 0 being the minimum and 100 being the maximum):  {category_scores} "
  f"in particular, they gave the following answers to the {priority_category} category: {answers_of_priority_category}."
  f"Use this information to give specific recommendations."
  f"Address this patient to tell them how they can work omn their lifestyle step-by-step." 
  f"Limit your recommendations to a few sentences. Omit greeting words, such as 'hello'." 
  )
  response = openai.chat.completions.create(
        model = "o1-mini",
        messages = [{"role": "user", "content": prompt}]
    )

  return response.choices[0].message.content.strip()
