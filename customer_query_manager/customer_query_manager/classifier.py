"""Rule-based query classifier and FAQ auto-responder.

No external ML libraries needed. Each category has weighted keywords; the
category with the highest score wins. Priority is detected from urgency words.
The FAQ matcher uses simple token-overlap (Jaccard) similarity.
"""
import re

CATEGORIES = {
    "Billing": ["bill", "billing", "invoice", "charge", "charged", "payment", "refund",
                "price", "pricing", "subscription", "fee", "credit", "card", "paid"],
    "Technical Support": ["error", "bug", "crash", "crashes", "not working", "broken", "login",
                          "password", "reset", "install", "update", "slow", "issue", "failed",
                          "cannot", "can't", "unable", "app", "website", "server"],
    "Shipping": ["delivery", "deliver", "shipping", "shipment", "courier", "tracking",
                 "package", "parcel", "delayed", "late", "dispatch", "address", "order"],
    "Returns & Exchange": ["return", "exchange", "replace", "replacement", "damaged",
                           "defective", "wrong item", "warranty", "cancel", "cancellation"],
    "Account": ["account", "profile", "email", "username", "register", "signup", "sign up",
                "delete account", "verification", "verify"],
    "General Inquiry": ["information", "info", "hours", "contact", "location", "support",
                        "how", "what", "when", "where", "help"],
}

URGENT_WORDS = ["urgent", "asap", "immediately", "emergency", "critical", "fraud",
                "unauthorized", "hacked", "stolen", "right now", "legal", "lawsuit"]
HIGH_WORDS = ["not working", "failed", "broken", "double charged", "charged twice",
              "damaged", "defective", "complaint", "angry", "worst", "unacceptable"]

NEGATIVE_WORDS = ["angry", "worst", "terrible", "horrible", "unacceptable", "disappointed",
                  "bad", "awful", "useless", "frustrated", "hate", "waste"]
POSITIVE_WORDS = ["thanks", "thank", "great", "good", "love", "excellent", "happy", "awesome"]

FAQS = [
    {"q": "How can I reset my password?",
     "a": "Go to the login page and click 'Forgot password'. Enter your registered email and "
          "we will send you a reset link valid for 30 minutes."},
    {"q": "How do I track my order?",
     "a": "Use the tracking number from your shipping confirmation email on our tracking page. "
          "Orders usually arrive within 3-7 business days."},
    {"q": "What is your refund policy?",
     "a": "Refunds are issued to the original payment method within 5-7 business days after "
          "we receive the returned item or approve the cancellation."},
    {"q": "How do I return or exchange a product?",
     "a": "Returns and exchanges are accepted within 30 days of delivery. Keep the item unused "
          "in original packaging and raise a return request from your orders page."},
    {"q": "I was charged twice for my payment.",
     "a": "Duplicate charges are usually temporary authorisations that drop off in 3-5 business "
          "days. If it remains after that, share your transaction ID and we will refund the extra amount."},
    {"q": "How can I change my account email or details?",
     "a": "Open Profile > Settings > Account Details, update your information and verify the "
          "new email address using the confirmation link."},
    {"q": "What are your support hours?",
     "a": "Our support team is available Monday to Saturday, 9 AM to 6 PM IST."},
    {"q": "The app keeps crashing or is not working.",
     "a": "Please update to the latest version, restart your device, and clear the app cache. "
          "If the problem continues, reply with your device model and app version."},
    {"q": "I received a damaged or wrong item.",
     "a": "We are sorry about that! Please share a photo of the item and your order number. "
          "We will arrange a free replacement or full refund."},
]

STOPWORDS = set("a an the is are was were am i my me we our you your to of for in on at and or "
                "it this that with have has had be do does did can could would should will "
                "how what when where why please hi hello".split())


def tokenize(text):
    return [t for t in re.findall(r"[a-z0-9']+", text.lower()) if t not in STOPWORDS]


def classify_category(text):
    t = text.lower()
    scores = {}
    for cat, words in CATEGORIES.items():
        score = 0
        for w in words:
            if " " in w:
                score += 2 * t.count(w)
            else:
                score += len(re.findall(r"\b" + re.escape(w) + r"\b", t))
        scores[cat] = score
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "General Inquiry"
    return best


def detect_priority(text):
    t = text.lower()
    if any(w in t for w in URGENT_WORDS):
        return "Urgent"
    if any(w in t for w in HIGH_WORDS):
        return "High"
    return "Normal"


def detect_sentiment(text):
    t = text.lower()
    neg = sum(w in t for w in NEGATIVE_WORDS)
    pos = sum(w in t for w in POSITIVE_WORDS)
    if neg > pos:
        return "Negative"
    if pos > neg:
        return "Positive"
    return "Neutral"


def find_faq_answer(text, threshold=0.18):
    """Return (answer, score) for the best FAQ match, or (None, score)."""
    q_tokens = set(tokenize(text))
    if not q_tokens:
        return None, 0.0
    best, best_score = None, 0.0
    for faq in FAQS:
        f_tokens = set(tokenize(faq["q"] + " " + faq["a"]))
        inter = len(q_tokens & f_tokens)
        union = len(q_tokens | f_tokens)
        score = inter / union if union else 0.0
        # reward overlap with the FAQ question itself
        q_only = set(tokenize(faq["q"]))
        score += 0.5 * (len(q_tokens & q_only) / len(q_only)) if q_only else 0
        if score > best_score:
            best, best_score = faq, score
    if best and best_score >= threshold:
        return best["a"], round(best_score, 2)
    return None, round(best_score, 2)


def analyze(text):
    answer, score = find_faq_answer(text)
    return {
        "category": classify_category(text),
        "priority": detect_priority(text),
        "sentiment": detect_sentiment(text),
        "auto_reply": answer,
        "confidence": score,
    }
