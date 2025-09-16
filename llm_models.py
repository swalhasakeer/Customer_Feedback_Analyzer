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

# Keywords for filtering
NEGATIVE_KEYWORDS = [
    'slow', 'overpriced', 'issue', 'problem', 'bug', 'crash',
    'expensive', 'difficult', 'limited', 'ads', 'doesn’t',
    'lack', 'not unique'
]

POSITIVE_KEYWORDS = [
    'useful', 'great', 'excellent', 'clean', 'fast',
    'intuitive', 'helpful', 'responsive'
]

# Sentiment Classification
def classify_sentiment(text, rating):
    """
    Classify sentiment based on rating + negative keyword detection.
    """
    text_lower = text.lower()
    has_negative = any(kw in text_lower for kw in NEGATIVE_KEYWORDS)

    # Mixed: high rating but contains negatives
    if rating in [4, 5] and has_negative:
        return "Mixed"

    if rating in [1, 2]:
        return "Negative"
    elif rating == 3:
        return "Neutral"
    else:
        return "Positive"

# Helper: Sentence Filtering
def filter_positive_sentences(feedback_list):
    positive_sentences = []
    for text in feedback_list:
        sentences = re.split(r'[.!?]', text)
        for s in sentences:
            s_clean = s.strip()
            if s_clean and not any(kw in s_clean.lower() for kw in NEGATIVE_KEYWORDS):
                positive_sentences.append(s_clean)
    return positive_sentences

def filter_negative_sentences(feedback_list):
    negative_sentences = []
    for text in feedback_list:
        sentences = re.split(r'[.!?]', text)
        for s in sentences:
            s_clean = s.strip()
            if s_clean and any(kw in s_clean.lower() for kw in NEGATIVE_KEYWORDS):
                negative_sentences.append(s_clean)
    return negative_sentences

# Summarization Functions
def summarize_praises(feedback_list):
    positive_sentences = filter_positive_sentences(feedback_list)
    if not positive_sentences:
        return "No major praises detected."

    text_to_summarize = " ".join(positive_sentences)
    if summarizer:
        try:
            result = summarizer(
                text_to_summarize,
                max_length=80,
                min_length=20,
                do_sample=False
            )
            return result[0]["summary_text"].strip()
        except Exception as e:
            logger.error(f"Summarizer error (praises): {e}")
            return text_to_summarize
    return text_to_summarize

def summarize_pain_points(feedback_list):
    negative_sentences = filter_negative_sentences(feedback_list)
    if not negative_sentences:
        return "No major pain points detected."

    text_to_summarize = " ".join(negative_sentences)
    if summarizer:
        try:
            result = summarizer(
                text_to_summarize,
                max_length=80,
                min_length=20,
                do_sample=False
            )
            return result[0]["summary_text"].strip()
        except Exception as e:
            logger.error(f"Summarizer error (pains): {e}")
            return text_to_summarize
    return text_to_summarize

# Actionable Recommendation
def generate_recommendation(all_text, classifications):
    """
    Generate ONE clear recommendation for the product/service team.
    """
    if not classifications:
        return "No feedback available to generate recommendations."

    if all("Positive" in c for c in classifications):
        return "All feedback is positive; the team should maintain their current approach."

    prompt = (
        "You are a senior consultant advising a PRODUCT and SERVICE team.\n"
        "Analyze the following customer feedback and provide ONE ACTIONABLE RECOMMENDATION.\n\n"
        "Rules:\n"
        "- Write directly to the team (e.g., 'The team should ...').\n"
        "- Do NOT repeat or paraphrase customer sentences.\n"
        "- Focus on the BIGGEST improvement opportunity.\n"
        "- Keep it short (1–2 sentences).\n\n"
        f"Customer Feedback:\n{all_text}\n\n"
        "Final Recommendation for the team:"
    )

    if generator:
        try:
            result = generator(
                prompt,
                max_length=60,
                min_length=15,
                do_sample=False
            )
            recommendation = result[0]["generated_text"].strip()

            # Safety filter to avoid echoing customer text
            banned_words = ["I ", "me ", "my ", "the app", "the service", "the design"]
            if any(word.lower() in recommendation.lower() for word in banned_words):
                return "The team should enhance stability, performance, and affordability to improve user trust and satisfaction."

            return recommendation
        except Exception as e:
            logger.error(f"Recommendation generation error: {e}")
            return "The team should prioritize fixing technical issues and improving performance."
    else:
        return "Recommendation generation failed."
