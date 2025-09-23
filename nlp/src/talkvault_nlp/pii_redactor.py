"""
PII (Personally Identifiable Information) Redactor
"""
import re
import spacy
from typing import List, Tuple, Dict

class PIIRedactor:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Warning: spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        # PII patterns
        self.pii_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b',
            'ssn': r'\b\d{3}-?\d{2}-?\d{4}\b',
            'credit_card': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            'ip_address': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            'url': r'https?://[^\s<>"\{\}|\\^`\[\]]+',
            'zipcode': r'\b\d{5}(?:-\d{4})?\b'
        }
        
        # Named entities to redact
        self.sensitive_entities = ['PERSON', 'ORG', 'GPE', 'LOC']
    
    async def redact_pii(self, text: str) -> str:
        """Redact PII from text"""
        if not text or not text.strip():
            return text
        
        redacted_text = text
        
        # Apply pattern-based redaction
        for pii_type, pattern in self.pii_patterns.items():
            redacted_text = re.sub(pattern, f'[{pii_type.upper()}_REDACTED]', redacted_text, flags=re.IGNORECASE)
        
        # Apply NER-based redaction if spaCy is available
        if self.nlp:
            redacted_text = self._redact_named_entities(redacted_text)
        
        return redacted_text
    
    def _redact_named_entities(self, text: str) -> str:
        """Redact named entities using spaCy NER"""
        try:
            doc = self.nlp(text)
            
            # Sort entities by start position in reverse order to maintain text positions
            entities = sorted(doc.ents, key=lambda x: x.start_char, reverse=True)
            
            redacted_text = text
            
            for ent in entities:
                if ent.label_ in self.sensitive_entities:
                    # Replace entity with redacted placeholder
                    placeholder = f'[{ent.label_}_REDACTED]'
                    redacted_text = redacted_text[:ent.start_char] + placeholder + redacted_text[ent.end_char:]
            
            return redacted_text
            
        except Exception as e:
            print(f"Error in NER redaction: {e}")
            return text
    
    def get_redaction_stats(self, original_text: str, redacted_text: str) -> Dict:
        """Get statistics about redactions performed"""
        redaction_count = {}
        
        # Count different types of redactions
        for pii_type in self.pii_patterns.keys():
            pattern = f'\[{pii_type.upper()}_REDACTED\]'
            count = len(re.findall(pattern, redacted_text, re.IGNORECASE))
            if count > 0:
                redaction_count[pii_type] = count
        
        # Count NER redactions
        for entity_type in self.sensitive_entities:
            pattern = f'\[{entity_type}_REDACTED\]'
            count = len(re.findall(pattern, redacted_text, re.IGNORECASE))
            if count > 0:
                redaction_count[entity_type.lower()] = count
        
        return {
            'total_redactions': sum(redaction_count.values()),
            'redaction_types': redaction_count,
            'original_length': len(original_text),
            'redacted_length': len(redacted_text)
        }
