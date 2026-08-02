import re
import logging
from typing import List
from pipeline.connectors.base import RawItem

logger = logging.getLogger(__name__)

class SpamFilter:
    """Flags promotional content and bot-like behavior."""
    
    def __init__(self):
        self.spam_patterns = [
            r"http[s]?://",                # Any URLs
            r"bit\.ly",                     # Link shorteners
            r"wa\.me",                      # WhatsApp links
            r"subscribe to my channel",     # YouTube self-promo
            r"use code",                    # Referral codes
            r"referral",                    
            r"click here",
            r"earn money",
            r"discount code",
            # Adult / Promo / Scams
            r"onlyfans",
            r"kik username",
            r"telegram:",
            r"adult toys",
            r"3way",
            r"cam2cam",
            r"sexting",
            # B2B / Hiring
            r"gohighlevel",
            r"social media chatbot",
            r"hiring for",
            r"digital partner",
            r"crypto",
            r"bitcoin",
            r"usdt",
            r"eth"
        ]
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.spam_patterns]

    def process(self, items: List[RawItem]) -> List[RawItem]:
        """Flags items with metadata['is_spam'] = True/False."""
        spam_count = 0
        
        for item in items:
            text = item.text
            is_spam = False
            
            # Check length heuristic (nonsense strings)
            if len(text) < 5 and not any(char.isalpha() for char in text):
                is_spam = True
            
            # Check patterns
            if not is_spam:
                for pattern in self.compiled_patterns:
                    if pattern.search(text):
                        is_spam = True
                        break
            
            item.metadata["is_spam"] = is_spam
            if is_spam:
                spam_count += 1
                
        logger.info(f"SpamFilter: Flagged {spam_count} items as spam.")
        return items
