"""Offline tests: python -m unittest discover -s tests"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from common import Retriever, build_chunks, chunk_text, find_secrets, normalize, tokenize  # noqa: E402

SAMPLE = ROOT / "examples" / "sample_data"


class TestText(unittest.TestCase):
    def test_persian_normalization(self):
        self.assertEqual(tokenize("می‌روم"), ["می", "روم"])  # ZWNJ splits
        self.assertEqual(normalize("كتاب"), normalize("کتاب"))  # Arabic kaf -> Persian kaf
        self.assertIn("2026", tokenize("۲۰۲۶"))  # Persian digits -> ASCII

    def test_plural_folding(self):
        self.assertEqual(tokenize("values"), tokenize("value"))

    def test_chunking_respects_limit(self):
        text = "\n\n".join(["word " * 100] * 6)
        for c in chunk_text(text, max_chars=900):
            self.assertLessEqual(len(c), 900)


class TestRetrieval(unittest.TestCase):
    def setUp(self):
        self.chunks = build_chunks(SAMPLE)
        self.r = Retriever(self.chunks)

    def test_chunks_have_dates(self):
        self.assertTrue(self.chunks)
        self.assertEqual({c["date"] for c in self.chunks}, {"2026-01-01", "2026-01-02"})

    def test_english_query(self):
        hits = self.r.search("what does he value most honesty")
        self.assertTrue(hits)
        self.assertIn("honesty", hits[0][0]["text"].lower())

    def test_persian_query(self):
        hits = self.r.search("توصیه برای جوان‌ترها")
        self.assertTrue(hits)
        self.assertIn("صبور", hits[0][0]["text"])

    def test_deployment_query(self):
        hits = self.r.search("how is the website deployed")
        self.assertIn("GitLab", hits[0][0]["text"])

    def test_unknown_topic_returns_nothing(self):
        self.assertEqual(self.r.search("zzzqqq xylophone"), [])


class TestSecrets(unittest.TestCase):
    def test_flags_secrets(self):
        self.assertTrue(find_secrets("password: hunter2"))  # secrets-ok
        self.assertTrue(find_secrets("رمز عبور: 12345"))  # secrets-ok
        self.assertTrue(find_secrets("sk-abcdefghijklmnopqrstuvwxyz"))  # secrets-ok

    def test_ignores_normal_text(self):
        self.assertEqual(find_secrets("I like tea and finishing what I start."), [])


if __name__ == "__main__":
    unittest.main()
