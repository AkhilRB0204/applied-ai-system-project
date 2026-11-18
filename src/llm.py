"""
Free, local AI model through Ollama (https://ollama.com).

OllamaClient mimics the small part of the Anthropic client that src/rag.py and
src/agent.py use (client.beta.messages.create), translating requests and
responses to Ollama's /api/chat format. That way the RAG pipeline and the
agent run unchanged on either a free local model or Claude.
"""

import json
import logging
import os
import re
import urllib.error
import urllib.request
from types import SimpleNamespace
from typing import Dict, List, Tuple

DEFAULT_OLLAMA_MODEL = "qwen3:4b-instruct"  # answers directly (no hidden reasoning)
DEFAULT_OLLAMA_URL = "http://localhost:11434"
TIMEOUT_SECONDS = 180

logger = logging.getLogger("vibematch.llm")


class LLMError(Exception):
    """Any failure talking to the local model (not running, model missing, bad reply)."""


class OllamaClient:
    """Minimal Anthropic-compatible client backed by a local Ollama model."""

    def __init__(self, model: str = None, base_url: str = None):
        self.model = model or os.environ.get("OLLAMA_MODEL") or DEFAULT_OLLAMA_MODEL
        self.base_url = (base_url or os.environ.get("OLLAMA_URL") or DEFAULT_OLLAMA_URL).rstrip("/")
        self.display_name = f"{self.model} (free local model via Ollama)"
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self.create))
        self._calls = 0

    # ------------------------------------------------------------ HTTP
    def _request(self, path: str, payload: Dict = None) -> Dict:
        data = json.dumps(payload).encode() if payload is not None else None
        request = urllib.request.Request(
            self.base_url + path, data=data, headers={"Content-Type": "application/json"},
            method="POST" if data else "GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as error:
            detail = error.read().decode(errors="replace")[:300]
            raise LLMError(f"Ollama returned HTTP {error.code}: {detail}") from error
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise LLMError(f"Could not reach Ollama at {self.base_url}: {error}") from error
        except json.JSONDecodeError as error:
            raise LLMError(f"Ollama sent invalid JSON: {error}") from error

    def check(self) -> Tuple[bool, str]:
        """Confirm Ollama is running and the model is downloaded."""
        try:
            tags = self._request("/api/tags")
        except LLMError:
            return False, ("Ollama is not running. Start the Ollama app (or run `ollama serve`), "
                           "then try again.")
        names = {m.get("name") for m in tags.get("models", [])} | {m.get("model") for m in tags.get("models", [])}
        if self.model not in names and f"{self.model}:latest" not in names:
            return False, f"The model {self.model} is not downloaded yet. Run: ollama pull {self.model}"
        return True, f"Using {self.display_name}"

    # ------------------------------------------------------------ translation
    @staticmethod
    def _to_ollama_messages(system: str, messages: List[Dict]) -> List[Dict]:
        out = [{"role": "system", "content": system}] if system else []
        tool_names = {}  # tool_use id -> tool name, for labelling tool results
        for message in messages:
            role, content = message["role"], message["content"]
            if isinstance(content, str):
                out.append({"role": role, "content": content})
                continue
            if role == "assistant":
                text, calls = [], []
                for block in content:
                    if getattr(block, "type", None) == "text":
                        text.append(block.text)
                    elif getattr(block, "type", None) == "tool_use":
                        tool_names[block.id] = block.name
                        calls.append({"function": {"name": block.name, "arguments": block.input}})
                entry = {"role": "assistant", "content": "\n".join(text)}
                if calls:
                    entry["tool_calls"] = calls
                out.append(entry)
            else:  # user turn carrying tool results
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        out.append({
                            "role": "tool",
                            "tool_name": tool_names.get(block["tool_use_id"], ""),
                            "content": str(block["content"]),
                        })
                    elif isinstance(block, dict) and block.get("type") == "text":
                        out.append({"role": "user", "content": block["text"]})
        return out

    @staticmethod
    def _to_ollama_tools(tools: List[Dict]) -> List[Dict]:
        return [
            {"type": "function", "function": {
                "name": t["name"], "description": t["description"], "parameters": t["input_schema"],
            }}
            for t in tools
        ]

    # ------------------------------------------------------------ API
    def create(self, *, system: str = "", messages: List[Dict], tools: List[Dict] = None,
               max_tokens: int = 1024, **_ignored) -> SimpleNamespace:
        """Same shape as Anthropic's messages.create: returns .stop_reason and .content blocks."""
        payload = {
            "model": self.model,
            "messages": self._to_ollama_messages(system, messages),
            "stream": False,
            "think": False,  # answer directly; no hidden reasoning text
            "options": {"temperature": 0.2, "num_predict": min(max_tokens, 600)},  # short answers only
        }
        if tools:
            payload["tools"] = self._to_ollama_tools(tools)
        reply = self._request("/api/chat", payload)
        message = reply.get("message") or {}

        content = []
        text = re.sub(r"<think>.*?</think>", "", message.get("content", ""), flags=re.S).strip()
        if text:
            content.append(SimpleNamespace(type="text", text=text))
        for call in message.get("tool_calls") or []:
            function = call.get("function", {})
            arguments = function.get("arguments", {})
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {}
            self._calls += 1
            content.append(SimpleNamespace(
                type="tool_use", id=f"call_{self._calls}", name=function.get("name", ""), input=arguments or {},
            ))

        if any(block.type == "tool_use" for block in content):
            stop_reason = "tool_use"
        elif reply.get("done_reason") == "length":
            stop_reason = "max_tokens"
        else:
            stop_reason = "end_turn"
        logger.info("Ollama %s replied: stop_reason=%s, %d block(s)", self.model, stop_reason, len(content))
        return SimpleNamespace(stop_reason=stop_reason, content=content)


def llm_errors() -> Tuple[type, ...]:
    """Exception types that mean 'the model call failed' for any provider."""
    errors: Tuple[type, ...] = (LLMError,)
    try:
        import anthropic
        errors += (anthropic.APIError,)
    except ImportError:
        pass
    return errors
