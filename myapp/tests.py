"""
Test suite for SKY Health Check Application
Covers: authentication, registration, voting, role-based access, profile management.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Department, Team, UserProfile, HealthCheckCard, Session, Vote


class SetupMixin:
    """Shared fixtures for all test classes."""
    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name="Test Dept")
        self.team = Team.objects.create(name="Test Team", department=self.dept)
        self.card = HealthCheckCard.objects.create(
            title="Easy to Release", description="Releasing is simple.",
            good_description="Fully automated.", bad_description="Manual and risky.",
            order=1
        )
        self.session = Session.objects.create(
            name="Test Session", start_date="2025-01-01", end_date="2025-03-31", is_active=True
        )
        # Engineer user
        self.eng_user = User.objects.create_user(
            username="eng1", password="TestPass123!", first_name="Alice", last_name="Smith"
        )
        UserProfile.objects.create(user=self.eng_user, role='engineer', team=self.team, department=self.dept)
        # Team leader
        self.tl_user = User.objects.create_user(username="tl1", password="TestPass123!")
        UserProfile.objects.create(user=self.tl_user, role='team_leader', team=self.team, department=self.dept)
        # Dept leader
        self.dl_user = User.objects.create_user(username="dl1", password="TestPass123!")
        UserProfile.objects.create(user=self.dl_user, role='dept_leader', department=self.dept)
        # Senior manager
        self.sm_user = User.objects.create_user(username="sm1", password="TestPass123!")
        UserProfile.objects.create(user=self.sm_user, role='senior_manager')


class AuthenticationTests(SetupMixin, TestCase):
    """TC-AUTH-01 to TC-AUTH-05"""

    def test_login_page_loads(self):
        """TC-AUTH-01: Login page is accessible."""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_valid_login(self):
        """TC-AUTH-02: Valid credentials redirect to dashboard."""
        response = self.client.post(reverse('login'), {
            'username': 'eng1', 'password': 'TestPass123!'
        }, follow=True)
        self.assertTrue(response.context['user'].is_authenticated)

    def test_invalid_login(self):
        """TC-AUTH-03: Invalid credentials show error, stay on login page."""
        response = self.client.post(reverse('login'), {
            'username': 'eng1', 'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        messages = list(response.context['messages'])
        self.assertTrue(any('Invalid' in str(m) for m in messages))

    def test_logout(self):
        """TC-AUTH-04: Logout ends session and redirects to login."""
        self.client.login(username='eng1', password='TestPass123!')
        response = self.client.get(reverse('logout'), follow=True)
        self.assertFalse(response.context['user'].is_authenticated)

    def test_dashboard_requires_login(self):
        """TC-AUTH-05: Dashboard redirects unauthenticated users to login."""
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, '/login/?next=/dashboard/')


class RegistrationTests(SetupMixin, TestCase):
    """TC-REG-01 to TC-REG-04"""

    def test_register_page_loads(self):
        """TC-REG-01: Registration page is accessible."""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_successful_registration(self):
        """TC-REG-02: Valid registration creates user and logs them in."""
        response = self.client.post(reverse('register'), {
            'first_name': 'John', 'last_name': 'Doe',
            'username': 'newuser', 'email': 'new@sky.com',
            'password': 'NewPass123!', 'confirm_password': 'NewPass123!',
            'role': 'engineer', 'department': self.dept.pk, 'team': self.team.pk
        }, follow=True)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.assertTrue(response.context['user'].is_authenticated)

    def test_duplicate_username(self):
        """TC-REG-03: Duplicate username returns error."""
        response = self.client.post(reverse('register'), {
            'first_name': 'Alice', 'last_name': 'Smith',
            'username': 'eng1', 'email': 'x@sky.com',
            'password': 'TestPass123!', 'confirm_password': 'TestPass123!',
            'role': 'engineer'
        })
        messages = list(response.context['messages'])
        self.assertTrue(any('taken' in str(m) for m in messages))

    def test_password_mismatch(self):
        """TC-REG-04: Mismatched passwords return error."""
        response = self.client.post(reverse('register'), {
            'first_name': 'Bob', 'last_name': 'X',
            'username': 'bobx', 'email': 'bob@sky.com',
            'password': 'Pass123!', 'confirm_password': 'DifferentPass!',
            'role': 'engineer'
        })
        messages = list(response.context['messages'])
        self.assertTrue(any('match' in str(m) for m in messages))


class VotingTests(SetupMixin, TestCase):
    """TC-VOTE-01 to TC-VOTE-05"""

    def test_voting_page_loads(self):
        """TC-VOTE-01: Voting page loads for authenticated engineer."""
        self.client.login(username='eng1', password='TestPass123!')
        response = self.client.get(reverse('vote_card', args=[self.session.pk, self.card.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Easy to Release')

    def test_submit_vote(self):
        """TC-VOTE-02: Submitting a valid vote saves it to the database."""
        self.client.login(username='eng1', password='TestPass123!')
        self.client.post(reverse('vote_card', args=[self.session.pk, self.card.pk]), {
            'vote': 'green', 'trend': 'improving', 'comment': 'Looking great!', 'save': '1'
        })
        self.assertTrue(Vote.objects.filter(
            user=self.eng_user, session=self.session, card=self.card, vote='green'
        ).exists())

    def test_update_vote(self):
        """TC-VOTE-03: Re-submitting a vote updates rather than duplicates."""
        self.client.login(username='eng1', password='TestPass123!')
        Vote.objects.create(user=self.eng_user, session=self.session, card=self.card, vote='green')
        self.client.post(reverse('vote_card', args=[self.session.pk, self.card.pk]), {
            'vote': 'red', 'trend': 'worse', 'save': '1'
        })
        self.assertEqual(Vote.objects.filter(user=self.eng_user, session=self.session, card=self.card).count(), 1)
        self.assertEqual(Vote.objects.get(user=self.eng_user, session=self.session, card=self.card).vote, 'red')

    def test_invalid_vote_rejected(self):
        """TC-VOTE-04: Submitting an invalid vote value fails."""
        self.client.login(username='eng1', password='TestPass123!')
        self.client.post(reverse('vote_card', args=[self.session.pk, self.card.pk]), {
            'vote': 'purple', 'save': '1'
        })
        self.assertFalse(Vote.objects.filter(user=self.eng_user, session=self.session, card=self.card).exists())

    def test_unauthenticated_cannot_vote(self):
        """TC-VOTE-05: Unauthenticated user cannot access voting page."""
        response = self.client.get(reverse('vote_card', args=[self.session.pk, self.card.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])


class RoleAccessTests(SetupMixin, TestCase):
    """TC-ROLE-01 to TC-ROLE-04: Role-based dashboard routing."""

    def _get_dashboard_template(self, user):
        self.client.login(username=user.username, password='TestPass123!')
        response = self.client.get(reverse('dashboard'))
        return response

    def test_engineer_gets_engineer_dashboard(self):
        """TC-ROLE-01: Engineer user is routed to engineer dashboard."""
        response = self._get_dashboard_template(self.eng_user)
        self.assertContains(response, 'Start Health Check')

    def test_team_leader_gets_tl_dashboard(self):
        """TC-ROLE-02: Team leader is routed to team leader dashboard."""
        response = self._get_dashboard_template(self.tl_user)
        self.assertContains(response, 'Team Leader Dashboard')

    def test_dept_leader_gets_dl_dashboard(self):
        """TC-ROLE-03: Department leader is routed to dept leader dashboard."""
        response = self._get_dashboard_template(self.dl_user)
        self.assertContains(response, 'Department Dashboard')

    def test_senior_manager_gets_sm_dashboard(self):
        """TC-ROLE-04: Senior manager is routed to senior manager dashboard."""
        response = self._get_dashboard_template(self.sm_user)
        self.assertContains(response, 'Senior Manager Dashboard')


class ProfileTests(SetupMixin, TestCase):
    """TC-PROF-01 to TC-PROF-02"""

    def test_profile_page_loads(self):
        """TC-PROF-01: Profile page loads for authenticated user."""
        self.client.login(username='eng1', password='TestPass123!')
        response = self.client.get(reverse('edit_profile'))
        self.assertEqual(response.status_code, 200)

    def test_profile_update(self):
        """TC-PROF-02: Updating profile saves new email."""
        self.client.login(username='eng1', password='TestPass123!')
        self.client.post(reverse('edit_profile'), {
            'first_name': 'Alice', 'last_name': 'Smith', 'email': 'alice.new@sky.com'
        })
        self.eng_user.refresh_from_db()
        self.assertEqual(self.eng_user.email, 'alice.new@sky.com')
