import os
from pathlib import Path

from dotenv import load_dotenv
import semantic_kernel as sk
from semantic_kernel.functions import KernelPlugin

root_dir = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=root_dir / ".env")


def get_kernel() -> sk.Kernel:
    kernel = sk.Kernel()

    # Best-effort: register a minimal AI service description so plugins
    # that expect a service_id can find it. Full connector implementations
    # may not be present in this environment; this is non-fatal.
    try:
        from semantic_kernel.services.ai_service_client_base import AIServiceClientBase

        class AzureOpenAIService(AIServiceClientBase):
            ai_model_id: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
            service_id: str = "azure_openai"

            def service_url(self) -> str | None:
                return os.getenv("AZURE_OPENAI_ENDPOINT")

        svc = AzureOpenAIService()
        kernel.add_service(svc)
    except Exception:
        # If we cannot add a full service, return kernel anyway.
        pass

    return kernel
