import os
import json
from typing import Dict

from semantic_kernel.functions import kernel_function

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KNOWLEDGE_DIR = os.path.join(BASE_DIR, "data", "knowledge")
CERT_FILE = os.path.join(BASE_DIR, "data", "synthetic", "certifications.json")


def _normalize_cert_filename(filename: str) -> str:
    cert = filename.replace("_guide.md", "")
    cert = cert.replace("az204", "AZ-204").replace("az400", "AZ-400").replace("dp203", "DP-203")
    return cert.upper()


class KnowledgePlugin:
    def __init__(self):
        if not os.path.isdir(KNOWLEDGE_DIR):
            raise FileNotFoundError(f"Knowledge directory not found: {KNOWLEDGE_DIR}")

        self.guides: Dict[str, str] = {}
        for filename in os.listdir(KNOWLEDGE_DIR):
            if filename.endswith("_guide.md"):
                path = os.path.join(KNOWLEDGE_DIR, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        self.guides[_normalize_cert_filename(filename)] = f.read()
                except Exception as exc:
                    print(f"[KnowledgePlugin] Failed to load guide {filename}: {exc}")

        try:
            with open(CERT_FILE, "r", encoding="utf-8") as f:
                self.certifications = json.load(f)
        except Exception as exc:
            print(f"[KnowledgePlugin] Failed to load certifications.json: {exc}")
            self.certifications = {}

    @kernel_function(name="load_guide", description="Load full study guide for a certification")
    def load_guide(self, certification: str) -> str:
        cert = certification.strip()
        guide = self.guides.get(cert)
        if guide:
            return guide
        return f"Guide not found for {certification}"

    @kernel_function(name="search_topics", description="Search for specific topics in a certification guide")
    def search_topics(self, certification: str, topic: str) -> str:
        cert = certification.strip()
        guide = self.guides.get(cert, "")
        if not guide:
            return f"Guide not found for {certification}"
        matches = []
        for line in guide.splitlines():
            if topic.lower() in line.lower():
                matches.append(line)
        if matches:
            return "\n".join(matches)
        return f"No content found for topic: {topic}"

    @kernel_function(name="get_exam_tips", description="Get exam tips for a certification")
    def get_exam_tips(self, certification: str) -> str:
        cert = certification.strip()
        guide = self.guides.get(cert, "")
        if not guide:
            return f"Guide not found for {certification}"
        tips = [
            line
            for line in guide.splitlines()
            if "tip" in line.lower() or "exam tip" in line.lower() or "remember" in line.lower()
        ]
        if tips:
            return "\n".join(tips)
        # fallback: last 20 lines
        lines = guide.splitlines()
        return "\n".join(lines[-20:])

    @kernel_function(name="get_skill_list", description="Get required skills for a certification")
    def get_skill_list(self, certification: str) -> str:
        cert = certification.strip()
        info = self.certifications.get(cert)
        if not info:
            return f"Certification data not found for {cert}"
        skills = info.get("skills", [])
        hours = info.get("recommended_hours", 0)
        lines = [f"{s}" for s in skills]
        lines.append(f"Recommended hours: {hours}")
        return "\n".join(lines)

    @kernel_function(name="get_domains", description="Get exam domains and weights for a certification")
    def get_domains(self, certification: str) -> str:
        cert = certification.strip()
        info = self.certifications.get(cert)
        if not info:
            return f"Certification data not found for {cert}"
        domains = info.get("domains", [])
        lines = [f"Domain: {d.get('name')} — {d.get('weight')}% of exam" for d in domains]
        return "\n".join(lines)


if __name__ == "__main__":
    p = KnowledgePlugin()
    print("Loaded guides:", list(p.guides.keys()))
    print("AZ-204 skills:\n", p.get_skill_list("AZ-204"))
