from django.contrib import admin
from .models import RoundResult

@admin.register(RoundResult)
class RoundResultAdmin(admin.ModelAdmin):
    list_display = ('final_rank', 'participant', 'r1_score', 'r2_score', 'r3_score', 'total_score', 'is_final_qualified', 'tab_violations_total')
    search_fields = ('participant__username', 'participant__profile__roll_number')
    list_filter = ('is_final_qualified', 'r1_qualified', 'r2_verified', 'r3_verified')
    ordering = ('final_rank', '-total_score')
