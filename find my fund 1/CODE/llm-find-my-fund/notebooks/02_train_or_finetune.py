"""
Train or Fine-tune Models for Fund Search

This script demonstrates how to fine-tune small language models for mutual fund search.
We'll use LoRA (Low-Rank Adaptation) to efficiently fine-tune a small language model
on a dataset of mutual fund descriptions and queries.
"""

import os
import sys
import pandas as pd
import numpy as np
import torch
from pathlib import Path
from tqdm import tqdm
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding
)
from peft import (
    get_peft_model,
    LoraConfig,
    TaskType
)
from datasets import Dataset
import evaluate

# Add the parent directory to the path so we can import modules
script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
parent_dir = script_dir.parent
sys.path.append(str(parent_dir))

# Import config
from config import FUNDS_DATA_PATH, MODELS_DIR

# Check if GPU is available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

def create_training_data():
    """
    Create a training dataset by generating query-fund pairs with relevance scores.
    
    In a real scenario, you'd have human-labeled data or real user interactions,
    but for this demo we'll generate synthetic training data.
    """
    # Load fund data
    if os.path.exists(FUNDS_DATA_PATH):
        funds_df = pd.read_csv(FUNDS_DATA_PATH)
    else:
        print("Error: Fund data not found. Please run 01_build_vector_store.py first.")
        sys.exit(1)
    
    # Define sample queries for different categories
    query_templates = {
        "ELSS": [
            "tax saving mutual funds",
            "ELSS funds with good returns",
            "funds for tax benefits under section 80C",
            "best tax saver funds"
        ],
        "Equity": [
            "{sector} equity funds",
            "mutual funds for {sector} stocks",
            "best {sector} funds",
            "high return equity funds in {sector}"
        ],
        "Index": [
            "index funds tracking nifty",
            "passive index funds",
            "low cost index funds",
            "best nifty index funds"
        ],
        "Debt": [
            "debt funds with stable returns",
            "low risk debt funds",
            "fixed income mutual funds",
            "corporate bond funds"
        ],
        "Hybrid": [
            "balanced hybrid funds",
            "funds with mix of equity and debt",
            "hybrid funds for moderate risk",
            "balanced mutual funds"
        ],
        "International": [
            "funds investing in international markets",
            "global exposure mutual funds",
            "foreign equity funds",
            "international diversification funds"
        ]
    }
    
    # Generate query-fund pairs
    data = []
    
    for _, fund in funds_df.iterrows():
        fund_name = fund["fund_name"]
        category = fund["category"]
        sector = fund["sector"]
        
        # Get relevant query templates
        templates = query_templates.get(category, [])
        
        # For Equity funds, add sector-specific queries
        if category == "Equity" and sector != "Diversified":
            templates = [template.format(sector=sector.lower()) for template in templates]
        elif category == "Equity":
            # For diversified equity, use general templates
            templates = [
                "diversified equity funds",
                "mutual funds with broad market exposure",
                "equity funds with diversification",
                "well diversified stock funds"
            ]
        
        # Add positive examples (relevant query-fund pairs)
        for template in templates:
            data.append({
                "query": template,
                "fund_name": fund_name,
                "relevance": 1,  # 1 means relevant
                "category": category,
                "sector": sector
            })
        
        # Add negative examples (irrelevant query-fund pairs)
        # Find categories different from this fund
        other_categories = [c for c in query_templates.keys() if c != category]
        
        # Sample 2 random categories
        if other_categories:
            sample_categories = np.random.choice(other_categories, min(2, len(other_categories)), replace=False)
            
            for cat in sample_categories:
                # Sample 1 query template from each category
                template = np.random.choice(query_templates[cat])
                
                # Format template if needed
                if "{sector}" in template:
                    # Find a different sector
                    other_sectors = ["Technology", "Healthcare", "Banking", "Energy", "Real Estate"]
                    other_sectors = [s for s in other_sectors if s.lower() != sector.lower()]
                    if other_sectors:
                        random_sector = np.random.choice(other_sectors)
                        template = template.format(sector=random_sector.lower())
                    else:
                        template = template.replace("{sector}", "general")
                
                data.append({
                    "query": template,
                    "fund_name": fund_name,
                    "relevance": 0,  # 0 means not relevant
                    "category": category,
                    "sector": sector
                })
    
    # Convert to DataFrame
    train_df = pd.DataFrame(data)
    print(f"Generated {len(train_df)} training examples")
    
    # Split into train/validation sets
    train_df = train_df.sample(frac=1, random_state=42).reset_index(drop=True)  # shuffle
    split_idx = int(len(train_df) * 0.8)
    train_set = train_df[:split_idx]
    val_set = train_df[split_idx:]
    
    print(f"Training set: {len(train_set)} examples")
    print(f"Validation set: {len(val_set)} examples")
    
    return train_set, val_set

def prepare_datasets(train_df, val_df, tokenizer, max_length=128):
    """Prepare the datasets for training"""
    
    def tokenize_function(examples):
        # Combine query and fund name for input
        texts = [q + " [SEP] " + f for q, f in zip(examples["query"], examples["fund_name"])]
        return tokenizer(texts, padding="max_length", truncation=True, max_length=max_length)
    
    # Convert to Hugging Face Datasets
    train_dataset = Dataset.from_pandas(train_df)
    val_dataset = Dataset.from_pandas(val_df)
    
    # Tokenize
    train_dataset = train_dataset.map(tokenize_function, batched=True)
    val_dataset = val_dataset.map(tokenize_function, batched=True)
    
    # Set format for pytorch
    train_dataset.set_format("torch", columns=["input_ids", "attention_mask", "relevance"])
    val_dataset.set_format("torch", columns=["input_ids", "attention_mask", "relevance"])
    
    return train_dataset, val_dataset

def fine_tune_model():
    """Fine-tune a model for fund relevance ranking"""
    # Create training data
    train_df, val_df = create_training_data()
    
    # Load base model and tokenizer
    model_name = "microsoft/MiniLM-L12-H384-uncased"  # A small but effective model
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    # Load base model for sequence classification (binary in this case)
    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)
    
    # Prepare the datasets
    train_dataset, val_dataset = prepare_datasets(train_df, val_df, tokenizer)
    
    # Define LoRA config for efficient fine-tuning
    peft_config = LoraConfig(
        task_type=TaskType.SEQ_CLS,
        r=8,  # rank of the update matrices
        lora_alpha=32,  # scaling factor
        lora_dropout=0.1,
        target_modules=["query", "key", "value"]  # which modules to apply LoRA to
    )
    
    # Get the PEFT model
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()  # Print trainable vs total parameters
    
    # Move model to the right device
    model.to(device)
    
    # Define training arguments
    training_args = TrainingArguments(
        output_dir=os.path.join(MODELS_DIR, "fund_ranker"),
        num_train_epochs=3,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        warmup_steps=500,
        weight_decay=0.01,
        logging_dir="./logs",
        logging_steps=100,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="accuracy",
        push_to_hub=False,  # Set to True if you want to push to Hugging Face Hub
    )
    
    # Define metrics for evaluation
    metric = evaluate.load("accuracy")
    
    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        predictions = np.argmax(logits, axis=-1)
        return metric.compute(predictions=predictions, references=labels)
    
    # Create Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
        tokenizer=tokenizer,
        data_collator=DataCollatorWithPadding(tokenizer),
    )
    
    # Train the model
    print("Starting training...")
    trainer.train()
    
    # Evaluate
    eval_results = trainer.evaluate()
    print(f"Evaluation results: {eval_results}")
    
    # Save the model
    output_dir = os.path.join(MODELS_DIR, "fund_ranker_final")
    os.makedirs(output_dir, exist_ok=True)
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    print(f"Model saved to {output_dir}")
    
    return model, tokenizer

def test_model(model, tokenizer):
    """Test the fine-tuned model with some examples"""
    # Load fund data
    funds_df = pd.read_csv(FUNDS_DATA_PATH)
    
    # Sample 5 random funds
    sample_funds = funds_df.sample(5)
    
    # Test queries
    test_queries = [
        "tax saving funds with high returns",
        "technology sector funds",
        "low risk debt funds",
        "index funds with low expense ratio",
        "funds for long term investment"
    ]
    
    # Move model to the right device
    model.to(device)
    model.eval()
    
    print("\nTesting model with sample queries:")
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        results = []
        
        for _, fund in sample_funds.iterrows():
            fund_name = fund["fund_name"]
            
            # Prepare input
            text = query + " [SEP] " + fund_name
            inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            # Get prediction
            with torch.no_grad():
                outputs = model(**inputs)
                logits = outputs.logits
                probabilities = torch.softmax(logits, dim=1)
                relevance_score = probabilities[0][1].item()  # Probability of being relevant
            
            results.append({
                "fund_name": fund_name,
                "relevance_score": relevance_score,
                "category": fund["category"],
                "sector": fund["sector"]
            })
        
        # Sort by relevance score
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        # Print top 3 results
        for i, result in enumerate(results[:3]):
            print(f"{i+1}. {result['fund_name']}")
            print(f"   Relevance Score: {result['relevance_score']:.4f}")
            print(f"   Category: {result['category']}")
            print(f"   Sector: {result['sector']}")

def main():
    """Main function to fine-tune and test the model"""
    print("Starting model fine-tuning...")
    
    # Create models directory if it doesn't exist
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    # Check if we should load a saved model or train a new one
    model_path = os.path.join(MODELS_DIR, "fund_ranker_final")
    
    if os.path.exists(model_path):
        print(f"Loading saved model from {model_path}")
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForSequenceClassification.from_pretrained(model_path)
    else:
        print("Training new model")
        model, tokenizer = fine_tune_model()
    
    # Test the model
    test_model(model, tokenizer)
    
    print("\nFine-tuning and testing completed!")

if __name__ == "__main__":
    # Check if CUDA is available
    if torch.cuda.is_available():
        print(f"CUDA is available. Using GPU: {torch.cuda.get_device_name(0)}")
    else:
        print("CUDA is not available. Training on CPU (this will be slow).")
    
    main() 