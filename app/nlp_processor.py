from ufal.udpipe import Model, Pipeline
from typing import Dict, List 

class MongolianNLPProcessor:
    def __init__(self, model_path="mn_model.udpipe"):
        self.model = Model.load(model_path)
        if not self.model:
            raise Exception(f"UDPipe модел ачаалагдсангүй: {model_path}")
        
        # БҮРЭН ПАРАМЕТР
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
        """
        processed = self.pipeline.process(text)
        sentences = self._parse_conllu(processed)
        return {"sentences": sentences}
    
    def extract_named_entities(self, processed_text: Dict) -> List[str]:
        """
        PROPN (proper noun) төрлийн үгсийг гаргах
        """
        entities = []
        for sentence in processed_text["sentences"]:
            for token in sentence:
                if token["upos"] == "PROPN":  # Нэр үг
                    entities.append(token["form"])
        return list(set(entities))