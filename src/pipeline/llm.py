"""Local LLM integration via Ollama — zero API key, fully offline.

Connects to Ollama at http://localhost:11434.
Auto-detects the best available model (llama3.2, mistral, phi3, …).
Falls back to smart context formatting when Ollama is not running.
"""

import json
import requests
from typing import Optional
from loguru import logger


OLLAMA_BASE_URL = "http://localhost:11434"

# Preference order — lightweight/fast models prioritised for hackathon speed
PREFERRED_MODELS = [
    "llama3.2", "llama3.1", "llama3",
    "mistral", "phi3", "phi",
    "gemma2", "gemma", "llama2", "orca-mini",
]

SYSTEM_PROMPT = (
    "You are an Industrial Knowledge Intelligence AI for an oil & gas / manufacturing plant. "
    "You answer safety and compliance questions using ONLY retrieved document context. "
    "Never fabricate facts. Always cite sources using [Source N] labels. "
    "Be precise, professional, and safety-conscious. "
    "Respond ONLY with valid JSON — no markdown fences, no extra text."
)

RAG_PROMPT = """Retrieved context from industrial safety documents:

=== DOCUMENT CONTEXT ===
{context}

=== KNOWLEDGE GRAPH RELATIONSHIPS ===
{graph_context}

=== QUESTION ===
{question}

Answer using ONLY the context above. Return ONLY this JSON object (pure JSON, no fences):
{{
  "answer": "<detailed answer citing [Source N] labels>",
  "confidence": "<High|Medium|Low>",
  "key_points": ["<key point 1>", "<key point 2>", "<key point 3>"],
  "entities_mentioned": ["<entity IDs or regulation refs found in context>"]
}}

Confidence rules:
- High   → direct, clear answer present in context
- Medium → partial or indirect information available
- Low    → context is insufficient or unrelated
If context is empty or irrelevant say so clearly in the answer field.
"""


# ── Ollama client ──────────────────────────────────────────────────────────────

class OllamaLLM:
    """Minimal Ollama HTTP client (uses only the `requests` library)."""

    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.model: Optional[str] = None
        self._detect_model()

    def _detect_model(self):
        """Ping Ollama and choose the best available model."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if resp.status_code != 200:
                logger.warning(f"Ollama /api/tags returned {resp.status_code}")
                return
            available = [m["name"] for m in resp.json().get("models", [])]
            if not available:
                logger.warning("Ollama is running but has no models installed. "
                               "Run: ollama pull llama3.2")
                return
            logger.info(f"Ollama available models: {available}")
            for pref in PREFERRED_MODELS:
                for name in available:
                    if pref in name.lower():
                        self.model = name
                        logger.info(f"Selected Ollama model: {self.model}")
                        return
            self.model = available[0]
            logger.info(f"Using first available Ollama model: {self.model}")
        except requests.exceptions.ConnectionError:
            logger.warning(
                "Ollama not running at localhost:11434. "
                "Install from https://ollama.com, then run: ollama pull llama3.2"
            )
        except Exception as e:
            logger.warning(f"Ollama detection error: {e}")

    @property
    def available(self) -> bool:
        return self.model is not None

    def generate(self, prompt: str, max_tokens: int = 1500) -> str:
        """Call Ollama generate and return raw response string."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": SYSTEM_PROMPT,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.05,    # near-deterministic for RAG
                "top_p": 0.9,
                "repeat_penalty": 1.1,
            },
        }
        resp = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=3,   # fast fail since local models might hang
        )
        resp.raise_for_status()
        return resp.json().get("response", "")


# ── JSON parsing ───────────────────────────────────────────────────────────────

def _extract_json(raw: str) -> dict:
    """Parse JSON from LLM output with multiple fallback strategies.

    Handles:
    - Pure JSON
    - JSON wrapped in markdown fences (```json ... ```)
    - Output preceded by <think>…</think> reasoning blocks (Qwen, DeepSeek-R1)
    - JSON embedded anywhere in a longer response
    """
    raw = raw.strip()

    # 1. Strip <think>…</think> / <reasoning>…</reasoning> blocks
    import re
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    raw = re.sub(r"<reasoning>.*?</reasoning>", "", raw, flags=re.DOTALL).strip()

    # 2. Strip markdown code fences (```json … ``` or ``` … ```)
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"```\s*$", "", raw, flags=re.MULTILINE)
    raw = raw.strip()

    # 3. Direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # 4. Extract first complete {...} block
    start = raw.find("{")
    end   = raw.rfind("}") + 1
    if 0 <= start < end:
        try:
            return json.loads(raw[start:end])
        except json.JSONDecodeError:
            pass

    # 5. Last resort — raise error to trigger fallback
    logger.warning(f"_extract_json: could not parse LLM output (len={len(raw)}). "
                   "Raw snippet: " + raw[:200])
    raise ValueError("Could not parse LLM response into JSON.")



# ── Smart fallback (no LLM) ────────────────────────────────────────────────────

def _smart_fallback(question: str, chunks: list, graph_context: list) -> dict:
    """Build a structured answer directly from retrieved chunks — no LLM needed."""
    if not chunks:
        return {
            "answer": (
                "No relevant documents found in the corpus for your query. "
                "Please open the **Control & Setup Panel** tab and click "
                "**Scan & Index Default Corpus** first."
            ),
            "confidence": "Low",
            "key_points": [],
            "entities_mentioned": [],
        }

    parts, key_points = [], []
    for i, c in enumerate(chunks[:4], 1):
        doc = c.get("citation", c.get("doc_id", "Unknown"))
        text = c.get("text", c.get("excerpt", "")).strip()[:500]
        parts.append(f"**[Source {i}] {doc}**\n{text}")
        key_points.append(text[:110] + "…")

    answer = "\n\n".join(parts)
    if graph_context:
        answer += "\n\n**Related graph connections:**\n" + "\n".join(
            f"• {g}" for g in graph_context[:5]
        )

    return {
        "answer": answer,
        "confidence": "Medium",
        "key_points": key_points[:3],
        "entities_mentioned": [],
    }


# ── Singleton ──────────────────────────────────────────────────────────────────

_llm: Optional[OllamaLLM] = None


def get_llm() -> OllamaLLM:
    global _llm
    if _llm is None:
        _llm = OllamaLLM()
    return _llm


def reset_llm():
    """Force re-detection of Ollama (useful after pulling a new model)."""
    global _llm
    _llm = None


# ── Public API ─────────────────────────────────────────────────────────────────

def generate_rag_answer(
    question: str,
    chunks: list,          # [{doc_id, text/excerpt, citation, distance}]
    graph_context: list,   # ["EQ-A01 --[linked_to]--> WO-2026-1001 (work_order)"]
    entities_used: list,   # entity IDs found via graph traversal
) -> dict:
    """
    Main RAG answer generation entry-point.

    Tries Ollama first; falls back to smart context formatting.

    Returns:
        answer           – markdown-formatted answer string
        confidence       – "High" | "Medium" | "Low"
        key_points       – list[str] short bullet summaries
        entities_mentioned – list[str] entity IDs referenced
        model_used       – human-readable label for sidebar display
    """
    llm = get_llm()

    # Build numbered context string for the prompt
    context_parts = []
    for i, c in enumerate(chunks[:5], 1):
        doc = c.get("citation", c.get("doc_id", "Unknown"))
        text = c.get("text", c.get("excerpt", "")).strip()
        dist = c.get("distance", 0.0)
        score = round(1.0 - float(dist), 3)
        context_parts.append(f"[Source {i}] {doc}  (relevance: {score})\n{text}")

    context_str = "\n\n---\n\n".join(context_parts) or "No documents retrieved."
    graph_str = (
        "\n".join(f"• {g}" for g in graph_context[:10])
        if graph_context else "No graph relationships found."
    )

    if llm.available:
        logger.info(f"Calling Ollama [{llm.model}] for RAG answer generation")
        prompt = RAG_PROMPT.format(
            context=context_str,
            graph_context=graph_str,
            question=question,
        )
        try:
            raw = llm.generate(prompt)
            result = _extract_json(raw)
            result.setdefault("key_points", [])
            result.setdefault("entities_mentioned", [])
            result["entities_mentioned"] = list(
                set(result["entities_mentioned"] + entities_used)
            )
            result["model_used"] = f"Ollama / {llm.model}"
            logger.info(
                f"RAG answer generated — confidence: {result.get('confidence')}, "
                f"model: {result['model_used']}"
            )
            return result
        except Exception as e:
            logger.error(f"Ollama generation failed ({e}). Switching to smart fallback.")

    # ── Fallback ───────────────────────────────────────────────────────────────
    logger.info("Ollama unavailable — using smart context fallback")
    result = _smart_fallback(question, chunks, graph_context)
    result["entities_mentioned"] = list(
        set(result.get("entities_mentioned", []) + entities_used)
    )
    result["model_used"] = "Smart Context (start Ollama for LLM answers)"
    return result
