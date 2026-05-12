from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from django.shortcuts import redirect
from . import views

urlpatterns = [
    path('', lambda request: redirect('login'), name='landing'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('vote/<int:session_id>/<int:card_id>/', views.voting_view, name='vote_card'),
    path('summary/', views.my_summary_view, name='summary'),
    path('profile/', views.edit_profile_view, name='edit_profile'),
    path('api/teams/<int:dept_id>/', views.teams_for_dept_view, name='teams_for_dept'),
    path('login_selection/', views.login_view, name='loginSelection'),
    path('sign_up/', views.register_view, name='signUp'),
    path('landing_page/', lambda request: redirect('dashboard'), name='landingPage'),
    path('voting_page/', lambda request: redirect('dashboard'), name='votingPage'),
    path('edit_profile/', views.edit_profile_view, name='editProfile'),
] + static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
