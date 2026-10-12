"""Conservative pharmacological mediation tests; synthetic evidence is not experimental verification."""
import importlib.util,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"methods"))
import electropharmaceutics_focus as focused
import audit_researcher_publications as references
def paper(title,abstract="",doi="10.1000/test",year=2024,kind="article"):
    return {"title":title,"abstract":abstract,"doi":doi,"year":year,
        "openalex_id":"https://openalex.org/W12345678","citations_openalex":5,
        "openalex_work_type":kind,"authors":[{"name":"Test Scientist",
        "orcid":"https://orcid.org/0000-0001-5079-3123",
        "openalex_author_id":"https://openalex.org/A10001","position":"last",
        "institutions":[{"name":"Example Institute","id":"https://openalex.org/I100"}]}]}

class FocusedPharmaceuticsTests(unittest.TestCase):
    def test_electrochemotherapy_drug_uptake_is_eligible(self):
        x=paper("Electrochemotherapy with bleomycin for cancer treatment")
        self.assertEqual(focused.candidate_role(x),"direct_candidate")
    def test_electrical_drug_response_is_eligible(self):
        x=paper("Tackling Anticancer Drug Resistance and Endosomal Escape in Aggressive Brain Tumors Using Bioelectronics",
           "Alternating electric fields enhance cisplatin response and nanoparticle endosomal escape.")
        self.assertEqual(focused.candidate_role(x),"direct_candidate")
        self.assertTrue(focused.screen([x])[0])
    def test_molecular_redox_therapeutic_effect_is_eligible(self):
        x=paper("Wireless electrical–molecular quantum signalling for cancer cell apoptosis",
             "Wireless electrochemistry switches the redox state of cytochrome c for cancer cell apoptosis.")
        self.assertEqual(focused.candidate_role(x),"direct_candidate")
    def test_wireless_electrochemical_drug_delivery_is_eligible(self):
        x=paper("Electrochemical and wirefree drug release for neuronal treatment",
             "Electrically controlled delivery of acetylcholine")
        self.assertEqual(focused.candidate_role(x),"direct_candidate")
    def test_coadministered_ttfields_does_not_infer_mediation(self):
        x=paper("Tumor Treating Fields Plus Maintenance Temozolomide Alone versus Temozolomide for Glioblastoma",
             "Alternating electric fields and temozolomide improve treatment outcomes.")
        self.assertEqual(focused.candidate_role(x),"out_of_scope")
    def test_electroporation_ablation_is_not_pharmaceutics(self):
        x=paper("Irreversible Electroporation Ablation of Pancreatic Cancer")
        self.assertNotEqual(focused.candidate_role(x),"direct_candidate")
    def test_deep_brain_stimulation_is_not_pharmaceutics(self):
        x=paper("Deep Brain Stimulation for Parkinson Disease")
        self.assertNotEqual(focused.candidate_role(x),"direct_candidate")
    def test_molecular_transport_and_impedance_enabling_not_scored(self):
        items=[
            paper("Electric Field Induced Biomimetic Transmembrane Electron Transport Using Carbon Nanotube Porins"),
            paper("Impedimetric Characterization of Bipolar Nanoelectrodes with Cancer Cells",
                "Electrical sensing of intracellular gold nanoparticles"),
            paper("Wireless Nanobioelectronics for Electrical Intracellular Sensing",
                "Externally controlled redox of zinc porphyrins in cells")
        ]
        self.assertEqual(len(focused.screen(items)[0]),0)
    def test_exclusion_of_review_without_credit(self):
        x=paper("Electrochemotherapy with bleomycin in cancer",kind="review")
        eligible,context=focused.screen([x])
        self.assertEqual(len(eligible),0)
        self.assertEqual(len(context),1)
    def test_focus_ranks_omit_unrelated_modalities(self):
        items=[paper("Electrochemotherapy with bleomycin for cancer",doi="10.1000/1"),
               paper("Wireless electrochemical drug release for cancer",doi="10.1000/2"),
               paper("Deep Brain Stimulation for Parkinson Disease",doi="10.1000/3")]
        d=focused.build(items)
        self.assertEqual(d["summary"]["machine_screened_papers"],2)
        self.assertEqual(set(d["rankings"]),{focused.FIELD,"Overall"})
        self.assertNotIn("TTFields",d["rankings"])
        self.assertNotIn("Neuromodulation",d["rankings"])
        self.assertEqual(d["scientific_validation"],"NOT_INDEPENDENTLY_SCREENED")
        self.assertEqual(d["rankings"]["Overall"][0]["publication_count"],2)
    def test_reference_audit_retains_missing_and_ineligible_works(self):
        work=paper("Wireless electrochemical drug release for cancer",doi="10.1000/1")
        work["authors"][0]["name"]="Frankie J. Rawson"
        work["authors"][0]["orcid"]="https://orcid.org/0000-0002-4872-8928"
        manifest={"researcher":"Frankie J. Rawson","orcid":"0000-0002-4872-8928",
                  "works":[
                    {"doi":"10.1000/1","year":2024,"title":"Drug release","source":"https://doi.org/10.1000/1","anticipated_review_class":"candidate"},
                    {"doi":"10.1000/missing","year":2023,"title":"Missing","source":"https://doi.org/10.1000/missing","anticipated_review_class":"context"}]}
        result=references.compare([work],manifest)
        self.assertEqual(result["found_in_candidate_corpus"],1)
        self.assertEqual(result["total_reference_works"],2)
        self.assertEqual(result["reference_works"][0]["author_identity_status"],"work_level_orcid_matches")
        self.assertEqual(result["reference_works"][1]["author_identity_status"],"publication_not_harvested")
        self.assertEqual(result["full_text_screened_independently"],0)

if __name__=="__main__": unittest.main()
