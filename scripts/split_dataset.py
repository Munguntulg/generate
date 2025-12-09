#!/usr/bin/env python3
"""
Өгөгдлийг Train/Val/Test хуваах
80% train, 10% validation, 10% test
"""

import json
import random
from pathlib import Path


def split_dataset(
    input_file: str,
    output_dir: str = "data/processed",
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    seed: int = 42
):
    """
    Өгөгдлийг хуваах
    
    Args:
        input_file: Орох файл
        output_dir: Гарах директор
        train_ratio: Train хувь (0.8 = 80%)
        val_ratio: Validation хувь (0.1 = 10%)
        seed: Random seed (reproducibility)
    """
    
    print(f"\n{'='*60}")
    print(f"ӨГӨГДӨЛ ХУВААХ")
    print(f"{'='*60}\n")
    
    # Өгөгдөл уншах
    print(f"1️⃣  Өгөгдөл уншиж байна...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    samples = data.get('samples', [])
    print(f"   ✓ {len(samples)} жишээ олдсон\n")
    
    # Shuffle
    print(f"2️⃣  Холих (seed={seed})...")
    random.seed(seed)
    random.shuffle(samples)
    
    # Хуваах
    total = len(samples)
    train_size = int(total * train_ratio)
    val_size = int(total * val_ratio)
    
    train_samples = samples[:train_size]
    val_samples = samples[train_size:train_size + val_size]
    test_samples = samples[train_size + val_size:]
    
    print(f"   ✓ Train: {len(train_samples)} ({len(train_samples)/total*100:.1f}%)")
    print(f"   ✓ Val:   {len(val_samples)} ({len(val_samples)/total*100:.1f}%)")
    print(f"   ✓ Test:  {len(test_samples)} ({len(test_samples)/total*100:.1f}%)\n")
    
    # Хадгалах
    print(f"3️⃣  Хадгалж байна...")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    splits = {
        "train": train_samples,
        "validation": val_samples,
        "test": test_samples
    }
    
    for split_name, split_samples in splits.items():
        filename = output_path / f"{split_name}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({"samples": split_samples}, f, ensure_ascii=False, indent=2)
        
        print(f"   ✓ {filename} ({len(split_samples)} жишээ)")
    
    print(f"\n{'='*60}")
    print(f"✅ АМЖИЛТТАЙ!")
    print(f"{'='*60}\n")
    
    # Статистик
    print(f"Файлууд:")
    for split_name in ["train", "validation", "test"]:
        filepath = output_path / f"{split_name}.json"
        size_kb = filepath.stat().st_size / 1024
        print(f"  📁 {filepath}")
        print(f"     Хэмжээ: {size_kb:.1f} KB\n")


if __name__ == "__main__":
    split_dataset(
        input_file="data/raw/expanded_dataset.json",
        output_dir="data/processed"
    )