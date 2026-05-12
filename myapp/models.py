from django.db import models
from django.contrib.auth.models import User


ROLE_CHOICES = [
    ('engineer', 'Engineer'),
    ('team_leader', 'Team Leader'),
    ('dept_leader', 'Department Leader'),
    ('senior_manager', 'Senior Manager'),
]

VOTE_CHOICES = [
    ('green', 'Green'),
    ('amber', 'Amber'),
    ('red', 'Red'),
]

TREND_CHOICES = [
    ('improving', 'Improving'),
    ('stable', 'Stable'),
    ('worse', 'Getting Worse'),
]


class Department(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Team(models.Model):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='teams')

    def __str__(self):
        return f"{self.name} ({self.department.name})"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='engineer')
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"


class HealthCheckCard(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    good_description = models.TextField(help_text="What 'Green' looks like", default="")
    bad_description = models.TextField(help_text="What 'Red' looks like", default="")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class Session(models.Model):
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.start_date} – {self.end_date})"


class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='votes')
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='votes')
    card = models.ForeignKey(HealthCheckCard, on_delete=models.CASCADE, related_name='votes')
    vote = models.CharField(max_length=10, choices=VOTE_CHOICES)
    trend = models.CharField(max_length=12, choices=TREND_CHOICES, blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'session', 'card')

    def __str__(self):
        return f"{self.user.username} | {self.card.title} | {self.vote}"
