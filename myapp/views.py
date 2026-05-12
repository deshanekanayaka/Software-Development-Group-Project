from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from .models import Department, Team, UserProfile, HealthCheckCard, Session, Vote, VOTE_CHOICES, TREND_CHOICES


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'login_selection.html')


def logout_view(request):
    logout(request)
    return redirect('login')


def register_view(request):
    departments = Department.objects.all()
    teams = Team.objects.select_related('department').all()
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        username   = request.POST.get('username', '').strip()
        email      = request.POST.get('email', '').strip()
        password   = request.POST.get('password', '')
        confirm    = request.POST.get('confirm_password', '')
        role       = request.POST.get('role', 'engineer')
        team_id    = request.POST.get('team')
        dept_id    = request.POST.get('department')

        if password != confirm:
            messages.error(request, 'Passwords do not match.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        else:
            user = User.objects.create_user(
                username=username, email=email, password=password,
                first_name=first_name, last_name=last_name
            )
            team = Team.objects.filter(pk=team_id).first() if team_id else None
            dept = Department.objects.filter(pk=dept_id).first() if dept_id else None
            if role in ('dept_leader', 'senior_manager'):
                team = None
            UserProfile.objects.create(user=user, role=role, team=team, department=dept)
            login(request, user)
            messages.success(request, f'Welcome, {first_name}!')
            return redirect('dashboard')
    return render(request, 'sign_up.html', {'departments': departments, 'teams': teams})


@login_required
def dashboard_view(request):
    if request.user.is_superuser:
        return redirect('/admin/')
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        messages.warning(request, 'Please complete your profile.')
        return redirect('edit_profile')
    role = profile.role
    if role == 'engineer':
        return engineer_dashboard(request, profile)
    elif role == 'team_leader':
        return team_leader_dashboard(request, profile)
    elif role == 'dept_leader':
        return dept_leader_dashboard(request, profile)
    elif role == 'senior_manager':
        return senior_manager_dashboard(request, profile)
    return redirect('login')


def engineer_dashboard(request, profile):
    sessions = Session.objects.filter(is_active=True).order_by('-start_date')
    cards = HealthCheckCard.objects.all()
    selected_session_id = request.GET.get('session')
    selected_session = None
    user_votes = {}

    if selected_session_id:
        selected_session = get_object_or_404(Session, pk=selected_session_id)
        user_votes = {v.card_id: v for v in Vote.objects.filter(user=request.user, session=selected_session)}

    return render(request, 'engineer_dashboard.html', {
        'profile': profile,
        'sessions': sessions,
        'cards': cards,
        'selected_session': selected_session,
        'user_votes': user_votes,
    })


@login_required
def voting_view(request, session_id, card_id):
    session   = get_object_or_404(Session, pk=session_id)
    card      = get_object_or_404(HealthCheckCard, pk=card_id)
    cards     = list(HealthCheckCard.objects.all())
    card_idx  = next((i for i, c in enumerate(cards) if c.pk == card.pk), 0)
    next_card = cards[card_idx + 1] if card_idx + 1 < len(cards) else None
    prev_card = cards[card_idx - 1] if card_idx > 0 else None
    existing_vote = Vote.objects.filter(user=request.user, session=session, card=card).first()

    if request.method == 'POST':
        vote_val    = request.POST.get('vote')
        trend_val   = request.POST.get('trend')
        comment_val = request.POST.get('comment', '')
        if vote_val in [v[0] for v in VOTE_CHOICES]:
            Vote.objects.update_or_create(
                user=request.user, session=session, card=card,
                defaults={'vote': vote_val, 'trend': trend_val, 'comment': comment_val}
            )
            if next_card and 'next' in request.POST:
                return redirect('vote_card', session_id=session.pk, card_id=next_card.pk)
            if not next_card:
                messages.success(request, '✅ All done! Your votes have been saved.')
                return redirect(f"{reverse('summary')}?session={session.pk}")
            messages.success(request, 'Vote saved.')
            return redirect('vote_card', session_id=session.pk, card_id=card.pk)
        else:
            messages.error(request, 'Please select a vote.')

    return render(request, 'Voting_Page.html', {
        'session': session,
        'card': card,
        'existing_vote': existing_vote,
        'next_card': next_card,
        'prev_card': prev_card,
        'card_number': card_idx + 1,
        'total_cards': len(cards),
        'vote_choices': VOTE_CHOICES,
        'trend_choices': TREND_CHOICES,
    })


@login_required
def my_summary_view(request):
    profile  = request.user.profile
    sessions = Session.objects.all().order_by('-start_date')
    cards    = HealthCheckCard.objects.all()
    selected_session_id = request.GET.get('session')
    selected_session = None
    votes_by_card = {}
    team_summary  = {}

    if selected_session_id:
        selected_session = get_object_or_404(Session, pk=selected_session_id)
        votes_by_card = {v.card_id: v for v in Vote.objects.filter(user=request.user, session=selected_session)}

        if profile.team:
            team_votes = Vote.objects.filter(session=selected_session, user__profile__team=profile.team)
            for card in cards:
                cv = team_votes.filter(card=card)
                team_summary[card.pk] = {
                    'green': cv.filter(vote='green').count(),
                    'amber': cv.filter(vote='amber').count(),
                    'red':   cv.filter(vote='red').count(),
                    'total': cv.count(),
                }

    return render(request, 'Summary.html', {
        'sessions': sessions,
        'selected_session': selected_session,
        'cards': cards,
        'votes_by_card': votes_by_card,
        'team_summary': team_summary,
    })


def team_leader_dashboard(request, profile):
    sessions = Session.objects.all().order_by('-start_date')
    selected_session_id = request.GET.get('session')
    selected_session = None
    team  = profile.team
    cards = HealthCheckCard.objects.all()
    team_summary = {}

    if selected_session_id:
        selected_session = get_object_or_404(Session, pk=selected_session_id)
        if team:
            team_votes = Vote.objects.filter(session=selected_session, user__profile__team=team)
            for card in cards:
                cv = team_votes.filter(card=card)
                team_summary[card.pk] = {
                    'card':  card,
                    'green': cv.filter(vote='green').count(),
                    'amber': cv.filter(vote='amber').count(),
                    'red':   cv.filter(vote='red').count(),
                    'total': cv.count(),
                }

    return render(request, 'teamLeader_Dashboard.html', {
        'profile': profile,
        'sessions': sessions,
        'selected_session': selected_session,
        'team': team,
        'cards': cards,
        'team_summary': team_summary,
    })


def dept_leader_dashboard(request, profile):
    department = profile.department
    sessions   = Session.objects.all().order_by('-start_date')
    selected_session_id = request.GET.get('session')
    selected_session = None
    cards       = HealthCheckCard.objects.all()
    teams_data  = []
    other_depts = []

    if selected_session_id:
        selected_session = get_object_or_404(Session, pk=selected_session_id)
        if department:
            for team in department.teams.all():
                tv = Vote.objects.filter(session=selected_session, user__profile__team=team)
                cards_summary = []
                for card in cards:
                    cv = tv.filter(card=card)
                    cards_summary.append({
                        'card':  card,
                        'green': cv.filter(vote='green').count(),
                        'amber': cv.filter(vote='amber').count(),
                        'red':   cv.filter(vote='red').count(),
                        'total': cv.count(),
                    })
                teams_data.append({'team': team, 'cards': cards_summary})

        for dept in Department.objects.exclude(pk=department.pk if department else 0):
            dv = Vote.objects.filter(session=selected_session, user__profile__department=dept)
            other_depts.append({
                'dept':  dept,
                'green': dv.filter(vote='green').count(),
                'amber': dv.filter(vote='amber').count(),
                'red':   dv.filter(vote='red').count(),
                'total': dv.count(),
            })

    return render(request, 'DASHBOARD_DepartmentLeader.html', {
        'profile': profile,
        'department': department,
        'sessions': sessions,
        'selected_session': selected_session,
        'teams_data': teams_data,
        'other_depts': other_depts,
        'cards': cards,
    })


def senior_manager_dashboard(request, profile):
    sessions = Session.objects.all().order_by('-start_date')
    selected_session_id = request.GET.get('session')
    selected_session = None
    cards       = HealthCheckCard.objects.all()
    depts_data  = []
    selected_team_id = request.GET.get('team')
    selected_team = None
    team_detail   = []

    if selected_session_id:
        selected_session = get_object_or_404(Session, pk=selected_session_id)
        for dept in Department.objects.all():
            dv = Vote.objects.filter(session=selected_session, user__profile__department=dept)
            teams_summary = []
            for team in dept.teams.all():
                tv = dv.filter(user__profile__team=team)
                teams_summary.append({
                    'team':  team,
                    'green': tv.filter(vote='green').count(),
                    'amber': tv.filter(vote='amber').count(),
                    'red':   tv.filter(vote='red').count(),
                    'total': tv.count(),
                })
            depts_data.append({
                'dept':  dept,
                'teams': teams_summary,
                'green': dv.filter(vote='green').count(),
                'amber': dv.filter(vote='amber').count(),
                'red':   dv.filter(vote='red').count(),
                'total': dv.count(),
            })

        if selected_team_id:
            selected_team = get_object_or_404(Team, pk=selected_team_id)
            tv = Vote.objects.filter(session=selected_session, user__profile__team=selected_team)
            for card in cards:
                cv = tv.filter(card=card)
                team_detail.append({
                    'card':  card,
                    'green': cv.filter(vote='green').count(),
                    'amber': cv.filter(vote='amber').count(),
                    'red':   cv.filter(vote='red').count(),
                    'total': cv.count(),
                })

    return render(request, 'dash_SM.html', {
        'profile': profile,
        'sessions': sessions,
        'selected_session': selected_session,
        'depts_data': depts_data,
        'cards': cards,
        'selected_team': selected_team,
        'team_detail': team_detail,
        'all_teams': Team.objects.select_related('department').all(),
    })


@login_required
def edit_profile_view(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = None

    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name  = request.POST.get('last_name',  user.last_name)
        user.email      = request.POST.get('email',      user.email)
        new_pass = request.POST.get('new_password', '')
        confirm  = request.POST.get('confirm_password', '')
        if new_pass:
            if new_pass == confirm:
                user.set_password(new_pass)
                messages.success(request, 'Password updated. Please log in again.')
            else:
                messages.error(request, 'Passwords do not match.')
        user.save()
        messages.success(request, 'Profile updated.')
        return redirect('edit_profile')

    return render(request, 'edit_profile.html', {'profile': profile})


def teams_for_dept_view(request, dept_id):
    teams = Team.objects.filter(department_id=dept_id).values('id', 'name')
    return JsonResponse({'teams': list(teams)})