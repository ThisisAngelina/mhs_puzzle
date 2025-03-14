from django.db import models
from django.contrib.auth.models import User

class SurveyCompletion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    completion_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Survey Completion for {self.user} on {self.completion_time.strftime('%Y-%m-%d')}"

#needed to track user engagenent with particular features, such as the share button
class UserInteraction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    event_type = models.CharField(max_length=255)
    content_id = models.CharField(max_length=255)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.event_type} by {self.user} on {self.timestamp.strftime('%Y-%m-%d')}"


#we have three areas: lifestyle, skincare, esthetic
class Area(models.Model):
    name = models.CharField(max_length=255, unique = True)
    max_score = models.FloatField()
    high_score_good = models.BooleanField(default=True)
    formula = models.CharField(max_length=1000)

    def __str__(self):
        return self.name


class Category(models.Model):
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, unique = True)
    max_score = models.FloatField()
    high_score_good = models.BooleanField(default=True)
    formula = models.CharField(max_length=1000)

    class Meta:
        verbose_name_plural = "Categories"  

    def __str__(self):
        return f"{self.name} in {self.area.name}"
    

class Question(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    alphabetic_id = models.TextField(blank=True, null=True)
    question_required = models.BooleanField(default=True)
    content = models.TextField(unique = True)

    def __str__(self):
        return f"{self.alphabetic_id}: {self.content}"

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField()
    score = models.FloatField()

    class Meta:
        unique_together = ('question', 'answer_text')

    def __str__(self):
        return f"Answer to '{self.question.alphabetic_id}': {self.answer_text} {self.score}"

class QuestionResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    completion_time = models.DateTimeField(auto_now_add=True)
    score = models.FloatField()

    def __str__(self):
        return f"Result for {self.user} on '{self.question}' with score {self.score}"

class CategoryResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    completion_time = models.DateTimeField(auto_now_add=True)
    score = models.FloatField()

    def __str__(self):
        return f"Result for {self.user} in category '{self.category}' with score {self.score}"
