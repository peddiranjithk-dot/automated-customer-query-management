"""Quick tests: python -m unittest test_app.py"""
import os
import tempfile
import unittest
from pathlib import Path

import database as db

db.DB_PATH = Path(tempfile.mkdtemp()) / "test.db"

import app as app_module  # noqa: E402  (imported after DB path override)
from classifier import analyze  # noqa: E402


class ClassifierTests(unittest.TestCase):
    def test_billing(self):
        r = analyze("I was charged twice for my invoice payment")
        self.assertEqual(r["category"], "Billing")
        self.assertEqual(r["priority"], "High")

    def test_urgent(self):
        self.assertEqual(analyze("My account was hacked, urgent!")["priority"], "Urgent")

    def test_faq_match(self):
        r = analyze("How can I reset my password?")
        self.assertIsNotNone(r["auto_reply"])

    def test_no_faq_for_unknown(self):
        r = analyze("Do you sponsor marathon events in Pune?")
        self.assertIsNone(r["auto_reply"])


class AppTests(unittest.TestCase):
    def setUp(self):
        db.DB_PATH = Path(tempfile.mkdtemp()) / "t.db"
        db.init_db()
        self.client = app_module.app.test_client()

    def test_submit_and_track(self):
        resp = self.client.post("/submit", data={
            "name": "Asha", "email": "asha@example.com",
            "subject": "Password", "message": "How can I reset my password please?"})
        self.assertEqual(resp.status_code, 302)
        ticket = resp.headers["Location"].rsplit("/", 1)[-1]
        resp = self.client.post("/track", data={"ticket_id": ticket})
        self.assertIn(ticket.encode(), resp.data)

    def test_validation(self):
        resp = self.client.post("/submit", data={"name": "", "email": "bad",
                                                 "subject": "x", "message": "short"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"valid email", resp.data)

    def test_admin_protected(self):
        self.assertEqual(self.client.get("/admin").status_code, 302)
        self.client.post("/admin/login", data={"username": "admin", "password": "admin123"})
        self.assertEqual(self.client.get("/admin").status_code, 200)


if __name__ == "__main__":
    unittest.main()
