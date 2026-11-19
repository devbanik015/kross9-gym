import unittest
import os
import sys
import tempfile
import datetime
import json

# Ensure parent directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import Config

# Create a temporary test database file for isolation
test_db_fd, test_db_path = tempfile.mkstemp(suffix=".db")
os.close(test_db_fd)
Config.DATABASE_PATH = test_db_path

from app import app
from database import init_db, get_db
from automations import run_daily_automations, generate_whatsapp_url, render_template

class Kross9GymTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        app.config["DATABASE_PATH"] = test_db_path
        with app.app_context():
            init_db(seed=True)

    @classmethod
    def tearDownClass(cls):
        try:
            if os.path.exists(test_db_path):
                os.remove(test_db_path)
        except Exception:
            pass

    def setUp(self):
        self.client = app.test_client()

    # -------------------------------------------------------------------------
    # 1. Public Pages & Contact
    # -------------------------------------------------------------------------
    def test_homepage_loads(self):
        """Test public homepage renders with Kross 9 Gym branding and Cooch Behar info."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        content = response.data.decode("utf-8")
        self.assertIn("KROSS 9", content)
        self.assertIn("Cooch Behar", content)
        self.assertIn("Bakultala More", content)
        self.assertIn("+91 74780 13363", content)

    def test_trial_pass_generation_and_view(self):
        """Test free 1-day pass booking and digital pass page rendering."""
        payload = {
            "name": "Test Athlete",
            "phone": "9876543210",
            "email": "athlete@test.com",
            "workout_date": "2026-11-25"
        }
        res = self.client.post("/api/trial-pass", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        pass_code = data["pass_code"]
        self.assertTrue(pass_code.startswith("K9-PASS-"))

        # View pass page
        view_res = self.client.get(f"/pass/{pass_code}")
        self.assertEqual(view_res.status_code, 200)
        self.assertIn(pass_code, view_res.data.decode("utf-8"))
        self.assertIn("Test Athlete", view_res.data.decode("utf-8"))

    def test_contact_form_submission(self):
        """Test contact inquiry submission."""
        payload = {
            "name": "Inquiry User",
            "phone": "9812345678",
            "email": "inquiry@test.com",
            "message": "Interested in 6 months membership and locker rental"
        }
        res = self.client.post("/api/contact", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")

    # -------------------------------------------------------------------------
    # 2. Admin & CRM Pages
    # -------------------------------------------------------------------------
    def test_admin_pages_load(self):
        """Test admin dashboard, members CRM, lockers, and automations console load."""
        for path in ["/admin", "/admin/members", "/admin/lockers", "/admin/automations"]:
            res = self.client.get(path)
            self.assertEqual(res.status_code, 200, f"Failed on path {path}")

    def test_api_stats(self):
        """Test stats endpoint returns key KPIs."""
        res = self.client.get("/api/stats")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("active_members", data)
        self.assertIn("occupied_lockers", data)

    # -------------------------------------------------------------------------
    # 3. Member CRUD Operations
    # -------------------------------------------------------------------------
    def test_member_crud_flow(self):
        """Test complete member lifecycle: create -> read -> update -> delete."""
        today = datetime.date.today().isoformat()
        end_date = (datetime.date.today() + datetime.timedelta(days=90)).isoformat()

        # Create
        new_member = {
            "name": "Tanmoy Roy",
            "phone": "9832001122",
            "email": "tanmoy@test.com",
            "plan_name": "Quarterly Pro",
            "plan_amount": 3999,
            "start_date": today,
            "end_date": end_date,
            "locker_number": "25",
            "locker_end_date": end_date,
            "notes": "Testing CRUD flow"
        }
        create_res = self.client.post("/api/members", json=new_member)
        self.assertEqual(create_res.status_code, 201)
        member_id = create_res.get_json()["member_id"]

        # Read
        get_res = self.client.get(f"/api/members/{member_id}")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.get_json()["name"], "Tanmoy Roy")
        self.assertEqual(get_res.get_json()["locker_number"], 25)

        # Update
        update_payload = {
            "name": "Tanmoy Roy Updated",
            "phone": "9832001122",
            "plan_name": "Quarterly Pro",
            "status": "active",
            "start_date": today,
            "end_date": end_date,
            "locker_number": "25",
            "locker_end_date": end_date
        }
        update_res = self.client.put(f"/api/members/{member_id}", json=update_payload)
        self.assertEqual(update_res.status_code, 200)

        # Verify update
        get_res2 = self.client.get(f"/api/members/{member_id}")
        self.assertEqual(get_res2.get_json()["name"], "Tanmoy Roy Updated")

        # Delete
        del_res = self.client.delete(f"/api/members/{member_id}")
        self.assertEqual(del_res.status_code, 200)

        # Verify deletion
        get_res3 = self.client.get(f"/api/members/{member_id}")
        self.assertEqual(get_res3.status_code, 404)

    # -------------------------------------------------------------------------
    # 4. Locker Bay Operations
    # -------------------------------------------------------------------------
    def test_locker_bay_listing_and_assignment(self):
        """Test locker listing, assignment, and release."""
        res = self.client.get("/api/lockers")
        self.assertEqual(res.status_code, 200)
        lockers = res.get_json()["lockers"]
        self.assertEqual(len(lockers), 30)

        # Assign Locker #3 to member 1
        assign_payload = {
            "locker_number": 3,
            "member_id": 1,
            "end_date": "2026-12-31"
        }
        assign_res = self.client.post("/api/lockers/assign", json=assign_payload)
        self.assertEqual(assign_res.status_code, 200)

        # Verify assignment in lockers list
        res2 = self.client.get("/api/lockers")
        locker3 = [l for l in res2.get_json()["lockers"] if l["locker_number"] == 3][0]
        self.assertEqual(locker3["status"], "assigned")
        self.assertEqual(locker3["member_id"], 1)

        # Release Locker #3
        release_res = self.client.post("/api/lockers/release", json={"locker_number": 3})
        self.assertEqual(release_res.status_code, 200)

        # Verify released
        res3 = self.client.get("/api/lockers")
        locker3_rel = [l for l in res3.get_json()["lockers"] if l["locker_number"] == 3][0]
        self.assertEqual(locker3_rel["status"], "available")
        self.assertIsNone(locker3_rel["member_id"])

    # -------------------------------------------------------------------------
    # 5. AUTOMATIONS ENGINE & EXPIRATION TRIGGERS
    # -------------------------------------------------------------------------
    def test_subscription_and_locker_automation_scan(self):
        """Test automated detection of expiring subscriptions and lockers."""
        # Clean any existing notification logs for a fresh test run
        conn = get_db()
        conn.execute("DELETE FROM notification_logs")
        conn.commit()
        conn.close()

        # Run automations for today
        result = run_daily_automations()
        self.assertEqual(result["status"], "success")
        self.assertGreater(result["messages_generated_count"], 0)

        # Check notification types generated
        generated_triggers = [msg["trigger_type"] for msg in result["messages"]]

        # Priya Sen (expiring in 3 days) -> sub_warning_3d
        self.assertIn("sub_warning_3d", generated_triggers)

        # Sourav Chakraborty (expiring in 1 day) -> sub_warning_1d
        self.assertIn("sub_warning_1d", generated_triggers)

        # Aniket Ghosh (expiring today) -> sub_expired
        self.assertIn("sub_expired", generated_triggers)

        # Sneha Paul (locker expiring in 3 days) -> locker_warning_3d
        self.assertIn("locker_warning_3d", generated_triggers)

        # Subhashish Barman (locker expired today) -> locker_expired
        self.assertIn("locker_expired", generated_triggers)

        # Verify WhatsApp URL format
        for msg in result["messages"]:
            if msg["channel"] == "whatsapp":
                self.assertTrue(msg["whatsapp_url"].startswith("https://wa.me/"))
                self.assertIn("text=", msg["whatsapp_url"])

    def test_automation_deduplication(self):
        """Test that running the audit twice on the same day does not produce duplicate messages."""
        # Initial run generates notifications
        first_run = run_daily_automations()
        self.assertGreater(first_run["messages_generated_count"], 0)
        
        # Second run on the same day should generate 0 new messages due to deduplication
        second_run = run_daily_automations()
        self.assertEqual(second_run["messages_generated_count"], 0)

    def test_template_rendering_and_customization(self):
        """Test placeholder interpolation in templates."""
        raw_template = "Hi {{name}}, your {{plan}} membership ends on {{end_date}} at {{gym_name}}."
        context = {
            "name": "Bikash",
            "plan": "Annual",
            "end_date": "2026-12-31",
            "gym_name": "Kross 9 Gym"
        }
        rendered = render_template(raw_template, context)
        self.assertEqual(rendered, "Hi Bikash, your Annual membership ends on 2026-12-31 at Kross 9 Gym.")

if __name__ == "__main__":
    unittest.main()
