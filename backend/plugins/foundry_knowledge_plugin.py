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
        self.foundry_client = None
        self.knowledge_base_id = os.getenv("FOUNDRY_KNOWLEDGE_BASE_ID")
        
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
        """Attempt to initialize Azure AI Foundry IQ client."""
        try:
            # Try to import and initialize Foundry SDK
            from azure.ai.projects import AIProjectClient
            from azure.identity import DefaultAzureCredential
            
            # Get connection string from env
            conn_str = os.getenv("AZURE_FOUNDRY_CONNECTION_STRING")
            
            if not conn_str:
                # Try to construct from components
                conn_str = self._construct_connection_string()
            
            if conn_str:
                self.foundry_client = AIProjectClient.from_connection_string(
                    conn_str=conn_str,
                    credential=DefaultAzureCredential()
                )
                print(f"[FoundryIQ] Connected to Foundry project")
                return True
            else:
                print("[FoundryIQ] No valid connection string provided")
                return False
                
        except ImportError:
            print("[FoundryIQ] azure-ai-projects not installed, using fallback")
            return False
        except Exception as e:
            print(f"[FoundryIQ] Client initialization failed: {e}, will use fallback")
            return False

    def _construct_connection_string(self) -> Optional[str]:
        """Construct connection string from environment components."""
        try:
            hub = os.getenv("AZURE_FOUNDRY_HUB", "certops-ai-resource")
            resource_group = os.getenv("AZURE_FOUNDRY_RESOURCE_GROUP", "rg-arungajapathi-3294")
            subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
            region = os.getenv("AZURE_FOUNDRY_REGION", "eastus")
            
            if not subscription_id:
                print("[FoundryIQ] AZURE_SUBSCRIPTION_ID not set, cannot construct connection string")
                return None
            
            # Format: {region}.api.azureml.ms;{subscription_id};{resource_group};{hub}
            conn_str = f"{region}.api.azureml.ms;{subscription_id};{resource_group};{hub}"
            print(f"[FoundryIQ] Constructed connection string from components")
            return conn_str
        except Exception as e:
            print(f"[FoundryIQ] Failed to construct connection string: {e}")
            return None

    def _query_foundry_iq(self, certification: str) -> Optional[Dict]:
        """Query Foundry IQ knowledge base using RAG."""
        if not self.foundry_client:
            return None
        
        try:
            print(f"[FoundryIQ] Querying knowledge base for {certification}...")
            
            # Try using agents API to query knowledge base
            try:
                kb_name = os.getenv("AZURE_FOUNDRY_KNOWLEDGE_BASE", "certops-knowledge")
                
                # Query the knowledge base
                response = self.foundry_client.agents.create_and_run_thread(
                    model="gpt-4o",
                    messages=[{
                        "role": "user",
                        "content": f"What are the exam objectives, skills, domains, and pass requirements for {certification}? Be specific and detailed."
                    }],
                    knowledge_bases=[kb_name]
                )
                
                if response and hasattr(response, 'messages'):
                    content = response.messages[0].content if response.messages else None
                    if content:
                        print(f"[FoundryIQ] Retrieved content for {certification}")
                        return {
                            "content": content,
                            "citations": [],
                            "source": "Foundry IQ"
                        }
            except Exception as e:
                print(f"[FoundryIQ] Thread API failed: {e}, trying alternative method")
            
            # Fallback to search API if available
            try:
                kb_id = os.getenv("AZURE_FOUNDRY_KNOWLEDGE_BASE_ID")
                if kb_id and hasattr(self.foundry_client, 'knowledge_bases'):
                    search_results = self.foundry_client.knowledge_bases.search(
                        knowledge_base_id=kb_id,
                        query=f"{certification} exam objectives skills domains"
                    )
                    
                    if search_results:
                        content = "\n".join([
                            f"- {r.get('content', '')}" 
                            for r in search_results.get('results', [])
                            if r.get('content')
                        ])
                        print(f"[FoundryIQ] Retrieved {len(search_results.get('results', []))} documents")
                        return {
                            "content": content,
                            "citations": [r.get('source', '') for r in search_results.get('results', [])],
                            "source": "Foundry IQ"
                        }
            except Exception as e:
                print(f"[FoundryIQ] Search API failed: {e}")
            
            return None
            
        except Exception as e:
            print(f"[FoundryIQ] Query failed: {e}")
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
