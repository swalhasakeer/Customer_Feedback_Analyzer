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
        logger.debug(f"Feedback: {text}, Sentiment: {sentiment_result}, Rating: {rating}")  # Debug log
        # Extract numeric value from label (e.g., '3 stars' -> 3)
        label = sentiment_result['label']
        match = re.search(r'\d+', label)  # Find the first number in the label
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
        return summarizer("Summarize key pain points: " + " ".join(pain_points), max_length=100, min_length=30, do_sample=False)[0]['summary_text']
    else:
        return "None"

def summarize_praises(praises):
    if summarizer and praises:
        return summarizer("Summarize key praises: " + " ".join(praises), max_length=100, min_length=30, do_sample=False)[0]['summary_text']
    else:
        return "None"

def generate_recommendation(all_text):
    if summarizer:
        prompt = (
            "You are an expert product consultant. "
            "Summarize all the feedback below and provide ONE clear, concise, and actionable recommendation. "
            "Do not repeat individual feedback texts or names. "
            "Focus on the biggest improvement opportunity. "
            f"\n\nFeedback:\n{all_text}\n\n"
            "Final Recommendation:"
        )
        return summarizer(prompt, max_length=60, min_length=20, do_sample=False)[0]['summary_text']
    else:
        return "Unable to generate recommendation due to model failure."
