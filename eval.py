import unittest
from rag_engine import RagEngine
import os

# To run this:
# 1. Fill in .env with valid keys
# 2. python eval.py

class TestMiniRAG(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        print("Initializing RAG Engine for Eval...")
        cls.engine = RagEngine()
        
        # Ingest a sample document for testing
        cls.sample_text = """
        The Apollo 11 mission was the first spaceflight that landed the first two people on the Moon. 
        Commander Neil Armstrong and lunar module pilot Buzz Aldrin landed the Apollo Lunar Module Eagle on July 20, 1969, at 20:17 UTC. 
        Armstrong became the first person to step onto the lunar surface six hours and 39 minutes later on July 21 at 02:56 UTC; 
        Aldrin joined him 19 minutes later. They spent about two and a quarter hours together outside the spacecraft.
        
        The mission was launched by a Saturn V rocket from Kennedy Space Center on Merritt Island, Florida, on July 16, at 13:32 UTC. 
        It was the fifth crewed mission of NASA's Apollo program. The Apollo spacecraft had three parts: a command module (CM) with a cabin for the three astronauts, 
        and the only part that returned to Earth; a service module (SM), which supported the command module with propulsion, electrical power, oxygen, and water; 
        and a lunar module (LM) that had two stages – a descent stage for landing on the Moon and an ascent stage to place the astronauts back into lunar orbit.
        """
        print("Ingesting sample text...")
        cls.engine.ingest_text(cls.sample_text)

    def test_qa_pairs(self):
        qa_pairs = [
            {
                "question": "Who was the first person to walk on the moon?",
                "expected_keywords": ["Neil Armstrong", "Armstrong"]
            },
            {
                "question": "What date did they land on the moon?",
                "expected_keywords": ["July 20, 1969"]
            },
            {
                "question": "How long did they spend on the lunar surface outside the spacecraft?",
                "expected_keywords": ["two and a quarter hours", "2.25 hours"]
            },
            {
                "question": "What rocket launched the mission?",
                "expected_keywords": ["Saturn V"]
            },
            {
                "question": "What were the three parts of the Apollo spacecraft?",
                "expected_keywords": ["command module", "service module", "lunar module"]
            }
        ]
        
        print("\n--- Running Evaluation (5 Pairs) ---")
        score = 0
        for i, pair in enumerate(qa_pairs):
            q = pair['question']
            expected = pair['expected_keywords']
            
            print(f"Q{i+1}: {q}")
            result = self.engine.search(q)
            answer = result['answer']
            print(f"A{i+1}: {answer[:100]}...") # Truncate for display
            
            # Simple keyword match
            correct = any(k.lower() in answer.lower() for k in expected)
            if correct:
                print("[PASS]")
                score += 1
            else:
                print(f"[FAIL] Expected one of {expected}")
            print("-" * 30)
            
        print(f"Final Score: {score}/{len(qa_pairs)}")
        self.assertTrue(score >= 4, "Should get at least 4/5 right")

if __name__ == '__main__':
    unittest.main()
