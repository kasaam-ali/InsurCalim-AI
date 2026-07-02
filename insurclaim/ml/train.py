"""Fine-tune a small transformer as the fraud classifier.

This is the project's "fine-tuning" deliverable. We take a small pre-trained
model (DistilBERT) and fine-tune it on our synthetic labeled claim narratives to
predict fraud vs. legit. The saved model is loaded by predict.py and used as one
layer inside the fraud agent.

Heavy libraries (torch, transformers, datasets) are imported lazily so the rest
of the project imports cleanly even before those packages are installed.

Run as a script:  python -m insurclaim.ml.train
"""

from __future__ import annotations

from pathlib import Path

from insurclaim.db import repo

BASE_MODEL = "distilbert-base-uncased"
MODEL_DIR = Path(__file__).resolve().parents[2] / "models" / "fraud_classifier"


def _load_dataset():
    """Build a HuggingFace dataset of (text, label) from labeled claims."""
    from datasets import Dataset

    claims = repo.list_labeled_claims()
    if not claims:
        raise RuntimeError("No labeled claims found. Generate synthetic data first.")

    texts = [c["description"] or "" for c in claims]
    labels = [1 if c["is_fraud"] else 0 for c in claims]  # 1 = fraud, 0 = legit
    return Dataset.from_dict({"text": texts, "label": labels})


def train(epochs: int = 3) -> Path:
    """Fine-tune DistilBERT on the labeled claims and save the model."""
    import numpy as np
    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        Trainer,
        TrainingArguments,
    )

    dataset = _load_dataset()
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

    def tokenize(batch):
        return tokenizer(batch["text"], truncation=True, padding="max_length", max_length=256)

    dataset = dataset.map(tokenize, batched=True)
    # Hold out 20% for a quick validation split.
    split = dataset.train_test_split(test_size=0.2, seed=42)

    model = AutoModelForSequenceClassification.from_pretrained(BASE_MODEL, num_labels=2)

    args = TrainingArguments(
        output_dir=str(MODEL_DIR / "checkpoints"),
        num_train_epochs=epochs,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        eval_strategy="epoch",
        logging_steps=10,
        report_to="none",
    )

    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        predictions = np.argmax(logits, axis=-1)
        accuracy = float((predictions == labels).mean())
        return {"accuracy": accuracy}

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=split["train"],
        eval_dataset=split["test"],
        compute_metrics=compute_metrics,
    )
    trainer.train()

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(MODEL_DIR)
    tokenizer.save_pretrained(MODEL_DIR)
    return MODEL_DIR


if __name__ == "__main__":
    saved_to = train()
    print(f"Fraud classifier trained and saved to {saved_to}")
