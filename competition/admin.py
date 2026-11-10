from django.contrib import admin
from .models import (
    CompetitionSettings, Round, Question, MCQOption,
    CodingChallenge, FlowchartQuestion, TestCase,
    ParticipantRound, AnswerSubmission, CodeSubmission,
    TabSwitchViolation, AuditLog
)

class MCQOptionInline(admin.TabularInline):
    model = MCQOption
    extra = 4

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('order', 'question_text', 'category', 'marks')
    list_filter = ('category',)
    inlines = [MCQOptionInline]

class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 2

@admin.register(CodingChallenge)
class CodingChallengeAdmin(admin.ModelAdmin):
    list_display = ('title', 'language', 'marks', 'order')
    list_filter = ('language',)
    inlines = [TestCaseInline]

@admin.register(FlowchartQuestion)
class FlowchartQuestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'language', 'marks', 'order')
    list_filter = ('language',)
    inlines = [TestCaseInline]

@admin.register(ParticipantRound)
class ParticipantRoundAdmin(admin.ModelAdmin):
    list_display = ('participant', 'round_number', 'selected_language', 'status', 'score', 'is_verified')
    list_filter = ('round_number', 'status', 'is_verified')
    search_fields = ('participant__username', 'participant__profile__roll_number')

@admin.register(AnswerSubmission)
class AnswerSubmissionAdmin(admin.ModelAdmin):
    list_display = ('participant_round', 'question', 'is_correct', 'marks_awarded')

@admin.register(CodeSubmission)
class CodeSubmissionAdmin(admin.ModelAdmin):
    list_display = ('participant_round', 'language', 'passed_test_cases', 'marks_awarded', 'submitted_at')

@admin.register(TabSwitchViolation)
class TabSwitchViolationAdmin(admin.ModelAdmin):
    list_display = ('participant', 'round_number', 'violation_count', 'event_type', 'timestamp')
    list_filter = ('round_number', 'event_type')
    search_fields = ('participant__username',)

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'admin_user', 'action', 'target_participant')
    search_fields = ('action', 'details', 'target_participant__username')

admin.site.register(CompetitionSettings)
admin.site.register(Round)
