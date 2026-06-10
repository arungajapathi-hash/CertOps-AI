import json
from typing import Dict

from backend.agents.base_agent import BaseAgent
from backend.sk_kernel import get_kernel


class StudyPlanAgent(BaseAgent):
    def __init__(self):
        super().__init__("StudyPlanAgent")
        self.kernel = get_kernel()

    async def execute(self, memory: Dict) -> Dict:
        self._log("StudyPlanAgent: creating dynamic study plan")
        
        system_prompt = (
            "You are a learning plan architect who creates realistic, week-by-week study schedules for busy engineers. "
            "You understand that engineers have meetings, deadlines, and limited focus time. "
            "You always break down complex certifications into manageable weekly milestones. "
            "Sequence topics from foundational to advanced. "
            "Return ONLY valid JSON with no markdown, no explanation, no code fences."
        )

        user_prompt = (
            f"""Create a detailed week-by-week study plan for:

Role: {memory.get('role')}
Certification: {memory.get('certification')}  
Target: {memory.get('target_weeks')} weeks
Skills to master: {json.dumps(memory.get('skill_map', []))}
Exam domains: {json.dumps(memory.get('exam_domains', []))}
Weak areas to prioritize: {json.dumps(memory.get('weak_topics', []))}
Estimated total hours: {memory.get('target_weeks', 6) * 5}

Create a learning plan that:
1. Sequences topics from foundational to advanced
2. Front-loads weak areas in weeks 1-3
3. Includes practice exams in final weeks
4. Allocates hours realistically (5-7 per week for {memory.get('target_weeks')} weeks)

Return ONLY valid JSON with this structure (no markdown fences, no explanation):
{{
  "study_plan": {{
    "week_1": {{
      "focus": "Foundation and core concepts",
      "topics": ["topic1", "topic2"],
      "hours": 5,
      "milestone": "Understand key concepts",
      "resources": ["Microsoft Learn module name"]
    }},
    "week_2": {{
      "focus": "Topic focus for week 2",
      "topics": ["topic1", "topic2"],
      "hours": 5,
      "milestone": "What you should master",
      "resources": ["Module name"]
    }}
  }},
  "total_hours": {memory.get('target_weeks', 6) * 5},
  "daily_recommendation": "1.5 hours/day on weekdays",
  "key_checkpoint_week": {max(1, memory.get('target_weeks', 6) - 2)},
  "final_review_week": {memory.get('target_weeks', 6)}
}}"""
        )

        resp = self._call_llm(system_prompt, user_prompt, temperature=0.25)
        try:
            # Clean response
            clean = resp.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            clean = clean.strip()
            
            result = json.loads(clean)
            study_plan = result.get("study_plan", {})
            total_hours = result.get("total_hours", 0)
        except Exception as e:
            self._log(f"StudyPlanAgent: JSON parse failed: {e}, using fallback plan")
            # Fallback: build a structured plan
            tw = memory.get("target_weeks", 1)
            study_plan = {}
            skills = memory.get("skill_map", ["Review certification guide"])
            
            for i in range(1, tw + 1):
                # Distribute skills across weeks
                week_skills = skills[(i-1) % len(skills):(i % len(skills)) + 1] if skills else ["Study week content"]
                study_plan[f"week_{i}"] = {
                    "focus": f"Week {i}: {week_skills[0] if week_skills else 'Core content'}",
                    "topics": week_skills[:3],
                    "hours": 5,
                    "milestone": f"Complete week {i} topics",
                    "resources": []
                }
            total_hours = tw * 5

        memory["study_plan"] = study_plan
        memory = self._append_log(
            memory, 
            f"StudyPlanAgent: {memory.get('target_weeks')}-week plan created — "
            f"{total_hours} total hours, {len(study_plan)} weeks structured"
        )
        return memory

