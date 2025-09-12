# 📊 **Customer Feedback Analyzer**



🚀 A full-stack web app built with Flask, Bootstrap, and SQLite, powered by Hugging Face Transformers, that collects customer feedback, analyzes sentiment, summarizes pain points and praises, and generates actionable recommendations for product & service teams.


<img width="854" height="565" alt="image" src="https://github.com/user-attachments/assets/e3cd113e-fcdc-408b-b5bf-a5cf421b2f0d" />

---
## ✨ Features  
- 📝 **Submit Feedback** – Users can add their name, feedback text, and rating (1–5 ⭐).  
- 💬 **Auto-Scrolling Feedback Carousel** – Displays feedback cards with star ratings and classification (Positive / Neutral / Negative).  
- 🤖 **AI Insights** powered by Hugging Face:  
  - Sentiment classification  
  - Summarization of pain points & praises  
  - Actionable product recommendations  
- 💾 **Persistent Storage** – Feedback stored in SQLite database.  
- 🎨 **Attractive UI** – Dark theme, Bootstrap , animated feedback cards, badges for sentiment.  



## 🛠️ Tech Stack  
**Frontend:** HTML, CSS, Bootstrap 
**Backend:** Python (Flask)  
**Database:** SQLite  
**AI Models:** Hugging Face Transformers  
- Sentiment → [`nlptown/bert-base-multilingual-uncased-sentiment`](https://huggingface.co/nlptown/bert-base-multilingual-uncased-sentiment)  
- Summarization → [`sshleifer/distilbart-cnn-12-6`](https://huggingface.co/sshleifer/distilbart-cnn-12-6)  



## 🚀 Getting Started  

### 1️⃣ Clone the repo  
```bash
git clone https://github.com/swalhasakeer/Customer_Feedback_Analyzer.git
cd Customer_Feedback_Analyzer
```

### 2️⃣ Create virtual environment
```bash
python -m venv venv
# Activate it
source venv/bin/activate    # macOS/Linux
venv\Scripts\activate       # Windows
```

### 3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Run the Flask app
```bash
python app.py
```

### 5️⃣ Open in browser

👉 http://127.0.0.1:5000

## 📂 Project Structure
```bash
customer-feedback-analyzer/
│
├── app.py              # Flask backend (routes, DB, APIs)
├── llm_models.py       # Hugging Face sentiment/summarization models
├── templates/
│   └── index.html      # Frontend 
├── feedback.db         # SQLite database 
├── requirements.txt    # Python dependencies
└── README.md           # Project documentation
```

## 📊 Example Workflow

- User submits feedback with rating ⭐ (1–5).

- Feedback saved in SQLite database.

- Feedback displayed in animated cards with stars + sentiment badge.

- Clicking Analyze All Feedback →

- AI sentiment classification

- Key pain points & praises summarized

- Actionable recommendation generated

## 🧠 Example AI Insights

### Classifications:

- ✅ Positive → “This product has superb quality.”

- ⚠️ Neutral → “The app works okay but could use more features.”

- ❌ Negative → “The app crashes frequently and is very slow.”

### Key Pain Points:

- Slow loading times

- Frequent crashes

- Too many ads

### Key Praises:

- Intuitive UI

- Responsive customer support

- High product quality

### Actionable Recommendation:

- “Focus on improving speed and stability, reducing intrusive ads, and ensuring affordability while maintaining strong UI design and responsive support.”

## 📌 Future Enhancements

- 🌐 Deployment on Heroku / Render / AWS

- 🔑 User authentication (admin panel for insights)

- 🌍 Multi-language support

- 📑 Export insights as PDF / CSV

- 📊 Dashboard with charts

## 🤝 Contributing

- Contributions are welcome! 

---
