"""Regression tests: known publication coverage is not equivalent to author identity or eligibility."""
import importlib.util
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "methods"))
spec = importlib.util.spec_from_file_location("forster_audit", ROOT / "methods" / "electrochemical_seed_audit.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class ForsterCoverageTests(unittest.TestCase):
    def test_known_forster_dois_have_auditable_expectations(self):
        rows = [s for s in audit.SEEDS if s.get("expected_author") == "Robert J. Forster"]
        self.assertEqual({s["doi"] for s in rows}, {
            "10.1016/j.elecom.2024.107832",
            "10.1039/d4cc03996c",
            "10.1021/acs.analchem.4c04454",
            "10.1002/celc.202400506",
        })
        self.assertEqual({s["expected_orcid"] for s in rows}, {"0000-0001-5079-3123"})
        self.assertEqual(sum(s["expected"] == "review-not-ranked" for s in rows), 1)

    def test_positive_identity_requires_paper_level_orcid(self):
        seed = {"expected_author": "Robert J. Forster", "expected_orcid": "0000-0001-5079-3123"}
        self.assertEqual(audit.author_identity_status(None, seed), "not_harvested")
        self.assertEqual(audit.author_identity_status({"authors": [{"name": "Robert J. Forster"}]}, seed),
                         "name_only_identity_not_verified")
        self.assertEqual(audit.author_identity_status({
            "authors": [{"name": "Robert J. Forster", "orcid": "https://orcid.org/0000-0001-5079-3123"}]
        }, seed), "orcid_verified_in_work_metadata")
        self.assertEqual(audit.author_identity_status({
            "authors": [{"name": "Robert Forster", "orcid": "0000-0003-1111-2222"}]
        }, seed), "name_only_identity_not_verified")
        self.assertEqual(audit.author_identity_status({
            "authors": [{"name": "Unrelated Author"}]
        }, seed), "expected_author_absent_from_work_metadata")

    def test_visible_correction_and_explicit_unavailable_fallback(self):
        page = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("publication and author-identity reconciliation pending", page)
        self.assertIn("DOI evidence file unavailable", page)
        self.assertIn("not</strong> evidence of a lack of relevant research", page)


if __name__ == "__main__":
    unittest.main()
