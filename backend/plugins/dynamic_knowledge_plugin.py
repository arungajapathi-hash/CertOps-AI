"""
DynamicKnowledgePlugin - Fetches certification content from Microsoft Learn or generates via LLM.
Replaces static markdown loading with live, dynamic knowledge retrieval.
"""
import os
import json
from typing import Optional

import requests
from bs4 import BeautifulSoup
from openai import AzureOpenAI


class DynamicKnowledgePlugin:
    def __init__(self):
        """Initialize plugin with session for web requests and LLM client."""
        self.cache = {}
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; CertOpsAI/1.0)"
        })
        
        # Initialize LLM client
        self.client = None
        try:
            self.client = AzureOpenAI(
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION")
            )
        except Exception as e:
            print(f"[DynamicKnowledge] LLM client init failed: {e}")

    def _fetch_ms_learn(self, certification: str) -> Optional[str]:
        """
        Fetch exam objectives from Microsoft Learn.
        URL pattern: https://learn.microsoft.com/en-us/credentials/certifications/exams/{cert-lower}/
        Example: AZ-204 → az-204
        """
        cert_slug = certification.lower().replace(" ", "-")
        url = f"https://learn.microsoft.com/en-us/credentials/certifications/exams/{cert_slug}/"
        
        try:
            response = self.session.get(url, timeout=5)  # Reduced timeout
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Extract main content
                content_div = soup.find("div", {"class": "content"}) or soup.find("main")
                if content_div:
                    text = content_div.get_text(separator="\n", strip=True)
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    result = "\n".join(lines[:300])
                    print(f"[DynamicKnowledge] Fetched {len(result)} chars from Microsoft Learn for {certification}")
                    return result
            return None
        except requests.exceptions.Timeout:
            print(f"[DynamicKnowledge] Web fetch timeout for {certification} (5s limit)")
            return None
        except Exception as e:
            print(f"[DynamicKnowledge] Fetch failed for {certification}: {e}")
            return None

    def _llm_generate_guide(self, certification: str) -> str:
        """
        If web fetch fails, use LLM to generate comprehensive guide
        based on its training knowledge.
        """
        if not self.client:
            return f"Study guide for {certification} (LLM client unavailable)"
        
        try:
            response = self.client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Microsoft certification expert with deep knowledge of all Azure, M365, Dynamics, and other Microsoft certification exams. Provide structured, actionable information."
                    },
                    {
                        "role": "user",
                        "content": f"""Generate a comprehensive study guide for the {certification} certification.

Include:
1. Exam overview and target role
2. All exam domains with percentage weights
3. Key skills measured under each domain (detailed bullet points)
4. Recommended study hours
5. Pass score threshold
6. Top 5 exam tips
7. Recommended learning resources from Microsoft Learn

Be specific and detailed. Format as plain text with clear sections."""
                    }
                ],
                max_tokens=2500,
                temperature=0.3
            )
            guide = response.choices[0].message.content
            print(f"[DynamicKnowledge] Generated {len(guide)} chars via LLM for {certification}")
            return guide
        except Exception as e:
            print(f"[DynamicKnowledge] LLM generation failed: {e}")
            return f"Fallback guide for {certification} — consult official Microsoft documentation"

    def get_certification_guide(self, certification: str) -> str:
        """
        Main method — tries web fetch first, falls back to LLM if insufficient.
        Results are cached to avoid repeated fetches.
        """
        if certification in self.cache:
            print(f"[DynamicKnowledge] Using cached guide for {certification}")
            return self.cache[certification]
        
        print(f"[DynamicKnowledge] Fetching guide for {certification}...")
        
        # Try web fetch first
        guide = self._fetch_ms_learn(certification)
        
        # If web fetch failed or too short, use LLM
        if not guide or len(guide) < 300:
            print(f"[DynamicKnowledge] Web fetch insufficient, generating via LLM")
            guide = self._llm_generate_guide(certification)
        
        self.cache[certification] = guide
        print(f"[DynamicKnowledge] Guide ready for {certification} — {len(guide)} chars")
        return guide

    def get_skill_list(self, certification: str) -> str:
        """Extract skills context from guide."""
        guide = self.get_certification_guide(certification)
        return guide[:1500]

    def get_domains(self, certification: str) -> str:
        """Extract domains/areas from guide."""
        guide = self.get_certification_guide(certification)
        lines = guide.split("\n")
        domain_lines = [l for l in lines if any(
            word in l.lower() for word in ["domain", "module", "skill", "area", "section", "%"]
        )]
        if domain_lines:
            return "\n".join(domain_lines[:20])
        return guide[500:1500]

    def get_exam_tips(self, certification: str) -> str:
        """Extract exam tips from guide."""
        guide = self.get_certification_guide(certification)
        lines = guide.split("\n")
        tips = [l for l in lines if any(
            word in l.lower() for word in ["tip", "remember", "important", "note", "key", "focus", "practice"]
        )]
        if tips:
            return "\n".join(tips[:15])
        return "Review official exam guide carefully. Practice with sample questions. Focus on weak areas."

    def search_topics(self, certification: str, topic: str) -> str:
        """Search guide for specific topic."""
        guide = self.get_certification_guide(certification)
        lines = guide.split("\n")
        matches = [l for l in lines if topic.lower() in l.lower()]
        if matches:
            return "\n".join(matches[:20])
        return f"Topic context for '{topic}' in {certification}:\n" + guide[:800]
