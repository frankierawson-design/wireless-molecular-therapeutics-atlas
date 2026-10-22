"""Explicit validation scopes; historic pilots must not validate a new field."""
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'methods'))
from collect_literature import DOI_SENTINELS
from electrical_treatment_coverage_audit import SENTINELS

SCOPES = {
    'legacy_wireless': ('Electrochemical', 'Ultrasound', 'Magnetic', 'Optical', 'Radiofrequency', 'Hybrid'),
    'electrical_therapies': ('TTFields', 'Electrochemotherapy', 'Electroporation', 'Neuromodulation', 'Electrical Stimulation', 'Electrochemical'),
    'electropharmaceutics': ('Electro-Mediated Pharmaceutics',),
}

def normalize_doi(value):
    value = str(value or '').strip().casefold()
    for prefix in ('https://doi.org/', 'http://doi.org/', 'https://dx.doi.org/', 'http://dx.doi.org/'):
        if value.startswith(prefix):
            return value[len(prefix):]
    return value

# Exclude every calibration DOI across scopes, not only one historic list.
KNOWN_SENTINELS = {normalize_doi(x if isinstance(x, str) else x['doi']) for x in DOI_SENTINELS}
KNOWN_SENTINELS.update(normalize_doi(x['doi']) for x in SENTINELS)
KNOWN_SENTINELS.add('10.1039/d3bm01946b')
