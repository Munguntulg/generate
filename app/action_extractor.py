#!/usr/bin/env python3
"""
SLM-ONLY Action Extractor - Fallback байхгүй
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
    Зөвхөн SLM ашиглах action extractor
    """
    
    def __init__(self, nlp_processor=None):
        self.nlp = nlp_processor
        self.model = "qwen2.5:7b"
        
        # SLM бэлэн эсэх шалгах
        if not OLLAMA_AVAILABLE:
            raise RuntimeError(
                "❌ Ollama суулгаагүй байна!\n"
                "   Суулгах: pip install ollama"
            )
        
        print(f"✅ Action Extractor бэлэн: {self.model}")
    
    def extract_actions_with_llm(self, text: str) -> List[Dict]:
        """
        SLM ашиглан action items гаргах
        
        Raises:
            RuntimeError: SLM ажиллахгүй бол
        """
        if not OLLAMA_AVAILABLE:
            raise RuntimeError("❌ SLM ажиллахгүй байна (Ollama суулгаагүй)")
        
        system_prompt = """Та протоколоос ажил үүрэг, шийдвэр гаргадаг мэргэжилтэн.

🎯 ОЛОХ ЗҮЙЛС:
1. ХЭН - Хариуцагч (нэр)
2. ЮУ - Хийх ажил
3. ХЭЗЭЭ - Хугацаа (даваа гараг, ирэх долоо хоног гэх мэт)
4. ТӨРӨЛ - "action" эсвэл "decision"

📋 JSON ФОРМАТ (ЗӨВХӨН ЭНЭ):
[
    {
        "who": "Хариуцагч нэр",
        "action": "Хийх ажлын тодорхойлолт",
        "due": "Хугацаа буюу 'Хугацаа заагаагүй'",
        "type": "action эсвэл decision",
        "confidence": 0.8
    }
]

ЖИШЭЭ:

Текст: "Анна: Би draft даваа гарагт илгээнэ."
JSON:
[{"who": "Анна", "action": "draft илгээх", "due": "даваа гараг", "type": "action", "confidence": 0.9}]

Текст: "Тогтоол: Ирэх долоо хоногт дуусгах."
JSON:
[{"who": "Хурлын шийдвэр", "action": "Ажлыг дуусгах", "due": "ирэх долоо хоног", "type": "decision", "confidence": 0.95}]

⚠️ ЧУХАЛ:
- Зөвхөн JSON array буцаа
- Тодорхой хариуцагч, ажил байхгүй бол ОРХИ
- "Тогтоол:", "Шийдвэр:" → type: "decision"
- Англи хэл ашиглахгүй
- Нэмэлт тайлбар бичихгүй"""

        user_prompt = f"""Энэ протоколоос ажил үүрэг, шийдвэр гарга:

{text}

Зөвхөн JSON array буцаа."""

        try:
            response = chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                options={
                    "temperature": 0.2,
                }
            )
            
            content = response["message"]["content"].strip()
            
            # JSON гаргаж авах
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if not json_match:
                raise RuntimeError(
                    f"❌ SLM JSON буцаагаагүй!\n"
                    f"   Үр дүн: {content[:200]}...\n"
                    f"   JSON формат шаардлагатай"
                )
            
            try:
                actions = json.loads(json_match.group())
            except json.JSONDecodeError as e:
                raise RuntimeError(
                    f"❌ JSON parsing алдаа!\n"
                    f"   Алдаа: {str(e)}\n"
                    f"   SLM үр дүн: {json_match.group()[:200]}..."
                )
            
            # Validation
            validated_actions = []
            for action in actions:
                if self._validate_action(action):
                    validated_actions.append(action)
                else:
                    print(f"   ⚠️  Буруу бүтэцтэй action алгассан: {action}")
            
            if not validated_actions:
                raise RuntimeError(
                    f"❌ Зөв action олдсонгүй!\n"
                    f"   SLM {len(actions)} action буцаасан боловч\n"
                    f"   бүгд буруу бүтэцтэй байна"
                )
            
            print(f"   ✅ SLM: {len(validated_actions)} action олсон")
            return validated_actions
            
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"❌ JSON parsing алдаа!\n"
                f"   {str(e)}"
            )
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise  # Манай алдааг дахин шидэх
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
    print("SLM-ONLY ACTION EXTRACTOR ТЕСТ")
    print("="*60 + "\n")
    
    try:
        extractor = SLMOnlyActionExtractor()
        
        test_text = """
        Анна: Би draft даваа гарагт илгээнэ.
        Жон: Би review хийж сэтгэгдэл өгнө.
        Тогтоол: Ирэх долоо хоногт эцсийн хувилбарыг илгээх.
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