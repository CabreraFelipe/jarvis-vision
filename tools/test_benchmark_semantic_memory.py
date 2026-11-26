import unittest
from benchmark_semantic_memory import run,CASES,NOTES

class BenchmarkTests(unittest.TestCase):
    def test_only_synthetic_cases(self):
        calls=[]
        def fake(rows,question):
            calls.append((rows,question))
            return []
        results=run(fake,lambda:0.0)
        self.assertEqual(len(results),len(CASES))
        self.assertTrue(all(rows==NOTES for rows,_ in calls))
        self.assertTrue(all(r[4]==0 for r in results))

if __name__=='__main__':unittest.main()
