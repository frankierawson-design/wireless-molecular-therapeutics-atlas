"""Mechanism-specific electrical-therapy regression and sentinel coverage tests.

These fixtures test classification, NOT scientific literature-completeness.
"""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"methods"))

def load(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/"methods"/file)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

model=load("expanded_ranker","build_provisional_rankings.py")
coverage=load("expanded_coverage","electrical_treatment_coverage_audit.py")

AUTHOR={"name":"Verified Researcher","openalex_author_id":"https://openalex.org/A999",
        "orcid":"","position":"last","institutions":[]}

def original(title,doi,year=2023):
    return {"doi":doi,"title":title,"year":year,"openalex_id":"https://openalex.org/W"+str(abs(hash(doi))),
            "citations_openalex":15,"openalex_work_type":"article",
            "authors":[dict(AUTHOR)],"publication_types":["Journal Article"],
            "abstract":"","source_queries":["fixture"],"source_databases":["OpenAlex"]}

TITLES=[
 ("TTFields","10.1001/jama.2017.18718",
  "Effect of Tumor-Treating Fields Plus Maintenance Temozolomide vs Maintenance Temozolomide Alone on Survival in Patients With Glioblastoma"),
 ("TTFields","10.1001/jama.2015.16669",
  "Maintenance Therapy With Tumor-Treating Fields Plus Temozolomide vs Temozolomide Alone for Glioblastoma"),
 ("Electrochemotherapy","10.1016/j.ejcsup.2006.08.002",
  "Electrochemotherapy - An easy, highly effective and safe treatment of cutaneous and subcutaneous metastases"),
 ("Electroporation","10.1007/s00270-010-9964-1",
  "Irreversible electroporation of renal cell carcinoma: a first-in-man phase I clinical study"),
 ("Electroporation","10.1056/nejmoa2307291",
  "Pulsed Field or Conventional Thermal Ablation for Paroxysmal Atrial Fibrillation"),
 ("Neuromodulation","10.1056/nejmoa060281",
  "A Randomized Trial of Deep-Brain Stimulation for Parkinson's Disease"),
 ("Neuromodulation","10.1056/nejmoa1612999",
  "Trial of Electrical Direct-Current Therapy versus Escitalopram for Depression"),
 ("Electrical Stimulation","10.1177/19322968211035128",
  "Home-Based Electrical Stimulation to Accelerate Wound Healing-A Double-Blinded Randomized Control Trial"),
 ("Electrical Stimulation","10.1016/j.apmr.2009.12.026",
  "Electrical stimulation therapy increases rate of healing of pressure ulcers in community-dwelling people with spinal cord injury"),
 ("Electrochemical","10.1016/j.apmt.2020.100804",
  "Bipolar electroactive conducting polymers for wireless cell stimulation"),
 ("Electrochemical","10.1016/j.elecom.2023.107626",
  "On demand, wireless electrochemical release of brain derived neurotrophic factor"),
]

class ElectricalExpansionTests(unittest.TestCase):
    def test_each_primary_study_classified_into_intended_treatment(self):
        for intended,doi,title in TITLES:
            with self.subTest(doi=doi,intended=intended):
                candidates,exclusions=model.classify([original(title,doi)])
                self.assertEqual(len(candidates),1,str(exclusions))
                self.assertIn(intended,candidates[0]["modalities"])

    def test_no_automatic_redox_label_for_wired_treatments(self):
        for intended,doi,title in TITLES:
            if intended=="Electrochemical":continue
            with self.subTest(doi=doi):
                rows,_=model.classify([original(title,doi)])
                self.assertNotIn("Electrochemical",rows[0]["modalities"])
                self.assertNotIn("Hybrid",rows[0]["modalities"])

    def test_no_mechanism_inference_for_electrical_simulation_or_diagnostics(self):
        bad=[
          "Numerical simulation of the distribution of electric fields in a dielectric",
          "Electroporation of bacteria for laboratory transformation",
          "Wireless bipolar electrochemical sensor for glucose monitoring",
        ]
        for n,title in enumerate(bad):
            with self.subTest(title=title):
                rows,_=model.classify([original(title,"10.1000/f"+str(n))])
                self.assertFalse(rows)

    def test_wired_electrochemotherapy_is_supported(self):
        r=original("Electrochemotherapy with bleomycin for head and neck cancer",
                   "10.1000/example-wire")
        classified,_=model.classify([r])
        self.assertIn("Electrochemotherapy",classified[0]["modalities"])
        self.assertNotIn("Electrochemical",classified[0]["modalities"])

    def test_independent_coverage_exposes_retrieval_vs_scoring(self):
        data=[original(title,doi) for _,doi,title in TITLES]
        report=coverage.audit(data)
        self.assertEqual(len(report["pathways"]),6)
        for group in report["pathways"]:
            self.assertGreaterEqual(group["sentinels_retrieved"],1)
            self.assertGreaterEqual(group["sentinels_machine_included"],1)
            self.assertFalse(group["completeness_confirmed"])
            self.assertEqual(group["independently_full_text_screened"],0)
        self.assertEqual(report["validation_status"],"MACHINE_SCREENED_NOT_INDEPENDENTLY_VALIDATED")
        self.assertTrue(all(item["classified_in_target_pathway"] for item in report["sentinels"]))

if __name__=="__main__":
    unittest.main()
