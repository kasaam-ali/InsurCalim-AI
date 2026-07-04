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


# Columns from the real dataset that carry fraud signal, encoded into text so the
# same DistilBERT fine-tuning pipeline can learn from tabular data.
REAL_FEATURES = [
    "incident_type", "collision_type", "incident_severity", "authorities_contacted",
    "number_of_vehicles_involved", "property_damage", "bodily_injuries", "witnesses",
    "police_report_available", "total_claim_amount", "injury_claim", "property_claim",
    "vehicle_claim", "insured_sex", "insured_education_level", "insured_occupation",
    "insured_relationship", "incident_hour_of_the_day", "months_as_customer", "age",
    "policy_annual_premium", "auto_make", "auto_year",
]


def _row_to_text(row: dict) -> str:
    """Turn one real claim row into a compact 'field: value; ...' string."""
    parts = [f"{name}: {row.get(name)}" for name in REAL_FEATURES if row.get(name)]
    return "; ".join(parts)


def _load_real_dataset():
    """Build a (text, label) dataset from the real_claims table."""
    from datasets import Dataset

    rows = repo.list_real_claims()
    if not rows:
        raise RuntimeError("No real claims found. Run 'python -m insurclaim.data.load_real' first.")

    texts = [_row_to_text(r) for r in rows]
    labels = [1 if r["is_fraud"] else 0 for r in rows]  # 1 = fraud, 0 = legit
    return Dataset.from_dict({"text": texts, "label": labels})


def train(epochs: int = 3, source: str = "narrative", max_length: int = 256) -> Path:
    """Fine-tune DistilBERT on labeled claims and save the model.

    source="narrative" trains on synthetic claim descriptions; source="real"
    trains on the real-world dataset (features encoded as text).
    """
    import numpy as np
    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        Trainer,
        TrainingArguments,
    )

    dataset = _load_real_dataset() if source == "real" else _load_dataset()
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

    def tokenize(batch):
        return tokenizer(batch["text"], truncation=True, padding="max_length", max_length=max_length)

    dataset = dataset.map(tokenize, batched=True)
    # Cast the label to a ClassLabel so the split can keep the fraud/legit ratio.
    dataset = dataset.class_encode_column("label")
    # Hold out 20% for validation, keeping the fraud/legit ratio in both parts.
    split = dataset.train_test_split(test_size=0.2, seed=42, stratify_by_column="label")

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
        from sklearn.metrics import precision_score, recall_score, f1_score

        logits, labels = eval_pred
        predictions = np.argmax(logits, axis=-1)
        return {
            "accuracy": float((predictions == labels).mean()),
            "precision": float(precision_score(labels, predictions, zero_division=0)),
            "recall": float(recall_score(labels, predictions, zero_division=0)),
            "f1": float(f1_score(labels, predictions, zero_division=0)),
        }

    import torch

    # The dataset is imbalanced (~75% legit). Without help the model collapses to
    # always predicting "legit" (high accuracy, zero fraud recall). Weight the
    # loss by inverse class frequency so the fraud class carries its fair share.
    train_labels = list(split["train"]["label"])
    n_legit = train_labels.count(0)
    n_fraud = train_labels.count(1)
    total = n_legit + n_fraud
    class_weights = torch.tensor(
        [total / (2 * n_legit), total / (2 * n_fraud)], dtype=torch.float
    )

    class WeightedTrainer(Trainer):
        """Trainer that applies class weights to counter label imbalance."""

        def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
            labels = inputs.pop("labels")
            outputs = model(**inputs)
            loss_fct = torch.nn.CrossEntropyLoss(
                weight=class_weights.to(outputs.logits.device)
            )
            loss = loss_fct(
                outputs.logits.view(-1, model.config.num_labels), labels.view(-1)
            )
            return (loss, outputs) if return_outputs else loss

    trainer = WeightedTrainer(
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
    import argparse

    parser = argparse.ArgumentParser(description="Fine-tune the fraud classifier.")
    parser.add_argument(
        "--source", choices=["narrative", "real"], default="narrative",
        help="which dataset to train on",
    )
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument(
        "--max-length", type=int, default=None,
        help="token length (defaults: 256 narrative, 128 real)",
    )
    args = parser.parse_args()

    max_length = args.max_length or (128 if args.source == "real" else 256)
    saved_to = train(epochs=args.epochs, source=args.source, max_length=max_length)
    print(f"Fraud classifier trained and saved to {saved_to}")
