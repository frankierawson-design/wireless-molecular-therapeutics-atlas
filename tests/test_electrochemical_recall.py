"""Regression checks for molecular electro-pharmaceutics recall and specificity.

All publications below are synthetic fixtures (not bibliographic verification).
"""
import importlib.util
from pathlib import Path
import unittest

file=Path(__file__).resolve().parents[1]/"methods"/"build_provisional_rankings.py"
spec=importlib.util.spec_from_file_location("build_rankings",file)
rank=importlib.util.module_from_spec(spec);spec.loader.exec_module(rank)

A={"name":"Researcher A","orcid":"https://orcid.org/0000-0002-4872-8928",
   "openalex_author_id":"https://openalex.org/A5030287864",
   "institutions":[{"name":"University of Nottingham","id":"https://openalex.org/I142263535"}],
   "position":"last"}

def p(title,abstract="",doi="10.1000/fixture",year=2025):
    return {"title":title,"abstract":abstract,"doi":doi,"year":year,
            "openalex_id":"https://openalex.org/W1","citations_openalex":8,
            "authors":[A],"source_queries":["fixture"],"source_databases":["OpenAlex"],
            "openalex_work_type":"article","publication_types":["Journal Article"]}

class ElectrochemicalScreeningTests(unittest.TestCase):
    def included(self,title,abstract="",doi="10.1000/fixture"):
        rows,exc=rank.classify([p(title,abstract,doi)])
        return bool(rows),rows,exc

    def test_wirefree_pedot_drug_release_platform(self):
        found,rows,_=self.included("Spatially Controlled, Wirefree, Drug Release along a Single PEDOT Film.")
        self.assertTrue(found)
        self.assertIn("Electrochemical",rows[0]["modalities"])
        self.assertEqual(rows[0]["evidence_tier"],"molecular_delivery_platform_candidate")

    def test_photovoltaic_wireless_ion_pump(self):
        found,rows,_=self.included("Wireless organic electronic ion pumps driven by photovoltaics",
            "This wireless photovoltaic device permits electronically controlled delivery of pharmacologically active ions and acetylcholine.")
        self.assertTrue(found)
        self.assertIn("Electrochemical",rows[0]["modalities"])

    def test_wireless_therapeutic_bipolar_drug_loading(self):
        found,rows,_=self.included("Bipolar electrochemistry-driven wireless drug loading and energy harvesting in conductive hybrid hydrogels")
        self.assertTrue(found)
        self.assertIn("Electrochemical",rows[0]["modalities"])

    def test_remotely_controlled_electrochemical_pump(self):
        found,rows,_=self.included("Nanofluidic-based electrochemical pump for remotely controlled, on-demand drug delivery")
        self.assertTrue(found)
        self.assertIn("Electrochemical",rows[0]["modalities"])

    def test_nanoantenna_apoptosis(self):
        found,rows,_=self.included("Wireless electrical-molecular quantum signalling for cancer cell apoptosis.")
        self.assertTrue(found)
        self.assertEqual(rows[0]["evidence_tier"],"therapeutic_biological_candidate")

    def test_globally_wired_only_electrochemotherapy_not_wireless(self):
        found,_,exc=self.included("Electrochemical drug release for cancer therapy via permanently wired electrodes.")
        self.assertFalse(found)
        self.assertEqual(exc["no_remote_electrochemical_actuation"],1)

    def test_electrochemical_diagnostic_monitor_not_therapy(self):
        found,_,_=self.included("Wireless electrochemical drug monitoring with an implantable sensor")
        self.assertFalse(found)

    def test_review_exclusion(self):
        found,_,exc=self.included("Wireless electrochemical stimulation of neuronal growth: a review")
        self.assertFalse(found)
        self.assertEqual(exc["possible_review_or_nonoriginal"],1)

    def test_pure_mechanistic_electrodeposition_not_therapy(self):
        found,_,_=self.included("Electric Field Distribution in Bipolar Electrochemical Cells: Effects on the Wirefree Electrodeposition of Conducting Polymer")
        self.assertFalse(found)

    def test_abstract_mechanism_rescues_delivery_platform(self):
        found,rows,_=self.included("Wireless PEDOT biomolecular delivery platform",
          "A wirefree bipolar electrochemical method is used to release drug molecules, creating electrochemically driven delivery.")
        self.assertTrue(found)
        self.assertIn("Electrochemical",rows[0]["modalities"])

if __name__=="__main__":unittest.main()
