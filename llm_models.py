# llm_models.py
from transformers import pipeline
import logging
import re

# Logging Setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load Hugging Face Models
try:
    sentiment_classifier = pipeline(
        "sentiment-analysis",
        model="nlptown/bert-base-multilingual-uncased-sentiment"
    )
    summarizer = pipeline(
        "summarization",
        model="facebook/bart-large-cnn"
    )
    generator = pipeline(
        "text2text-generation",
        model="google/flan-t5-base"
    )
    logger.info("✅ All LLM models loaded successfully.")
except Exception as e:
    logger.error(f"❌ Failed to load LLM models: {str(e)}")
    sentiment_classifier, summarizer, generator = None, None, None

# Sentiment Classification
def classify_sentiment(text, rating):
    """
    Classify sentiment using BERT model and refine with keyword analysis for mixed feedback.
    Falls back to rating if model fails.
    """
    if sentiment_classifier:
        try:
            sentiment_result = sentiment_classifier(text[:512])[0]  # truncate long text
            logger.debug(f"Feedback: {text}, Sentiment raw: {sentiment_result}, Rating: {rating}")

            # Extract numeric stars (e.g., '3 stars' -> 3)
            label = sentiment_result["label"]
            match = re.search(r"\d+", label)
            sentiment_value = int(match.group()) if match else 3

            # Check for negative keywords to detect mixed feedback
            negative_keywords = ['slow', 'overpriced', 'issue', 'problem', 'bug', 'crash', 'expensive', 'difficult']
            has_negative = any(keyword in text.lower() for keyword in negative_keywords)
            has_positive = sentiment_value >= 4 or rating >= 4

            if has_negative and has_positive:
                return "Mixed"
            elif sentiment_value >= 4:
                return "Positive"
            elif sentiment_value == 3:
                return "Neutral"
            else:
                return "Negative"
        except Exception as e:
            logger.error(f"Sentiment classification error: {e}")

    # Fallback: use numeric rating
    if rating >= 4:
        return "Positive"
    elif rating == 3:
        return "Neutral"
    else:
        return "Negative"

# Summarization of Pain Points
def summarize_pain_points(pain_points):
    if summarizer and pain_points:
        try:
            text = "Summarize key pain points: " + " ".join(pain_points)
            result = summarizer(text, max_length=100, min_length=30, do_sample=False)
            return result[0]["summary_text"].strip()
        except Exception as e:
            logger.error(f"Summarizer error (pain points): {e}")
            return "None"
    return "None"

# Summarization of Praises
def summarize_praises(praises):
    if summarizer and praises:
        try:
            text = "Summarize key praises: " + " ".join(praises)
            result = summarizer(text, max_length=100, min_length=30, do_sample=False)
            return result[0]["summary_text"].strip()
        except Exception as e:
            logger.error(f"Summarizer error (praises): {e}")
            return "None"
    return "None"

# Actionable Recommendation
def generate_recommendation(all_text, classifications):
    if generator:
        # Clean feedback (remove names/ratings)
        feedback_only = " ".join(
            [line.split(":", 1)[-1].strip() for line in all_text.splitlines() if ":" in line]
        )

        # Check if all feedback is positive
        is_all_positive = all("Positive" in classification for classification in classifications)

        # If all feedback is positive, return fixed response
        if is_all_positive:
            return "All feedback is positive; no action needed, customers are satisfied now."

        # Improved prompt for mixed or negative feedback
        prompt = (
            "You are a senior product strategy consultant. "
            "Analyze the following customer feedback and provide a short recommendation.\n\n"
            "Rules:\n"
            "1. Feedback contains mixed or negative sentiments, so suggest the single biggest improvement.\n"
            "2. Focus on addressing negative aspects (e.g., performance issues, pricing concerns).\n"
            "3. Do not repeat customer sentences or names.\n"
            "4. Keep the answer to ONE sentence only.\n\n"
            f"Customer Feedback:\n{feedback_only}\n\n"
            "Final Recommendation:"
        )

        try:
            result = generator(prompt, max_length=50, min_length=10, do_sample=False)
            recommendation = result[0]['generated_text'].strip()
            return recommendation
        except Exception as e:
            logger.error(f"Recommendation generation error: {e}")
            return "Recommendation generation failed."

    return "Recommender model not available."