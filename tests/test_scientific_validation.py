"""Validation suite: blinding, preregistered sampling, reviewer locks and metrics."""
import importlib.util, pathlib, tempfile, json, unittest, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"methods"))
sys.path.insert(0,str(ROOT/"validation"))
import generate_review_packets as gen
import evaluate_reviews as ev
import ranking_sensitivity as stability
import generate_author_identity_audit as identities

def paper(title,doi,abstract="",oa="article"):
    return {"title":title,"doi":doi,"pmid":"","year":2024,
         "openalex_id":"https://openalex.org/W"+str(sum(map(ord,doi))),
         "citations_openalex":10,"openalex_work_type":oa,
         "authors":[{"name":"Test Scientist","openalex_author_id":"https://openalex.org/A2345"}],
         "abstract":abstract,"publication_types":["Journal Article"],"source_queries":["fixture"],
         "source_databases":["OpenAlex"]}
class ValidationTests(unittest.TestCase):
    def test_blinded_review_packet_never_contains_rank_or_machine_decision(self):
        works=[
          paper("Wireless bipolar electrochemistry for cancer cell apoptosis",
                "10.1000/a"),
          paper("Electrochemical drug release for cancer therapy using permanently wired electrodes","10.1000/b"),
          paper("Ultrasound-driven molecule delivery cancer therapy","10.1000/c"),
          paper("Population genetics survey of healthy humans","10.1000/d")]
        frame,blind,key,sizes=gen.make_packets(works,n_negative=1,seed=42)
        self.assertEqual(len(blind),4)
        self.assertEqual(len({x["record_id"] for x in blind}),4)
        self.assertTrue(all("machine_eligible_electrochemical" not in row for row in blind))
        self.assertTrue(all("doi" not in row and "authors" not in row for row in blind))
        self.assertEqual({x["record_id"] for x in blind},{x["record_id"] for x in key})
        self.assertTrue(all(float(x["inverse_probability_weight"])>=1 for x in key))

    def test_doi_less_queue_work_resolves_to_frozen_openalex_record(self):
        item=paper("Wireless bipolar electrochemistry cancer cell therapy","")
        item["openalex_id"]="https://openalex.org/W9922001"
        frames,blind,key,sizes=gen.make_packets([item],n_negative=2,seed=42)
        self.assertEqual(sizes["electro_queue_census"],1)
        self.assertEqual(len(blind),1)
        self.assertEqual(key[0]["openalex_work_id"],"https://openalex.org/W9922001")

    def test_blind_packets_reproducible(self):
        records=[paper("Wireless molecular drug delivery cancer cell","10.1000/"+str(x))
                 for x in range(7)]
        a=gen.make_packets(records,n_negative=2,seed=123)
        b=gen.make_packets(records,n_negative=2,seed=123)
        self.assertEqual(a[1],b[1])
        self.assertEqual(a[2],b[2])

    def test_blank_reviews_cannot_produce_accuracy(self):
        key=[{"record_id":"E1","frame_stratum":"electro_queue_census","inverse_probability_weight":"1",
             "machine_eligible_electrochemical":"include"}]
        blank=[{"record_id":"E1","initial_eligibility_include_exclude_uncertain":"",
                "reviewer_code":""}]
        result=ev.review_section(blank,blank,[{"record_id":"E1"}],key)
        self.assertFalse(result["validation_ready"])
        self.assertEqual(result["expected_records"],1)
        self.assertNotIn("weighted_rates",result)

    def test_dual_agreement_is_not_automated_adjudication(self):
        key=[{"record_id":"E1","frame_stratum":"S1","inverse_probability_weight":"1","machine_eligible_electrochemical":"include"},
             {"record_id":"E2","frame_stratum":"S2","inverse_probability_weight":"2","machine_eligible_electrochemical":"exclude"}]
        ra=[{"record_id":"E1","initial_eligibility_include_exclude_uncertain":"include","reviewer_code":"R-A"},
            {"record_id":"E2","initial_eligibility_include_exclude_uncertain":"include","reviewer_code":"R-A"}]
        rb=[{"record_id":"E1","initial_eligibility_include_exclude_uncertain":"include","reviewer_code":"R-B"},
            {"record_id":"E2","initial_eligibility_include_exclude_uncertain":"exclude","reviewer_code":"R-B"}]
        pending=ev.review_section(ra,rb,[],key)
        self.assertFalse(pending["validation_ready"])
        adj=[{"record_id":"E2","adjudicator_code":"R-C",
              "final_eligibility_include_exclude_uncertain":"exclude",
              "evidence_source_url":"https://doi.org/10.1000/test"}]
        result=ev.review_section(ra,rb,adj,key)
        self.assertTrue(result["validation_ready"])
        self.assertEqual(result["weighted_confusion"]["TP"],1)
        self.assertEqual(result["weighted_confusion"]["TN"],2)
        self.assertEqual(result["weighted_rates"]["recall"],1)
        self.assertEqual(result["adjudicated"],1)

    def test_reference_seed_does_not_count_as_independent(self):
        rows=[{"modality":"Electrochemical","doi":"10.1038/s41565-023-01496-y",
               "independent_eligibility_include_exclude_uncertain":"include",
               "source_before_atlas_lookup":"yes","reviewer_confirmed_original_yes_no":"yes",
               "verification_url":"https://doi.org/10.1038/s41565-023-01496-y",
               "independent_discovery_method":"independent DOI search"}]
        result=ev.reference_section(rows,[{"doi":rows[0]["doi"]}])
        self.assertEqual(result["modalities"]["Electrochemical"]["independent_verified_eligible"],0)
        self.assertNotEqual(result["status"],"EVALUATED_WITH_INDEPENDENT_REFERENCE_DATA")

    def test_wilson_bounds_valid(self):
        lo,hi=ev.wilson(49,50)
        self.assertLess(lo,.98);self.assertGreaterEqual(hi,.98)

    def test_author_paper_sampling_has_source_links_without_rank_labels(self):
        works=[paper("Wireless bipolar electrochemistry cancer cell therapy", "10.1000/a"),
               paper("Remote conductive polymer drug release in cellular therapy","10.1000/b"),
               paper("General unrelated study with author affiliation","10.1000/c")]
        ranks={"rankings":{"Overall":[{"openalex_author_id":"https://openalex.org/A2345"}]}}
        reviewers,key,manifest=identities.sampling(works,ranks,seed=41,
            quotas={k:2 for k in identities.QUOTAS})
        self.assertGreater(len(reviewers),0)
        self.assertEqual(len(reviewers),len(key))
        self.assertEqual(len({x["audit_id"] for x in reviewers}),len(reviewers))
        self.assertTrue(all("rank" not in x and "sampling_weight" not in x for x in reviewers))
        self.assertTrue(all(not x["classification_correct_wrong_person_split_ambiguous_unverifiable"] for x in reviewers))
        self.assertEqual(reviewers,identities.sampling(works,ranks,seed=41,
            quotas={k:2 for k in identities.QUOTAS})[0])

    def test_rank_model_is_explicitly_not_world_validated(self):
        data={"methods_version":"fixture","rankings":{"Overall":[
         {"name":"A","openalex_author_id":"https://openalex.org/A1","orcid":"","institution":"X","publication_count":3,"score":40,
          "components":{"citation_impact":90,"relevant_output":20,"authorship_leadership":20,"translational_indicators":20,"sustained_activity":20},"papers":[]},
         {"name":"B","openalex_author_id":"https://openalex.org/A2","orcid":"","institution":"Y","publication_count":3,"score":40,
          "components":{"citation_impact":15,"relevant_output":100,"authorship_leadership":20,"translational_indicators":20,"sustained_activity":20},"papers":[]} ]}}
        result=stability.evaluate(data)
        self.assertEqual(result["validity_status"],"EXPLORATORY_CONDITIONAL_STABILITY_ONLY")
        self.assertIn("citation_emphasis",result["modalities"]["Overall"]["comparison"])

if __name__=="__main__":unittest.main()
