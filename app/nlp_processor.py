"""
UDPipe ашиглан Монгол хэлний NLP боловсруулалт
"""

from ufal.udpipe import Model, Pipeline
from typing import Dict, List


class MongolianNLPProcessor:
    """
    UDPipe ашиглан текст боловсруулах:
    - Tokenization
    - POS tagging
    - Named Entity Recognition
    """
    
    def __init__(self, model_path: str = "mn_model.udpipe"):
        """
        UDPipe модель ачаалах
        
        Args:
            model_path: UDPipe модель файлын зам
        
        Raises:
            Exception: Модель ачаалагдахгүй бол
        """
        self.model = Model.load(model_path)
        
        if not self.model:
            raise Exception(f"UDPipe модел ачаалагдсангүй: {model_path}")
        
        # Pipeline үүсгэх (БҮРЭН параметр)
        self.pipeline = Pipeline(
            self.model,
            "tokenize",           # Tokenize options
            Pipeline.DEFAULT,     # Tagger options  
            Pipeline.DEFAULT,     # Parser options
            "conllu"             # Output format
        )
    
    def process_text(self, text: str) -> Dict:
        """
        Текстийг боловсруулж CoNLL-U формат гаргах
        
        Args:
            text: Боловсруулах текст
        
        Returns:
            Dict with 'sentences' key containing parsed sentences
        """
        try:
            processed = self.pipeline.process(text)
            sentences = self._parse_conllu(processed)
            
            return {
                "sentences": sentences,
                "sentence_count": len(sentences)
            }
        except Exception as e:
            print(f"⚠️  UDPipe боловсруулалт алдаа: {e}")
            return {"sentences": [], "sentence_count": 0}
    
    def _parse_conllu(self, conllu_text: str) -> List[List[Dict]]:
        """
        CoNLL-U форматыг задлах
        
        CoNLL-U формат жишээ:
        # sent_id = 1
        # text = Өнөөдөр хурал болно.
        1    Өнөөдөр    өнөөдөр    NOUN    ...
        2    хурал      хурал      NOUN    ...
        
        Args:
            conllu_text: CoNLL-U формат текст
        
        Returns:
            Өгүүлбэр бүр token-уудын жагсаалт
        """
        sentences = []
        current_sentence = []
        
        for line in conllu_text.split('\n'):
            line = line.strip()
            
            # Тайлбар мөр (# -ээр эхлэх)
            if line.startswith('#'):
                continue
            
            # Хоосон мөр = өгүүлбэр дууссан
            if not line:
                if current_sentence:
                    sentences.append(current_sentence)
                    current_sentence = []
                continue
            
            # Token мэдээлэл задлах
            parts = line.split('\t')
            if len(parts) >= 10:
                token_info = {
                    "id": parts[0],           # Token ID
                    "form": parts[1],         # Үгийн хэлбэр
                    "lemma": parts[2],        # Үндсэн хэлбэр
                    "upos": parts[3],         # Universal POS tag
                    "xpos": parts[4],         # Language-specific POS
                    "feats": parts[5],        # Морфологийн шинж чанар
                    "head": parts[6],         # Syntactic head
                    "deprel": parts[7],       # Dependency relation
                    "deps": parts[8],         # Enhanced dependencies
                    "misc": parts[9]          # Miscellaneous
                }
                current_sentence.append(token_info)
        
        # Сүүлчийн өгүүлбэр
        if current_sentence:
            sentences.append(current_sentence)
        
        return sentences
    
    def extract_named_entities(self, processed_text: Dict) -> List[str]:
        """
        Нэр үгсийг (PROPN) гаргаж авах
        
        Args:
            processed_text: process_text()-ийн үр дүн
        
        Returns:
            Нэрсийн жагсаалт
        """
        entities = set()
        
        for sentence in processed_text.get("sentences", []):
            for token in sentence:
                # Нэр үг (Proper Noun)
                if token.get("upos") == "PROPN":
                    entities.add(token["form"])
        
        return sorted(list(entities))
    
    def extract_verbs(self, processed_text: Dict) -> List[Dict]:
        """
        Үйл үгсийг гаргах
        
        Args:
            processed_text: process_text()-ийн үр дүн
        
        Returns:
            Үйл үгсийн мэдээлэл
        """
        verbs = []
        
        for sent_idx, sentence in enumerate(processed_text.get("sentences", [])):
            for token in sentence:
                if token.get("upos") == "VERB":
                    verbs.append({
                        "verb": token["form"],
                        "lemma": token.get("lemma", ""),
                        "sentence_index": sent_idx
                    })
        
        return verbs
    
    def get_statistics(self, processed_text: Dict) -> Dict:
        """
        Текстийн статистик мэдээлэл
        
        Args:
            processed_text: process_text()-ийн үр дүн
        
        Returns:
            Статистик мэдээлэл
        """
        stats = {
            "sentence_count": 0,
            "word_count": 0,
            "pos_distribution": {},
            "avg_sentence_length": 0.0
        }
        
        sentences = processed_text.get("sentences", [])
        stats["sentence_count"] = len(sentences)
        
        total_words = 0
        for sentence in sentences:
            total_words += len(sentence)
            
            for token in sentence:
                pos = token.get("upos", "UNKNOWN")
                stats["pos_distribution"][pos] = stats["pos_distribution"].get(pos, 0) + 1
        
        stats["word_count"] = total_words
        
        if stats["sentence_count"] > 0:
            stats["avg_sentence_length"] = round(
                total_words / stats["sentence_count"], 2
            )
        
        return stats