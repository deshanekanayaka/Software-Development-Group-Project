from django.contrib import admin
from .models import Department, Team, UserProfile, HealthCheckCard, Session, Vote


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'department')
    list_filter = ('department',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'team', 'department')
    list_filter = ('role', 'department')
    search_fields = ('user__username', 'user__email')


@admin.register(HealthCheckCard)
class HealthCheckCardAdmin(admin.ModelAdmin):
    list_display = ('order', 'title')
    ordering = ('order',)


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_active')
    list_editable = ('is_active',)


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'session', 'card', 'vote', 'trend', 'updated_at')
    list_filter = ('session', 'vote', 'card')
    search_fields = ('user__username',)
