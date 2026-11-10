from django.utils import timezone
from django.db.models import Sum
from .models import (
    CompetitionSettings, ParticipantRound, Round, Question,
    CodingChallenge, FlowchartQuestion, AnswerSubmission,
    CodeSubmission, TabSwitchViolation, AuditLog
)
from results.models import RoundResult

def initialize_participant_competition(user):
    """
    Guarantees all 3 rounds and result tracking are initialized for the participant.
    Round 1 begins UNLOCKED. Round 2 and Round 3 begin LOCKED.
    """
    settings = CompetitionSettings.get_settings()

    # Round 1
    r1, _ = ParticipantRound.objects.get_or_create(
        participant=user,
        round_number=1,
        defaults={
            'status': 'UNLOCKED' if settings.r1_enabled else 'LOCKED',
            'total_possible_score': 15.0,
        }
    )

    # Round 2
    r2, _ = ParticipantRound.objects.get_or_create(
        participant=user,
        round_number=2,
        defaults={
            'status': 'LOCKED',
            'total_possible_score': 25.0,
        }
    )

    # Round 3
    r3, _ = ParticipantRound.objects.get_or_create(
        participant=user,
        round_number=3,
        defaults={
            'status': 'LOCKED',
            'total_possible_score': 30.0,
        }
    )

    # RoundResult in results app
    res, _ = RoundResult.objects.get_or_create(participant=user)
    return r1, r2, r3, res

def check_round_accessibility(user, round_number: int):
    """
    Enforces strict sequential unlocking on the Django backend.
    Returns (is_accessible: bool, message: str, participant_round: ParticipantRound)
    """
    settings = CompetitionSettings.get_settings()
    initialize_participant_competition(user)

    try:
        p_round = ParticipantRound.objects.get(participant=user, round_number=round_number)
    except ParticipantRound.DoesNotExist:
        return False, "Invalid round identifier.", None

    # Check if participant is disqualified
    if hasattr(user, 'profile') and user.profile.is_disqualified:
        return False, f"Account disqualified: {user.profile.disqualification_reason or 'Policy violation.'}", p_round

    if round_number == 1:
        if not settings.r1_enabled:
            return False, "Round 1 (Code Quest) is currently disabled by the administrator.", p_round
        if p_round.is_completed():
            return False, f"Round 1 has already been submitted. Score: {p_round.score}/15.", p_round
        return True, "Round 1 is open.", p_round

    elif round_number == 2:
        if not settings.r2_enabled:
            return False, "Round 2 (Bug Bounty) is currently disabled by the administrator.", p_round

        # Check Round 1 completion and qualification
        try:
            r1 = ParticipantRound.objects.get(participant=user, round_number=1)
        except ParticipantRound.DoesNotExist:
            return False, "You must attempt Round 1 first.", p_round

        if r1.status != 'QUALIFIED':
            req = settings.r1_qualifying_marks
            return False, f"Round 2 is LOCKED. You need at least {req}/15 in Round 1 (Code Quest) to qualify. (Your score: {r1.score}/15)", p_round

        if p_round.is_completed():
            return False, f"Round 2 has already been submitted and is {p_round.get_status_display().lower()}.", p_round

        return True, "Round 2 is unlocked.", p_round

    elif round_number == 3:
        if not settings.r3_enabled:
            return False, "Round 3 (Logic Launch) is currently disabled by the administrator.", p_round

        # Check Round 2 verification status
        try:
            r2 = ParticipantRound.objects.get(participant=user, round_number=2)
        except ParticipantRound.DoesNotExist:
            return False, "You must complete previous rounds first.", p_round

        if not (r2.is_verified and r2.status == 'VERIFIED'):
            return False, "Round 3 is LOCKED. Round 2 (Bug Bounty) must be evaluated and verified by the competition administrator before accessing Round 3.", p_round

        if p_round.is_completed():
            return False, f"Round 3 has already been submitted and is {p_round.get_status_display().lower()}.", p_round

        return True, "Round 3 is unlocked.", p_round

    return False, "Unknown round.", None

def evaluate_and_finalize_round_1(participant_round: ParticipantRound):
    """
    Calculates the final score for Round 1, checks qualification,
    unlocks Round 2 if qualified, and updates results.
    """
    settings = CompetitionSettings.get_settings()
    answers = AnswerSubmission.objects.filter(participant_round=participant_round)
    total_score = sum(a.marks_awarded for a in answers)
    participant_round.score = round(total_score, 2)
    participant_round.completion_time = timezone.now()

    is_qualified = (total_score >= settings.r1_qualifying_marks)
    participant_round.status = 'QUALIFIED' if is_qualified else 'NOT_QUALIFIED'
    participant_round.save()

    # Update RoundResult
    result, _ = RoundResult.objects.get_or_create(participant=participant_round.participant)
    result.r1_score = participant_round.score
    result.r1_qualified = is_qualified
    result.recalculate_total()
    result.save()

    # If qualified, unlock Round 2
    if is_qualified:
        r2, _ = ParticipantRound.objects.get_or_create(
            participant=participant_round.participant,
            round_number=2,
            defaults={'total_possible_score': 25.0}
        )
        if r2.status == 'LOCKED':
            r2.status = 'UNLOCKED'
            r2.save()

    return is_qualified, total_score

def log_tab_violation(user, round_number: int, event_type: str = "tab_switch", details: str = ""):
    """
    Logs browser focus loss or tab change to the database.
    Increments participant violation records.
    """
    existing_count = TabSwitchViolation.objects.filter(participant=user, round_number=round_number).count()
    new_count = existing_count + 1

    violation = TabSwitchViolation.objects.create(
        participant=user,
        round_number=round_number,
        violation_count=new_count,
        event_type=event_type,
        details=details or f"Participant switched tab/lost window focus during Round {round_number}"
    )

    # Sync total in RoundResult
    total_all_rounds = TabSwitchViolation.objects.filter(participant=user).count()
    result, _ = RoundResult.objects.get_or_create(participant=user)
    result.tab_violations_total = total_all_rounds
    result.save()

    return new_count

def admin_verify_round_2(participant_round: ParticipantRound, admin_user, new_score=None, remarks=""):
    """
    Administrative action to verify Round 2 code submissions and unlock Round 3.
    """
    settings = CompetitionSettings.get_settings()
    if new_score is not None:
        participant_round.score = float(new_score)

    qualifying_marks = settings.r2_qualifying_marks
    is_qualified = (participant_round.score >= qualifying_marks)

    participant_round.is_verified = True
    participant_round.verified_by = admin_user
    participant_round.verified_at = timezone.now()
    participant_round.verification_remarks = remarks
    participant_round.status = 'VERIFIED' if is_qualified else 'NOT_QUALIFIED'
    participant_round.save()

    # Sync with results
    result, _ = RoundResult.objects.get_or_create(participant=participant_round.participant)
    result.r2_score = participant_round.score
    result.r2_verified = is_qualified
    result.recalculate_total()
    result.save()

    # Unlock Round 3 if verified and qualified
    if is_qualified:
        r3, _ = ParticipantRound.objects.get_or_create(
            participant=participant_round.participant,
            round_number=3,
            defaults={'total_possible_score': 30.0}
        )
        if r3.status == 'LOCKED':
            r3.status = 'UNLOCKED'
            r3.save()

    AuditLog.objects.create(
        admin_user=admin_user,
        action=f"Verified Round 2 for {participant_round.participant.username}",
        target_participant=participant_round.participant,
        details=f"Score: {participant_round.score}/25 | Status: {participant_round.status} | Remarks: {remarks}"
    )
    return is_qualified

def admin_verify_round_3(participant_round: ParticipantRound, admin_user, new_score=None, remarks=""):
    """
    Administrative action to verify Round 3 flowchart-to-code submissions.
    """
    if new_score is not None:
        participant_round.score = float(new_score)

    participant_round.is_verified = True
    participant_round.verified_by = admin_user
    participant_round.verified_at = timezone.now()
    participant_round.verification_remarks = remarks
    participant_round.status = 'VERIFIED'
    participant_round.save()

    result, _ = RoundResult.objects.get_or_create(participant=participant_round.participant)
    result.r3_score = participant_round.score
    result.r3_verified = True
    result.is_final_qualified = True
    result.completion_time = participant_round.completion_time or timezone.now()
    result.recalculate_total()
    result.save()

    AuditLog.objects.create(
        admin_user=admin_user,
        action=f"Verified Round 3 for {participant_round.participant.username}",
        target_participant=participant_round.participant,
        details=f"Score: {participant_round.score}/30 | Remarks: {remarks}"
    )
    return True

def recalculate_leaderboard():
    """
    Calculates ranks based on tie-breaking rules:
    1. Total score (descending)
    2. Round 3 score (descending)
    3. Final submission time (earlier is better)
    """
    results = RoundResult.objects.filter(is_published=True).order_by(
        '-total_score',
        '-r3_score',
        'completion_time'
    )
    rank = 1
    for res in results:
        res.final_rank = rank
        res.save(update_fields=['final_rank'])
        rank += 1
    return results

