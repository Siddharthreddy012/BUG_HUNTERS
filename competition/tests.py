from django.test import TestCase, Client
from django.contrib.auth.models import User
from accounts.models import ParticipantProfile
from competition.models import (
    CompetitionSettings, ParticipantRound, Question, MCQOption,
    CodingChallenge, FlowchartQuestion, TestCase as ModelTestCase,
    AnswerSubmission, CodeSubmission, TabSwitchViolation
)
from competition.services import (
    initialize_participant_competition,
    check_round_accessibility,
    evaluate_and_finalize_round_1,
    admin_verify_round_2,
    admin_verify_round_3,
    recalculate_leaderboard
)
from results.models import RoundResult

class CompetitionPlatformTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Setup settings
        self.settings = CompetitionSettings.get_settings()
        self.settings.r1_qualifying_marks = 9
        self.settings.r2_qualifying_marks = 15
        self.settings.save()

        # Create admin user
        self.admin_user = User.objects.create_superuser('admin', 'admin@bughunters.edu', 'adminpass')
        ParticipantProfile.objects.create(
            user=self.admin_user,
            full_name="Admin Convenor",
            roll_number="ADM001",
            department="Computer Science & Engineering"
        )

        # Create participant user
        self.student = User.objects.create_user('student1', 'student1@college.edu', 'studentpass')
        self.student_profile = ParticipantProfile.objects.create(
            user=self.student,
            full_name="Jane Doe",
            roll_number="22CS099",
            department="Computer Science & Engineering",
            year="3rd Year"
        )

        # Initialize rounds
        initialize_participant_competition(self.student)

    def test_initial_round_states(self):
        """Test that Round 1 is unlocked by default, and Rounds 2 & 3 are locked."""
        r1_access, _, r1 = check_round_accessibility(self.student, 1)
        r2_access, _, r2 = check_round_accessibility(self.student, 2)
        r3_access, _, r3 = check_round_accessibility(self.student, 3)

        self.assertTrue(r1_access)
        self.assertFalse(r2_access)
        self.assertFalse(r3_access)

    def test_round_1_qualification_progression(self):
        """Test that qualifying Round 1 unlocks Round 2."""
        r1 = ParticipantRound.objects.get(participant=self.student, round_number=1)
        
        # Create a sample question and answer
        q = Question.objects.create(question_text="Sample Q", category="Python", marks=10.0)
        opt = MCQOption.objects.create(question=q, identifier="A", option_text="Correct", is_correct=True)
        
        AnswerSubmission.objects.create(
            participant_round=r1,
            question=q,
            selected_option=opt,
            is_correct=True,
            marks_awarded=10.0
        )

        is_qual, score = evaluate_and_finalize_round_1(r1)
        self.assertTrue(is_qual)
        self.assertEqual(score, 10.0)

        # Round 2 should now be accessible
        r2_access, _, _ = check_round_accessibility(self.student, 2)
        self.assertTrue(r2_access)

        # Round 3 should still be locked until R2 is verified by admin
        r3_access, _, _ = check_round_accessibility(self.student, 3)
        self.assertFalse(r3_access)

    def test_round_2_verification_progression(self):
        """Test that Round 2 verification unlocks Round 3."""
        # Qualify R1 first
        r1 = ParticipantRound.objects.get(participant=self.student, round_number=1)
        r1.score = 12.0
        r1.status = 'QUALIFIED'
        r1.save()

        r2 = ParticipantRound.objects.get(participant=self.student, round_number=2)
        r2.score = 20.0
        r2.status = 'UNDER_EVALUATION'
        r2.save()

        # Admin verifies Round 2
        is_verified = admin_verify_round_2(r2, self.admin_user, remarks="All 4 test cases verified.")
        self.assertTrue(is_verified)
        self.assertEqual(r2.status, 'VERIFIED')

        # Round 3 should now be accessible
        r3_access, _, _ = check_round_accessibility(self.student, 3)
        self.assertTrue(r3_access)

    def test_tab_switch_violation_recording(self):
        """Test API for tab switch detection and counter."""
        self.client.login(username='student1', password='studentpass')
        response = self.client.post(
            '/competition/api/log-violation/',
            data='{"round_number": 1, "event_type": "tab_switch"}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['violation_count'], 1)

        # Check DB
        violations = TabSwitchViolation.objects.filter(participant=self.student)
        self.assertEqual(violations.count(), 1)

    def test_public_pages_and_navigation(self):
        """Test HTTP responses of key pages."""
        pages = ['/', '/about/', '/rules/', '/rounds/', '/leaderboard/', '/login/', '/register/']
        for url in pages:
            res = self.client.get(url)
            self.assertEqual(res.status_code, 200, f"Page {url} failed with status {res.status_code}")

    def test_dashboard_requires_login(self):
        """Test dashboard access redirect for anonymous users."""
        res = self.client.get('/dashboard/')
        self.assertEqual(res.status_code, 302)

    def test_admin_portal_requires_staff(self):
        """Test admin portal blocks regular students."""
        self.client.login(username='student1', password='studentpass')
        res = self.client.get('/competition/portal/admin/')
        self.assertEqual(res.status_code, 302)

        # Staff user should get 200
        self.client.login(username='admin', password='adminpass')
        res_admin = self.client.get('/competition/portal/admin/')
        self.assertEqual(res_admin.status_code, 200)
