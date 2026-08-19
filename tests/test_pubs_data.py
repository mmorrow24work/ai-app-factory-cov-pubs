"""Tests for data/pubs.json and the scripts/refresh_pubs.py normaliser.

pytest, stdlib only, no network. Passes against both the committed empty
data/pubs.json and a populated one produced by a later refresh run.
"""

import importlib.util
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = REPO_ROOT / "data" / "pubs.json"
SCRIPT_PATH = REPO_ROOT / "scripts" / "refresh_pubs.py"

SLUG_RE = re.compile(r"^[a-z0-9-]+$")

COVENTRY_LAT_MIN, COVENTRY_LAT_MAX = 52.36, 52.46
COVENTRY_LON_MIN, COVENTRY_LON_MAX = -1.62, -1.41

FACILITY_STATES = {"yes", "no", "unknown"}


def _load_refresh_pubs():
    spec = importlib.util.spec_from_file_location("refresh_pubs", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


refresh_pubs = _load_refresh_pubs()


def _load_data():
    with open(DATA_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


# --- Synthetic Overpass fixture -------------------------------------------
#
# A node with full tags, a way with partial tags (cuisine-only food signal,
# no addr:housenumber/street), a relation sharing the way's name with no
# facility tags at all, a non-pub amenity that must be filtered out, and a
# pub with no name that must also be dropped.

SAMPLE_ELEMENTS = [
    {
        "type": "node",
        "id": 1001,
        "lat": 52.408,
        "lon": -1.512,
        "tags": {
            "name": "The Old Windmill",
            "amenity": "pub",
            "food": "yes",
            "outdoor_seating": "yes",
            "parking": "no",
            "addr:housenumber": "22",
            "addr:street": "Spon Street",
            "addr:city": "Coventry",
            "addr:postcode": "CV1 3BA",
            "website": "https://example.com/old-windmill",
        },
    },
    {
        "type": "way",
        "id": 2002,
        "center": {"lat": 52.39, "lon": -1.47},
        "tags": {
            "name": "Bear & Ragged Staff",
            "amenity": "pub",
            "cuisine": "british",
            "beer_garden": "yes",
            "parking": "surface",
            "addr:postcode": "CV3 6AA",
        },
    },
    {
        "type": "relation",
        "id": 3003,
        "center": {"lat": 52.41, "lon": -1.55},
        "tags": {
            "name": "Bear & Ragged Staff",
            "amenity": "pub",
        },
    },
    {
        "type": "node",
        "id": 4004,
        "lat": 52.4,
        "lon": -1.5,
        "tags": {"name": "The Bar", "amenity": "bar"},
    },
    {
        "type": "node",
        "id": 5005,
        "lat": 52.4,
        "lon": -1.5,
        "tags": {"amenity": "pub"},
    },
]


def test_pubs_json_matches_schema():
    data = _load_data()
    assert set(data.keys()) == {"attribution", "generated_from", "pubs"}
    assert data["attribution"] == "© OpenStreetMap contributors"
    assert isinstance(data["generated_from"], str) and data["generated_from"]
    assert isinstance(data["pubs"], list)

    for pub in data["pubs"]:
        assert set(pub.keys()) == {
            "id",
            "slug",
            "name",
            "lat",
            "lon",
            "address",
            "postcode",
            "website",
            "facilities",
            "osm_url",
        }
        assert re.match(r"^(node|way|relation)/[0-9]+$", pub["id"])
        assert set(pub["facilities"].keys()) == {"food", "garden", "parking"}


def test_pubs_have_names_and_are_within_coventry_bbox():
    data = _load_data()
    for pub in data["pubs"]:
        assert isinstance(pub["name"], str) and pub["name"].strip()
        assert COVENTRY_LAT_MIN <= pub["lat"] <= COVENTRY_LAT_MAX
        assert COVENTRY_LON_MIN <= pub["lon"] <= COVENTRY_LON_MAX


def test_slugs_are_unique_and_valid():
    data = _load_data()
    slugs = [pub["slug"] for pub in data["pubs"]]
    assert len(slugs) == len(set(slugs))
    for slug in slugs:
        assert SLUG_RE.match(slug)
        assert "%" not in slug
        assert "/" not in slug


def test_facility_values_are_three_state():
    data = _load_data()
    for pub in data["pubs"]:
        for value in pub["facilities"].values():
            assert value in FACILITY_STATES


def test_no_facility_tags_normalises_to_unknown_not_no():
    facilities = refresh_pubs._facilities_from_tags({"amenity": "pub"})
    assert facilities == {"food": "unknown", "garden": "unknown", "parking": "unknown"}


def test_normalise_pubs_drops_non_pubs_and_unnamed_elements():
    pubs = refresh_pubs.normalise_pubs(SAMPLE_ELEMENTS)
    assert len(pubs) == 3
    ids = {pub["id"] for pub in pubs}
    assert "node/4004" not in ids  # amenity=bar
    assert "node/5005" not in ids  # no name


def test_normalise_pubs_is_sorted_by_slug():
    pubs = refresh_pubs.normalise_pubs(SAMPLE_ELEMENTS)
    slugs = [pub["slug"] for pub in pubs]
    assert slugs == sorted(slugs)


def test_normalise_pubs_slugs_are_unique_and_valid():
    pubs = refresh_pubs.normalise_pubs(SAMPLE_ELEMENTS)
    slugs = [pub["slug"] for pub in pubs]
    assert len(slugs) == len(set(slugs))
    for slug in slugs:
        assert SLUG_RE.match(slug)
        assert "%" not in slug
        assert "/" not in slug


def test_normalise_pubs_name_collision_yields_distinct_slugs():
    pubs_by_id = {pub["id"]: pub for pub in refresh_pubs.normalise_pubs(SAMPLE_ELEMENTS)}
    way_slug = pubs_by_id["way/2002"]["slug"]
    relation_slug = pubs_by_id["relation/3003"]["slug"]
    assert way_slug != relation_slug
    assert way_slug.startswith("bear-and-ragged-staff-")
    assert relation_slug.startswith("bear-and-ragged-staff-")


def test_normalise_pubs_full_tags_and_address_assembly():
    pubs_by_id = {pub["id"]: pub for pub in refresh_pubs.normalise_pubs(SAMPLE_ELEMENTS)}
    windmill = pubs_by_id["node/1001"]
    assert windmill["slug"] == "the-old-windmill"
    assert windmill["address"] == "22 Spon Street, Coventry"
    assert windmill["postcode"] == "CV1 3BA"
    assert windmill["website"] == "https://example.com/old-windmill"
    assert windmill["osm_url"] == "https://www.openstreetmap.org/node/1001"
    assert windmill["facilities"] == {"food": "yes", "garden": "yes", "parking": "no"}


def test_normalise_pubs_partial_tags():
    pubs_by_id = {pub["id"]: pub for pub in refresh_pubs.normalise_pubs(SAMPLE_ELEMENTS)}
    bear_way = pubs_by_id["way/2002"]
    assert bear_way["address"] is None
    assert bear_way["postcode"] == "CV3 6AA"
    assert bear_way["website"] is None
    assert bear_way["facilities"] == {"food": "yes", "garden": "yes", "parking": "yes"}

    bear_relation = pubs_by_id["relation/3003"]
    assert bear_relation["address"] is None
    assert bear_relation["postcode"] is None
    assert bear_relation["facilities"] == {
        "food": "unknown",
        "garden": "unknown",
        "parking": "unknown",
    }
