"""Thin multi-provider LLM client for InsurCalim AI.

Every model call in the project goes through call_llm() so the rest of the code
never talks to a provider SDK directly. The wrapper tries providers in order
(Claude -> Gemini -> Groq) and returns the first successful response. This gives
us resilience (if one provider is down or rate-limited, another answers) and lets
us test on free Gemini/Groq tiers without spending Claude credits.

Claude stays the primary provider for quality; Gemini and Groq are fallbacks.
Groq is text-only, so image tasks should skip it (added in a later phase).
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

# Load the values from the .env file into the process environment
# (API keys and model names). Safe to call once at import time.
load_dotenv()

# Model names come from .env so we can change them without editing code.
CLAUDE_REASONING_MODEL = os.getenv("CLAUDE_REASONING_MODEL", "claude-opus-4-8")
CLAUDE_EXTRACTION_MODEL = os.getenv("CLAUDE_EXTRACTION_MODEL", "claude-haiku-4-5")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


class LLMError(RuntimeError):
    """Raised when every provider in the fallback chain fails."""


def _call_claude(prompt: str, system: str | None, reasoning: bool) -> str:
    """Call the Claude API (primary provider)."""
    import anthropic

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
    model = CLAUDE_REASONING_MODEL if reasoning else CLAUDE_EXTRACTION_MODEL

    kwargs: dict = {
        "model": model,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system
    if reasoning:
        # Adaptive thinking lets Opus decide how much to reason. Only the Opus
        # reasoning model supports it; the Haiku extraction model would reject it.
        kwargs["thinking"] = {"type": "adaptive"}
        kwargs["output_config"] = {"effort": "high"}

    response = client.messages.create(**kwargs)
    # response.content is a list of blocks; return the first text block's text.
    return next((block.text for block in response.content if block.type == "text"), "")


def _call_gemini(prompt: str, system: str | None, reasoning: bool) -> str:
    """Call the Gemini API (fallback 1; also supports vision)."""
    from google import genai

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    # Gemini's simple call has no separate system field, so we prepend it.
    contents = f"{system}\n\n{prompt}" if system else prompt
    response = client.models.generate_content(model=GEMINI_MODEL, contents=contents)
    return response.text or ""


def _call_groq(prompt: str, system: str | None, reasoning: bool) -> str:
    """Call the Groq API (fallback 2; very fast, text-only)."""
    from groq import Groq

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    response = client.chat.completions.create(model=GROQ_MODEL, messages=messages)
    return response.choices[0].message.content or ""


# Ordered fallback chain. Each entry is (provider_name, provider_function).
_PROVIDERS = [
    ("claude", _call_claude),
    ("gemini", _call_gemini),
    ("groq", _call_groq),
]


def call_llm(prompt: str, system: str | None = None, reasoning: bool = False) -> str:
    """Send a prompt to the LLM and return the text response.

    Tries each provider in order and returns the first non-empty result.
    Raises LLMError only if every provider fails.

    Args:
        prompt: The user text to send.
        system: Optional system instructions that set the model's role.
        reasoning: If True, use the Opus reasoning model with adaptive thinking;
            otherwise use the cheaper Haiku extraction model.
    """
    errors: list[str] = []
    for name, provider in _PROVIDERS:
        try:
            text = provider(prompt, system, reasoning)
            if text:
                return text
            errors.append(f"{name}: empty response")
        except Exception as exc:  # we intentionally fall through to the next provider
            errors.append(f"{name}: {exc}")

    raise LLMError("All LLM providers failed:\n" + "\n".join(errors))


def call_llm_json(prompt: str, system: str | None = None, reasoning: bool = False) -> dict:
    """Call the LLM and parse the reply as JSON.

    Convenience wrapper for the agents, which almost always want structured data.
    Strips common Markdown code fences before parsing so ```json ... ``` also works.
    """
    import json

    text = call_llm(prompt, system=system, reasoning=reasoning).strip()
    if text.startswith("```"):
        # Drop the opening fence (``` or ```json) and the closing fence.
        text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
    return json.loads(text)


if __name__ == "__main__":
    # Quick smoke test. Needs at least one API key in .env to actually run.
    print(call_llm("Reply with the single word: OK"))
