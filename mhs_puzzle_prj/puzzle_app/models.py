from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='puzzle_app_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='puzzle_app_user_permissions_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

class SurveyCompletion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    survey_date = models.DateTimeField(auto_now_add=True)

#needed to track user engagenent with particular features, such as the share button
class UserInteraction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    event_type = models.CharField(max_length=255)
    content_id = models.CharField(max_length=255)
    notes = models.TextField(blank=True)

class Area(models.Model):
    name = models.CharField(max_length=255)
    max_score = models.IntegerField()
    high_score_good = models.BooleanField(default=True)
    formula = models.CharField(max_length=255)

class Category(models.Model):
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    max_score = models.IntegerField()
    high_score_good = models.BooleanField(default=True)
    formula = models.CharField(max_length=255)

class Question(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    question_required = models.BooleanField(default=True)
    content = models.TextField()

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField()
    score = models.IntegerField()

class QuestionResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField()

class CategoryResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField()

class AreaResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField()

class Focus(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    lifestyle_focus = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='lifestyle_focus_set')
    skincare_focus = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='skincare_focus_set')
    esthetic_focus = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='esthetic_focus_set')

class Recommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    lifestyle_recommendation = models.TextField()
    skincare_recommendation = models.TextField()
    esthetic_recommendation = models.TextField()

class Prompt(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    version = models.IntegerField()
    content = models.TextField()
