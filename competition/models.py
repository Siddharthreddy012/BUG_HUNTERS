from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class CompetitionSettings(models.Model):
    title = models.CharField(max_length=200, default="BUG HUNTERS 2026")
    tagline = models.CharField(max_length=255, default="Think Smart. Debug Fast. Code Better.")
    college_name = models.CharField(max_length=255, default="Apex Institute of Technology")
    
    # Round 1 settings
    r1_qualifying_marks = models.IntegerField(default=9, help_text="Default 9 out of 15")
    r1_total_questions = models.IntegerField(default=15)
    r1_time_per_question_seconds = models.IntegerField(default=60, help_text="Time per question in seconds (1 min)")
    r1_enabled = models.BooleanField(default=True)
    
    # Round 2 settings
    r2_qualifying_marks = models.IntegerField(default=15, help_text="Default 15 out of 25")
    r2_total_questions = models.IntegerField(default=5)
    r2_time_per_question_seconds = models.IntegerField(default=300, help_text="Time per question in seconds (5 min)")
    r2_enabled = models.BooleanField(default=True)
    
    # Round 3 settings
    r3_total_questions = models.IntegerField(default=3)
    r3_time_per_question_seconds = models.IntegerField(default=600, help_text="Time per question in seconds (10 min)")
    r3_enabled = models.BooleanField(default=True)
    
    # Platform settings
    allow_registration = models.BooleanField(default=True)
    leaderboard_published = models.BooleanField(default=True)
    anti_cheating_enabled = models.BooleanField(default=True)
    max_warning_violations = models.IntegerField(default=3)
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Competition Setting"
        verbose_name_plural = "Competition Settings"

    def __str__(self):
        return f"{self.title} Settings"

    @classmethod
    def get_settings(cls):
        settings, created = cls.objects.get_or_create(id=1)
        return settings


class Round(models.Model):
    DIFFICULTY_CHOICES = [
        ('MEDIUM', 'Medium'),
        ('HARD', 'Hard'),
        ('VERY_HARD', 'Very Hard'),
    ]

    round_number = models.IntegerField(unique=True)
    name = models.CharField(max_length=100)
    tagline = models.CharField(max_length=150)
    description = models.TextField()
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    total_questions = models.IntegerField()
    marks_per_question = models.FloatField()
    total_marks = models.FloatField()
    time_per_question_minutes = models.IntegerField()
    qualifying_marks = models.FloatField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['round_number']

    def __str__(self):
        return f"Round {self.round_number}: {self.name}"


class Question(models.Model):
    """Round 1: Code Quest MCQs"""
    CATEGORY_CHOICES = [
        ('C', 'C Programming'),
        ('Python', 'Python Programming'),
        ('Java', 'Java Programming'),
        ('Logic', 'Programming Logic & Output Prediction'),
        ('Data Structures', 'Data Structures & Algorithms'),
    ]

    question_text = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Python')
    code_snippet = models.TextField(blank=True, help_text="Optional code snippet for output prediction")
    marks = models.FloatField(default=1.0)
    explanation = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"Q{self.order or self.id}: {self.question_text[:60]}..."


class MCQOption(models.Model):
    question = models.ForeignKey(Question, related_name='options', on_delete=models.CASCADE)
    identifier = models.CharField(max_length=2)  # A, B, C, D
    option_text = models.TextField()
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ['identifier']
        unique_together = ('question', 'identifier')

    def __str__(self):
        return f"[{self.identifier}] {self.option_text[:40]}"


class CodingChallenge(models.Model):
    """Round 2: Bug Bounty (Error Line Coding)"""
    LANGUAGE_CHOICES = [
        ('c', 'C'),
        ('python', 'Python'),
        ('java', 'Java'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES)
    buggy_code = models.TextField(help_text="Code snippet containing intentional errors")
    corrected_reference_code = models.TextField(help_text="Reference corrected code used for comparison/fallback")
    marks = models.FloatField(default=5.0)
    order = models.IntegerField(default=0)
    error_summary = models.TextField(blank=True, help_text="Internal notes on the intentional bugs")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['language', 'order', 'id']

    def __str__(self):
        return f"[{self.get_language_display()}] {self.title}"


class FlowchartQuestion(models.Model):
    """Round 3: Logic Launch (Flowchart to Code)"""
    LANGUAGE_CHOICES = [
        ('c', 'C'),
        ('python', 'Python'),
        ('java', 'Java'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES)
    flowchart_svg = models.TextField(blank=True, help_text="Raw SVG XML or Mermaid definition of the flowchart")
    flowchart_image = models.ImageField(upload_to='flowcharts/', blank=True, null=True)
    input_specification = models.TextField()
    output_specification = models.TextField()
    sample_input = models.TextField(blank=True)
    sample_output = models.TextField(blank=True)
    starter_template = models.TextField(blank=True)
    reference_solution = models.TextField(blank=True)
    marks = models.FloatField(default=10.0)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['language', 'order', 'id']

    def __str__(self):
        return f"[{self.get_language_display()}] {self.title}"


class TestCase(models.Model):
    coding_challenge = models.ForeignKey(CodingChallenge, null=True, blank=True, related_name='test_cases', on_delete=models.CASCADE)
    flowchart_question = models.ForeignKey(FlowchartQuestion, null=True, blank=True, related_name='test_cases', on_delete=models.CASCADE)
    input_data = models.TextField(blank=True, default='')
    expected_output = models.TextField()
    is_hidden = models.BooleanField(default=True)
    explanation = models.CharField(max_length=255, blank=True)

    def __str__(self):
        target = self.coding_challenge or self.flowchart_question
        return f"Test for {target} ({'Hidden' if self.is_hidden else 'Sample'})"


class ParticipantRound(models.Model):
    STATUS_CHOICES = [
        ('LOCKED', 'Locked'),
        ('UNLOCKED', 'Unlocked'),
        ('IN_PROGRESS', 'In Progress'),
        ('SUBMITTED', 'Submitted'),
        ('UNDER_EVALUATION', 'Under Evaluation'),
        ('QUALIFIED', 'Qualified'),
        ('NOT_QUALIFIED', 'Not Qualified'),
        ('VERIFIED', 'Verified'),
    ]

    participant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='competition_rounds')
    round_number = models.IntegerField()
    selected_language = models.CharField(max_length=20, blank=True)  # 'c', 'python', 'java'
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='LOCKED')
    score = models.FloatField(default=0.0)
    total_possible_score = models.FloatField(default=0.0)
    
    # Timing and progress tracking
    start_time = models.DateTimeField(null=True, blank=True)
    completion_time = models.DateTimeField(null=True, blank=True)
    current_question_index = models.IntegerField(default=0)  # 0-indexed question currently being viewed/attempted
    current_question_start_time = models.DateTimeField(null=True, blank=True)  # timestamp when the active question was shown
    
    # Admin verification
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, null=True, blank=True, related_name='verified_participant_rounds', on_delete=models.SET_NULL)
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_remarks = models.TextField(blank=True)

    class Meta:
        unique_together = ('participant', 'round_number')
        ordering = ['participant', 'round_number']

    def __str__(self):
        return f"{self.participant.username} - Round {self.round_number} ({self.status})"

    def is_completed(self):
        return self.status in ['SUBMITTED', 'UNDER_EVALUATION', 'QUALIFIED', 'NOT_QUALIFIED', 'VERIFIED']


class AnswerSubmission(models.Model):
    """Round 1 MCQ Participant Answers"""
    participant_round = models.ForeignKey(ParticipantRound, related_name='mcq_answers', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(MCQOption, null=True, blank=True, on_delete=models.SET_NULL)
    is_correct = models.BooleanField(default=False)
    marks_awarded = models.FloatField(default=0.0)
    submitted_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('participant_round', 'question')

    def __str__(self):
        return f"{self.participant_round.participant.username} - Q{self.question.id}: {self.marks_awarded} marks"


class CodeSubmission(models.Model):
    """Round 2 and Round 3 Code Submissions"""
    participant_round = models.ForeignKey(ParticipantRound, related_name='code_submissions', on_delete=models.CASCADE)
    coding_challenge = models.ForeignKey(CodingChallenge, null=True, blank=True, on_delete=models.CASCADE)
    flowchart_question = models.ForeignKey(FlowchartQuestion, null=True, blank=True, on_delete=models.CASCADE)
    submitted_code = models.TextField()
    language = models.CharField(max_length=20)
    passed_test_cases = models.IntegerField(default=0)
    total_test_cases = models.IntegerField(default=0)
    execution_output = models.TextField(blank=True)
    evaluation_status = models.CharField(max_length=30, default='EVALUATED')
    marks_awarded = models.FloatField(default=0.0)
    submitted_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        target = self.coding_challenge or self.flowchart_question
        return f"{self.participant_round.participant.username} - {target}: {self.marks_awarded} pts"


class TabSwitchViolation(models.Model):
    participant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tab_violations')
    round_number = models.IntegerField(default=1)
    violation_count = models.IntegerField(default=1)
    event_type = models.CharField(max_length=50, default='tab_switch')  # 'tab_switch', 'window_blur', 'page_hidden'
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.participant.username} - Round {self.round_number} (Violation #{self.violation_count})"


class AuditLog(models.Model):
    admin_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=150)
    target_participant = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_records')
    details = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {self.action} by {self.admin_user or 'System'}"
