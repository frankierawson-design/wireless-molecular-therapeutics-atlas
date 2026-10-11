"""Source-anchored DOI reconciliation tests. Synthetic fixtures do not certify the harvest."""
import importlib.util
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/"methods"/path)
    value=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value
collector=module("doi_collector","collect_literature.py")
rank=module("doi_ranker","build_provisional_rankings.py")
ORCID="0000-0001-5079-3123"
PAPERS=[
 ("10.1016/j.apmt.2020.100804",2020,"Bipolar electroactive conducting polymers for wireless cell stimulation"),
 ("10.1016/j.apmt.2022.101481",2022,"Enhanced wireless cell stimulation using soft and improved bipolar electroactive conducting polymer templates"),
 ("10.1016/j.elecom.2023.107626",2023,"On demand, wireless electrochemical release of brain derived neurotrophic factor"),
 ("10.1021/acs.langmuir.6c00755",2026,"Spatially Controlled, Wirefree, Drug Release along a Single PEDOT Film"),
]

def paper(doi,year,title,aid):
    return {"doi":doi,"year":year,"title":title,"abstract":"",
            "openalex_id":"https://openalex.org/W"+str(year),"citations_openalex":5,
            "openalex_work_type":"article","source_databases":["OpenAlex"],
            "source_queries":["exact-doi:"+doi],
            "publication_types":["Journal Article"],
            "authors":[{"name":"Robert J. Forster","orcid":"","openalex_author_id":aid,
                        "position":"middle","institutions":[{"name":"Dublin City University","id":"https://openalex.org/I1234"}]}]}

class DOICorroborationTests(unittest.TestCase):
    def test_four_original_dois_exist_in_reconciliation_registry(self):
        for doi,_,_ in PAPERS:
            self.assertIn(doi,collector.DOI_SENTINELS)
            self.assertEqual(collector.DOCUMENTED_DOI_ORCID.get(doi),ORCID)

    def test_all_four_originals_pass_same_machine_screen_as_others(self):
        records=[]
        for n,(doi,year,title) in enumerate(PAPERS):
            record=paper(doi,year,title,"https://openalex.org/A"+str(500+n))
            self.assertTrue(collector.reconcile_documented_authorship(record))
            records.append(record)
        included,excluded=rank.classify(records)
        self.assertEqual(len(included),4,excluded)
        self.assertTrue(all("Electrochemical" in w["modalities"] for w in included))
        ranks,_,_=rank.make_ranks(included,records)
        self.assertEqual(len(ranks["Electrochemical"]),1)
        self.assertEqual(len(ranks["Overall"]),1)
        for group in ("Overall","Electrochemical"):
            row=ranks[group][0]
            self.assertEqual(row["publication_count"],4)
            self.assertEqual(row["institution"],"Dublin City University")
            self.assertEqual(row["orcid"],ORCID)

    def test_no_identity_inference_without_verified_byline(self):
        record=paper(PAPERS[0][0],2020,PAPERS[0][2],"https://openalex.org/A500")
        record["authors"][0]["name"]="An unrelated researcher"
        self.assertFalse(collector.reconcile_documented_authorship(record))
        self.assertNotIn("verified_orcid_from_publication",record["authors"][0])
        self.assertEqual(rank.author_key(record["authors"][0],{}),"https://openalex.org/A500")
        record["authors"][0]["name"]="Robert J. Forster"
        record["authors"][0]["orcid"]="https://orcid.org/0000-0001-0000-0001"
        self.assertFalse(collector.reconcile_documented_authorship(record))
        self.assertTrue(record["documented_identity_conflict"])

    def test_review_excluded_by_same_rules(self):
        record=paper("10.1016/j.elecom.2024.107832",2024,
                     "Wirefree Electrochemistry for Enhanced Detection and Treatment of Disease",
                     "https://openalex.org/A500")
        collector.reconcile_documented_authorship(record)
        included,excluded=rank.classify([record])
        self.assertEqual(included,[])
        self.assertGreater(excluded["possible_review_or_nonoriginal"],0)

if __name__=="__main__":
    unittest.main()
