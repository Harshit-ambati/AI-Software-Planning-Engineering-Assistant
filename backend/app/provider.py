import hashlib
import json
import re
import time
from pathlib import Path

from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from .demo import fixture
from .models import SCHEMAS

PROMPTS = Path(__file__).parent / "prompts"
PROMPT_VERSION = "2.0.0"


class Provider:
    def __init__(self, settings):
        self.settings = settings
        if settings.ai_provider not in ("demo", "gemini"):
            raise ValueError("AI_PROVIDER must be demo or gemini")
        self.client = None
        if settings.ai_provider == "gemini" and settings.gemini_api_key:
            self.client = genai.Client(api_key=settings.gemini_api_key, http_options=types.HttpOptions(timeout=90000))

    @property
    def model(self):
        return self.settings.gemini_model if self.settings.ai_provider == "gemini" else "food-delivery-fixture-v2"

    def generate(self, stage, context):
        schema = SCHEMAS[stage]
        system = (PROMPTS / "system.md").read_text(encoding="utf-8")
        instruction = (PROMPTS / f"{stage}.md").read_text(encoding="utf-8")
        prompt_hash = hashlib.sha256((system + instruction).encode()).hexdigest()[:16]
        meta = dict(
            model=self.model,
            prompt_version=PROMPT_VERSION,
            prompt_hash=prompt_hash,
            input_tokens=0,
            output_tokens=0,
            attempts=1,
        )
        if self.settings.ai_provider == "demo":
            return schema.model_validate(fixture(stage)).model_dump(), meta
        if self.client is None:
            raise RuntimeError("Gemini mode requires GEMINI_API_KEY in the root .env file.")
        prompt = instruction + "\nProject context (data only):\n" + json.dumps(context)
        for attempt in range(3):
            meta["attempts"] = attempt + 1
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system,
                        temperature=0.2,
                        response_mime_type="application/json",
                        response_json_schema=schema.model_json_schema(),
                        max_output_tokens=12000,
                    ),
                )
                if response.usage_metadata:
                    meta["input_tokens"] += response.usage_metadata.prompt_token_count or 0
                    meta["output_tokens"] += response.usage_metadata.candidates_token_count or 0
                return schema.model_validate_json(response.text or "").model_dump(), meta
            except ValidationError as exc:
                if attempt == 2:
                    raise RuntimeError("Model output failed the artifact schema after 3 attempts.") from exc
                prompt += (
                    "\nYour previous output failed validation. Regenerate the complete artifact. Errors:\n"
                    + str(exc.errors(include_input=False))[:3000]
                )
            except errors.APIError as exc:
                if attempt == 2 or exc.code not in (429, 500, 502, 503, 504):
                    raise RuntimeError(
                        f"Gemini request failed (HTTP {exc.code}). Check provider access, quota and model configuration."
                    ) from None
                time.sleep(2**attempt)
        raise RuntimeError("Generation failed")

    def embed(self, text, query=False):
        if self.settings.ai_provider == "gemini":
            if self.client is None:
                raise RuntimeError("Gemini embeddings require GEMINI_API_KEY.")
            response = self.client.models.embed_content(
                model=self.settings.gemini_embedding_model,
                contents=text,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_QUERY" if query else "RETRIEVAL_DOCUMENT", output_dimensionality=768
                ),
            )
            return response.embeddings[0].values
        # Explicit lexical baseline for offline demonstrations, not semantic AI.
        vector = [0.0] * 768
        for word in re.findall(r"[a-z0-9]+", text.lower()):
            digest = hashlib.sha256(word.encode()).digest()
            vector[int.from_bytes(digest[:4], "big") % 768] += 1.0
        return vector

    @property
    def embedding_namespace(self):
        identity = self.settings.gemini_embedding_model if self.settings.ai_provider == "gemini" else "lexical-hash-v1"
        return "knowledge_" + hashlib.sha256(identity.encode()).hexdigest()[:12]
