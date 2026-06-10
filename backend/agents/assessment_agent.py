"""AssessmentAgent - Generates mock exam questions and evaluates answers."""
import json
from typing import Dict, List, Any

from backend.agents.base_agent import BaseAgent
from backend.plugins.knowledge_router import get_knowledge_plugin
from backend import database


class AssessmentAgent(BaseAgent):
    def __init__(self):
        super().__init__("AssessmentAgent")
        self.knowledge = get_knowledge_plugin()

    async def execute(self, memory: Dict) -> Dict:
        """Generate assessment questions based on certification and weak topics."""
        self._log("Generating assessment questions...")

        certification = memory.get("certification", "Unknown")
        weak_topics = memory.get("weak_topics", [])
        skill_map = memory.get("skill_map", [])

        # Step 1: Get certification guide
        try:
            guide = self.knowledge.get_certification_guide(certification)
            content = guide.get("content", "") if isinstance(guide, dict) else str(guide)
        except Exception as e:
            self._log(f"Error fetching guide: {e}")
            content = f"General {certification} exam content"

        # Step 2: Generate questions via LLM
        system_prompt = (
            "You are a Microsoft certification exam question generator. "
            "Generate realistic exam-style questions grounded in official exam content. "
            "Every question must include a source citation. "
            "Questions must be multiple choice with 4 options. "
            "One correct answer only. "
            "Focus heavily on weak topics. "
            "Return only valid JSON."
        )

        user_prompt = (
            f"Generate 10 exam questions for {certification}.\n\n"
            f"Certification content:\n{content[:2000]}\n\n"
            f"Focus these weak topics heavily (60% of questions):\n{weak_topics}\n\n"
            f"Also cover these skills (40% of questions):\n{skill_map[:5] if skill_map else ['General certification topics']}\n\n"
            f"Return JSON:\n"
            f"{{\n"
            f"  'questions': [\n"
            f"    {{\n"
            f"      'id': 1,\n"
            f"      'topic': 'topic name',\n"
            f"      'question': 'question text',\n"
            f"      'options': {{\n"
            f"        'A': 'option text',\n"
            f"        'B': 'option text',\n"
            f"        'C': 'option text',\n"
            f"        'D': 'option text'\n"
            f"      }},\n"
            f"      'correct_answer': 'A',\n"
            f"      'explanation': 'why this is correct',\n"
            f"      'source': 'document section citation'\n"
            f"    }}\n"
            f"  ]\n"
            f"}}"
        )

        response = self._call_llm(system_prompt, user_prompt, temperature=0.7)

        # Step 3: Parse questions
        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            clean = clean.strip()

            result = json.loads(clean)
            questions = result.get("questions", [])

            if not questions:
                # Fallback questions
                questions = self._generate_fallback_questions(certification, weak_topics)

            memory["assessment_questions"] = questions
            self._append_log(memory, f"AssessmentAgent: Generated {len(questions)} questions for {certification}")

        except json.JSONDecodeError as e:
            self._log(f"JSON parse error: {e}")
            questions = self._generate_fallback_questions(certification, weak_topics)
            memory["assessment_questions"] = questions
            self._append_log(memory, f"AssessmentAgent: Using fallback questions ({len(questions)})")

        return memory

    async def evaluate(self, memory: Dict, answers: Dict) -> Dict:
        """Evaluate submitted answers and calculate scores."""
        self._log("Evaluating assessment answers...")

        questions = memory.get("assessment_questions", [])
        if not questions:
            self._log("No questions found in memory")
            memory["assessment_score"] = 0
            memory["assessment_outcome"] = "FAIL"
            return memory

        # Step 1: Score answers
        correct = 0
        topic_scores = {}
        wrong_questions = []

        for q in questions:
            q_id = str(q.get("id", ""))
            correct_answer = q.get("correct_answer", "")
            user_answer = answers.get(q_id, "").upper()
            is_correct = user_answer == correct_answer.upper()

            if is_correct:
                correct += 1
            else:
                wrong_questions.append(q)

            topic = q.get("topic", "General")
            if topic not in topic_scores:
                topic_scores[topic] = {"correct": 0, "total": 0}
            topic_scores[topic]["total"] += 1
            if is_correct:
                topic_scores[topic]["correct"] += 1

        # Step 2: Calculate scores
        overall_score = (correct / len(questions)) * 100 if questions else 0

        topic_breakdown = {}
        for topic, scores in topic_scores.items():
            topic_breakdown[topic] = {
                "score": (scores["correct"] / scores["total"]) * 100 if scores["total"] > 0 else 0,
                "correct": scores["correct"],
                "total": scores["total"]
            }

        outcome = "PASS" if overall_score >= 70 else "FAIL"

        # Step 3: Identify new weak topics from wrong answers
        new_weak = [
            t for t, s in topic_breakdown.items()
            if s["score"] < 60
        ]
        memory["weak_topics"] = list(set(
            memory.get("weak_topics", []) + new_weak
        ))

        # Step 4: Update memory
        memory["assessment_score"] = overall_score
        memory["assessment_breakdown"] = topic_breakdown
        memory["assessment_outcome"] = outcome
        memory["wrong_questions"] = wrong_questions
        memory["last_answers"] = answers

        # Step 5: Save to SQLite
        try:
            conn = database.get_connection()
            cursor = conn.cursor()

            learner_id = memory.get("learner_id", "unknown")
            certification = memory.get("certification", "unknown")

            cursor.execute("""
                INSERT INTO assessment_results (learner_id, certification, score, topic_breakdown, outcome)
                VALUES (?, ?, ?, ?, ?)
            """, (
                learner_id,
                certification,
                overall_score,
                json.dumps(topic_breakdown),
                outcome
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            self._log(f"Error saving assessment result: {e}")

        self._append_log(
            memory,
            f"AssessmentAgent: Score {overall_score:.1f}% — {outcome}"
        )

        return memory

    def _generate_fallback_questions(self, certification: str, weak_topics: List[str]) -> List[Dict]:
        """Generate fallback questions when LLM fails."""
        questions = []
        topics = weak_topics if weak_topics else [f"{certification} General"]

        for i in range(10):
            topic = topics[i % len(topics)]
            questions.append({
                "id": i + 1,
                "topic": topic,
                "question": f"Sample question {i+1} about {topic} for {certification}?",
                "options": {
                    "A": f"Option A for {topic}",
                    "B": f"Option B for {topic}",
                    "C": f"Option C for {topic}",
                    "D": f"Option D for {topic}"
                },
                "correct_answer": "A",
                "explanation": f"Option A is correct because it properly addresses {topic}.",
                "source": f"{certification} Exam Guide - {topic}"
            })

        return questions

