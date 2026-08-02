import logging
from typing import Dict, Any, List
import asyncio
from collections import Counter

from pipeline.config import SEED_QUESTIONS
from server.retriever import retriever
from server.synthesizer import synthesizer

logger = logging.getLogger(__name__)

_cached_themes = None
_cached_themes_hash = None

def get_emergent_themes() -> List[Dict[str, Any]]:
    """Scans ChromaDB metadata to find frequent, interesting tag combinations."""
    global _cached_themes, _cached_themes_hash
    
    try:
        # Fetch all metadata from ChromaDB
        results = retriever.collection.get(include=["metadatas"])
        metadatas = results.get("metadatas", [])
        
        if not metadatas:
            return ["No data available to detect themes."]
            
        # Very simple hash based on count of metadatas
        current_hash = len(metadatas)
        if _cached_themes is not None and _cached_themes_hash == current_hash:
            return _cached_themes
            
        # Look for combinations of Category + Barrier/Frustration
        theme_counter = Counter()
        for meta in metadatas:
            cat = meta.get("category_mentioned", "not stated")
            barrier = meta.get("barrier_type", "not stated")
            
            if cat != "not stated" and cat != "other" and barrier != "not stated":
                theme_key = (barrier, cat)
                theme_counter[theme_key] += 1
                
        # Load items to extract real examples
        from pipeline.store.tagged_store import tagged_store
        items = tagged_store.get_all()
        
        # Get top 3 themes
        top_themes = []
        for (barrier, cat), count in theme_counter.most_common(3):
            # Find an example quote for this theme
            examples = [
                i["text"] for i in items 
                if i.get("metadata", {}).get("barrier_type") == barrier 
                and i.get("metadata", {}).get("category_mentioned") == cat 
                and i.get("metadata", {}).get("relevant")
            ]
            
            # Generate a PM-grade title and description using the AI Synthesizer
            if examples:
                ai_theme = synthesizer.generate_theme_title(barrier, cat, examples)
                title = ai_theme.get("title", f"{barrier.title()} in {cat}")
                desc = ai_theme.get("description", f"Identified in {count} reviews.")
            else:
                title = f"{barrier.title()} in {cat}"
                desc = f"Identified in {count} reviews."
                
            top_themes.append({
                "title": title,
                "mentions": count,
                "description": desc,
                "barrier": barrier,
                "category": cat
            })
        
        if not top_themes:
            return []
            
        _cached_themes = top_themes
        _cached_themes_hash = current_hash
        return top_themes
    except Exception as e:
        logger.error(f"Failed to extract emergent themes: {e}")
        return []

def get_sneak_peek_data() -> Dict[str, Any]:
    """Extracts high-level insights for the sneak peek section from tagged store."""
    from pipeline.store.tagged_store import tagged_store
    items = tagged_store.get_all()
    
    categories = Counter()
    intents = Counter()
    behaviors = Counter()
    drivers = Counter()
    
    for item in items:
        meta = item.get("metadata", {})
        if not meta.get("relevant"):
            continue
            
        cat = meta.get("category_mentioned")
        is_valid_cat = cat and cat != "not stated" and cat != "other"
        
        if is_valid_cat:
            categories[cat] += 1
            
        intent = meta.get("discovery_channel")
        if intent and intent != "not stated":
            intents[intent] += 1
                
        behavior = meta.get("behavior_type")
        if behavior and behavior != "not stated":
            behaviors[behavior] += 1
            
        driver = meta.get("purchase_driver")
        if driver and driver != "not stated":
            drivers[driver] += 1
            
    def _to_chart_data(counter: Counter, top_k: int = 5, format_title: bool = False) -> List[Dict[str, Any]]:
        if not counter:
            return []
        total = sum(counter.values())
        top_items = counter.most_common(top_k)
        chart_data = []
        captured = 0
        for name, count in top_items:
            # Replaces hyphens with spaces and titles it
            display_name = name.replace("-", " ").title() if format_title else name
            percentage = round((count / total) * 100, 1) if total > 0 else 0
            chart_data.append({"name": display_name, "value": count, "percentage": percentage})
            captured += count
            
        other_count = total - captured
        if other_count > 0:
            percentage = round((other_count / total) * 100, 1) if total > 0 else 0
            chart_data.append({"name": "Other", "value": other_count, "percentage": percentage})
            
        return chart_data
        
    return {
        "most_popular": _to_chart_data(categories),
        "top_behaviors": _to_chart_data(behaviors, format_title=True),
        "shopping_intent": _to_chart_data(intents, format_title=True),
        "purchase_drivers": _to_chart_data(drivers, format_title=True)
    }

def generate_insight_summary(question_indices: List[int] | str = "all") -> Dict[str, Any]:
    """
    Runs the seed questions through the RAG pipeline to generate a summary.
    """
    if question_indices == "all":
        questions_to_run = SEED_QUESTIONS
    else:
        questions_to_run = [SEED_QUESTIONS[i] for i in question_indices if i < len(SEED_QUESTIONS)]
        
    answers = []
    
    for q in questions_to_run:
        try:
            logger.info(f"Generating summary for question: {q}")
            evidence = retriever.retrieve(query=q, top_k=8)
            messages = [{"role": "user", "content": q}]
            
            # Use non-streaming synthesis for the report
            answer_text = synthesizer.synthesize(messages, evidence)
            
            answers.append({
                "q": q,
                "a": answer_text
            })
        except Exception as e:
            logger.error(f"Failed to generate summary for '{q}': {e}")
            answers.append({
                "q": q,
                "a": f"Failed to generate answer: {str(e)}"
            })
            
    themes = get_emergent_themes()
    
    return {
        "answers": answers,
        "emergent_themes": themes
    }
