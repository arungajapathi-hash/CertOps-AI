"""RiskAnalystAgent - Calculates coverage gaps and risk scores."""
import json
from typing import Dict

from backend.agents.base_agent import BaseAgent


class RiskAnalystAgent(BaseAgent):
    def __init__(self):
        super().__init__("RiskAnalyst")

    async def execute(self, memory: Dict) -> Dict:
        """Execute risk analysis - calculate coverage gaps and domain risks."""
        self._log("Starting risk analyst analysis...")

        system_prompt = (
            "You are the Risk Analyst on a certification readiness council. "
            "Your role is to calculate COVERAGE GAPS and SCHEDULE RISK. "
            "Be mathematical and precise. "
            "Calculate probability of failure per domain, overall risk score. "
            "Return ONLY valid JSON with no markdown:\n"
            "{"
            '"agent": "RiskAnalyst", '
            '"verdict": "READY|NOT_READY|DELAY", '
            '"confidence": 0-100, '
            '"evidence": ["risk1", "gap1", "coverage1"], '
            '"recommendation": "mitigation strategy"'
            "}"
        )

        certification = memory.get("certification", "Unknown")
        hours_studied = memory.get("hours_studied", 0)
        weak_topics = memory.get("weak_topics", [])
        exam_domains = memory.get("exam_domains", [])
        target_weeks = memory.get("target_weeks", 6)
        practice_score = memory.get("practice_score_avg", 0)

        # Calculate domain risks
        high_weight_domains = [d for d in exam_domains if d.get("weight_percent", 0) > 20]
        domain_risks = []
        for domain in high_weight_domains:
            domain_name = domain.get("domain", "Unknown")
            weight = domain.get("weight_percent", 0)
            # Simple risk: if domain name appears in weak topics, it's high risk
            is_weak = any(topic.lower() in domain_name.lower() for topic in weak_topics)
            risk_level = "HIGH" if is_weak else "MEDIUM"
            domain_risks.append(f"{domain_name} ({weight}% weight): {risk_level} risk")

        # Estimate recommended hours (rough approximation)
        recommended_hours = target_weeks * 15  # ~15 hrs/week baseline

        user_prompt = (
            f"Risk assessment for {certification}:\n\n"
            f"COVERAGE ANALYSIS:\n"
            f"- Hours studied: {hours_studied}\n"
            f"- Recommended hours: {recommended_hours}\n"
            f"- Coverage: {(hours_studied/recommended_hours*100) if recommended_hours > 0 else 0:.0f}%\n"
            f"- Gap: {max(0, recommended_hours - hours_studied)} hours\n\n"
            f"DOMAIN ANALYSIS:\n"
            f"Total domains: {len(exam_domains)}\n"
            f"High-weight domains (>20%): {len(high_weight_domains)}\n"
            f"Domain risks:\n"
            f"{json.dumps(domain_risks, indent=2)}\n\n"
            f"Weak topics identified: {weak_topics}\n\n"
            f"RISK CALCULATION:\n"
            f"- Calculate overall risk as weighted average of domain risks\n"
            f"- HIGH-weight domain weakness = critical risk\n"
            f"- Coverage <70% = significant risk\n"
            f"- Gap >50 hours = concerning\n\n"
            f"Verdict rules:\n"
            f"- NOT_READY: High-weight domain weak + large gap\n"
            f"- DELAY: Medium risk, fixable with focused effort\n"
            f"- READY: Low overall risk, good coverage\n"
            f"Confidence 0-100 based on risk calculation certainty."
        )

        response = self._call_llm(system_prompt, user_prompt, temperature=0.3)

        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            clean = clean.strip()

            result = json.loads(clean)
            result["agent"] = "RiskAnalyst"
            memory["council_votes"]["risk_analyst"] = result
            
            self._append_log(
                memory,
                f"RiskAnalyst: {result['verdict']} ({result['confidence']}%)"
            )
        except json.JSONDecodeError as e:
            self._log(f"JSON parse error: {e}")
            result = {
                "agent": "RiskAnalyst",
                "verdict": "DELAY",
                "confidence": 55,
                "evidence": ["Parse error", "Unable to calculate risk", "Manual review"],
                "recommendation": "Assess coverage gaps"
            }
            memory["council_votes"]["risk_analyst"] = result
            self._append_log(memory, "RiskAnalyst: Parse error, fallback used")

        return memory
