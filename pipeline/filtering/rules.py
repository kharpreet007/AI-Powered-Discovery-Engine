import logging
from typing import List
from pipeline.connectors.base import RawItem
from pipeline.config import CATEGORY_KEYWORDS, BEHAVIOR_SIGNAL_WORDS, TECH_ONLY_VOCAB

logger = logging.getLogger(__name__)

class RuleBasedFilter:
    """Zero-cost relevance filter to discard noise before expensive LLM extraction."""
    
    def __init__(self):
        # Flatten all category keywords into a single set for fast lookup
        self.all_category_keywords = set(
            word.lower() for words in CATEGORY_KEYWORDS.values() for word in words
        )
        self.behavior_keywords = set(word.lower() for word in BEHAVIOR_SIGNAL_WORDS)
        self.tech_keywords = set(word.lower() for word in TECH_ONLY_VOCAB)
        self.delivery_complaints = {"delivery", "late", "slow", "delayed", "time", "wait"}
        
        self.generic_phrases = {
            "very good", "good", "nice", "great app", "worst app", "bad service", 
            "nice app", "very bad", "excellent", "superb", "super", "ok", "average", 
            "awesome", "good app", "bad app", "very nice", "best app", "great experience",
            "good work", "wonderful service", "best app for"
        }
        self.snippeting_keywords = {"blinkit", "zepto", "instamart", "swiggy", "zomato", "grocery", "minute"}

    def process(self, items: List[RawItem]) -> List[RawItem]:
        """Flags items with metadata['stage1_passed'] = True/False."""
        passed_count = 0
        failed_count = 0
        
        for item in items:
            text = item.text.lower()
            
            # If already flagged as spam, it fails stage 1 automatically
            if item.metadata.get("is_spam", False):
                item.metadata["stage1_passed"] = False
                failed_count += 1
                continue
                
            has_category = any(kw in text for kw in self.all_category_keywords)
            has_behavior = any(kw in text for kw in self.behavior_keywords)
            has_tech = any(kw in text for kw in self.tech_keywords)
            has_delivery_complaint = any(kw in text for kw in self.delivery_complaints)
            
            passed = True
            
            # Clean text of basic punctuation for generic matching
            clean_text = "".join(c for c in text if c.isalpha() or c.isspace()).strip()
            
            # Rule 1: Generic Phrase Pruning
            if clean_text in self.generic_phrases:
                passed = False
                
            # Rule 2: Too short AND no category mention -> discard
            elif len(text) < 20 and not has_category:
                passed = False
                
            # Rule 3: Only tech vocabulary AND no behavior signal AND no delivery complaints -> discard
            elif has_tech and not has_behavior and not has_delivery_complaint:
                passed = False
                
            # Rule 4: Snippeting for long text (e.g. Reddit)
            elif passed and len(text.split()) > 100:
                import re
                sentences = re.split(r'(?<=[.!?]) +', item.text)
                relevant_sentences = []
                for idx, sentence in enumerate(sentences):
                    if any(kw in sentence.lower() for kw in self.snippeting_keywords):
                        # Keep surrounding sentences
                        start = max(0, idx - 1)
                        end = min(len(sentences), idx + 2)
                        for s in sentences[start:end]:
                            if s not in relevant_sentences:
                                relevant_sentences.append(s)
                
                if relevant_sentences:
                    item.text = " ".join(relevant_sentences)
                else:
                    passed = False # If it's a huge post and doesn't mention our keywords, drop it
                
            item.metadata["stage1_passed"] = passed
            if passed:
                passed_count += 1
            else:
                failed_count += 1
                
        logger.info(f"RuleBasedFilter: Passed {passed_count}, Failed {failed_count}.")
        return items
