# finbert_utils.py

from transformers import BertTokenizer, BertForSequenceClassification
import torch
import torch.nn.functional as F

# Modell & Tokenizer laden (einmalig)
tokenizer = BertTokenizer.from_pretrained("ProsusAI/finbert")
model = BertForSequenceClassification.from_pretrained("ProsusAI/finbert")

def estimate_sentiment(texts):
    """
    Analysiert eine Liste von Texten (z. B. News Headlines) und gibt:
    - die durchschnittliche Wahrscheinlichkeit für positives Sentiment zurück,
    - das dominante Sentiment: "positive", "neutral" oder "negative"
    """
    inputs = tokenizer(texts, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)

    probs = F.softmax(outputs.logits, dim=-1)
    avg_probs = probs.mean(dim=0)

    sentiments = ["positive", "negative", "neutral"]
    sentiment = sentiments[avg_probs.argmax().item()]
    probability = avg_probs.max()

    return probability, sentiment
