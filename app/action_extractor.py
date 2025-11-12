#!/usr/bin/env python3
"""
SLM-ONLY Action Extractor - УТГА ХАДГАЛАХ сайжруулалт
"""

import json
import re
from typing import List, Dict

try:
    from ollama import chat
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


class SLMOnlyActionExtractor:
    """
    Зөвхөн SLM ашиглах action extractor - УТГА ХАДГАЛНА
    """
    
    def __init__(self, nlp_processor=None):
        self.nlp = nlp_processor
        self.model = "qwen2.5:7b"
        
        if not OLLAMA_AVAILABLE:
            raise RuntimeError(
                "❌ Ollama суулгаагүй байна!\n"
                "   Суулгах: pip install ollama"
            )
        
        print(f"✅ Action Extractor бэлэн: {self.model}")
    
    def extract_actions_with_llm(self, text: str) -> List[Dict]:
        """
        SLM ашиглан action items гаргах - УТГА ХАДГАЛНА
        """
        if not OLLAMA_AVAILABLE:
            raise RuntimeError("❌ SLM ажиллахгүй байна (Ollama суулгаагүй)")
        
        # САЙЖРУУЛСАН PROMPT - АГУУЛГА ӨӨРЧЛӨХГҮЙ
        system_prompt = """Та протоколоос ажил үүрэг, шийдвэр гаргадаг мэргэжилтэн.

🎯 ХАМГИЙН ЧУХАЛ: АГУУЛГА ӨӨРЧЛӨХГҮЙ
- Нэр → нэр (яг хуулах)
- Огноо → огноо (яг хуулах) 
- Ажил → ажил (яг хуулах)

⚠️ ОГНОО ЗААВАЛ ОЛОХ:
- Текстэд огноо байвал ЗААВАЛ "due" талбарт бичих
- "даваа гараг", "долоо хоног", "маргааш" гэх мэт
- Огноо байхгүй бол "Хугацаа заагаагүй"

📋 ОЛОХ ЗҮЙЛС:
1. ХЭН - Хариуцагч (анхны текст дэх нэр)
2. ЮУ - Хийх ажил (анхны текст дэх ажил)
3. ХЭЗЭЭ - Хугацаа (анхны текст дэх огноо)
4. ТӨРӨЛ - "action" эсвэл "decision"

JSON ФОРМАТ:
[
    {
        "who": "Яг анхны нэр",
        "action": "Яг анхны ажил",
        "due": "Яг анхны огноо",
        "type": "action/decision",
        "confidence": 0.8
    }
]

ЖИШЭЭ - АНХНЫ ТЕКСТЭЭС ЯАЖ ГАРГАХ:

Текст: "Анна: Би төслийг даваа гарагт дуусгах болно."
JSON:
[{
    "who": "Анна",
    "action": "төслийг дуусгах",
    "due": "даваа гараг",
    "type": "action",
    "confidence": 0.9
}]

АНХААР: "Анна" → "Анна" (өөрчлөхгүй)
АНХААР: "даваа гараг" → "даваа гараг" (өөрчлөхгүй)
АНХААР: "төслийг дуусгах" → агуулга хадгал

⚠️ ХОРИОТОЙ:
- Нэр солихгүй (Анна → Жон БИШІ)
- Огноо солихгүй (даваа гараг → мягмар гараг БИШІ)
- Ажил өөрчлөхгүй (дуусгах → хийх БИШІ)
- Утгагүй үг БАЙХГҮЙ (хэдүүлэх гэх мэт)
- Англи хэл БАЙХГҮЙ
- Тайлбар БАЙХГҮЙ

Зөвхөн JSON array буцаа."""

        user_prompt = f"""Энэ протоколоос ажил үүрэг, шийдвэр гарга. АГУУЛГА ХАДГАЛ.

ПРОТОКОЛ:
{text}

Зөвхөн JSON array буцаа. Нэр, огноо, ажлыг ӨӨРЧЛӨХГҮЙ."""

        try:
            response = chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                options={
                    "temperature": 0.15,  # 0.2 → 0.15 (илүү консерватив)
                    "top_p": 0.8,
                    "num_predict": 2000,
                    "repeat_penalty": 1.1,
                }
            )
            
            content = response["message"]["content"].strip()
            
            # JSON гаргаж авах
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if not json_match:
                raise RuntimeError(
                    f"❌ SLM JSON буцаагаагүй!\n"
                    f"   Үр дүн: {content[:200]}..."
                )
            
            try:
                actions = json.loads(json_match.group())
            except json.JSONDecodeError as e:
                raise RuntimeError(
                    f"❌ JSON parsing алдаа!\n"
                    f"   Алдаа: {str(e)}\n"
                    f"   SLM үр дүн: {json_match.group()[:200]}..."
                )
            
            # УТГЫН ШАЛГАЛТ + Validation
            validated_actions = []
            for action in actions:
                # Үндсэн validation
                if not self._validate_action(action):
                    print(f"   ⚠️  Буруу бүтэцтэй action алгассан: {action}")
                    continue
                
                # Утгын шалгалт
                if not self._check_action_meaning(action, text):
                    print(f"   ⚠️  Утгагүй action алгассан: {action.get('who', '?')} - {action.get('action', '?')[:30]}")
                    continue
                
                validated_actions.append(action)
            
            if not validated_actions:
                raise RuntimeError(
                    f"❌ Зөв action олдсонгүй!\n"
                    f"   SLM {len(actions)} action буцаасан боловч\n"
                    f"   бүгд буруу эсвэл утгагүй байна"
                )
            
            print(f"   ✅ SLM: {len(validated_actions)} action олсон")
            return validated_actions
            
        except json.JSONDecodeError as e:
            raise RuntimeError(f"❌ JSON parsing алдаа!\n{str(e)}")
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise
            else:
                raise RuntimeError(
                    f"❌ Action extraction алдаа!\n"
                    f"   Model: {self.model}\n"
                    f"   Алдаа: {str(e)}"
                )
    
    def _validate_action(self, action: Dict) -> bool:
        """
        Action item зөв бүтэцтэй эсэхийг шалгах
        """
        required_fields = ["who", "action"]
        
        # Шаардлагатай талбарууд байгаа эсэх
        for field in required_fields:
            if field not in action or not action[field]:
                return False
        
        # Утга хоосон биш эсэх
        if len(action["who"].strip()) < 2 or len(action["action"].strip()) < 5:
            return False
        
        return True
    
    def _check_action_meaning(self, action: Dict, original_text: str) -> bool:
        """
        ШИНЭ: Action-ийн утга зөв эсэх шалгах
        
        Шалгах зүйлс:
        1. Хариуцагч нэр анхны текстэд байгаа эсэх
        2. Огноо анхны текстэд байгаа эсэх
        3. Утгагүй үг байгаа эсэх
        """
        who = action.get("who", "").strip()
        action_text = action.get("action", "").strip()
        due = action.get("due", "").strip()
        
        # 1. Нэр шалгах - анхны текстэд байгаа эсэх
        # "Анна", "А.Анна", "Анны" гэх мэт хувилбар зөвшөөрнө
        if who and who not in ["Тодорхойгүй", "Хурлын шийдвэр"]:
            # Үндсэн нэрийг гаргах (А.Анна → Анна)
            base_name = who.split('.')[-1]
            
            # Анхны текстэд байгаа эсэх
            if base_name not in original_text and who not in original_text:
                print(f"      ⚠️ '{who}' нэр анхны текстэд байхгүй")
                return False
        
        # 2. Утгагүй үг шалгах
        nonsense_patterns = [
            r'хэдүүлэх',  # Утгагүй үйл үг
            r'[а-яёүө]{20,}',  # Хэт урт үг
            r'\b[а-яёүө]\b\s+\b[а-яёүө]\b\s+\b[а-яёүө]\b',  # "а б в"
        ]
        
        combined = f"{who} {action_text} {due}"
        for pattern in nonsense_patterns:
            if re.search(pattern, combined):
                print(f"      ⚠️ Утгагүй үг: {pattern}")
                return False
        
        # 3. Огноо шалгах - хэрэв байвал анхны текстэд байгаа эсэх
        if due and due not in ["Тодорхойгүй", "Хугацаа заагаагүй"]:
            # Огноо patterns
            date_keywords = [
                'даваа', 'мягмар', 'лхагва', 'пүрэв', 'баасан', 'бямба', 'ням',
                'долоо хоног', 'сар', 'өдөр', 'жил', 'өнөөдөр', 'маргааш', 'ирэх'
            ]
            
            has_date_keyword = any(kw in due.lower() for kw in date_keywords)
            
            if has_date_keyword:
                # Огноо анхны текстэд байгаа эсэх
                date_in_original = any(kw in original_text.lower() for kw in date_keywords if kw in due.lower())
                
                if not date_in_original:
                    print(f"      ⚠️ '{due}' огноо анхны текстэд байхгүй")
                    return False
        
        # 4. Action текст хоосон эсвэл хэт богино эсэх
        if len(action_text) < 5:
            print(f"      ⚠️ Ажил хэт богино: '{action_text}'")
            return False
        
        return True
    
    def extract_action_summary(self, actions: List[Dict]) -> Dict:
        """
        Action items-ийн товч тайлан
        """
        summary = {
            "total_actions": len(actions),
            "by_type": {},
            "by_person": {},
            "with_deadline": 0,
            "without_deadline": 0
        }
        
        for action in actions:
            # Төрлөөр
            action_type = action.get("type", "unknown")
            summary["by_type"][action_type] = summary["by_type"].get(action_type, 0) + 1
            
            # Хүнээр
            who = action.get("who", "Unknown")
            summary["by_person"][who] = summary["by_person"].get(who, 0) + 1
            
            # Хугацаатай эсэх
            due = action.get("due", "")
            if due and due != "Хугацаа заагаагүй" and due != "Тодорхойгүй":
                summary["with_deadline"] += 1
            else:
                summary["without_deadline"] += 1
        
        return summary


# ============================================
# ТЕСТЛЭХ КОД
# ============================================

def test_slm_action_extractor():
    """
    Action extractor тестлэх
    """
    print("\n" + "="*60)
    print("УТГА ХАДГАЛАХ ACTION EXTRACTOR ТЕСТ")
    print("="*60 + "\n")
    
    try:
        extractor = SLMOnlyActionExtractor()
        
        # ТЕСТ 1: Огноотой текст
        test_text = """
        Анна: Би төслийг даваа гарагт дуусгах болно.
        Жон: Би тайланг мягмар гарагт илгээнэ.
        Тогтоол: Ирэх долоо хоногт бүх ажлыг дуусгах.
        """
        
        print("Анхны текст:")
        print(test_text)
        print("\n" + "-"*60 + "\n")
        
        actions = extractor.extract_actions_with_llm(test_text)
        
        print("✅ Олсон action items:\n")
        for i, action in enumerate(actions, 1):
            print(f"{i}. {action['who']}: {action['action']}")
            print(f"   Хугацаа: {action.get('due', 'Тодорхойгүй')}")
            print(f"   Төрөл: {action.get('type', 'unknown')}")
            
            # ШАЛГАЛТ: Огноо хадгалагдсан эсэх
            due = action.get('due', '')
            if 'даваа' in test_text.lower() and i == 1:
                if 'даваа' in due.lower():
                    print(f"   ✅ Огноо хадгалагдсан")
                else:
                    print(f"   ❌ Огноо алдагдсан! ('{due}' байх ёстой 'даваа гараг')")
            
            print()
        
        # Summary
        summary = extractor.extract_action_summary(actions)
        print("-"*60)
        print(f"Нийт: {summary['total_actions']} ажил үүрэг")
        print(f"Төрөл: {summary['by_type']}")
        print(f"Хугацаатай: {summary['with_deadline']}, "
              f"Хугацаагүй: {summary['without_deadline']}")
        
        print("\n" + "="*60)
        print("✅ АМЖИЛТТАЙ!")
        print("="*60 + "\n")
        
    except RuntimeError as e:
        print("\n" + "="*60)
        print("❌ АЛДАА ГАРЛАА")
        print("="*60)
        print(f"\n{str(e)}\n")
        return False
    
    return True


if __name__ == "__main__":
    test_slm_action_extractor()