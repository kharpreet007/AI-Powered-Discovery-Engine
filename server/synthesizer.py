import json
import logging
from typing import List, Dict, Any, Generator

import google.generativeai as genai
from groq import Groq


from pipeline.config import settings
from server.retriever import RetrievedItem

logger = logging.getLogger(__name__)

SYNTHESIS_PROMPT = """
You are a Senior Product Manager brainstorming partner for Blinkit.
We are conducting a "5 Whys" deep-dive analysis on user feedback.

You have been provided with two sets of data below:
1. [MACRO STATS]: The concrete mathematical aggregation of our database (the "Graded Forms"). Use this to find the actual macro trends and root causes (e.g. "40% of users cited Trust").
2. [MICRO QUOTES]: 2-3 vivid, exact user quotes related to the current topic to provide the "Voice of the Customer".

Follow these rules strictly:
1. Ground your answer in the [MACRO STATS] so we aren't guessing. Cite the hard numbers.
2. Weave the [MICRO QUOTES] naturally into your response to provide emotional context and empathy.
3. Engage in a natural chat progression. Do not output a rigid "5 Whys" analysis. Simply end your response with a brief, natural follow-up question to guide the user deeper.
4. Keep it concise, punchy, and highly analytical.

Data:
{retrieved_chunks_with_metadata}
"""

class Synthesizer:
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel("gemini-flash-latest")
        self.model_fallback = genai.GenerativeModel("gemini-flash-latest")
        if settings.groq_api_key:
            self.groq_client = Groq(api_key=settings.groq_api_key)
        else:
            self.groq_client = None

    def _format_evidence(self, items: List[RetrievedItem], stats: str) -> str:
        formatted = ["[MACRO STATS]\n" + stats + "\n\n[MICRO QUOTES]"]
        for i, item in enumerate(items[:3]): # only top 3 for micro quotes
            meta = item.metadata
            chunk = (
                f"--- Evidence Item ID: {i+1} ---\n"
                f"Source: {meta.get('source', 'unknown')}\n"
                f"ID: {item.item_id}\n"
                f"Evidence Type: {meta.get('evidence_type', 'unknown')}\n"
                f"Category: {meta.get('category_mentioned', 'unknown')}\n"
                f"Behavior: {meta.get('behavior_type', 'unknown')}\n"
                f"Frustration: {meta.get('frustration', 'none')}\n"
                f"Snippet: {item.document}\n"
            )
            formatted.append(chunk)
        return "\n".join(formatted)

    def synthesize_stream(self, messages: List[Dict[str, str]], evidence: List[RetrievedItem], stats: str) -> Generator[str, None, None]:
        logger.info(f"Synthesizing answer with {len(evidence)} evidence chunks and {len(messages)} past messages.")
        
        evidence_text = self._format_evidence(evidence, stats)
        system_prompt = SYNTHESIS_PROMPT.replace("{retrieved_chunks_with_metadata}", evidence_text)
        
        def _groq_stream():
            logger.info("Calling Groq (primary) for chat engine...")
            if not self.groq_client:
                raise ValueError("Groq client not initialized")
            
            groq_messages = [{"role": "system", "content": system_prompt}]
            for msg in messages:
                role = "user" if msg["role"] == "user" else "assistant"
                groq_messages.append({"role": role, "content": msg["content"]})
                
            response = self.groq_client.chat.completions.create(
                model="groq/compound",
                messages=groq_messages,
                stream=True,
                temperature=0.0
            )
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

        def _gemini_stream_fallback():
            logger.info("Falling back to Gemini...")
            try:
                genai.configure(api_key=settings.gemini_api_key)
                contents = []
                for msg in messages[:-1]:
                    role = "user" if msg["role"] == "user" else "model"
                    contents.append({"role": role, "parts": [msg["content"]]})
                    
                last_query = messages[-1]["content"] if messages else ""
                full_prompt = f"System Instructions & Evidence:\n{system_prompt}\n\nUser Question: {last_query}"
                contents.append({"role": "user", "parts": [full_prompt]})
                
                response = self.model.generate_content(
                    contents,
                    stream=True,
                    generation_config=genai.GenerationConfig(temperature=0.0),
                    request_options={"retry": None, "timeout": 60.0}
                )
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
            finally:
                pass

        # Try Groq first
        if self.groq_client:
            gen = _groq_stream()
            try:
                first_chunk = next(gen)
                yield first_chunk
                for chunk in gen:
                    yield chunk
            except Exception as e:
                logger.warning(f"Groq failed ({e}). Falling back to Gemini.")
                fallback_gen = _gemini_stream_fallback()
                for chunk in fallback_gen:
                    yield chunk
        else:
            fallback_gen = _gemini_stream_fallback()
            for chunk in fallback_gen:
                yield chunk

    def synthesize(self, messages: List[Dict[str, str]], evidence: List[RetrievedItem], stats: str) -> str:
        """Non-streaming version for simple testing."""
        result = ""
        for chunk in self.synthesize_stream(messages, evidence, stats):
            result += chunk
        return result

    def generate_theme_title(self, barrier: str, category: str, examples: List[str]) -> Dict[str, str]:
        """
        Takes a cluster of user quotes and acts as a Senior PM to generate an actionable theme title and description.
        Returns a dictionary with 'title' and 'description'.
        """
        prompt = f"""You are a Senior Product Manager analyzing user feedback. 
You found a cluster of feedback regarding the barrier '{barrier}' in the '{category}' category.

Here are 5 representative user quotes:
{chr(10).join(f"- {ex}" for ex in examples[:5])}

Your task:
1. Provide a highly actionable, punchy 3-6 word title for this theme (e.g., instead of "Trust in Fruits", use "Quality Assurance Friction in Fresh Produce").
2. Provide a single, punchy 1-sentence description of the root cause or impact.

Format your output EXACTLY as valid JSON with no markdown formatting, like this:
{{
  "title": "Your Punchy Title",
  "description": "Your 1-sentence description."
}}
"""
        try:
            # Try Gemini first
            response = self.model.generate_content(
                prompt,
                request_options={"retry": None, "timeout": 3.0}
            )
            result_text = response.text.strip()
            # Clean up potential markdown formatting from Gemini
            if result_text.startswith("```json"):
                result_text = result_text[7:-3]
            elif result_text.startswith("```"):
                result_text = result_text[3:-3]
            
            return json.loads(result_text)
        except Exception as e:
            logger.warning(f"Gemini failed for theme generation ({e}). Falling back to secondary Gemini.")
            try:
                genai.configure(api_key=settings.gemini_api_key_secondary)
                response = self.model_fallback.generate_content(
                    prompt,
                    request_options={"retry": None, "timeout": 3.0}
                )
                result_text = response.text.strip()
                if result_text.startswith("```json"):
                    result_text = result_text[7:-3]
                elif result_text.startswith("```"):
                    result_text = result_text[3:-3]
                return json.loads(result_text)
            except Exception as inner_e:
                logger.error(f"Gemini fallback failed for theme generation: {inner_e}")
            finally:
                genai.configure(api_key=settings.gemini_api_key)
                # Ultimate fallback to generic statistical naming
                return {
                    "title": f"{barrier.title()} in {category}",
                    "description": f"Users are consistently reporting {barrier.lower()} issues in {category}."
                }

    def generate_executive_summary(self, stats: str, themes: list) -> str:
        """
        Generates a comprehensive executive summary in Markdown format based on macro stats and emergent themes.
        """
        prompt = f"""You are a Senior Product Manager at Blinkit.
Please generate a comprehensive "Executive Product Insights Summary" in Markdown format.

Here are the macro statistics and data overview:
[MACRO STATS]
{stats}

Here are the top emergent themes identified from user feedback:
[EMERGENT THEMES]
{json.dumps(themes, indent=2)}

Your report should include:
1. An Executive Summary (TL;DR).
2. Key Insights and Trends (based on the stats and themes).
3. Strategic Recommendations (what we should do next).
4. A brief note at the end under a section "Report Metadata" mentioning that this report was generated by the Discovery Engine LLM, typically consumes ~2,000-4,000 tokens per run.

Make the formatting professional, punchy, and highly analytical. Use bolding, bullet points, and headers.
"""
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(temperature=0.2),
                request_options={"retry": None, "timeout": 60.0}
            )
            return response.text.strip()
        except Exception as e:
            logger.warning(f"Gemini failed for executive summary ({e}). Falling back to secondary Gemini.")
            try:
                genai.configure(api_key=settings.gemini_api_key_secondary)
                response = self.model_fallback.generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(temperature=0.2),
                    request_options={"retry": None, "timeout": 60.0}
                )
                return response.text.strip()
            except Exception as inner_e:
                logger.error(f"Gemini fallback failed for executive summary: {inner_e}")
                return "# Error\\nFailed to generate summary due to AI engine errors."
            finally:
                genai.configure(api_key=settings.gemini_api_key)

# Global instance
synthesizer = Synthesizer()
