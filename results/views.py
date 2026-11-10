import csv
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseForbidden
from django.utils import timezone
from .models import RoundResult
from competition.models import CompetitionSettings, ParticipantRound
from competition.services import recalculate_leaderboard

def is_admin_user(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required
def my_results_view(request):
    """Displays individual participant's detailed performance breakdown."""
    user = request.user
    result, _ = RoundResult.objects.get_or_create(participant=user)
    
    r1 = ParticipantRound.objects.filter(participant=user, round_number=1).first()
    r2 = ParticipantRound.objects.filter(participant=user, round_number=2).first()
    r3 = ParticipantRound.objects.filter(participant=user, round_number=3).first()

    context = {
        'result': result,
        'r1': r1,
        'r2': r2,
        'r3': r3,
    }
    return render(request, 'results.html', context)


def leaderboard_view(request):
    """
    Renders public leaderboard ordered by:
    1. Total score (descending)
    2. Round 3 score (descending)
    3. Final submission time (earlier is better)
    """
    settings = CompetitionSettings.get_settings()
    is_admin = request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)

    # Re-calculate ranks
    recalculate_leaderboard()

    dept_filter = request.GET.get('department', '')
    query = request.GET.get('q', '').strip()

    leaderboard_qs = RoundResult.objects.filter(is_published=True).select_related('participant', 'participant__profile')
    
    if dept_filter:
        leaderboard_qs = leaderboard_qs.filter(participant__profile__department=dept_filter)
    if query:
        leaderboard_qs = leaderboard_qs.filter(
            participant__profile__full_name__icontains=query
        ) | leaderboard_qs.filter(
            participant__profile__roll_number__icontains=query
        )

    leaderboard = list(leaderboard_qs)
    top_3 = leaderboard[:3]
    remaining = leaderboard[3:]

    context = {
        'is_published': settings.leaderboard_published or is_admin,
        'leaderboard': leaderboard,
        'top_3': top_3,
        'remaining': remaining,
        'dept_filter': dept_filter,
        'query': query,
    }
    return render(request, 'leaderboard.html', context)


@user_passes_test(is_admin_user, login_url='login')
def export_results_csv(request):
    """Exports all participant scores and standings as CSV file."""
    recalculate_leaderboard()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="BUG_HUNTERS_RESULTS_{timezone.now().strftime("%Y%m%d_%H%M")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Rank', 'Roll Number', 'Full Name', 'Department', 'Year',
        'Email', 'Round 1 Score', 'Round 2 Score', 'Round 3 Score',
        'Total Score', 'Tab Violations', 'Final Qualification', 'Completion Time'
    ])

    results = RoundResult.objects.all().select_related('participant', 'participant__profile')
    for res in results:
        profile = getattr(res.participant, 'profile', None)
        writer.writerow([
            res.final_rank or 'N/A',
            profile.roll_number if profile else res.participant.username,
            profile.full_name if profile else res.participant.get_full_name(),
            profile.department if profile else 'N/A',
            profile.year if profile else 'N/A',
            res.participant.email,
            res.r1_score,
            res.r2_score,
            res.r3_score,
            res.total_score,
            res.tab_violations_total,
            'Qualified' if res.is_final_qualified else 'Not Qualified',
            res.completion_time.strftime('%Y-%m-%d %H:%M:%S') if res.completion_time else 'N/A'
        ])

    return response


@user_passes_test(is_admin_user, login_url='login')
def export_results_excel(request):
    """Exports formatted table compatible with MS Excel (.xls)."""
    recalculate_leaderboard()
    results = RoundResult.objects.all().select_related('participant', 'participant__profile')
    
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = f'attachment; filename="BUG_HUNTERS_REPORT_{timezone.now().strftime("%Y%m%d_%H%M")}.xls"'
    
    html = """
    <html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
    <head><meta charset="utf-8"></head>
    <body>
    <table border="1">
        <tr style="background-color: #0d1b2a; color: #ffffff;">
            <th>Rank</th>
            <th>Roll Number</th>
            <th>Participant Name</th>
            <th>Department</th>
            <th>Year</th>
            <th>Email</th>
            <th>Round 1 (Code Quest /15)</th>
            <th>Round 2 (Bug Bounty /25)</th>
            <th>Round 3 (Logic Launch /30)</th>
            <th>Total Score (/70)</th>
            <th>Tab Violations</th>
            <th>Final Qualification</th>
        </tr>
    """
    for res in results:
        profile = getattr(res.participant, 'profile', None)
        html += f"""
        <tr>
            <td>{res.final_rank or ''}</td>
            <td>{profile.roll_number if profile else ''}</td>
            <td>{profile.full_name if profile else res.participant.username}</td>
            <td>{profile.department if profile else ''}</td>
            <td>{profile.year if profile else ''}</td>
            <td>{res.participant.email}</td>
            <td>{res.r1_score}</td>
            <td>{res.r2_score}</td>
            <td>{res.r3_score}</td>
            <td><b>{res.total_score}</b></td>
            <td>{res.tab_violations_total}</td>
            <td>{'QUALIFIED' if res.is_final_qualified else 'NOT QUALIFIED'}</td>
        </tr>
        """
    html += "</table></body></html>"
    response.write(html)
    return response
