"""
Meeting Summarizer using TextRank algorithm
"""
import spacy
from typing import List
import re

class MeetingSummarizer:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")  # Using small model as fallback
        except OSError:
            print("Warning: spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
    
    async def summarize(self, text: str, max_sentences: int = 5) -> str:
        """Summarize meeting text using extractive summarization"""
        if not text or not text.strip():
            return "No content to summarize"
        
        if self.nlp is None:
            # Fallback to simple sentence extraction
            return self._simple_summarize(text, max_sentences)
        
        try:
            # Process text with spaCy
            doc = self.nlp(text)
            
            # Extract sentences
            sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 20]
            
            if len(sentences) <= max_sentences:
                return " ".join(sentences)
            
            # Simple scoring based on sentence length and position
            scored_sentences = []
            for i, sentence in enumerate(sentences):
                score = len(sentence.split())  # Word count as basic score
                if i < len(sentences) * 0.3:  # Boost early sentences
                    score *= 1.2
                scored_sentences.append((sentence, score))
            
            # Sort by score and take top sentences
            scored_sentences.sort(key=lambda x: x[1], reverse=True)
            top_sentences = [sent[0] for sent in scored_sentences[:max_sentences]]
            
            return " ".join(top_sentences)
            
        except Exception as e:
            print(f"Error in summarization: {e}")
            return self._simple_summarize(text, max_sentences)
    
    def _simple_summarize(self, text: str, max_sentences: int = 5) -> str:
        """Fallback simple summarization"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if len(sentences) <= max_sentences:
            return ". ".join(sentences) + "."
        
        # Take first and last sentences, and some from middle
        selected = []
        selected.append(sentences[0])  # First sentence
        
        if max_sentences > 2:
            middle_start = len(sentences) // 3
            middle_end = 2 * len(sentences) // 3
            middle_sentences = sentences[middle_start:middle_end]
            selected.extend(middle_sentences[:max_sentences-2])
        
        if max_sentences > 1:
            selected.append(sentences[-1])  # Last sentence
        
        return ". ".join(selected) + "."
