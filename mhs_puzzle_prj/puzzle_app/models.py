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

    def __str__(self):
        return self.username

class SurveyCompletion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    survey_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Survey Completion for {self.user} on {self.survey_date.strftime('%Y-%m-%d')}"

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
    formula = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Category(models.Model):
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, unique = True)
    max_score = models.FloatField()
    high_score_good = models.BooleanField(default=True)
    formula = models.CharField(max_length=255)

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
        return self.content

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField()
    score = models.FloatField()

    class Meta:
        unique_together = ('question', 'answer_text')

    def __str__(self):
        return f"Answer to '{self.question}': {self.answer_text} {self.score}"

class QuestionResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    score = models.FloatField()

    def __str__(self):
        return f"Result for {self.user} on '{self.question}' with score {self.score}"

class CategoryResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    score = models.FloatField()

    def __str__(self):
        return f"Result for {self.user} in category '{self.category}' with score {self.score}"

class AreaResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    score = models.FloatField()

    def __str__(self):
        return f"Result for {self.user} in area '{self.area}' with score {self.score}"


class Focus(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    lifestyle_focus = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='lifestyle_focus_set')
    skincare_focus = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='skincare_focus_set')
    esthetic_focus = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='esthetic_focus_set')
    
    class Meta:
        verbose_name_plural = "Focus"  

    def __str__(self):
        return f"Focus for {self.user} on {self.date.strftime('%Y-%m-%d')}"
    
class Recommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    lifestyle_recommendation = models.TextField()
    skincare_recommendation = models.TextField()
    esthetic_recommendation = models.TextField()

    def __str__(self):
        return f"Recommendation for {self.user} on {self.date.strftime('%Y-%m-%d')}"


class Prompt(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    content = models.TextField()

    def __str__(self):
        return f"Prompt for category '{self.category}' (v{self.version})"