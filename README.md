# SKY Health Check Application

A full-stack Django web application implementing the Spotify Squad Health Check
technique for SKY's Engineering Department. Built as part of the 5COSC021W
Software Development Group Project at the University of Westminster.

## Overview

Engineering teams use this app to assess the health of their operations across
10 critical health-check cards. Results are visualised by role, from individual
engineers up to senior management.

## Features

- **Role-based access control** — Engineer, Team Leader, Department Leader, Senior Manager
- **Self-registration** with role and team assignment
- **Traffic-light voting** (Green / Amber / Red) with trend tracking (Improving / Stable / Getting Worse)
- **10 Spotify health check cards** — Easy to Release, Suitable Process, Tech Quality, Value, Speed, Mission, Fun, Learning, Support, Pawns or Players
- **Session management** — Admins create sessions; users vote per session
- **Completion confirmation** — success banner after submitting all 10 cards
- **Progress tracking** — card grid shows voted/unvoted state with colour-coded borders
- **Role-specific dashboards** — each role sees appropriate summaries; individual votes are never exposed beyond engineer level
- **Team summary** — stacked bar charts showing Green/Amber/Red distribution per card
- **Superuser admin** — Django admin panel for full CRUD on all data
- **Avatar initials** — navbar shows user initials, falls back to username initial
- **20 automated tests** covering authentication, registration, voting, role routing, and profile management

## Tech Stack

- **Backend:** Python 3 / Django 5
- **Database:** SQLite (via Django ORM)
- **Frontend:** Bootstrap 5, vanilla JS
- **Tests:** Django TestCase

## Setup

```bash
# 1. Create and activate a virtual environment
python3 -m venv env
source env/bin/activate        # Windows: env\Scripts\activate

# 2. Install dependencies
pip install django

# 3. Apply migrations
python3 manage.py migrate

# 4. Seed initial data (departments, teams, cards, demo users)
python3 seed.py

# 5. Run the development server
python3 manage.py runserver
```

Open http://127.0.0.1:8000/

## Demo Credentials

| Username     | Password     | Role              |
|--------------|--------------|-------------------|
| alice.smith  | Password123! | Engineer          |
| bob.jones    | Password123! | Engineer          |
| tom.leader   | Password123! | Team Leader       |
| diana.dept   | Password123! | Department Leader |
| sam.senior   | Password123! | Senior Manager    |
| admin        | admin123     | Django Admin      |

Django admin panel: http://127.0.0.1:8000/admin/

## Running Tests

```bash
python3 manage.py test myapp --verbosity=2
```
All 20 tests should pass.

## Architecture Notes

- `UserProfile` extends Django's built-in `User` via OneToOne, adding role, team, and department fields.
- `dashboard_view` acts as a router — superusers go to `/admin/`, all other roles are dispatched to their respective dashboard view.
- Votes are unique per `(user, session, card)` — re-submitting updates the existing vote rather than creating a duplicate.
- After voting on all 10 cards, users are automatically redirected to their summary page with a confirmation message.
- Department Leaders see full team breakdowns within their own department, and aggregate-only totals for other departments.
- Senior Managers can drill down to per-card team breakdowns across the entire organisation.
- The navbar avatar shows first + last name initials when available, falling back to the first character of the username (e.g. admin → A).

## Notes on Seed Data

The seed script creates 5 demo engineers on **Sky Go Team** with Q1 2025 votes already populated. If you register a new account on the same team, the Team Summary section will include those seeded votes — this is correct behaviour, as team summaries aggregate all team members. To clear seed votes run:

```bash
python3 manage.py shell -c "from myapp.models import Vote, Session; Vote.objects.filter(session=Session.objects.get(name='Q1 2025')).delete()"
```