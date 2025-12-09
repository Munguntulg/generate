#!/usr/bin/env python3
"""
Unsloth ашиглан qwen2.5:7b fine-tune хийх

Суулгах:
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
pip install --no-deps "xformers<0.0.27" "trl<0.9.0" peft accelerate bitsandbytes
"""

import json
from pathlib import Path
from unsloth import FastLanguageModel
from datasets import Dataset
from trl import SFTTrainer
from transformers import TrainingArguments
import torch


def load_training_data(filepath: str) -> list:
    """Өгөгдөл уншах"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('samples', [])


def format_sample(sample: dict) -> str:
    """
    Sample-г chat format болгох
    
    Qwen2.5 format:
    <|im_start|>system
    {system_prompt}<|im_end|>
    <|im_start|>user
    {user_message}<|im_end|>
    <|im_start|>assistant
    {assistant_response}<|im_end|>
    """
    
    system_prompt = """Та протоколоос ярианы хэлийг албан хэл болгодог мэргэжилтэн.

ЧУХАЛ ДҮРЭМ:
1. АГУУЛГА ӨӨРЧЛӨХГҮЙ (нэр, огноо, тоо)
2. Хэллэг үгс АРИЛГА (шүү дээ, л байх даа)
3. Үйл үг албан хэл болго (хийх → гүйцэтгэх)

Зөвхөн албан хувилбар буцаа."""
    
    user_message = f"Энэ текстийг албан протокол болго:\n\n{sample['input']}"
    assistant_response = sample['output']
    
    formatted = f"""<|im_start|>system
{system_prompt}<|im_end|>
<|im_start|>user
{user_message}<|im_end|>
<|im_start|>assistant
{assistant_response}<|im_end|>"""
    
    return formatted


def prepare_dataset(samples: list) -> Dataset:
    """Dataset бэлтгэх"""
    formatted_texts = [format_sample(s) for s in samples]
    
    dataset_dict = {
        "text": formatted_texts,
        "id": [s['id'] for s in samples]
    }
    
    return Dataset.from_dict(dataset_dict)


def finetune_model(
    train_file: str = "data/processed/train.json",
    val_file: str = "data/processed/validation.json",
    output_dir: str = "models/qwen2.5-mongolian-protocol",
    max_seq_length: int = 2048,
    learning_rate: float = 2e-4,
    num_epochs: int = 3,
    batch_size: int = 4
):
    """
    Fine-tuning хийх
    """
    
    print(f"\n{'='*60}")
    print(f"FINE-TUNING ЭХЛҮҮЛЖ БАЙНА")
    print(f"{'='*60}\n")
    
    # 1. Model ачаалах
    print(f"1️⃣  Model ачаалж байна...")
    print(f"   Base model: qwen2.5:7b")
    print(f"   Max sequence: {max_seq_length}")
    
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="Qwen/Qwen2.5-7B-Instruct",  # HuggingFace model нэр
        max_seq_length=max_seq_length,
        dtype=None,  # Auto detect
        load_in_4bit=True,  # 4-bit quantization (memory хэмнэх)
    )
    
    print(f"   ✓ Model ачаалагдсан\n")
    
    # 2. LoRA config
    print(f"2️⃣  LoRA тохируулж байна...")
    
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,  # LoRA rank
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj"
        ],
        lora_alpha=16,
        lora_dropout=0.05,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42,
    )
    
    print(f"   ✓ LoRA ready\n")
    
    # 3. Dataset бэлтгэх
    print(f"3️⃣  Өгөгдөл бэлтгэж байна...")
    
    train_samples = load_training_data(train_file)
    val_samples = load_training_data(val_file)
    
    train_dataset = prepare_dataset(train_samples)
    val_dataset = prepare_dataset(val_samples)
    
    print(f"   ✓ Train: {len(train_dataset)} жишээ")
    print(f"   ✓ Val:   {len(val_dataset)} жишээ\n")
    
    # 4. Training arguments
    print(f"4️⃣  Training тохиргоо...")
    
    training_args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        gradient_accumulation_steps=4,
        warmup_steps=10,
        num_train_epochs=num_epochs,
        learning_rate=learning_rate,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=10,
        eval_strategy="steps",
        eval_steps=50,
        save_strategy="steps",
        save_steps=100,
        save_total_limit=3,
        load_best_model_at_end=True,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        seed=42,
    )
    
    print(f"   ✓ Epochs: {num_epochs}")
    print(f"   ✓ Batch size: {batch_size}")
    print(f"   ✓ Learning rate: {learning_rate}\n")
    
    # 5. Trainer
    print(f"5️⃣  Trainer үүсгэж байна...")
    
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        dataset_text_field="text",
        max_seq_length=max_seq_length,
        args=training_args,
    )
    
    print(f"   ✓ Trainer бэлэн\n")
    
    # 6. FINE-TUNING ЭХЛЭХ
    print(f"{'='*60}")
    print(f"⏳ TRAINING ЭХЭЛЖ БАЙНА...")
    print(f"{'='*60}\n")
    
    trainer.train()
    
    print(f"\n{'='*60}")
    print(f"✅ TRAINING ДУУСЛАА!")
    print(f"{'='*60}\n")
    
    # 7. Model хадгалах
    print(f"6️⃣  Model хадгалж байна...")
    
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    print(f"   ✓ Хадгалсан: {output_dir}\n")
    
    # 8. Ollama-д export хийх
    print(f"7️⃣  Ollama format руу хөрвүүлж байна...")
    
    # GGUF format (Ollama-д зориулж)
    model.save_pretrained_gguf(
        f"{output_dir}/gguf",
        tokenizer,
        quantization_method="q4_k_m"  # 4-bit quantization
    )
    
    print(f"   ✓ GGUF export: {output_dir}/gguf\n")
    
    print(f"{'='*60}")
    print(f"🎉 БҮГД АМЖИЛТТАЙ!")
    print(f"{'='*60}\n")
    
    print(f"Дараагийн алхам:")
    print(f"1. Ollama Modelfile үүсгэх:")
    print(f"   cat > Modelfile << 'EOF'")
    print(f"   FROM {output_dir}/gguf/model.gguf")
    print(f"   TEMPLATE [... template ...]")
    print(f"   EOF")
    print(f"\n2. Ollama-д import:")
    print(f"   ollama create mongolian-protocol -f Modelfile")
    print(f"\n3. Тестлэх:")
    print(f"   ollama run mongolian-protocol\n")


if __name__ == "__main__":
    # GPU шалгах
    if torch.cuda.is_available():
        print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
        print(f"   Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB\n")
    else:
        print(f"⚠️  GPU байхгүй - CPU ашиглана (удаан болно)\n")
    
    # Fine-tuning эхлүүлэх
    finetune_model(
        train_file="data/processed/train.json",
        val_file="data/processed/validation.json",
        output_dir="models/qwen2.5-mongolian-protocol",
        num_epochs=3,
        batch_size=2 if not torch.cuda.is_available() else 4
    )