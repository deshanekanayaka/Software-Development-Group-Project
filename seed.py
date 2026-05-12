"""Run with: python manage.py shell < seed.py"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_project.settings')
django.setup()

from django.contrib.auth.models import User
from myapp.models import Department, Team, UserProfile, HealthCheckCard, Session, Vote
from datetime import date, timedelta

# ── Departments & Teams ──────────────────────────────────────
d1 = Department.objects.get_or_create(name="Engineering")[0]
d2 = Department.objects.get_or_create(name="Platform")[0]
d3 = Department.objects.get_or_create(name="Data & Analytics")[0]

teams = {}
for tname, dept in [
    ("Sky Go Team", d1), ("Peacock Dev", d1), ("Streaming Core", d1), ("Mobile Apps", d1), ("Sky Sports Tech", d1),
    ("Cloud Infra", d2), ("DevOps", d2), ("API Gateway", d2), ("Security", d2), ("Reliability", d2),
    ("Data Engineering", d3), ("ML Platform", d3), ("BI Tools", d3), ("Insights", d3), ("Data Ops", d3),
]:
    teams[tname] = Team.objects.get_or_create(name=tname, department=dept)[0]

# ── Health Check Cards (Spotify's 10) ───────────────────────
cards_data = [
    (1, "Easy to Release", "Releasing is simple, safe, painless and mostly automated.",
     "Releasing is fully automated and happens multiple times a day.",
     "Releasing is risky, manual and infrequent."),
    (2, "Suitable Process", "Our way of working fits us perfectly.",
     "Our process is tuned to our needs – we own and adapt it freely.",
     "Our process is a burden that slows us down."),
    (3, "Tech Quality", "We're proud of the quality of our code and infrastructure.",
     "We have excellent test coverage and clean architecture we're proud of.",
     "We have significant technical debt that blocks progress."),
    (4, "Value", "We deliver great value and our stakeholders are happy.",
     "We ship features our users love and can measure the impact clearly.",
     "We build things nobody uses or nobody knows if they matter."),
    (5, "Speed", "We move quickly and are not blocked.",
     "We can go from idea to production in days.",
     "We feel slow and it's hard to get anything done."),
    (6, "Mission", "We know exactly why we are here and we're proud of it.",
     "Our mission is crystal clear and inspires us every day.",
     "We have no clear mission or it changes constantly."),
    (7, "Fun", "We enjoy coming to work and have fun together.",
     "Work is energising; we laugh, collaborate and celebrate together.",
     "Work is dull or stressful; team morale is low."),
    (8, "Learning", "We're learning lots of interesting stuff all the time.",
     "We have time and support to grow skills; knowledge is shared freely.",
     "We never have time to learn and knowledge is siloed."),
    (9, "Support", "We always get great support and help when we ask for it.",
     "Help is just a message away and never blocked by bureaucracy.",
     "Getting support is slow, unreliable or almost impossible."),
    (10, "Pawns or Players", "We are in control of our destiny and can influence our priorities.",
     "We own our roadmap and make our own technical decisions.",
     "We're told what to build with no room for input or ownership."),
]
for order, title, desc, good, bad in cards_data:
    HealthCheckCard.objects.get_or_create(order=order, defaults={
        'title': title, 'description': desc, 'good_description': good, 'bad_description': bad
    })

# ── Sessions ─────────────────────────────────────────────────
today = date.today()
s1 = Session.objects.get_or_create(name="Q1 2025", defaults={'start_date': date(2025,1,1), 'end_date': date(2025,3,31), 'is_active': False})[0]
s2 = Session.objects.get_or_create(name="Q2 2025", defaults={'start_date': date(2025,4,1), 'end_date': date(2025,6,30), 'is_active': True})[0]
s3 = Session.objects.get_or_create(name="Q3 2025", defaults={'start_date': today, 'end_date': today + timedelta(days=90), 'is_active': True})[0]

# ── Demo users ───────────────────────────────────────────────
def make_user(username, first, last, email, role, team=None, dept=None):
    u, created = User.objects.get_or_create(username=username)
    if created:
        u.first_name = first; u.last_name = last; u.email = email
        u.set_password('Password123!')
        u.save()
    UserProfile.objects.get_or_create(user=u, defaults={'role': role, 'team': team, 'department': dept})
    return u

# Engineers (5 per first team)
eng_team = teams["Sky Go Team"]
engineers = [
    make_user('alice.smith', 'Alice', 'Smith', 'alice@sky.com', 'engineer', eng_team, d1),
    make_user('bob.jones', 'Bob', 'Jones', 'bob@sky.com', 'engineer', eng_team, d1),
    make_user('carol.white', 'Carol', 'White', 'carol@sky.com', 'engineer', eng_team, d1),
    make_user('dave.black', 'Dave', 'Black', 'dave@sky.com', 'engineer', eng_team, d1),
    make_user('eve.brown', 'Eve', 'Brown', 'eve@sky.com', 'engineer', eng_team, d1),
]
tl = make_user('tom.leader', 'Tom', 'Leader', 'tom@sky.com', 'team_leader', eng_team, d1)
dl = make_user('diana.dept', 'Diana', 'Dept', 'diana@sky.com', 'dept_leader', None, d1)
sm = make_user('sam.senior', 'Sam', 'Senior', 'sam@sky.com', 'senior_manager', None, d1)

# Admin superuser
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@sky.com', 'admin123')

# ── Demo votes for Q1 ────────────────────────────────────────
import random
cards = list(HealthCheckCard.objects.all())
vote_opts = ['green', 'green', 'amber', 'red']
trend_opts = ['improving', 'stable', 'worse']
for eng in engineers:
    for card in cards:
        Vote.objects.get_or_create(
            user=eng, session=s1, card=card,
            defaults={
                'vote': random.choice(vote_opts),
                'trend': random.choice(trend_opts),
                'comment': 'Auto-generated seed vote.'
            }
        )

print("✅ Seed complete!")
print("   Users: alice.smith / bob.jones / carol.white / dave.black / eve.brown (engineers)")
print("          tom.leader (team leader) | diana.dept (dept leader) | sam.senior (senior manager)")
print("          admin (Django admin) — passwords: Password123! (or admin123 for admin)")
