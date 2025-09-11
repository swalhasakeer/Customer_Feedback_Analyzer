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

def generate_recommendation(pain_summary, praise_summary):
    if summarizer:
        prompt = f"Based on the following summaries:\n- Key Pain Points: {pain_summary}\n- Key Praises: {praise_summary}\nProvide a detailed actionable recommendation in bullet points, separated into two sections: 'For the Product Team' and 'For the Service Team'. Exclude any raw feedback or ratings, and focus on specific improvements and strengths to leverage."
        result = summarizer(prompt, max_length=200, min_length=50, do_sample=False)[0]['summary_text']
        lines = result.split('\n')
        cleaned_lines = [line.strip() for line in lines if line.strip()]
        formatted_lines = []
        current_section = None
        for line in cleaned_lines:
            if line.startswith('For the Product Team') or line.startswith('For the Service Team'):
                current_section = line
                formatted_lines.append(f"<strong>{current_section}:</strong>")
            elif line and current_section:
                formatted_lines.append(f"- {line}" if not line.startswith('-') else line)
        return '\n'.join(formatted_lines) if formatted_lines else "No specific recommendations available."
    else:
        return "Unable to generate recommendation due to model failure."