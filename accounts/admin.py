from django.contrib import admin
from .models import ParticipantProfile

@admin.register(ParticipantProfile)
class ParticipantProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'roll_number', 'department', 'year', 'is_disqualified', 'created_at')
    search_fields = ('full_name', 'roll_number', 'user__username', 'user__email')
    list_filter = ('department', 'year', 'is_disqualified')
