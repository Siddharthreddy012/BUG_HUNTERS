from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import ParticipantRegistrationForm
from competition.services import initialize_participant_competition
from competition.models import CompetitionSettings

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    settings = CompetitionSettings.get_settings()
    if not settings.allow_registration:
        messages.error(request, "Registration for BUG HUNTERS is currently closed by the administrator.")
        return redirect('home')

    if request.method == 'POST':
        form = ParticipantRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Initialize participant competition state
            initialize_participant_competition(user)
            messages.success(request, f"Registration Successful! Welcome to BUG HUNTERS, {user.profile.full_name}.")
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors indicated below.")
    else:
        form = ParticipantRegistrationForm()

    return render(request, 'registration.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        identifier = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # Allow login via username or email
        user = authenticate(request, username=identifier, password=password)
        if user is None and '@' in identifier:
            try:
                user_obj = User.objects.get(email__iexact=identifier)
                user = authenticate(request, username=user_obj.username, password=password)
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                user = None

        if user is not None:
            # Check if disqualified
            if hasattr(user, 'profile') and user.profile.is_disqualified:
                messages.error(request, f"Access Denied: Your account has been disqualified. Reason: {user.profile.disqualification_reason}")
                return render(request, 'login.html')

            login(request, user)
            initialize_participant_competition(user)
            messages.success(request, "Welcome Back! Get ready to hunt some bugs.")
            
            # Redirect staff to admin dashboard or participant dashboard
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            if user.is_staff or user.is_superuser:
                return redirect('admin_dashboard')
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username/email or password. Please try again.")

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.info(request, "You have been securely logged out. Thank you for participating in BUG HUNTERS.")
    return redirect('home')

@login_required
def profile_view(request):
    return render(request, 'profile.html', {'user': request.user})
