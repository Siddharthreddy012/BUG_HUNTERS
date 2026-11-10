import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Count, Q, Avg

from .models import (
    CompetitionSettings, Round, Question, MCQOption,
    CodingChallenge, FlowchartQuestion, TestCase,
    ParticipantRound, AnswerSubmission, CodeSubmission,
    TabSwitchViolation, AuditLog
)
from results.models import RoundResult
from .services import (
    initialize_participant_competition,
    check_round_accessibility,
    evaluate_and_finalize_round_1,
    log_tab_violation,
    admin_verify_round_2,
    admin_verify_round_3,
    recalculate_leaderboard
)
from .evaluation import evaluate_submission, run_python_code, run_c_code, run_java_code, normalize_output


# --- Public / Informational Views ---

def home_view(request):
    settings = CompetitionSettings.get_settings()
    rounds = Round.objects.all().order_by('round_number')
    
    # Quick statistics
    stats = {
        'total_participants': User.objects.filter(is_staff=False).count(),
        'rounds_count': 3,
        'r1_qualifying': settings.r1_qualifying_marks,
        'r2_qualifying': settings.r2_qualifying_marks,
    }
    return render(request, 'home.html', {
        'comp_settings': settings,
        'rounds': rounds,
        'stats': stats,
    })

def about_view(request):
    return render(request, 'about.html')

def rules_view(request):
    settings = CompetitionSettings.get_settings()
    return render(request, 'rules.html', {'comp_settings': settings})

def rounds_overview_view(request):
    rounds = Round.objects.all().order_by('round_number')
    return render(request, 'rounds_overview.html', {'rounds': rounds})


# --- Participant Dashboard ---

@login_required
def dashboard_view(request):
    initialize_participant_competition(request.user)
    settings = CompetitionSettings.get_settings()
    
    p_rounds = ParticipantRound.objects.filter(participant=request.user).order_by('round_number')
    r_dict = {pr.round_number: pr for pr in p_rounds}
    
    r1 = r_dict.get(1)
    r2 = r_dict.get(2)
    r3 = r_dict.get(3)
    
    # Calculate overall progress percentage
    completed_steps = 0
    if r1 and r1.is_completed():
        completed_steps += 1
    if r2 and r2.is_completed():
        completed_steps += 1
    if r3 and r3.is_completed():
        completed_steps += 1
    progress_percentage = int((completed_steps / 3) * 100)
    
    # Overall score
    total_score = (r1.score if r1 else 0) + (r2.score if r2 else 0) + (r3.score if r3 else 0)
    
    # Tab violations
    violation_count = TabSwitchViolation.objects.filter(participant=request.user).count()

    context = {
        'r1': r1,
        'r2': r2,
        'r3': r3,
        'total_score': round(total_score, 2),
        'max_total_score': 70.0,
        'progress_percentage': progress_percentage,
        'violation_count': violation_count,
        'comp_settings': settings,
    }
    return render(request, 'dashboard.html', context)


# --- Round 1: Code Quest (MCQ Challenge) ---

@login_required
def round1_view(request):
    accessible, msg, p_round = check_round_accessibility(request.user, 1)
    if not accessible:
        messages.warning(request, msg)
        return redirect('dashboard')

    settings = CompetitionSettings.get_settings()
    questions = list(Question.objects.all().order_by('order', 'id'))
    total_q = len(questions)
    time_limit_sec = settings.r1_time_per_question_seconds  # default 60s

    if total_q == 0:
        messages.error(request, "Round 1 questions have not been configured yet.")
        return redirect('dashboard')

    # Initialize start time if beginning
    if not p_round.start_time:
        p_round.start_time = timezone.now()
        p_round.status = 'IN_PROGRESS'
        p_round.current_question_index = 0
        p_round.current_question_start_time = timezone.now()
        p_round.save()

    curr_idx = p_round.current_question_index

    # Check if participant finished all questions
    if curr_idx >= total_q:
        is_qual, score = evaluate_and_finalize_round_1(p_round)
        if is_qual:
            messages.success(request, f"Congratulations! You qualified Round 1 with {score}/15 marks! Round 2 is now unlocked.")
        else:
            messages.warning(request, f"Round 1 completed. Score: {score}/15. Minimum qualifying marks: {settings.r1_qualifying_marks}/15.")
        return redirect('dashboard')

    # Handle answer submission
    if request.method == 'POST':
        selected_option_id = request.POST.get('selected_option')
        action = request.POST.get('action', 'next')
        current_question = questions[curr_idx]

        if selected_option_id:
            try:
                opt = MCQOption.objects.get(id=selected_option_id, question=current_question)
                is_corr = opt.is_correct
                awarded = current_question.marks if is_corr else 0.0
                AnswerSubmission.objects.update_or_create(
                    participant_round=p_round,
                    question=current_question,
                    defaults={
                        'selected_option': opt,
                        'is_correct': is_corr,
                        'marks_awarded': awarded,
                    }
                )
            except MCQOption.DoesNotExist:
                pass
        else:
            # Saved as unattempted/skipped
            AnswerSubmission.objects.update_or_create(
                participant_round=p_round,
                question=current_question,
                defaults={
                    'selected_option': None,
                    'is_correct': False,
                    'marks_awarded': 0.0,
                }
            )

        # Advance to next question
        p_round.current_question_index += 1
        p_round.current_question_start_time = timezone.now()
        p_round.save()

        # If completed all questions
        if p_round.current_question_index >= total_q:
            is_qual, score = evaluate_and_finalize_round_1(p_round)
            return render(request, 'round_qualification_popup.html', {
                'round_num': 1,
                'round_name': 'Code Quest',
                'score': score,
                'max_score': 15,
                'qualifying_score': settings.r1_qualifying_marks,
                'is_qualified': is_qual,
                'next_url': '/competition/round2/' if is_qual else '/dashboard/',
            })

        return redirect('round1')

    # Calculate remaining seconds based on server timestamp
    now = timezone.now()
    if not p_round.current_question_start_time:
        p_round.current_question_start_time = now
        p_round.save()

    elapsed = (now - p_round.current_question_start_time).total_seconds()
    remaining_seconds = max(0, int(time_limit_sec - elapsed))

    # Auto-advance if time already expired during previous page load/idle
    if remaining_seconds <= 0:
        current_question = questions[curr_idx]
        AnswerSubmission.objects.get_or_create(
            participant_round=p_round,
            question=current_question,
            defaults={'selected_option': None, 'is_correct': False, 'marks_awarded': 0.0}
        )
        p_round.current_question_index += 1
        p_round.current_question_start_time = now
        p_round.save()

        if p_round.current_question_index >= total_q:
            is_qual, score = evaluate_and_finalize_round_1(p_round)
            return render(request, 'round_qualification_popup.html', {
                'round_num': 1,
                'round_name': 'Code Quest',
                'score': score,
                'max_score': 15,
                'qualifying_score': settings.r1_qualifying_marks,
                'is_qualified': is_qual,
                'next_url': '/competition/round2/' if is_qual else '/dashboard/',
            })
        return redirect('round1')

    active_question = questions[curr_idx]
    options = active_question.options.all().order_by('identifier')

    # Build status palette for answered/unanswered
    submitted_q_ids = set(AnswerSubmission.objects.filter(
        participant_round=p_round,
        selected_option__isnull=False
    ).values_list('question_id', flat=True))

    question_status_list = []
    for i, q in enumerate(questions):
        status = 'current' if i == curr_idx else ('answered' if q.id in submitted_q_ids else ('skipped' if i < curr_idx else 'unanswered'))
        question_status_list.append({
            'index': i + 1,
            'status': status,
        })

    violation_count = TabSwitchViolation.objects.filter(participant=request.user, round_number=1).count()

    context = {
        'question': active_question,
        'options': options,
        'current_number': curr_idx + 1,
        'total_questions': total_q,
        'remaining_seconds': remaining_seconds,
        'question_status_list': question_status_list,
        'violation_count': violation_count,
        'round_number': 1,
    }
    return render(request, 'round1.html', context)


# --- Round 2: Bug Bounty (Error Line Coding) ---

@login_required
def round2_view(request):
    accessible, msg, p_round = check_round_accessibility(request.user, 2)
    if not accessible:
        messages.warning(request, msg)
        return redirect('dashboard')

    settings = CompetitionSettings.get_settings()
    time_limit_sec = settings.r2_time_per_question_seconds  # default 300s (5 min)

    # Language selection step
    if not p_round.selected_language:
        if request.method == 'POST' and 'selected_language' in request.POST:
            lang = request.POST.get('selected_language')
            if lang in ['c', 'python', 'java']:
                p_round.selected_language = lang
                p_round.start_time = timezone.now()
                p_round.status = 'IN_PROGRESS'
                p_round.current_question_index = 0
                p_round.current_question_start_time = timezone.now()
                p_round.save()
                messages.success(request, f"Language locked to {lang.upper()}. Round 2 started!")
                return redirect('round2')
            else:
                messages.error(request, "Invalid language chosen.")
        return render(request, 'round_language_select.html', {
            'round_num': 2,
            'round_name': 'Bug Bounty',
            'round_tagline': 'Identify errors, fix code lines, and optimize solutions.',
            'qualifying_score': settings.r2_qualifying_marks,
            'total_score': 25,
            'duration_per_question': '5 Minutes',
            'total_questions': 5,
        })

    # Load challenges for the selected language
    challenges = list(CodingChallenge.objects.filter(language=p_round.selected_language).order_by('order', 'id'))
    total_c = len(challenges)

    if total_c == 0:
        messages.error(request, f"No Round 2 challenges configured for {p_round.selected_language.upper()}. Contact administrator.")
        return redirect('dashboard')

    curr_idx = p_round.current_question_index

    # Check if finished
    if curr_idx >= total_c:
        # Finalize Round 2
        p_round.status = 'UNDER_EVALUATION'
        p_round.completion_time = timezone.now()
        # Sum marks awarded
        submissions = CodeSubmission.objects.filter(participant_round=p_round)
        p_round.score = round(sum(s.marks_awarded for s in submissions), 2)
        p_round.save()

        # Update RoundResult
        result, _ = RoundResult.objects.get_or_create(participant=request.user)
        result.r2_score = p_round.score
        result.recalculate_total()
        result.save()

        messages.info(request, f"Round 2 submitted! Your responses are saved and currently under administrator verification.")
        return redirect('dashboard')

    active_challenge = challenges[curr_idx]

    # Handle Question submission
    if request.method == 'POST':
        submitted_code = request.POST.get('submitted_code', '')
        test_cases = list(active_challenge.test_cases.all())

        # Evaluate code
        passed, total, marks, log_text, details = evaluate_submission(
            submitted_code,
            p_round.selected_language,
            test_cases,
            max_marks=active_challenge.marks,
            reference_code=active_challenge.corrected_reference_code
        )

        CodeSubmission.objects.update_or_create(
            participant_round=p_round,
            coding_challenge=active_challenge,
            defaults={
                'submitted_code': submitted_code,
                'language': p_round.selected_language,
                'passed_test_cases': passed,
                'total_test_cases': total,
                'execution_output': log_text,
                'marks_awarded': marks,
                'evaluation_status': 'EVALUATED'
            }
        )

        p_round.current_question_index += 1
        p_round.current_question_start_time = timezone.now()
        p_round.save()

        if p_round.current_question_index >= total_c:
            p_round.status = 'UNDER_EVALUATION'
            p_round.completion_time = timezone.now()
            submissions = CodeSubmission.objects.filter(participant_round=p_round)
            p_round.score = round(sum(s.marks_awarded for s in submissions), 2)
            p_round.save()

            result, _ = RoundResult.objects.get_or_create(participant=request.user)
            result.r2_score = p_round.score
            result.recalculate_total()
            result.save()

            return render(request, 'round_submission_confirmation.html', {
                'round_num': 2,
                'round_name': 'Bug Bounty',
                'score': p_round.score,
                'max_score': 25,
                'status': 'Under Evaluation & Administrator Verification',
                'message': 'Your corrections have been successfully compiled, evaluated, and saved for admin review.',
            })

        return redirect('round2')

    # Server-backed timer
    now = timezone.now()
    if not p_round.current_question_start_time:
        p_round.current_question_start_time = now
        p_round.save()

    elapsed = (now - p_round.current_question_start_time).total_seconds()
    remaining_seconds = max(0, int(time_limit_sec - elapsed))

    # Existing code submission if already partially saved
    prior_submission = CodeSubmission.objects.filter(participant_round=p_round, coding_challenge=active_challenge).first()
    editor_code = prior_submission.submitted_code if prior_submission else active_challenge.buggy_code

    # Add line numbers helper for buggy code display
    buggy_lines = active_challenge.buggy_code.split('\n')
    line_numbered_code = [{'number': i + 1, 'text': line} for i, line in enumerate(buggy_lines)]

    violation_count = TabSwitchViolation.objects.filter(participant=request.user, round_number=2).count()

    context = {
        'challenge': active_challenge,
        'line_numbered_code': line_numbered_code,
        'editor_code': editor_code,
        'current_number': curr_idx + 1,
        'total_questions': total_c,
        'remaining_seconds': remaining_seconds,
        'selected_language': p_round.selected_language,
        'violation_count': violation_count,
        'round_number': 2,
    }
    return render(request, 'round2.html', context)


# --- Round 3: Logic Launch (Flowchart to Code) ---

@login_required
def round3_view(request):
    accessible, msg, p_round = check_round_accessibility(request.user, 3)
    if not accessible:
        messages.warning(request, msg)
        return redirect('dashboard')

    settings = CompetitionSettings.get_settings()
    time_limit_sec = settings.r3_time_per_question_seconds  # default 600s (10 min)

    # Language selection step
    if not p_round.selected_language:
        if request.method == 'POST' and 'selected_language' in request.POST:
            lang = request.POST.get('selected_language')
            if lang in ['c', 'python', 'java']:
                p_round.selected_language = lang
                p_round.start_time = timezone.now()
                p_round.status = 'IN_PROGRESS'
                p_round.current_question_index = 0
                p_round.current_question_start_time = timezone.now()
                p_round.save()
                messages.success(request, f"Language locked to {lang.upper()}. Round 3 started!")
                return redirect('round3')
            else:
                messages.error(request, "Invalid language chosen.")
        return render(request, 'round_language_select.html', {
            'round_num': 3,
            'round_name': 'Logic Launch',
            'round_tagline': 'Convert visual algorithmic flowcharts into clean executable programs.',
            'qualifying_score': 0,
            'total_score': 30,
            'duration_per_question': '10 Minutes',
            'total_questions': 3,
        })

    questions = list(FlowchartQuestion.objects.filter(language=p_round.selected_language).order_by('order', 'id'))
    total_q = len(questions)

    if total_q == 0:
        messages.error(request, f"No Round 3 questions configured for {p_round.selected_language.upper()}. Contact administrator.")
        return redirect('dashboard')

    curr_idx = p_round.current_question_index

    if curr_idx >= total_q:
        p_round.status = 'SUBMITTED'
        p_round.completion_time = timezone.now()
        submissions = CodeSubmission.objects.filter(participant_round=p_round)
        p_round.score = round(sum(s.marks_awarded for s in submissions), 2)
        p_round.save()

        result, _ = RoundResult.objects.get_or_create(participant=request.user)
        result.r3_score = p_round.score
        result.completion_time = p_round.completion_time
        result.recalculate_total()
        result.save()

        messages.success(request, "Competition completed! Your Round 3 code solutions are submitted for final verification.")
        return redirect('dashboard')

    active_question = questions[curr_idx]

    # Handle Question submission
    if request.method == 'POST':
        submitted_code = request.POST.get('submitted_code', '')
        test_cases = list(active_question.test_cases.all())

        passed, total, marks, log_text, details = evaluate_submission(
            submitted_code,
            p_round.selected_language,
            test_cases,
            max_marks=active_question.marks,
            reference_code=active_question.reference_solution
        )

        CodeSubmission.objects.update_or_create(
            participant_round=p_round,
            flowchart_question=active_question,
            defaults={
                'submitted_code': submitted_code,
                'language': p_round.selected_language,
                'passed_test_cases': passed,
                'total_test_cases': total,
                'execution_output': log_text,
                'marks_awarded': marks,
                'evaluation_status': 'EVALUATED'
            }
        )

        p_round.current_question_index += 1
        p_round.current_question_start_time = timezone.now()
        p_round.save()

        if p_round.current_question_index >= total_q:
            p_round.status = 'SUBMITTED'
            p_round.completion_time = timezone.now()
            submissions = CodeSubmission.objects.filter(participant_round=p_round)
            p_round.score = round(sum(s.marks_awarded for s in submissions), 2)
            p_round.save()

            result, _ = RoundResult.objects.get_or_create(participant=request.user)
            result.r3_score = p_round.score
            result.completion_time = p_round.completion_time
            result.recalculate_total()
            result.save()

            return render(request, 'round_submission_confirmation.html', {
                'round_num': 3,
                'round_name': 'Logic Launch',
                'score': p_round.score,
                'max_score': 30,
                'status': 'Completed & Awaiting Final Verification',
                'message': 'All rounds completed! You can view your verified results once finalized by the administrator.',
            })

        return redirect('round3')

    # Server-backed timer
    now = timezone.now()
    if not p_round.current_question_start_time:
        p_round.current_question_start_time = now
        p_round.save()

    elapsed = (now - p_round.current_question_start_time).total_seconds()
    remaining_seconds = max(0, int(time_limit_sec - elapsed))

    prior_submission = CodeSubmission.objects.filter(participant_round=p_round, flowchart_question=active_question).first()
    editor_code = prior_submission.submitted_code if prior_submission else (active_question.starter_template or "")

    violation_count = TabSwitchViolation.objects.filter(participant=request.user, round_number=3).count()

    context = {
        'question': active_question,
        'editor_code': editor_code,
        'current_number': curr_idx + 1,
        'total_questions': total_q,
        'remaining_seconds': remaining_seconds,
        'selected_language': p_round.selected_language,
        'violation_count': violation_count,
        'round_number': 3,
    }
    return render(request, 'round3.html', context)


# --- Anti-Cheating & Execution APIs ---

@login_required
@require_POST
def api_log_violation(request):
    """AJAX endpoint for browser tab switch and visibility loss detection."""
    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    round_num = int(data.get('round_number', 1))
    event_type = data.get('event_type', 'tab_switch')
    details = data.get('details', '')

    count = log_tab_violation(request.user, round_num, event_type, details)
    settings = CompetitionSettings.get_settings()

    return JsonResponse({
        'status': 'success',
        'violation_count': count,
        'max_warnings': settings.max_warning_violations,
        'flagged': count >= settings.max_warning_violations,
        'message': 'Tab switch recorded.'
    })

@login_required
@require_POST
def api_test_run_code(request):
    """
    Live test execution endpoint for participant editor.
    Runs submitted code with sample or custom test cases without saving final round submission.
    """
    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    code = data.get('code', '')
    language = data.get('language', 'python').lower()
    input_data = data.get('custom_input', '')

    if not code.strip():
        return JsonResponse({'status': 'error', 'message': 'Code cannot be empty.'})

    ret = 0
    stdout = ""
    stderr = ""

    if language == 'python':
        ret, stdout, stderr = run_python_code(code, input_data)
    elif language == 'c':
        ret, stdout, stderr = run_c_code(code, input_data)
    elif language == 'java':
        ret, stdout, stderr = run_java_code(code, input_data)
    else:
        return JsonResponse({'status': 'error', 'message': f'Unsupported language: {language}'})

    return JsonResponse({
        'status': 'success',
        'return_code': ret,
        'output': stdout,
        'error': stderr,
    })


# --- Admin Dashboard & Management ---

def is_admin_user(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@user_passes_test(is_admin_user, login_url='login')
def admin_dashboard_view(request):
    settings = CompetitionSettings.get_settings()
    
    # Overview statistics
    total_participants = User.objects.filter(is_staff=False).count()
    r1_attempted = ParticipantRound.objects.filter(round_number=1, start_time__isnull=False).count()
    r1_qualified = ParticipantRound.objects.filter(round_number=1, status='QUALIFIED').count()
    r2_completed = ParticipantRound.objects.filter(round_number=2, status__in=['SUBMITTED', 'UNDER_EVALUATION', 'VERIFIED']).count()
    r2_verified = ParticipantRound.objects.filter(round_number=2, is_verified=True).count()
    r3_completed = ParticipantRound.objects.filter(round_number=3, status__in=['SUBMITTED', 'VERIFIED']).count()
    final_qualified = RoundResult.objects.filter(is_final_qualified=True).count()

    # Participants list with query & filter
    query = request.GET.get('q', '').strip()
    dept_filter = request.GET.get('department', '')
    year_filter = request.GET.get('year', '')

    participants = User.objects.filter(is_staff=False).select_related('profile', 'competition_result')
    if query:
        participants = participants.filter(
            Q(username__icontains=query) |
            Q(profile__full_name__icontains=query) |
            Q(profile__roll_number__icontains=query) |
            Q(email__icontains=query)
        )
    if dept_filter:
        participants = participants.filter(profile__department=dept_filter)
    if year_filter:
        participants = participants.filter(profile__year=year_filter)

    # Violations summary
    recent_violations = TabSwitchViolation.objects.select_related('participant', 'participant__profile')[:15]
    
    # Audit log
    audit_logs = AuditLog.objects.select_related('admin_user', 'target_participant')[:15]

    context = {
        'comp_settings': settings,
        'stats': {
            'total_participants': total_participants,
            'r1_attempted': r1_attempted,
            'r1_qualified': r1_qualified,
            'r2_completed': r2_completed,
            'r2_verified': r2_verified,
            'r3_completed': r3_completed,
            'final_qualified': final_qualified,
        },
        'participants': participants,
        'recent_violations': recent_violations,
        'audit_logs': audit_logs,
        'query': query,
        'dept_filter': dept_filter,
        'year_filter': year_filter,
    }
    return render(request, 'admin_dashboard.html', context)


@user_passes_test(is_admin_user, login_url='login')
def admin_participant_detail_view(request, user_id):
    participant = get_object_or_404(User, id=user_id)
    r1 = ParticipantRound.objects.filter(participant=participant, round_number=1).first()
    r2 = ParticipantRound.objects.filter(participant=participant, round_number=2).first()
    r3 = ParticipantRound.objects.filter(participant=participant, round_number=3).first()

    r1_answers = AnswerSubmission.objects.filter(participant_round=r1).select_related('question', 'selected_option') if r1 else []
    r2_submissions = CodeSubmission.objects.filter(participant_round=r2).select_related('coding_challenge') if r2 else []
    r3_submissions = CodeSubmission.objects.filter(participant_round=r3).select_related('flowchart_question') if r3 else []
    violations = TabSwitchViolation.objects.filter(participant=participant)

    return render(request, 'admin_participant_detail.html', {
        'target_user': participant,
        'r1': r1,
        'r2': r2,
        'r3': r3,
        'r1_answers': r1_answers,
        'r2_submissions': r2_submissions,
        'r3_submissions': r3_submissions,
        'violations': violations,
    })


@user_passes_test(is_admin_user, login_url='login')
@require_POST
def admin_verify_round_action(request, round_id):
    p_round = get_object_or_404(ParticipantRound, id=round_id)
    score_override = request.POST.get('score')
    remarks = request.POST.get('remarks', '')

    new_score = float(score_override) if score_override and score_override.strip() else None

    if p_round.round_number == 2:
        is_qual = admin_verify_round_2(p_round, request.user, new_score=new_score, remarks=remarks)
        messages.success(request, f"Round 2 verified for {p_round.participant.username}. Status: {'QUALIFIED & UNLOCKED R3' if is_qual else 'NOT QUALIFIED'}.")
    elif p_round.round_number == 3:
        admin_verify_round_3(p_round, request.user, new_score=new_score, remarks=remarks)
        recalculate_leaderboard()
        messages.success(request, f"Round 3 verified for {p_round.participant.username}. Leaderboard updated.")

    return redirect('admin_participant_detail', user_id=p_round.participant.id)


@user_passes_test(is_admin_user, login_url='login')
@require_POST
def admin_manual_qualification_override(request, user_id):
    participant = get_object_or_404(User, id=user_id)
    round_num = int(request.POST.get('round_number', 1))
    new_status = request.POST.get('new_status')
    reason = request.POST.get('reason', 'Admin override')

    p_round = get_object_or_404(ParticipantRound, participant=participant, round_number=round_num)
    old_status = p_round.status
    p_round.status = new_status
    p_round.save()

    # If Round 1 qualified, unlock Round 2
    if round_num == 1 and new_status == 'QUALIFIED':
        r2 = ParticipantRound.objects.filter(participant=participant, round_number=2).first()
        if r2 and r2.status == 'LOCKED':
            r2.status = 'UNLOCKED'
            r2.save()

    AuditLog.objects.create(
        admin_user=request.user,
        action=f"Manually altered Round {round_num} status ({old_status} -> {new_status})",
        target_participant=participant,
        details=f"Reason: {reason}"
    )

    messages.success(request, f"Status updated to {new_status} for {participant.username} (Round {round_num}).")
    return redirect('admin_participant_detail', user_id=participant.id)


@user_passes_test(is_admin_user, login_url='login')
def admin_settings_view(request):
    settings = CompetitionSettings.get_settings()
    if request.method == 'POST':
        settings.title = request.POST.get('title', settings.title)
        settings.r1_qualifying_marks = int(request.POST.get('r1_qualifying_marks', settings.r1_qualifying_marks))
        settings.r1_time_per_question_seconds = int(request.POST.get('r1_time_per_question_seconds', settings.r1_time_per_question_seconds))
        settings.r2_qualifying_marks = int(request.POST.get('r2_qualifying_marks', settings.r2_qualifying_marks))
        settings.r2_time_per_question_seconds = int(request.POST.get('r2_time_per_question_seconds', settings.r2_time_per_question_seconds))
        settings.r3_time_per_question_seconds = int(request.POST.get('r3_time_per_question_seconds', settings.r3_time_per_question_seconds))
        
        settings.r1_enabled = 'r1_enabled' in request.POST
        settings.r2_enabled = 'r2_enabled' in request.POST
        settings.r3_enabled = 'r3_enabled' in request.POST
        settings.allow_registration = 'allow_registration' in request.POST
        settings.leaderboard_published = 'leaderboard_published' in request.POST
        settings.anti_cheating_enabled = 'anti_cheating_enabled' in request.POST
        settings.save()

        AuditLog.objects.create(
            admin_user=request.user,
            action="Updated Competition Settings",
            details="Settings parameters updated via Admin Dashboard."
        )
        messages.success(request, "Competition Settings updated successfully.")
        return redirect('admin_settings')

    return render(request, 'admin_settings.html', {'comp_settings': settings})


@user_passes_test(is_admin_user, login_url='login')
def admin_questions_view(request):
    mcq_questions = Question.objects.all().prefetch_related('options')
    coding_challenges = CodingChallenge.objects.all().prefetch_related('test_cases')
    flowchart_questions = FlowchartQuestion.objects.all().prefetch_related('test_cases')

    return render(request, 'admin_questions.html', {
        'mcq_questions': mcq_questions,
        'coding_challenges': coding_challenges,
        'flowchart_questions': flowchart_questions,
    })
