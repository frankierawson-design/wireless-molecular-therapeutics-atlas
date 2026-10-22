import copy
import pathlib
import sys
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'validation'))
sys.path.insert(0,str(ROOT/'methods'))
import evaluate_reviews as ev
import audit_release_evidence as audit
import generate_review_packets as gen
from scopes import SCOPES,KNOWN_SENTINELS

class ReleaseGateTests(unittest.TestCase):
    def reviews(self):
        row={'record_id':'x','reviewer_code':'A','initial_eligibility_include_exclude_uncertain':'include',
             'review_date_yyyy_mm_dd':'2026-10-22','reason_code':'original study'}
        key=[{'record_id':'x','frame_stratum':'census','inverse_probability_weight':1,
              'machine_eligible_electrochemical':'include'}]
        return [row],[dict(row,reviewer_code='B')],key

    def test_agreement_without_full_text_is_not_validated(self):
        a,b,k=self.reviews()
        r=ev.review_section(a,b,[],k)
        self.assertFalse(r['validation_ready'])
        self.assertNotIn('weighted_rates',r)

    def test_empty_reviews_not_validated(self):
        self.assertFalse(ev.review_section([],[],[],[])['validation_ready'])

    def test_scope_mismatch_rejected_even_with_blank_reviews(self):
        a,b,k=self.reviews()
        with self.assertRaises(ValueError):ev.review_section(a,b,[],k,'electropharmaceutics')

    def test_all_clinical_sentinels_excluded(self):
        from electrical_treatment_coverage_audit import SENTINELS
        self.assertTrue(all(x['doi'].lower() in KNOWN_SENTINELS for x in SENTINELS))

    def test_reference_duplicates_and_unknown_categories_cannot_pass(self):
        row={'modality':'Electro-Mediated Pharmaceutics','doi':'10.9999/independent',
             'independent_eligibility_include_exclude_uncertain':'include',
             'source_before_atlas_lookup':'yes','reviewer_confirmed_original_yes_no':'yes',
             'verification_url':'https://example.org/fulltext','independent_discovery_method':'external bibliography',
             'reviewer_id':'C','review_date':'2026-10-22','full_text_page_or_quotation':'p4',
             'evidence_tier_T0_T1_T2_T3':'T3'}
        rows=[copy.deepcopy(row) for _ in range(30)]
        rows.append(dict(row,modality='Ultrasound'))
        r=ev.reference_section(rows,[{'doi':row['doi']}],'electropharmaceutics')
        self.assertEqual(r['modalities'][row['modality']]['independent_verified_eligible'],1)
        self.assertEqual(r['unknown_modality_rows'],1)
        self.assertNotEqual(r['status'],'EVALUATED_WITH_INDEPENDENT_REFERENCE_DATA')

    def test_threshold_failure_and_unresolved_identity_cannot_pass(self):
        review={'validation_ready':True,'threshold_check':{'recall_point_ge_0_95':True,'precision_point_ge_0_90':True}}
        ref={'status':'EVALUATED_WITH_INDEPENDENT_REFERENCE_DATA','modalities':{'x':{'recall_point_ge_0_95':True}}}
        authors={'not_yet_validated':False}
        self.assertEqual(ev.evaluation_status(review,ref,authors),'PILOT_THRESHOLDS_MET_SIGNOFF_PENDING')
        for section,key in [(review['threshold_check'],'recall_point_ge_0_95'),(review['threshold_check'],'precision_point_ge_0_90'),(ref['modalities']['x'],'recall_point_ge_0_95')]:
            section[key]=False
            self.assertEqual(ev.evaluation_status(review,ref,authors),'PILOT_THRESHOLDS_NOT_MET')
            section[key]=True
        authors['not_yet_validated']=True
        self.assertEqual(ev.evaluation_status(review,ref,authors),'PILOT_THRESHOLDS_NOT_MET')

    def test_later_failure_does_not_inherit_old_success(self):
        events=[{'source':'OpenAlex','query':'q','page':1,'complete_for_query':True,'error':''},
                {'source':'OpenAlex','query':'q','page':1,'complete_for_query':False,'error':'429'}]
        r=audit.query_report(events)[0]
        self.assertEqual(r['status'],'error')
        self.assertEqual(r['historical_error_events'],1)

    def test_page_cap_not_complete(self):
        r=audit.query_report([{'source':'OpenAlex','query':'q','page':3,'complete_for_query':False}])[0]
        self.assertEqual(r['status'],'bounded_or_unresolved')

    def test_focused_packet_uses_current_classifier(self):
        record={'title':'Electrochemotherapy bleomycin drug uptake therapy','year':2024,
                'doi':'10.9999/x','openalex_id':'https://openalex.org/W1','citations_openalex':4,
                'openalex_work_type':'article','authors':[{'name':'A','openalex_author_id':'https://openalex.org/A1'}]}
        frames,blind,key,sizes=gen.make_packets([record],1,42,'electropharmaceutics')
        self.assertEqual(key[0]['validation_scope'],'electropharmaceutics')
        self.assertEqual(key[0]['machine_eligible'],'include')
        self.assertNotIn('machine_eligible',blind[0])

if __name__=='__main__':unittest.main()
