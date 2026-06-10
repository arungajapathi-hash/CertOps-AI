import json
from typing import Dict
import os

from backend.agents.base_agent import BaseAgent


class EngagementAgent(BaseAgent):
    def __init__(self):
        super().__init__("EngagementAgent")

    def _load_work_signals(self) -> list:
        """Load work signals from synthetic data."""
        try:
            ws_path = json.load(open('data/synthetic/work_signals.json', 'r', encoding='utf-8'))
            return ws_path if isinstance(ws_path, list) else []
        except Exception:
            try:
                base = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                    'data', 'synthetic', 'work_signals.json'
                )
                ws_path = json.load(open(base, 'r', encoding='utf-8'))
                return ws_path if isinstance(ws_path, list) else []
            except Exception:
                return []

    def _generate_work_signal(self, role: str) -> dict:
        """Generate realistic work signal via LLM if not in synthetic data."""
        system_prompt = "Return only valid JSON. No explanation or markdown."
        
        user_prompt = f"""Generate realistic work signals for a {role} at a mid-size tech company.
Return ONLY this JSON structure (no markdown fences):
{{
  "employee_id": "EMP-DYNAMIC",
  "meeting_hours_per_week": 15,
  "focus_hours_per_week": 15,
  "preferred_learning_slot": "Evening",
  "current_workload": "Medium"
}}"""
        
        response = self._call_llm(system_prompt, user_prompt, temperature=0.5)
        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            clean = clean.strip()
            return json.loads(clean)
        except Exception:
            return {
                "employee_id": "EMP-DEFAULT",
                "meeting_hours_per_week": 15,
                "focus_hours_per_week": 15,
                "preferred_learning_slot": "Morning",
                "current_workload": "Medium"
            }

    async def execute(self, memory: Dict) -> Dict:
        self._log("EngagementAgent: collecting work signals and recommending windows")
        
        # Load work signals from synthetic data
        work_data = self._load_work_signals()
        
        learner_id = memory.get('learner_id', 'L-1001')
        # Map L-1001 -> EMP-001
        emp_id = 'EMP-001'
        try:
            num = int(learner_id.split('-')[-1])
            emp_id = f'EMP-{num:03d}'
        except Exception:
            pass

        # Try to find matching work signal
        work_signal = next((e for e in work_data if e.get('employee_id') == emp_id), None)
        
        # If not found, generate dynamically
        if not work_signal:
            self._log(f"No work signal for {emp_id}, generating dynamically")
            work_signal = self._generate_work_signal(memory.get('role', 'Cloud Engineer'))
        
        memory['work_signals'] = work_signal

        system_prompt = (
            "You are a learning engagement specialist who understands how work patterns affect study habits. "
            "You recommend realistic study windows that fit around an engineer's actual workload without creating burnout. "
            "Be specific about days and times. Return ONLY valid JSON with no markdown fences or explanation."
        )

        study_hours = sum([
            w.get('hours', 0) 
            for w in (memory.get('study_plan', {}).values() 
                     if isinstance(memory.get('study_plan', {}), dict) else [])
        ])

        user_prompt = (
            f"""Recommend study windows for:

Meeting hours/week: {work_signal.get('meeting_hours_per_week', 15)}
Focus hours/week: {work_signal.get('focus_hours_per_week', 15)}
Preferred slot: {work_signal.get('preferred_learning_slot', 'Morning')}
Current workload: {work_signal.get('current_workload', 'Medium')}
Target cert: {memory.get('certification', 'AZ-204')}
Study hours/week needed: {study_hours / max(1, memory.get('target_weeks', 6))}

Return ONLY this JSON (no markdown):
{{
  "recommended_windows": [
    {{"day": "Tuesday", "time": "7:00 AM", "duration_hours": 1.5, "reason": "Morning focus slot"}},
    {{"day": "Thursday", "time": "7:00 AM", "duration_hours": 1.5, "reason": "Before meetings"}},
    {{"day": "Saturday", "time": "10:00 AM", "duration_hours": 2.0, "reason": "Weekend deep dive"}}
  ],
  "weekly_study_hours_possible": 6.0,
  "workload_risk": "Medium",
  "engagement_tip": "Block focus time calendar invites"
}}"""
        )

        resp = self._call_llm(system_prompt, user_prompt, temperature=0.3)
        try:
            clean = resp.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            clean = clean.strip()
            result = json.loads(clean)
        except Exception:
            result = {
                'recommended_windows': [
                    {'day': 'Tuesday', 'time': '7:00 AM', 'duration_hours': 1.5, 'reason': 'Morning focus'},
                    {'day': 'Thursday', 'time': '7:00 AM', 'duration_hours': 1.5, 'reason': 'Lower meeting load'},
                    {'day': 'Saturday', 'time': '10:00 AM', 'duration_hours': 2.0, 'reason': 'Weekend study'},
                ],
                'weekly_study_hours_possible': 6.0,
                'workload_risk': 'Medium',
                'engagement_tip': 'Block time on calendar',
            }

        # Ensure all durations are valid numbers
        windows = result.get('recommended_windows', [])
        for window in windows:
            if 'duration_hours' not in window or window['duration_hours'] is None:
                window['duration_hours'] = 1.5
            try:
                window['duration_hours'] = float(window['duration_hours'])
            except (ValueError, TypeError):
                window['duration_hours'] = 1.5

        memory['work_signals']['recommended_windows'] = windows
        memory['work_signals']['workload_risk'] = result.get('workload_risk', 'Medium')
        
        self._append_log(
            memory, 
            f"EngagementAgent: Study windows identified — "
            f"workload risk: {result.get('workload_risk')}, "
            f"{len(windows)} windows recommended"
        )
        return memory
