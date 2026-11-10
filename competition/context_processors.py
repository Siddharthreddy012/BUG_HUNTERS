from .models import CompetitionSettings, ParticipantRound

def competition_context(request):
    settings = CompetitionSettings.get_settings()
    user_rounds = {}
    if request.user.is_authenticated:
        rounds = ParticipantRound.objects.filter(participant=request.user)
        for r in rounds:
            user_rounds[r.round_number] = r
            
    return {
        'comp_settings': settings,
        'user_rounds': user_rounds,
        'app_name': 'BUG HUNTERS',
    }

