import json
import re
from typing import List, Dict, Optional

try:
    from ollama import chat
except ImportError:
    print("⚠️  Ollama суулгаагүй байна. pip install ollama")
    chat = None


class ActionItemExtractor:
    """
    Протоколоос ажил үүрэг, шийдвэрүүдийг гаргаж авах
    """
    
    def __init__(self, nlp_processor=None):
        self.nlp = nlp_processor
        self.model = "mistral"
    
    def extract_actions_with_llm(self, text: str) -> List[Dict]:
        """
        LLM ашиглан action items гаргах
        """
        if chat is None:
            print("⚠️  Ollama байхгүй байна, rule-based ашиглана")
            return self._extract_actions_rule_based(text)
        
        system_prompt = """Та протоколоос ажил үүрэг, шийдвэр гаргадаг мэргэжилтэн.

Дараах зүйлсийг олж гаргах:
1. ХЭН юу хийх вэ (Хариуцагч)
2. ЮУ хийх вэ (Үйлдэл/Ажил)
3. ХЭЗЭЭ дуусгах вэ (Хугацаа)
4. Төрөл: "шийдвэр" эсвэл "ажил"

JSON array форматаар ЗӨВХӨН дараах бүтэцтэй буцаа:
[
    {
        "who": "Хариуцагч нэр",
        "action": "Хийх ажлын тодорхойлолт",
        "due": "Хугацаа (даваа гараг, ирэх долоо хоног гэх мэт)",
        "type": "action эсвэл decision",
        "confidence": 0.0-1.0
    }
]

ЧУХАЛ: 
- Зөвхөн JSON array буцаа, нэмэлт тайлбар бичихгүй
- Тодорхой хариуцагч, үйлдэл байхгүй бол тухайн зүйлийг орхи
- "Тогтоол:", "Шийдвэр:" гэсэн хэсгүүдийг анхаар"""

        user_prompt = f"""Энэ хурлын протоколоос ажил үүрэг, шийдвэрүүдийг гарга:

{text}

Жишээ өгүүлбэрүүд:
- "Анна draft ийг даваа гарагт илгээх болно" → Анна, draft илгээх, даваа гараг, action
- "Тогтоол: Ирэх даваа гарагт эцсийн хувилбарыг илгээх" → Тогтоол (бүгд), эцсийн хувилбар илгээх, даваа гараг, decision
- "Би тайлангийн эхний хэсгийг бэлдэх" → Тухайн хүн, тайланг бэлдэх, тодорхойгүй, action"""

        try:
            response = chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                options={
                    "temperature": 0.2,  # Тогтвортой үр дүн
                }
            )
            
            content = response["message"]["content"].strip()
            
            # JSON гаргаж авах
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                actions = json.loads(json_match.group())
                
                # Validation
                validated_actions = []
                for action in actions:
                    if self._validate_action(action):
                        validated_actions.append(action)
                
                return validated_actions
            else:
                print("LLM JSON буцаагаагүй, rule-based ашиглана")
                return self._extract_actions_rule_based(text)
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing алдаа: {e}")
            return self._extract_actions_rule_based(text)
        except Exception as e:
            print(f"Action extraction алдаа: {e}")
            return self._extract_actions_rule_based(text)
    
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
    
    def _extract_actions_rule_based(self, text: str) -> List[Dict]:
        """
        Rule-based action extraction (fallback)
        """
        actions = []
        
        # Шийдвэр гаргах хэсгийг хайх
        decision_section = self._extract_decisions(text)
        actions.extend(decision_section)
        
        # Хувь хүний ажил үүргийг хайх
        individual_actions = self._extract_individual_actions(text)
        actions.extend(individual_actions)
        
        return actions
    
    def _extract_decisions(self, text: str) -> List[Dict]:
        """
        "Тогтоол:", "Шийдвэр:" хэсгүүдээс мэдээлэл гаргах
        """
        decisions = []
        
        # Тогтоол/шийдвэр хэсгийг олох
        decision_patterns = [
            r'[Тт]огтоол\s*:\s*([^.]+)',
            r'[Шш]ийдвэр\s*:\s*([^.]+)',
            r'[Тт]огтсон\s*:\s*([^.]+)',
        ]
        
        for pattern in decision_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                decision_text = match.group(1).strip()
                
                due_date = self._extract_due_date(decision_text)
                
                decisions.append({
                    "who": "Хурлын шийдвэр",
                    "action": decision_text,
                    "due": due_date,
                    "type": "decision",
                    "confidence": 0.8
                })
        
        return decisions
    
    def _extract_individual_actions(self, text: str) -> List[Dict]:
        """
        Хувь хүний ажил үүргийг гаргах
        """
        actions = []
        
        # Монгол хэлний action үйлдэл үгс
        action_verbs = [
            "хийнэ", "илгээнэ", "бэлдэнэ", "гаргана", "хүргүүлнэ",
            "хийх", "илгээх", "бэлдэх", "гаргах", "хүргүүлэх",
            "хийж", "илгээж", "бэлдэж", "гаргаж", "хүргүүлж",
            "дуусгах", "эхлэх", "үргэлжлүүлэх", "review хийх",
            "санал өгөх", "шалгах", "нэгтгэх"
        ]
        
        verb_pattern = '|'.join(action_verbs)
        
        # Pattern: Нэр: Үйлдэл
        pattern1 = r'([А-ЯЁҮӨ][а-яёүө]+)\s*:\s*([^.]*(?:' + verb_pattern + r')[^.]*)'
        
        matches = re.finditer(pattern1, text, re.IGNORECASE)
        for match in matches:
            who = match.group(1).strip()
            action_text = match.group(2).strip()
            
            if len(action_text) > 10:  # Утга бүхий үйлдэл эсэх
                due_date = self._extract_due_date(action_text)
                
                actions.append({
                    "who": who,
                    "action": action_text,
                    "due": due_date,
                    "type": "action",
                    "confidence": 0.7
                })
        
        # Pattern: Би/Миний ... үйлдэл
        pattern2 = r'([А-ЯЁҮӨ][а-яёүө]+)\s*:\s*[Бб]и\s+([^.]*(?:' + verb_pattern + r')[^.]*)'
        
        matches = re.finditer(pattern2, text, re.IGNORECASE)
        for match in matches:
            who = match.group(1).strip()
            action_text = match.group(2).strip()
            
            if len(action_text) > 10:
                due_date = self._extract_due_date(action_text)
                
                actions.append({
                    "who": who,
                    "action": action_text,
                    "due": due_date,
                    "type": "action",
                    "confidence": 0.75
                })
        
        return actions
    
    def _extract_due_date(self, text: str) -> str:
        """
        Хугацаа илрүүлэх
        """
        date_patterns = [
            (r'(даваа|мягмар|лхагва|пүрэв|баасан|бямба|ням)\s+гараг', 'weekday'),
            (r'ирэх\s+(долоо\s+хоног|сар)', 'relative'),
            (r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', 'absolute'),
            (r'\d{1,2}[-/]\d{1,2}', 'month_day'),
            (r'өнөөдөр|маргааш|нөгөөдөр', 'relative_day'),
        ]
        
        for pattern, date_type in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group()
        
        return "Хугацаа заагаагүй"
    
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