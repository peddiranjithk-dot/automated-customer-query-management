"""Automated Customer Query Management System - Flask app.

Run:  python app.py   then open http://127.0.0.1:5000
Admin login: see ADMIN_USER / ADMIN_PASS below (or set env variables).
"""
import os
import re
from functools import wraps

from flask import (Flask, flash, redirect, render_template, request, session, url_for)

import database as db
from classifier import analyze, CATEGORIES

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-in-production")

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin123")
STATUSES = ["Open", "In Progress", "Resolved", "Closed", "Auto-Resolved"]
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

db.init_db()


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return wrapper


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/submit", methods=["GET", "POST"])
def submit():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        errors = []
        if len(name) < 2:
            errors.append("Please enter your name.")
        if not EMAIL_RE.match(email):
            errors.append("Please enter a valid email address.")
        if len(subject) < 3:
            errors.append("Subject is too short.")
        if len(message) < 10:
            errors.append("Please describe your query in at least 10 characters.")
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("submit.html", form=request.form)

        analysis = analyze(f"{subject}. {message}")
        ticket_id = db.create_query(name, email, subject, message, analysis)
        return redirect(url_for("result", ticket_id=ticket_id))
    return render_template("submit.html", form={})


@app.route("/result/<ticket_id>")
def result(ticket_id):
    q = db.get_by_ticket(ticket_id)
    if not q:
        flash("Ticket not found.", "error")
        return redirect(url_for("track"))
    return render_template("result.html", q=q)


@app.route("/track", methods=["GET", "POST"])
def track():
    q = None
    if request.method == "POST":
        ticket_id = request.form.get("ticket_id", "").strip()
        q = db.get_by_ticket(ticket_id)
        if not q:
            flash("No ticket found with that ID.", "error")
    return render_template("track.html", q=q)


# ---------------- Admin ----------------
@app.route("/admin/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if (request.form.get("username") == ADMIN_USER
                and request.form.get("password") == ADMIN_PASS):
            session["admin"] = True
            return redirect(request.args.get("next") or url_for("dashboard"))
        flash("Invalid credentials.", "error")
    return render_template("login.html")


@app.route("/admin/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/admin")
@login_required
def dashboard():
    status = request.args.get("status") or None
    category = request.args.get("category") or None
    search = request.args.get("search") or None
    queries = db.list_queries(status, category, search)
    return render_template("dashboard.html", queries=queries, stats=db.stats(),
                           statuses=STATUSES, categories=list(CATEGORIES.keys()),
                           f={"status": status, "category": category, "search": search or ""})


@app.route("/admin/query/<int:qid>", methods=["GET", "POST"])
@login_required
def query_detail(qid):
    q = db.get_by_id(qid)
    if not q:
        flash("Query not found.", "error")
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        status = request.form.get("status", q["status"])
        if status not in STATUSES:
            status = q["status"]
        db.update_query(qid, status, request.form.get("agent_reply", "").strip())
        flash("Query updated.", "success")
        return redirect(url_for("query_detail", qid=qid))
    return render_template("detail.html", q=q, statuses=STATUSES)


if __name__ == "__main__":
    app.run(debug=True)
