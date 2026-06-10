import os
from datetime import datetime
from pathlib import Path

import openai
from dotenv import load_dotenv

root_dir = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=root_dir / ".env")


class BaseAgent:
    def __init__(self, name: str):
        self.name = name
        self.endpoint = (
            os.getenv("AZURE_OPENAI_ENDPOINT", "")
            or os.getenv("OPENAI_BASE_URL", "")
        )
        if self.endpoint and "/api/projects/" in self.endpoint:
            base_host = self.endpoint.split("/api/projects/")[0]
            self.endpoint = f"{base_host}/openai/v1/"
        self.api_key = (
            os.getenv("AZURE_OPENAI_API_KEY", "")
            or os.getenv("OPENAI_API_KEY", "")
        )
        self.api_version = (
            os.getenv("AZURE_OPENAI_API_VERSION", "")
            or os.getenv("api_version", "")
            or os.getenv("OPENAI_API_VERSION", "")
        )
        self.deployment = (
            os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
            or os.getenv("OPENAI_MODEL", "")
            or os.getenv("MODEL", "gpt-4o")
        )

        self.client = None
        self.client_error = None
        client_cls = getattr(openai, "OpenAI", None)
        if client_cls is None:
            raise RuntimeError("Unable to load OpenAI client from openai package")

        if not self.api_key:
            self.client_error = "No OpenAI API key found"
            self._log("No OpenAI API key found; LLM calls will use fallback behavior")
            return

        try:
            self.client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.endpoint or None,
            )
        except Exception as exc:
            self.client = None
            self.client_error = str(exc)
            self._log(f"LLM client initialization failed: {exc}")

    def execute(self, memory: dict) -> dict:
        raise NotImplementedError("Each agent must implement execute()")

    def _call_llm(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        if self.client is None:
            if self.client_error:
                return f"LLM error: {self.client_error}"
            return "LLM error: missing or invalid OpenAI credentials"
        if not self.deployment:
            return "LLM error: missing model/deployment configuration"

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=1000,
            )
            msg = response.choices[0].message
            content = msg.content if hasattr(msg, "content") else msg.get("content", "")
            return content.strip() if content else ""
        except Exception as exc:
            return f"LLM error: {exc}"

    def _log(self, message: str) -> None:
        timestamp = datetime.utcnow().isoformat()
        print(f"[{self.name}] {timestamp} - {message}")

    def _append_log(self, memory: dict, message: str) -> dict:
        if "session_log" not in memory or not isinstance(memory["session_log"], list):
            memory["session_log"] = []
        memory["session_log"].append(message)
        return memory
