# Automated Customer Query Management

A simple Flask + SQLite web app that automatically handles customer queries.

## Features
- Customers submit a query and receive a unique **ticket ID**
- **Auto-categorisation** (Billing, Technical Support, Shipping, Returns & Exchange, Account, General Inquiry)
- **Priority detection** (Urgent / High / Normal) and basic **sentiment** tagging
- **Automatic FAQ reply** when the query matches a known FAQ (status becomes *Auto-Resolved*)
- Customers can **track** ticket status with their ticket ID
- **Admin dashboard** (login required): stats, filter/search, reply to and update tickets

## Setup
```bash
cd customer_query_manager
python -m venv venv
# Windows: venv\Scripts\activate     Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

Admin login: `admin` / `admin123`
(change with env variables `ADMIN_USER`, `ADMIN_PASS`, `SECRET_KEY`)

## Run tests
```bash
python -m unittest test_app.py
```

## Project structure
```
app.py            Flask routes (customer + admin)
classifier.py     Categorisation, priority, sentiment, FAQ matching (edit FAQS here)
database.py       SQLite helpers
templates/        HTML pages
static/style.css  Styling
test_app.py       Unit tests
```

## Ideas to extend
- Send email replies (smtplib), connect a real NLP model, add agent roles, export to CSV.
