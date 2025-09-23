"""
Action Item Extractor using rule-based approach and NLP
"""
import re
import spacy
from typing import List, Dict, Any
from datetime import datetime, timedelta
import dateparser

class ActionExtractor:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Warning: spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        # Action keywords and patterns
        self.action_keywords = [
            'will', 'shall', 'should', 'need to', 'must', 'have to', 'going to',
            'action item', 'todo', 'task', 'follow up', 'deliverable', 'deadline',
            'assign', 'responsible', 'owner', 'due', 'complete', 'finish'
        ]
        
        self.action_patterns = [
            r'(?:will|shall|should|need to|must|have to|going to)\s+(.{10,100})',
            r'action item[:\-]?\s*(.{10,100})',
            r'(?:assign|assigned to|responsible)\s+([\w\s]+?)(?:\s+(?:will|to|for))',
            r'due\s+(?:date|by|on)?\s*([^.\n]{5,30})',
            r'deadline[:\-]?\s*([^.\n]{5,30})'
        ]
    
    async def extract_actions(self, text: str) -> List[Dict[str, Any]]:
        """Extract action items from meeting text"""
        if not text or not text.strip():
            return []
        
        actions = []
        
        # Split text into sentences
        sentences = self._split_sentences(text)
        
        for i, sentence in enumerate(sentences):
            if self._contains_action_keywords(sentence):
                action = self._extract_action_from_sentence(sentence, i)
                if action:
                    actions.append(action)
        
        # Remove duplicates and merge similar actions
        actions = self._deduplicate_actions(actions)
        
        return actions
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        if self.nlp:
            doc = self.nlp(text)
            return [sent.text.strip() for sent in doc.sents]
        else:
            # Simple sentence splitting
            sentences = re.split(r'[.!?]+', text)
            return [s.strip() for s in sentences if len(s.strip()) > 10]
    
    def _contains_action_keywords(self, sentence: str) -> bool:
        """Check if sentence contains action-indicating keywords"""
        sentence_lower = sentence.lower()
        return any(keyword in sentence_lower for keyword in self.action_keywords)
    
    def _extract_action_from_sentence(self, sentence: str, index: int) -> Dict[str, Any]:
        """Extract action details from a sentence"""
        action = {
            'id': index + 1,
            'description': sentence.strip(),
            'assigned_to': self._extract_assignee(sentence),
            'due_date': self._extract_due_date(sentence),
            'priority': self._determine_priority(sentence),
            'status': 'pending',
            'extracted_from': f'Sentence {index + 1}'
        }
        
        # Clean up description
        action['description'] = self._clean_description(action['description'])
        
        return action
    
    def _extract_assignee(self, sentence: str) -> str:
        """Extract assigned person from sentence"""
        # Look for patterns like "John will", "assigned to Mary", etc.
        patterns = [
            r'(?:assigned to|assign to|responsible)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:will|shall|should)',
            r'@([A-Za-z]+(?:\s+[A-Za-z]+)?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_due_date(self, sentence: str) -> str:
        """Extract due date from sentence"""
        # Look for date patterns
        date_patterns = [
            r'due\s+(?:by|on)?\s*([^.\n,]{5,30})',
            r'deadline[:\-]?\s*([^.\n,]{5,30})',
            r'by\s+([A-Z][a-z]+\s+\d{1,2}(?:st|nd|rd|th)?)',
            r'on\s+(\d{1,2}/\d{1,2}(?:/\d{2,4})?)',
            r'(next\s+(?:week|month|friday|monday|tuesday|wednesday|thursday|saturday|sunday))',
            r'(tomorrow|today|this\s+week|next\s+week)'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match:
                date_str = match.group(1).strip()
                # Try to parse the date
                try:
                    parsed_date = dateparser.parse(date_str)
                    if parsed_date:
                        return parsed_date.strftime('%Y-%m-%d')
                except:
                    pass
                return date_str
        
        return None
    
    def _determine_priority(self, sentence: str) -> str:
        """Determine priority based on keywords"""
        sentence_lower = sentence.lower()
        
        high_priority_words = ['urgent', 'asap', 'immediately', 'critical', 'important']
        low_priority_words = ['when possible', 'eventually', 'low priority']
        
        if any(word in sentence_lower for word in high_priority_words):
            return 'high'
        elif any(word in sentence_lower for word in low_priority_words):
            return 'low'
        else:
            return 'medium'
    
    def _clean_description(self, description: str) -> str:
        """Clean and format action description"""
        # Remove extra whitespace
        description = ' '.join(description.split())
        
        # Capitalize first letter
        if description:
            description = description[0].upper() + description[1:]
        
        # Ensure it ends with proper punctuation
        if description and not description.endswith(('.', '!', '?')):
            description += '.'
        
        return description
    
    def _deduplicate_actions(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate actions based on similarity"""
        if len(actions) <= 1:
            return actions
        
        unique_actions = []
        
        for action in actions:
            is_duplicate = False
            for existing in unique_actions:
                # Simple similarity check based on description
                if self._are_similar(action['description'], existing['description']):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_actions.append(action)
        
        return unique_actions
    
    def _are_similar(self, desc1: str, desc2: str, threshold: float = 0.7) -> bool:
        """Check if two descriptions are similar"""
        # Simple word overlap similarity
        words1 = set(desc1.lower().split())
        words2 = set(desc2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        similarity = len(intersection) / len(union) if union else 0
        return similarity >= threshold
