from django.db import models
from django.contrib.auth.models import User

class RoundResult(models.Model):
    participant = models.OneToOneField(User, on_delete=models.CASCADE, related_name='competition_result')
    r1_score = models.FloatField(default=0.0)
    r1_qualified = models.BooleanField(default=False)
    
    r2_score = models.FloatField(default=0.0)
    r2_verified = models.BooleanField(default=False)
    
    r3_score = models.FloatField(default=0.0)
    r3_verified = models.BooleanField(default=False)
    
    total_score = models.FloatField(default=0.0)
    tab_violations_total = models.IntegerField(default=0)
    is_final_qualified = models.BooleanField(default=False)
    
    final_rank = models.IntegerField(null=True, blank=True)
    completion_time = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-total_score', '-r3_score', 'completion_time']

    def __str__(self):
        return f"{self.participant.username} - Total: {self.total_score} (Rank: {self.final_rank or 'N/A'})"

    def recalculate_total(self):
        self.total_score = round(self.r1_score + self.r2_score + self.r3_score, 2)
        return self.total_score
