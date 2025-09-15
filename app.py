from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_restful import Api, Resource, reqparse
import sqlite3
import logging
import re
import os
from llm_models import (
    classify_sentiment,
    summarize_pain_points,
    summarize_praises,
    generate_recommendation,
    NEGATIVE_KEYWORDS,
    POSITIVE_KEYWORDS,
)

app = Flask(__name__)
api = Api(app)

# ---------------------------
# Logging
# ---------------------------
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ---------------------------
# Database setup
# ---------------------------
DATABASE = os.path.join(os.path.dirname(__file__), "feedback.db")


def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            feedback_text TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5)
        )
    """
    )
    conn.commit()
    conn.close()


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


init_db()

# ---------------------------
# Helper
# ---------------------------
def get_default_classifications(feedbacks):
    classifications = []
    for fb in feedbacks:
        sentiment = classify_sentiment(fb["feedback_text"], fb["rating"])
        classifications.append(f"{fb['name']}: {sentiment}")
    return classifications


# ---------------------------
# Frontend Routes
# ---------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    success_message = None

    with get_db() as conn:
        cursor = conn.cursor()

        if request.method == "POST" and "name" in request.form:
            name = request.form["name"].strip()
            feedback_text = request.form["feedback_text"].strip()
            rating = request.form.get("rating")

            if not (name and feedback_text and rating and rating.isdigit()):
                cursor.execute(
                    "SELECT id, name, feedback_text, rating FROM feedback ORDER BY id DESC"
                )
                feedbacks = cursor.fetchall()
                classifications = get_default_classifications(feedbacks)
                return render_template(
                    "index.html",
                    feedbacks=feedbacks,
                    classifications=classifications,
                    error="⚠️ All fields are required",
                    show_feedback=False,
                )

            rating = int(rating)
            if rating < 1 or rating > 5:
                cursor.execute(
                    "SELECT id, name, feedback_text, rating FROM feedback ORDER BY id DESC"
                )
                feedbacks = cursor.fetchall()
                classifications = get_default_classifications(feedbacks)
                return render_template(
                    "index.html",
                    feedbacks=feedbacks,
                    classifications=classifications,
                    error="⚠️ Rating must be between 1 and 5",
                    show_feedback=False,
                )

            # Insert feedback
            cursor.execute(
                "INSERT INTO feedback (name, feedback_text, rating) VALUES (?, ?, ?)",
                (name, feedback_text, rating),
            )
            conn.commit()
            success_message = "✅ Submitted successfully!"

        cursor.execute(
            "SELECT id, name, feedback_text, rating FROM feedback ORDER BY id DESC"
        )
        feedbacks = cursor.fetchall()
        classifications = get_default_classifications(feedbacks)

    return render_template(
        "index.html",
        feedbacks=feedbacks,
        classifications=classifications,
        success_message=success_message,
        show_feedback=False,
    )


@app.route("/analyze", methods=["POST"])
def analyze_feedback():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, feedback_text, rating FROM feedback")
        feedbacks = cursor.fetchall()

    all_text = ""
    praises_list, pains_list = [], []
    classifications = []

    for fb in feedbacks:
        name, text, rating = fb["name"], fb["feedback_text"], fb["rating"]
        classification = classify_sentiment(text, rating)
        classifications.append(f"{name}: {classification}")

        all_text += f"{name}: {text} (Rating: {rating})\n"

        # Split sentences and assign to praise or pain
        sentences = re.split(r"[.!?]", text)
        for s in sentences:
            s_clean = s.strip()
            if not s_clean:
                continue
            if any(kw in s_clean.lower() for kw in NEGATIVE_KEYWORDS):
                pains_list.append(s_clean)
            elif any(kw in s_clean.lower() for kw in POSITIVE_KEYWORDS):
                praises_list.append(s_clean)

    pain_summary = summarize_pain_points(pains_list)
    praise_summary = summarize_praises(praises_list)
    recommendation = generate_recommendation(all_text, classifications)

    return render_template(
        "index.html",
        feedbacks=feedbacks,
        classifications=classifications,
        pain_summary=pain_summary,
        praise_summary=praise_summary,
        recommendation=recommendation,
        show_feedback=True,
    )


# ---------------------------
# API (Flask-RESTful)
# ---------------------------
feedback_parser = reqparse.RequestParser()
feedback_parser.add_argument("name", type=str, required=True, help="Name is required")
feedback_parser.add_argument(
    "feedback_text", type=str, required=True, help="Feedback is required"
)
feedback_parser.add_argument(
    "rating", type=int, required=True, help="Rating is required (1–5)"
)


class FeedbackList(Resource):
    def get(self):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, feedback_text, rating FROM feedback ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "id": r["id"],
                "name": r["name"],
                "feedback_text": r["feedback_text"],
                "rating": r["rating"],
            }
            for r in rows
        ]

    def post(self):
        args = feedback_parser.parse_args()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO feedback (name, feedback_text, rating) VALUES (?, ?, ?)",
            (args["name"], args["feedback_text"], args["rating"]),
        )
        conn.commit()
        conn.close()
        return {"success": True, "message": "Feedback added"}, 201


class Analyze(Resource):
    def post(self):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name, feedback_text, rating FROM feedback")
        rows = cursor.fetchall()
        conn.close()

        feedbacks = [
            {"name": r["name"], "feedback_text": r["feedback_text"], "rating": r["rating"]}
            for r in rows
        ]
        classifications, all_text = [], ""

        for fb in feedbacks:
            classification = classify_sentiment(fb["feedback_text"], fb["rating"])
            classifications.append(f"{fb['name']}: {classification}")
            all_text += f"{fb['name']}: {fb['feedback_text']} (Rating: {fb['rating']})\n"

        pain_summary = summarize_pain_points(
            [f["feedback_text"] for f in feedbacks if classify_sentiment(f["feedback_text"], f["rating"]) == "Negative"]
        )
        praise_summary = summarize_praises(
            [f["feedback_text"] for f in feedbacks if classify_sentiment(f["feedback_text"], f["rating"]) == "Positive"]
        )
        recommendation = generate_recommendation(all_text, classifications)

        return {
            "success": True,
            "classifications": classifications,
            "pain_summary": pain_summary,
            "praise_summary": praise_summary,
            "recommendation": recommendation,
        }


api.add_resource(FeedbackList, "/api/feedback")
api.add_resource(Analyze, "/api/analyze")

if __name__ == "__main__":
    app.run(debug=True)
