"""Regressions for the electrical-treatment literature screening register."""
import importlib.util
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"methods"))
spec=importlib.util.spec_from_file_location("electrical_register",ROOT/"methods"/"build_electrical_treatment_queue.py")
queue=importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue)

def article(title,doi,year=2023,kind="article"):
    return {
        "title":title,"doi":doi,"year":year,"openalex_id":"https://openalex.org/W123",
        "citations_openalex":5,"openalex_work_type":kind,
        "source_databases":["OpenAlex"],"source_queries":["sentinel"],
        "authors":[{"name":"A Verified Author","openalex_author_id":"https://openalex.org/A1234",
                    "orcid":"","position":"first","institutions":[]}],
        "publication_types":["Journal Article"],
    }

class RegisterTests(unittest.TestCase):
    def test_each_clinical_therapy_visible_for_independent_screening(self):
        examples=[
            ("Tumor Treating Fields Plus Temozolomide for Glioblastoma","10.1111/ttf","TTFields"),
            ("Electrochemotherapy with Bleomycin for Melanoma","10.1111/ect","Electrochemotherapy"),
            ("Irreversible Electroporation for Pancreatic Cancer","10.1111/ire","Electroporation"),
            ("Deep Brain Stimulation for Parkinson Disease","10.1111/dbs","Neuromodulation"),
            ("Electrical Stimulation Therapy for Wound Healing","10.1111/wound","Electrical Stimulation"),
            ("Wireless Bipolar Electrochemistry for Cancer Therapy","10.1111/bpe","Electrochemical"),
        ]
        out=queue.collect([article(t,d) for t,d,_ in examples])
        self.assertEqual(out["total_candidate_records"],len(examples))
        for _,doi,pathway in examples:
            row=next(p for p in out["papers"] if p["doi"]==doi)
            self.assertIn(pathway,row["pathways"])
            self.assertEqual(row["scientific_validation"],"NOT_INDEPENDENTLY_SCREENED")
        self.assertEqual(out["independent_full_text_screening_completed"],0)

    def test_reviews_remain_visible_but_not_scored_as_originals(self):
        sample=article("Systematic Review of Tumor Treating Fields for Glioblastoma",
                       "10.1111/review",kind="review")
        out=queue.collect([sample])
        self.assertEqual(out["papers"][0]["screening_status"],"review_or_background_candidate")

    def test_no_false_confirmation_from_search_leads(self):
        sample=article("Cancer treatment by a novel technique","10.1111/ambiguous")
        sample["source_queries"]=["irreversible electroporation cancer ablation clinical trial"]
        out=queue.collect([sample])
        self.assertGreaterEqual(out["total_candidate_records"],1)
        self.assertTrue(all(p["scientific_validation"]=="NOT_INDEPENDENTLY_SCREENED" for p in out["papers"]))

    def test_technical_nontherapeutic_false_positive_screened_out(self):
        sample=article("Lithium Ion Battery Anode Conductivity","10.1111/battery")
        sample["source_queries"]=["electrical stimulation wound healing"]
        self.assertEqual(queue.collect([sample])["papers"],[])

    def test_retrieval_deduplicates_exact_dois(self):
        a=article("Electrochemotherapy for skin metastases","10.1111/one")
        b=dict(a);b["title"]="Electrochemotherapy for skin metastases, online version"
        out=queue.collect([a,b])
        self.assertEqual(out["total_candidate_records"],1)

if __name__=="__main__":
    unittest.main()
