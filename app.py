from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import json  # For JSON responses
import torch  # Explicitly import torch to avoid 'not defined' error
import logging
from llm_models import classify_sentiment, summarize_pain_points, summarize_praises, generate_recommendation

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE = 'feedback.db'

# Initialize database
def init_db():
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

# Helper function to get a database connection
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn

# Initialize database on app start
init_db()

# Homepage route: Display form and feedback cards
@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, feedback_text, rating FROM feedback ORDER BY id DESC')
            feedbacks = cursor.fetchall()

            # Handle feedback submission
            if request.method == 'POST' and 'name' in request.form:
                name = request.form['name'].strip()
                feedback_text = request.form['feedback_text'].strip()
                rating = request.form.get('rating')

                if not name or not feedback_text:
                    logger.error("Submission failed: Name and feedback text are required")
                    return render_template('index.html', feedbacks=feedbacks, error='Name and feedback text are required')
                if not rating or not rating.isdigit():
                    logger.error("Submission failed: Rating is required and must be a number")
                    return render_template('index.html', feedbacks=feedbacks, error='Rating is required and must be a number')
                rating = int(rating)
                if rating < 1 or rating > 5:
                    logger.error("Submission failed: Rating must be between 1 and 5")
                    return render_template('index.html', feedbacks=feedbacks, error='Rating must be between 1 and 5')

                cursor.execute('INSERT INTO feedback (name, feedback_text, rating) VALUES (?, ?, ?)',
                              (name, feedback_text, rating))
                conn.commit()
                logger.info(f"Feedback inserted: {name}, {feedback_text}, {rating}")

                # Verify insertion by fetching the last inserted row
                cursor.execute('SELECT * FROM feedback WHERE id = last_insert_rowid()')
                verify = cursor.fetchone()
                if verify:
                    logger.info(f"Verified insertion: {verify['name']}, {verify['feedback_text']}, {verify['rating']}")
                else:
                    logger.error("Verification failed: No data inserted")

                return redirect(url_for('index'))

            # Handle toggle feedback
            if request.method == 'POST' and 'toggle_feedback' in request.form:
                return render_template('index.html', feedbacks=feedbacks, show_feedback=True)

            return render_template('index.html', feedbacks=feedbacks, show_feedback=False)
    except sqlite3.Error as e:
        logger.error(f"Database error in index: {str(e)}")
        return render_template('index.html', feedbacks=[], error=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in index: {str(e)}")
        return render_template('index.html', feedbacks=[], error=f"Unexpected error: {str(e)}")

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
            all_text += f"{name}: {text} (Rating: {rating})\n"

        # Summarize pain points and praises separately
        pain_summary = summarize_pain_points(pain_points)
        praise_summary = summarize_praises(praises)

        # Generate recommendation based on summaries
        recommendation = generate_recommendation(pain_summary, praise_summary)

        return render_template('index.html', feedbacks=feedbacks, classifications=classifications, pain_summary=pain_summary, praise_summary=praise_summary, recommendation=recommendation, show_feedback=True)
    except sqlite3.Error as e:
        logger.error(f"Database error in analyze_feedback: {str(e)}")
        return render_template('index.html', feedbacks=[], error=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Error in analyze_feedback: {str(e)}")
        return render_template('index.html', feedbacks=[], error=f"Analysis failed: {str(e)}")

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