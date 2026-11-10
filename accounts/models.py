from django.db import models
from django.contrib.auth.models import User

class ParticipantProfile(models.Model):
    YEAR_CHOICES = [
        ('1st Year', '1st Year'),
        ('2nd Year', '2nd Year'),
        ('3rd Year', '3rd Year'),
        ('4th Year', '4th Year'),
    ]

    DEPARTMENT_CHOICES = [
        ('Computer Science & Engineering', 'Computer Science & Engineering (CSE)'),
        ('Information Technology', 'Information Technology (IT)'),
        ('Artificial Intelligence & Data Science', 'Artificial Intelligence & Data Science (AI & DS)'),
        ('Electronics & Communication', 'Electronics & Communication (ECE)'),
        ('Electrical & Electronics', 'Electrical & Electronics (EEE)'),
        ('Mechanical Engineering', 'Mechanical Engineering (ME)'),
        ('Civil Engineering', 'Civil Engineering (CE)'),
        ('Other', 'Other Department'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=150)
    roll_number = models.CharField(max_length=50, unique=True, db_index=True)
    department = models.CharField(max_length=100, choices=DEPARTMENT_CHOICES, default='Computer Science & Engineering')
    year = models.CharField(max_length=20, choices=YEAR_CHOICES, default='3rd Year')
    phone = models.CharField(max_length=20, blank=True)
    college = models.CharField(max_length=150, default='National Institute of Engineering')
    is_disqualified = models.BooleanField(default=False)
    disqualification_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['roll_number']

    def __str__(self):
        return f"{self.full_name} ({self.roll_number})"

    @property
    def email(self):
        return self.user.email
