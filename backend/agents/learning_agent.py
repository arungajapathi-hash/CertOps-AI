import json
from typing import Dict

from backend.agents.base_agent import BaseAgent
from backend.sk_kernel import get_kernel
from backend.plugins.knowledge_router import get_knowledge_plugin


class LearningAgent(BaseAgent):
    def __init__(self):
        super().__init__("LearningAgent")
        self.kernel = get_kernel()
        
        # Use knowledge router to get the appropriate plugin
        try:
            self.knowledge = get_knowledge_plugin()
            print(f"[LearningAgent] Knowledge plugin initialized")
        except Exception as exc:
            print(f"[LearningAgent] Knowledge plugin init error: {exc}")
            self.knowledge = None

    async def execute(self, memory: Dict) -> Dict:
        self._log("LearningAgent: starting skill map construction")

        certification = memory.get("certification", "").upper()
        role = memory.get("role", "Engineer")
        target_weeks = memory.get("target_weeks", 6)
        
        self._log(f"Fetching knowledge for {certification}...")
        
        # Get knowledge guide with source tracking
        guide_data = None
        knowledge_source = "Unknown"
        citations = []
        
        if self.knowledge is not None:
            try:
                guide_data = self.knowledge.get_certification_guide(certification)
                if isinstance(guide_data, dict):
                    guide_content = guide_data.get("content", "")
                    citations = guide_data.get("citations", [])
                    knowledge_source = guide_data.get("source", "Unknown")
                else:
                    # Handle old format for backwards compatibility
                    guide_content = guide_data if isinstance(guide_data, str) else ""
                    knowledge_source = "Legacy"
            except Exception as e:
                self._log(f"Knowledge retrieval error: {e}")
                guide_content = ""
                knowledge_source = "Error"
        else:
            guide_content = ""
            knowledge_source = "Unavailable"

        # Final fallback
        if not guide_content or len(guide_content) < 100:
            guide_content = f"Study guide for {certification} certification. Please check official Microsoft Learn documentation."
            citations = ["https://learn.microsoft.com"]
            knowledge_source = "Fallback"

        system_prompt = (
            "You are a senior certification learning architect with deep expertise in Microsoft certifications. "
            "You create precise, personalized learning plans based on official exam content. "
            "You always structure your response as valid JSON only — no markdown, no explanation, no code fences. "
            "Base your recommendations strictly on the provided exam guide content."
        )

        user_prompt = (
            f"""Create a detailed skill map and learning analysis for this engineer:

Role: {role}
Certification: {certification}
Target: {target_weeks} weeks
Knowledge Source: {knowledge_source}

Official Exam Guide Content:
{guide_content[:2000]}

Return ONLY valid JSON with this exact structure (no markdown, no explanation):
{{
  "skill_map": ["skill1", "skill2", "skill3", "skill4", "skill5"],
  "priority_topics": ["highest priority", "second priority", "third priority"],
  "weak_areas_to_watch": ["common failure area", "another weakness"],
  "recommended_materials": [
    {{"title": "Module name", "section": "Section", "reason": "Why important"}}
  ],
  "estimated_hours": 20,
  "exam_domains": [
    {{"domain": "Domain name", "weight_percent": 25, "key_topics": ["topic1", "topic2"]}}
  ],
  "source_citation": "{knowledge_source}"
}}"""
        )

        response = self._call_llm(system_prompt, user_prompt, temperature=0.3)
        
        try:
            # Clean response — remove markdown fences if present
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            clean = clean.strip()
            
            result = json.loads(clean)
            
            memory["skill_map"] = result.get("skill_map", [])
            memory["recommended_materials"] = result.get("recommended_materials", [])
            memory["weak_topics"] = result.get("weak_areas_to_watch", [])
            memory["exam_domains"] = result.get("exam_domains", [])
            memory["knowledge_source"] = knowledge_source
            memory["citations"] = citations
            
            self._append_log(memory, 
                f"LearningAgent: Skill map built for {certification} — "
                f"{len(memory['skill_map'])} skills, "
                f"{result.get('estimated_hours')} hours estimated "
                f"(source: {knowledge_source})")
                
        except json.JSONDecodeError as e:
            self._log(f"JSON parse error: {e}")
            self._log(f"Raw response: {response[:200]}")
            # Fallback — extract skills
            memory["skill_map"] = self._extract_skills_fallback(certification)
            memory["exam_domains"] = []
            memory["weak_topics"] = []
            memory["recommended_materials"] = []
            memory["knowledge_source"] = knowledge_source
            memory["citations"] = citations
            self._append_log(memory, f"LearningAgent: Used fallback for {certification}")
        
        return memory

    def _extract_skills_fallback(self, certification: str) -> list:
        """Fallback if JSON parsing fails — returns sensible defaults"""
        fallbacks = {
            "AZ-204": ["Azure Functions", "App Service", "Storage", "Authentication", "Containers"],
            "AZ-400": ["CI/CD", "GitHub Actions", "Monitoring", "Infrastructure as Code", "Security"],
            "DP-203": ["Data Pipelines", "Spark", "Synapse", "Delta Lake", "Streaming"],
            "AZ-900": ["Azure Services", "Pricing", "Compliance", "Cloud Concepts", "Support"],
        }
        return fallbacks.get(certification, ["Review official exam guide", "Complete practice tests", "Study weak areas"])

