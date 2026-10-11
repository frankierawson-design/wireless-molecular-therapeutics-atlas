"""Regression suite for critical global ranking research-integrity safeguards."""
import importlib.util
from pathlib import Path
import unittest

root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("rank_model",root/"methods"/"build_provisional_rankings.py")
rank=importlib.util.module_from_spec(spec);spec.loader.exec_module(rank)
a={"name":"A Researcher","openalex_author_id":"https://openalex.org/A12345",
   "orcid":"https://orcid.org/0000-0002-4872-8928","position":"last",
   "institutions":[{"name":"Test Institution","id":"https://openalex.org/I33"}]}
def doc(title,doi,year=2024,work_type="article",citations=10):
    return {"title":title,"doi":doi,"year":year,"openalex_id":"https://openalex.org/W"+str(abs(hash(doi))%1000000),
            "citations_openalex":citations,"openalex_work_type":work_type,
            "authors":[dict(a)],"publication_types":["Journal Article"],
            "source_databases":["OpenAlex"],"source_queries":["fixture"]}

TITLE="Wireless electrical-molecular quantum signalling for cancer cell apoptosis"
OTHER="Wireless bioelectronic modulation of membrane potential in glioblastoma"
THIRD="Bipolar electroactive conducting polymers for wireless cell stimulation"

class QualityGateTests(unittest.TestCase):
    def test_dissertation_with_therapeutic_title_is_not_a_scored_article(self):
        works=[doc("ONDEMAND Drug Delivery: The Role of Conducting Polymers and Wirefree Electrochemistry",
                 "",work_type="dissertation")]
        included,exc=rank.classify(works)
        self.assertEqual(included,[])
        self.assertEqual(exc["nonoriginal_openalex_work_type_dissertation"],1)

    def test_conference_and_book_not_scored(self):
        for kind in ("conference-paper","conference-abstract","book","book-chapter","review","preprint","editorial"):
            with self.subTest(kind=kind):
                included,ex=rank.classify([doc(TITLE,"10.1016/mock",work_type=kind)])
                self.assertFalse(included)
                self.assertEqual(ex["nonoriginal_openalex_work_type_"+kind],1)

    def test_same_author_copy_with_different_doi_counts_once(self):
        works=[doc(TITLE,"10.1000/journal-main",year=2024,citations=20),
               doc(TITLE,"10.1000/journal-copy",year=2025,citations=5),
               doc(OTHER,"10.1000/other",year=2026,citations=2),
               doc(THIRD,"10.1000/third",year=2022,citations=13)]
        included,_=rank.classify(works)
        ranks,_,_=rank.make_ranks(included,works)
        row=ranks["Overall"][0]
        self.assertEqual(row["publication_count"],3)
        self.assertEqual(row["duplicates_suppressed"],1)
        self.assertEqual(row["document_types_confirmed"],3)
        self.assertIn("10.1000/journal-main",[r["doi"] for r in row["papers"]])

    def test_arxiv_and_institutional_deposits_are_not_original_papers(self):
        for doi in ("10.48550/arxiv.1103.4711","10.17615/9pmk-wn51",
                    "10.2139/ssrn.5026819","10.25148/etd.fidc001249"):
            with self.subTest(doi=doi):
                included,_=rank.classify([doc(TITLE,doi,work_type="")])
                self.assertFalse(included)

    def test_no_doi_or_pmid_does_not_pass_original_article_gate(self):
        item=doc(TITLE,"",work_type="")
        included,exc=rank.classify([item])
        self.assertFalse(included)
        self.assertEqual(exc["unverified_work_without_doi_or_pmid"],1)

    def test_original_peer_reviewed_journal_study_still_passes(self):
        item=doc(TITLE,"10.1038/s41565-023-01496-y")
        included,_=rank.classify([item])
        self.assertEqual(len(included),1)

if __name__=="__main__":unittest.main()
