from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import json
import torch
import logging
from llm_models import classify_sentiment, summarize_pain_points, summarize_praises, generate_recommendation
import os

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Database configuration with absolute path
DATABASE = os.path.join(os.path.dirname(__file__), 'feedback.db')

# Initialize database
def init_db():
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    feedback_text TEXT NOT NULL,
                    rating INTEGER NOT NULL,
                    CHECK(rating BETWEEN 1 AND 5)
                )
            ''')
            conn.commit()
            logger.info("Database initialized successfully")
    except sqlite3.Error as e:
        logger.error(f"Failed to initialize database: {str(e)}")

# Helper function to get a database connection
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn

# Initialize database on app start
init_db()

# Helper function to generate default classifications based on rating
def get_default_classifications(feedbacks):
    classifications = []
    for fb in feedbacks:
        rating = fb['rating']
        sentiment = 'Positive' if rating >= 4 else 'Neutral' if rating == 3 else 'Negative'
        classifications.append(f"{fb['name']}: {sentiment}")
    return classifications

# Homepage route: Display form and feedback cards
@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, feedback_text, rating FROM feedback ORDER BY id DESC')
            feedbacks = cursor.fetchall()

            # Generate default classifications for initial display
            classifications = get_default_classifications(feedbacks)

            # Handle feedback submission
            if request.method == 'POST' and 'name' in request.form:
                name = request.form['name'].strip()
                feedback_text = request.form['feedback_text'].strip()
                rating = request.form.get('rating')

                if not name or not feedback_text:
                    logger.error("Submission failed: Name and feedback text are required")
                    return render_template('index.html', feedbacks=feedbacks, classifications=classifications, error='Name and feedback text are required', show_feedback=False)
                if not rating or not rating.isdigit():
                    logger.error("Submission failed: Rating is required and must be a number")
                    return render_template('index.html', feedbacks=feedbacks, classifications=classifications, error='Rating is required and must be a number', show_feedback=False)
                rating = int(rating)
                if rating < 1 or rating > 5:
                    logger.error("Submission failed: Rating must be between 1 and 5")
                    return render_template('index.html', feedbacks=feedbacks, classifications=classifications, error='Rating must be between 1 and 5', show_feedback=False)

                try:
                    cursor.execute('INSERT INTO feedback (name, feedback_text, rating) VALUES (?, ?, ?)',
                                  (name, feedback_text, rating))
                    conn.commit()
                    logger.info(f"Feedback inserted: {name}, {feedback_text}, {rating}")
                    cursor.execute('SELECT * FROM feedback WHERE id = last_insert_rowid()')
                    verify = cursor.fetchone()
                    if verify:
                        logger.info(f"Verified insertion: {verify['name']}, {verify['feedback_text']}, {verify['rating']}")
                    else:
                        logger.error("Verification failed: No data inserted")
                except sqlite3.Error as e:
                    logger.error(f"Failed to insert feedback: {str(e)}")
                    return render_template('index.html', feedbacks=feedbacks, classifications=classifications, error=f"Failed to save feedback: {str(e)}", show_feedback=False)

                return redirect(url_for('index'))

            return render_template('index.html', feedbacks=feedbacks, classifications=classifications, show_feedback=False)
    except sqlite3.Error as e:
        logger.error(f"Database error in index: {str(e)}")
        return render_template('index.html', feedbacks=[], classifications=[], error=f"Database error: {str(e)}", show_feedback=False)
    except Exception as e:
        logger.error(f"Unexpected error in index: {str(e)}")
        return render_template('index.html', feedbacks=[], classifications=[], error=f"Unexpected error: {str(e)}", show_feedback=False)

# Analyze feedback route
@app.route('/analyze', methods=['POST'])
def analyze_feedback():
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT name, feedback_text, rating FROM feedback')
            feedbacks = cursor.fetchall()

        classifications = []
        pain_points = []
        praises = []
        mixed_feedbacks = []
        all_text = ""

        for fb in feedbacks:
            name = fb['name']
            text = fb['feedback_text']
            rating = fb['rating']
            classification = classify_sentiment(text, rating)
            classifications.append(f"{name}: {classification}")
            if classification == 'Positive':
                praises.append(text)
            elif classification == 'Negative':
                pain_points.append(text)
            elif classification == 'Mixed':
                mixed_feedbacks.append(text)
            all_text += f"{name}: {text} (Rating: {rating})\n"

        # Summarize pain points, praises, and mixed feedback
        pain_summary = summarize_pain_points(pain_points + mixed_feedbacks)
        praise_summary = summarize_praises(praises + mixed_feedbacks)

        # Generate recommendation, passing classifications to guide logic
        recommendation = generate_recommendation(all_text, classifications)

        return render_template('index.html', feedbacks=feedbacks, classifications=classifications,
                               pain_summary=pain_summary, praise_summary=praise_summary,
                               recommendation=recommendation, show_feedback=True)
    except sqlite3.Error as e:
        logger.error(f"Database error in analyze_feedback: {str(e)}")
        return render_template('index.html', feedbacks=[], classifications=[], error=f"Database error: {str(e)}", show_feedback=False)
    except Exception as e:
        logger.error(f"Error in analyze_feedback: {str(e)}")
        return render_template('index.html', feedbacks=[], classifications=[], error=f"Analysis failed: {str(e)}", show_feedback=False)

# API: GET /feedback - Fetch all feedback
@app.route('/feedback', methods=['GET'])
def get_feedback():
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, feedback_text, rating FROM feedback ORDER BY id DESC')
            feedbacks = cursor.fetchall()
        feedback_list = [{'id': fb['id'], 'name': fb['name'], 'feedback_text': fb['feedback_text'], 'rating': fb['rating']} for fb in feedbacks]
        return jsonify({'success': True, 'feedbacks': feedback_list})
    except sqlite3.Error as e:
        logger.error(f"Database error in get_feedback: {str(e)}")
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)