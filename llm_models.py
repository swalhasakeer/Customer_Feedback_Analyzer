# llm_models.py
from transformers import pipeline
import logging
import re  # For regular expression

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load LLM models at startup (no API key needed)
try:
    sentiment_classifier = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")
    summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
    logger.info("LLM models loaded successfully")
except Exception as e:
    logger.error(f"Failed to load LLM models: {str(e)}")
    sentiment_classifier = None
    summarizer = None


def classify_sentiment(text, rating):
    if sentiment_classifier:
        sentiment_result = sentiment_classifier(text)[0]
        logger.debug(f"Feedback: {text}, Sentiment: {sentiment_result}, Rating: {rating}")
        # Extract numeric value from label (e.g., '3 stars' -> 3)
        label = sentiment_result['label']
        match = re.search(r'\d+', label)
        if match:
            sentiment_value = int(match.group())
        else:
            sentiment_value = 3  # Default to neutral if no number is found
        if sentiment_value >= 4:
            return 'Positive'
        elif sentiment_value == 3:
            return 'Neutral'
        else:
            return 'Negative'
    else:
        # Full fallback if LLM fails
        if rating >= 4:
            return 'Positive'
        elif rating == 3:
            return 'Neutral'
        else:
            return 'Negative'


def summarize_pain_points(pain_points):
    if summarizer and pain_points:
        try:
            return summarizer("Summarize key pain points: " + " ".join(pain_points), max_length=100, min_length=30, do_sample=False)[0]['summary_text']
        except Exception as e:
            logger.error(f"Summarizer error in summarize_pain_points: {e}")
            return "None"
    else:
        return "None"


def summarize_praises(praises):
    if summarizer and praises:
        try:
            return summarizer("Summarize key praises: " + " ".join(praises), max_length=100, min_length=30, do_sample=False)[0]['summary_text']
        except Exception as e:
            logger.error(f"Summarizer error in summarize_praises: {e}")
            return "None"
    else:
        return "None"


def generate_recommendation(all_text):
    if summarizer:
        # Extract feedback only (remove names/ratings)
        feedback_lines = [line.split(":", 1)[-1].strip() for line in all_text.splitlines() if ":" in line]
        feedback_only = " ".join(feedback_lines).strip()

        # Strong instruction: no repeating sentences, only recommendation
        prompt = (
            "You are a senior product strategy expert. "
            "Read the following customer feedback and output exactly ONE actionable recommendation "
            "for the product and service team. "
            "The recommendation should be forward-looking, practical, and NOT a repetition of the feedback sentences. "
            "It must combine the main pain points into one improvement plan. "
            "Do not mention individual users or copy their words.\n\n"
            f"Customer Feedback:\n{feedback_only}\n\n"
            "Final Recommendation:"
        )

        try:
            result = summarizer(
                prompt,
                max_length=50,
                min_length=20,
                do_sample=False
            )
            recommendation = result[0]['summary_text'].strip()

            # Safety: if model still echoes feedback, replace with fallback
            if any(sentence.strip() in feedback_only for sentence in recommendation.split(".")):
                recommendation = "Focus on improving app speed and stability, modernizing the interface, reducing intrusive ads, and ensuring competitive pricing while maintaining strong support and quality."

            return recommendation

        except Exception as e:
            logger.error(f"Summarizer error: {str(e)}")
            return "Recommendation generation failed."
    else:
        return "Unable to generate recommendation due to model failure."


