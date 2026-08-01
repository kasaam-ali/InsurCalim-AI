"""Thin multi-provider LLM client for InsurClaim AI.

Every model call in the project goes through call_llm() so the rest of the code
never talks to a provider SDK directly. The wrapper tries providers in order
(OpenRouter -> Claude -> Gemini -> Groq) and returns the first successful
response. This gives us resilience (if one provider is down or rate-limited,
another answers) and lets us develop cheaply without spending Claude credits.

OpenRouter is an OpenAI-compatible gateway that can reach Claude models with a
single key. During development we route through it to cheaper Claude tiers
(Sonnet/Haiku) so the direct Anthropic Opus quota is preserved for the real
demo. Remove OPENROUTER_API_KEY from .env to fall back to the direct providers.

Claude (direct) stays the quality anchor; Gemini and Groq are further fallbacks.
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
# Groq vision model (free tier) - a working second vision provider alongside Gemini.
GROQ_VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
# OpenRouter Claude tiers used during development (cheaper than direct Opus).
OPENROUTER_REASONING_MODEL = os.getenv("OPENROUTER_REASONING_MODEL", "anthropic/claude-sonnet-4.5")
OPENROUTER_EXTRACTION_MODEL = os.getenv("OPENROUTER_EXTRACTION_MODEL", "anthropic/claude-haiku-4.5")
# OpenRouter reserves credit up front against max_tokens, so keep it modest on a
# small balance. Raise OPENROUTER_MAX_TOKENS once the account is funded.
OPENROUTER_MAX_TOKENS = int(os.getenv("OPENROUTER_MAX_TOKENS", "1500"))
# Free models get rate-limited (429); retry a few times with a short backoff.
OPENROUTER_MAX_RETRIES = int(os.getenv("OPENROUTER_MAX_RETRIES", "4"))
OPENROUTER_RETRY_WAIT_SECONDS = int(os.getenv("OPENROUTER_RETRY_WAIT_SECONDS", "12"))
# Vision model for reading damage photos (OpenRouter, OpenAI-compatible).
OPENROUTER_VISION_MODEL = os.getenv("OPENROUTER_VISION_MODEL", "google/gemini-2.0-flash-exp:free")

# Z.AI (Zhipu GLM) - OpenAI-compatible, has a free text model (glm-4.5-flash).
# A strong free fallback for text when Gemini/OpenRouter free quotas are exhausted.
ZAI_BASE_URL = os.getenv("ZAI_BASE_URL", "https://api.z.ai/api/paas/v4/")
ZAI_MODEL = os.getenv("ZAI_MODEL", "glm-4.5-flash")
ZAI_MAX_TOKENS = int(os.getenv("ZAI_MAX_TOKENS", "2000"))
# Z.AI vision model (GLM-4V family) - a second vision provider alongside Gemini.
ZAI_VISION_MODEL = os.getenv("ZAI_VISION_MODEL", "glm-4.5v")


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


def _call_openrouter(prompt: str, system: str | None, reasoning: bool) -> str:
    """Call OpenRouter (OpenAI-compatible gateway) to reach Claude models cheaply.

    Preferred during development so the direct Anthropic Opus quota is preserved.
    Reads OPENROUTER_API_KEY; a missing key raises and the caller falls through
    to the next provider.
    """
    from openai import OpenAI

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )
    model = OPENROUTER_REASONING_MODEL if reasoning else OPENROUTER_EXTRACTION_MODEL

    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    # Free models are often rate-limited upstream (429). Retry a few times with a
    # short, capped backoff before giving up and letting the caller fall through.
    import time

    last_error: Exception | None = None
    for attempt in range(OPENROUTER_MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=model, messages=messages, max_tokens=OPENROUTER_MAX_TOKENS
            )
            return response.choices[0].message.content or ""
        except Exception as exc:  # noqa: BLE001 - retry only on rate limits
            last_error = exc
            if "429" not in str(exc) or attempt == OPENROUTER_MAX_RETRIES - 1:
                raise
            time.sleep(OPENROUTER_RETRY_WAIT_SECONDS)
    raise last_error  # unreachable, but keeps type checkers happy


def _zai_keys() -> list[str]:
    """Return the configured Z.AI API keys (ZAI_API_KEY may hold several, comma-separated)."""
    raw = os.getenv("ZAI_API_KEY", "")
    return [k.strip() for k in raw.split(",") if k.strip()]


def _call_zai(prompt: str, system: str | None, reasoning: bool) -> str:
    """Call Z.AI (Zhipu GLM, OpenAI-compatible). Free text model glm-4.5-flash.

    ZAI_API_KEY may hold several comma-separated keys; they are tried in turn so
    that when one key's quota is exhausted the next takes over. A missing key
    raises and the caller falls through to the next provider. GLM-4.5's "thinking"
    mode consumes the token budget, so we disable it for these structured calls.
    """
    from openai import OpenAI

    keys = _zai_keys()
    if not keys:
        raise KeyError("ZAI_API_KEY")

    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    last_error: Exception | None = None
    for key in keys:
        try:
            client = OpenAI(base_url=ZAI_BASE_URL, api_key=key)
            response = client.chat.completions.create(
                model=ZAI_MODEL,
                messages=messages,
                max_tokens=ZAI_MAX_TOKENS,
                extra_body={"thinking": {"type": "disabled"}},
            )
            return response.choices[0].message.content or ""
        except Exception as exc:  # noqa: BLE001 - try the next key on quota/errors
            last_error = exc
            continue
    raise last_error  # every key failed; caller falls through to the next provider


def _call_gemini(prompt: str, system: str | None, reasoning: bool) -> str:
    """Call the Gemini API (fallback 1; also supports vision)."""
    from google import genai

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    # Gemini's simple call has no separate system field, so we prepend it.
    contents = f"{system}\n\n{prompt}" if system else prompt
    response = client.models.generate_content(model=GEMINI_MODEL, contents=contents)
    return response.text or ""


def search_web(prompt: str, system: str | None = None) -> str:
    """Answer a prompt grounded in live Google Search results (via Gemini).

    Enables Gemini's Google Search tool so the reply is based on real, current web
    content (e.g. actual market prices) rather than the model's own memory. Reads
    GEMINI_API_KEY; a missing key or any error raises so callers can degrade to a
    knowledge-only path. Note: Google Search grounding is billed per grounded prompt
    beyond the free tier, so callers should use it only where live data matters.
    """
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    contents = f"{system}\n\n{prompt}" if system else prompt
    config = types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())]
    )
    response = client.models.generate_content(
        model=GEMINI_MODEL, contents=contents, config=config
    )
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
# Z.AI (free glm-4.5-flash, with key rotation) is first for text so we don't burn
# the tiny Gemini/OpenRouter free quotas; the rest are fallbacks. A provider whose
# key is absent raises and we fall through to the next one.
_PROVIDERS = [
    ("zai", _call_zai),
    ("openrouter", _call_openrouter),
    ("gemini", _call_gemini),
    ("claude", _call_claude),
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


def _openrouter_vision(prompt: str, image_bytes: bytes, mime: str) -> str:
    """Read an image via an OpenRouter vision model."""
    import base64

    from openai import OpenAI

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )
    data_url = f"data:{mime};base64,{base64.b64encode(image_bytes).decode()}"
    response = client.chat.completions.create(
        model=OPENROUTER_VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
        max_tokens=OPENROUTER_MAX_TOKENS,
    )
    return response.choices[0].message.content or ""


def _zai_vision(prompt: str, image_bytes: bytes, mime: str) -> str:
    """Read an image via a Z.AI vision model (GLM-4V), with key rotation.

    OpenAI-compatible, so it uses the same image_url content shape as OpenRouter.
    ZAI_API_KEY may hold several comma-separated keys; they are tried in turn. A
    missing key or all-keys-failed raises so call_vision falls through.
    """
    import base64

    from openai import OpenAI

    keys = _zai_keys()
    if not keys:
        raise KeyError("ZAI_API_KEY")

    data_url = f"data:{mime};base64,{base64.b64encode(image_bytes).decode()}"
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        }
    ]

    last_error: Exception | None = None
    for key in keys:
        try:
            client = OpenAI(base_url=ZAI_BASE_URL, api_key=key)
            response = client.chat.completions.create(
                model=ZAI_VISION_MODEL, messages=messages, max_tokens=ZAI_MAX_TOKENS
            )
            return response.choices[0].message.content or ""
        except Exception as exc:  # noqa: BLE001 - try the next key on quota/errors
            last_error = exc
            continue
    raise last_error  # every key failed; caller falls through to the next provider


def _groq_vision(prompt: str, image_bytes: bytes, mime: str) -> str:
    """Read an image via a Groq vision model (free tier, OpenAI-compatible).

    Uses the same image_url content shape as OpenRouter. A missing GROQ_API_KEY
    raises so call_vision falls through to the next provider.
    """
    import base64

    from openai import OpenAI

    client = OpenAI(
        base_url="https://api.groq.com/openai/v1", api_key=os.environ["GROQ_API_KEY"]
    )
    data_url = f"data:{mime};base64,{base64.b64encode(image_bytes).decode()}"
    response = client.chat.completions.create(
        model=GROQ_VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
        max_tokens=1024,
    )
    return response.choices[0].message.content or ""


def _gemini_vision(prompt: str, image_bytes: bytes, mime: str) -> str:
    """Read an image via the Gemini API (vision-capable)."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[types.Part.from_bytes(data=image_bytes, mime_type=mime), prompt],
    )
    return response.text or ""


def call_vision(prompt: str, image_bytes: bytes, mime: str = "image/jpeg") -> str:
    """Describe an image (e.g. vehicle damage) with a vision model.

    Tries OpenRouter first, then Gemini as a fallback. Raises LLMError only if
    both fail; callers should handle that (degrade gracefully).
    """
    # Gemini first (reliable), then Groq (free, working), then Z.AI (needs balance),
    # then OpenRouter as a last resort. Any one working provider satisfies the call.
    errors: list[str] = []
    for name, fn in (
        ("gemini", _gemini_vision),
        ("groq", _groq_vision),
        ("zai", _zai_vision),
        ("openrouter", _openrouter_vision),
    ):
        try:
            text = fn(prompt, image_bytes, mime)
            if text:
                return text
            errors.append(f"{name}: empty response")
        except Exception as exc:
            errors.append(f"{name}: {exc}")
    raise LLMError("All vision providers failed:\n" + "\n".join(errors))


def extract_json(text: str) -> dict | None:
    """Parse a JSON object out of an LLM reply, tolerating Markdown code fences.

    Strips ```json ... ``` fences and falls back to the first {...} span. Returns
    None instead of raising when nothing parseable is found, so callers that only
    want a best-effort parse (e.g. the vision checks) can ignore failures.
    """
    import json

    text = (text or "").strip()
    if text.startswith("```"):
        # Drop the opening fence (``` or ```json) and the closing fence.
        text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
    text = text.strip()
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except ValueError:
                return None
        return None


def call_llm_json(prompt: str, system: str | None = None, reasoning: bool = False) -> dict:
    """Call the LLM and parse the reply as JSON.

    Convenience wrapper for the agents, which almost always want structured data.
    Strips common Markdown code fences before parsing so ```json ... ``` also works.
    """
    import json

    text = call_llm(prompt, system=system, reasoning=reasoning).strip()
    parsed = extract_json(text)
    if parsed is None:
        raise json.JSONDecodeError("no JSON object in LLM reply", text, 0)
    return parsed


if __name__ == "__main__":
    # Quick smoke test. Needs at least one API key in .env to actually run.
    print(call_llm("Reply with the single word: OK"))
