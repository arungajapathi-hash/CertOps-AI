"""
FoundryKnowledgePlugin - Primary knowledge source using Azure AI Foundry IQ.
Queries indexed certification knowledge base with automatic fallback to DynamicKnowledgePlugin.
"""
import os
from typing import Optional, Dict

from backend.plugins.dynamic_knowledge_plugin import DynamicKnowledgePlugin


class FoundryKnowledgePlugin:
    def __init__(self):
        """Initialize Foundry IQ client with automatic fallback setup."""
        self.cache = {}
        self.source_log = {}  # Track which source served each cert
        self.fallback = None
        self.foundry_client = None          # OpenAI v1 client bound to the agent
        self._token_provider = None
        self.knowledge_base_id = os.getenv("AZURE_FOUNDRY_KNOWLEDGE_BASE_ID")
        # The agent deployment name in Foundry (configured with the knowledge base).
        self.agent_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "certops-agent")

        # Try to initialize Foundry client
        self._init_foundry_client()

        # Always initialize fallback
        try:
            self.fallback = DynamicKnowledgePlugin()
            print("[FoundryIQ] DynamicKnowledgePlugin loaded as fallback")
        except Exception as e:
            print(f"[FoundryIQ] Fallback plugin init error: {e}")
            self.fallback = None

    def _init_foundry_client(self):
        """Initialize the Foundry agent client via the OpenAI v1 endpoint.

        The agent (configured in Foundry with the knowledge base) is invoked
        through the OpenAI-compatible Responses API on the project's
        /openai/v1 endpoint, authenticated with a bearer token from
        DefaultAzureCredential. Local dev only needs `az login`; deployment
        uses a service principal (AZURE_CLIENT_ID/SECRET/TENANT_ID) — no secret
        or connection string in code.
        """
        try:
            from openai import OpenAI
            from azure.identity import DefaultAzureCredential, get_bearer_token_provider

            endpoint = self._get_openai_v1_endpoint()
            if not endpoint:
                print("[FoundryIQ] No Foundry endpoint configured, using fallback")
                return False

            self._token_provider = get_bearer_token_provider(
                DefaultAzureCredential(), "https://ai.azure.com/.default"
            )
            self.foundry_client = OpenAI(base_url=endpoint, api_key=self._token_provider())
            print(f"[FoundryIQ] Connected to Foundry agent '{self.agent_deployment}' at {endpoint}")
            return True

        except ImportError as e:
            print(f"[FoundryIQ] SDK not installed ({e}), using fallback")
            return False
        except Exception as e:
            print(f"[FoundryIQ] Client initialization failed: {e}, will use fallback")
            return False

    def _get_openai_v1_endpoint(self) -> Optional[str]:
        """Resolve the OpenAI v1 endpoint for the Foundry resource.

        Prefers AZURE_OPENAI_ENDPOINT; if a project endpoint is provided
        (.../api/projects/<name>) it is normalised to the /openai/v1 form.
        """
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("AZURE_EXISTING_AIPROJECT_ENDPOINT")
        if not endpoint:
            return None
        endpoint = endpoint.rstrip("/")
        if "/api/projects/" in endpoint:
            endpoint = f"{endpoint.split('/api/projects/')[0]}/openai/v1"
        return endpoint

    def query(self, prompt: str, isolation_suffix: str = "") -> Optional[str]:
        """Run a prompt against the Foundry agent and return its text reply.

        The agent does the knowledge-base RAG grounding server-side, so we just
        send the prompt to the Responses API and read the answer. A fresh bearer
        token is fetched per call so long-running processes never use an expired
        one.
        """
        if not self.foundry_client:
            return None
        try:
            # Refresh the bearer token (DefaultAzureCredential caches internally).
            if self._token_provider:
                self.foundry_client.api_key = self._token_provider()
            response = self.foundry_client.responses.create(
                model=self.agent_deployment,
                input=prompt,
            )
            text = getattr(response, "output_text", None)
            if not text and getattr(response, "output", None):
                # Fallback: concatenate any text content in the output items.
                parts = []
                for item in response.output:
                    for c in getattr(item, "content", []) or []:
                        t = getattr(c, "text", None)
                        if t:
                            parts.append(t)
                text = "\n".join(parts) if parts else None
            return text
        except Exception as e:
            print(f"[FoundryIQ] Agent query failed: {e}")
            return None

    def _query_foundry_iq(self, certification: str) -> Optional[Dict]:
        """Query the Foundry agent (knowledge-base grounded) for a cert guide."""
        if not self.foundry_client:
            return None
        print(f"[FoundryIQ] Querying Foundry agent for {certification}...")
        prompt = (
            f"What are the exam objectives, skills measured, domains with their "
            f"weightings, and pass requirements for the {certification} "
            f"certification? Be specific and detailed."
        )
        content = self.query(prompt, isolation_suffix=certification)
        if content:
            print(f"[FoundryIQ] Retrieved {len(content)} chars for {certification}")
            return {"content": content, "citations": [], "source": "Foundry IQ"}
        return None

    def get_certification_guide(self, certification: str) -> Dict:
        """
        Get certification guide from Foundry IQ or fallback.
        Returns dict with content, citations, and source.
        """
        cert_key = certification.upper()
        
        # Check cache first
        if cert_key in self.cache:
            print(f"[FoundryIQ] Using cached guide for {cert_key}")
            return self.cache[cert_key]
        
        result = None
        source_used = "Unknown"
        
        # Try Foundry IQ first
        if self.foundry_client:
            result = self._query_foundry_iq(cert_key)
            if result:
                source_used = "Foundry IQ"
                print(f"[FoundryIQ] Successfully retrieved {cert_key} from Foundry")
        
        # Fallback to DynamicKnowledgePlugin if Foundry fails
        if not result and self.fallback:
            try:
                print(f"[Fallback] Foundry IQ unavailable, activating DynamicKnowledgePlugin for {cert_key}")
                dynamic_guide = self.fallback.get_certification_guide(cert_key)
                
                # Determine source
                if dynamic_guide and len(dynamic_guide) > 200:
                    source_used = "Dynamic Web" if "http" in dynamic_guide.lower() else "LLM Knowledge"
                
                result = {
                    "content": dynamic_guide,
                    "citations": [],
                    "source": source_used
                }
            except Exception as e:
                print(f"[Fallback] DynamicKnowledgePlugin failed: {e}")
        
        # Final fallback: offline guide
        if not result:
            result = {
                "content": f"Study guide for {cert_key} certification. Please check official Microsoft Learn documentation.",
                "citations": ["https://learn.microsoft.com"],
                "source": "Offline Fallback"
            }
            source_used = "Offline Fallback"
        
        # Cache and log
        self.cache[cert_key] = result
        self.source_log[cert_key] = source_used
        
        print(f"[FoundryIQ] Guide ready for {cert_key} ({source_used})")
        return result

    def get_skill_list(self, certification: str) -> str:
        """Extract skills from guide content."""
        guide = self.get_certification_guide(certification)
        content = guide.get("content", "")
        return content[:1500]

    def get_domains(self, certification: str) -> str:
        """Extract exam domains from guide content."""
        guide = self.get_certification_guide(certification)
        content = guide.get("content", "")
        lines = content.split("\n")
        domain_lines = [l for l in lines if any(
            word in l.lower() for word in ["domain", "objective", "skill", "area", "%", "weight"]
        )]
        if domain_lines:
            return "\n".join(domain_lines[:25])
        return content[500:2000]

    def get_exam_tips(self, certification: str) -> str:
        """Extract exam tips from guide content."""
        guide = self.get_certification_guide(certification)
        content = guide.get("content", "")
        lines = content.split("\n")
        tips = [l for l in lines if any(
            word in l.lower() for word in ["tip", "remember", "important", "key", "focus", "pass"]
        )]
        if tips:
            return "\n".join(tips[:15])
        return "Review exam objectives carefully. Practice with mock exams. Focus on weak areas."

    def search_topics(self, certification: str, topic: str) -> str:
        """Search guide for specific topic."""
        guide = self.get_certification_guide(certification)
        content = guide.get("content", "")
        lines = content.split("\n")
        matches = [l for l in lines if topic.lower() in l.lower()]
        if matches:
            return "\n".join(matches[:20])
        return f"Topic context for '{topic}' in {certification}:\n" + content[:800]

    def get_source_log(self) -> Dict[str, str]:
        """Return log of which source served each certification."""
        return self.source_log.copy()
