# Instamart Customer Intelligence & Support Copilot

## Project Overview
An end-to-end data analytics and AI-powered support solution built for a simulated Instamart environment. The project helps analyze customer behaviour, predict customer lapses, classify support tickets, and automate policy-based refund assistance.

## Key Features
- **Data Engineering:** Data auditing, cleaning, validation, and SQLite integration.
- **Customer Analytics:** RFM analysis, K-Means segmentation, and lapse prediction using Logistic Regression and Random Forest.
- **Support Ticket Intelligence:** Ticket classification, PII redaction, retry handling, and intelligent routing.
- **Policy RAG & Refund Copilot:** TF-IDF-based policy retrieval, order validation, refund eligibility checks, and human escalation.

## Technology Stack
Python | SQL | Pandas | NumPy | Scikit-learn | SQLite | TF-IDF | Joblib

## Run the Project

```bash
pip install -r requirements.txt
python generate_data.py
python run_project.py
python run_refund_tests.py
```

## Outputs
Generated results include customer segments, lapse predictions, support ticket classifications, RAG evaluation results, refund execution logs, and a SQLite database.

**Note:** Uses synthetic data and an offline mock LLM. No external API key is required.