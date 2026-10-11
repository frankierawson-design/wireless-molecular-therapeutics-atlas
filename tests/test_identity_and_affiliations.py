"""Offline regression tests for responsible researcher identity and institution matching."""
import importlib.util
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/"methods"/path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
collector=load("collector","collect_literature.py")
rank=load("ranking","build_provisional_rankings.py")

ORCID="0000-0002-4872-8928"
RAWSON="https://openalex.org/A5030287864"
def paper(title, doi, year, citations, authors):
    return {"title":title,"doi":doi,"year":year,"citations_openalex":citations,
            "openalex_id":"https://openalex.org/W"+str(abs(hash(doi))%100000000),
            "authors":authors,"source_databases":["OpenAlex"],"source_queries":["fixture"]}
def rawson(year,with_id=True,with_orcid=True,institution="University of Nottingham"):
    return {"name":"Frankie James Rawson" if with_id else "Rawson FJ",
            "orcid":"https://orcid.org/"+ORCID if with_orcid else "",
            "openalex_author_id":RAWSON if with_id else "",
            "position":"last",
            "institutions":[{"name":institution,"id":"https://openalex.org/I100000000"}] if institution else []}

class IdentityTests(unittest.TestCase):
    def test_europe_pmc_first_keeps_richer_openalex_authors(self):
        doi="10.1038/s41565-023-01496-y"
        ep={"title":"Wireless electrical-molecular quantum signalling for cancer cell apoptosis.",
            "doi":doi,"year":"2024","openalex_id":"","citations_openalex":None,
            "source_databases":["Europe PMC"],"source_queries":["electrochemical"],
            "authors":[{"name":"Rawson FJ","orcid":ORCID}]}
        oa=paper(ep["title"],doi,2024,53,[rawson(2024)])
        out={}
        collector.merge(out,ep)
        collector.merge(out,oa)
        record=list(out.values())[0]
        self.assertEqual(record["authors"][0]["openalex_author_id"],RAWSON)
        self.assertEqual(record["authors"][0]["institutions"][0]["name"],"University of Nottingham")
        self.assertEqual(record["citations_openalex"],53)

    def test_orcid_only_bylines_resolve_to_unique_openalex_author(self):
        linked=paper("Wireless Bioelectronic Modulation of Membrane Potential in Glioblastoma",
                     "10.1002/advs.202516561",2026,0,[rawson(2026)])
        early=paper("Wireless electrical-molecular quantum signalling for cancer cell apoptosis.",
                     "10.1038/s41565-023-01496-y",2024,53,[rawson(2024,False)])
        link,conflicts=rank.identity_map([linked,early])
        self.assertEqual(conflicts,0)
        self.assertEqual(rank.author_key(early["authors"][0],link),RAWSON)

    def test_same_name_different_identifiers_never_merge(self):
        x={"name":"A. Researcher","orcid":"0000-0001-0000-0001"}
        y={"name":"A. Researcher","orcid":"0000-0002-0000-0002"}
        links,_=rank.identity_map([])
        self.assertNotEqual(rank.author_key(x,links),rank.author_key(y,links))

    def test_institution_latest_documented_year_not_current_claim(self):
        old=paper("Wireless bipolar electrochemistry cancer cell therapy",
                  "10.1000/test-one",2022,15,[rawson(2022,institution="Old University")])
        new=paper("Wireless Bioelectronic Modulation of Membrane Potential in Glioblastoma",
                  "10.1000/test-two",2026,3,[rawson(2026)])
        inst=rank.institution_lookup([old,new],{})
        self.assertEqual(inst[RAWSON][0]["name"],"University of Nottingham")
        self.assertEqual(inst[RAWSON][0]["last_year"],2026)

    def test_journal_work_included_and_preprint_excluded(self):
        journal=paper("Wireless Bioelectronic Modulation of Membrane Potential in Glioblastoma",
                      "10.1002/advs.202516561",2026,3,[rawson(2026)])
        preprint=paper(journal["title"],"10.1101/2025.07.04.663176",2025,0,[rawson(2025)])
        eligible,excluded=rank.classify([journal,preprint])
        self.assertEqual(len(eligible),1)
        self.assertEqual(excluded["preprint_not_in_primary_ranking"],1)

    def test_cancer_wireless_electrochemical_originals_are_rankable(self):
        records=[
          paper("Wireless electrical-molecular quantum signalling for cancer cell apoptosis.",
                "10.1038/s41565-023-01496-y",2024,53,[rawson(2024)]),
          paper("Bipolar electrochemical growth of conductive microwires for cancer spheroid integration",
                "10.1038/s41598-024-71236-2",2024,3,[rawson(2024)]),
          paper("Wireless Bioelectronic Modulation of Membrane Potential in Glioblastoma Using Carbon Nanotube Porins",
                "10.1002/advs.202516561",2026,0,[rawson(2026)]),
        ]
        eligible,exclusion=rank.classify(records)
        self.assertEqual(len(eligible),3,exclusion)
        ranks,authors,conflicts=rank.make_ranks(eligible,records)
        self.assertEqual(authors,1)
        self.assertEqual(len(ranks["Overall"]),1)
        self.assertEqual(ranks["Overall"][0]["publication_count"],3)
        self.assertEqual(ranks["Overall"][0]["institution"],"University of Nottingham")
        self.assertEqual(ranks["Overall"][0]["rank"],None)

if __name__=="__main__":
    unittest.main()
