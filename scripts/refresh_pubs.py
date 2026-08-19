#!/usr/bin/env python3
"""Fetch Coventry's amenity=pub nodes/ways/relations from Overpass and normalise them
into data/pubs.json.

Stdlib only, no third-party dependencies, so this runs on a bare runner.

Two modes:
    --out data/pubs.json           Fetch from the Overpass API and write the result.
    --from-json FILE               Normalise an already-saved Overpass JSON response,
                                    with no network access. This is what the test
                                    suite uses.
"""

import argparse
import hashlib
import json
import re
import urllib.parse
import urllib.request
from collections import Counter

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# amenity=pub only: bars, biergartens, clubs and restaurants are out of scope
# per the design doc's non-goals. Coventry means the city's administrative
# boundary (area filter below), not a bounding box.
OVERPASS_QUERY = """
[out:json][timeout:60];
area["name"="Coventry"]["boundary"="administrative"]["admin_level"="8"]->.covArea;
(
  node["amenity"="pub"](area.covArea);
  way["amenity"="pub"](area.covArea);
  relation["amenity"="pub"](area.covArea);
);
out center tags;
""".strip()

ATTRIBUTION = "© OpenStreetMap contributors"

_NONALNUM_RE = re.compile(r"[^a-z0-9]+")
_APOSTROPHE_RE = re.compile(r"[’']")


def _slugify(name):
    """Lowercase a pub name into a slug matching ^[a-z0-9-]+$.

    Apostrophes are dropped, ampersands become "and", and every other
    run of non-alphanumeric characters collapses to a single hyphen.
    Never percent-encodes anything into a slug.
    """
    text = name.lower()
    text = text.replace("&", " and ")
    text = _APOSTROPHE_RE.sub("", text)
    text = _NONALNUM_RE.sub("-", text)
    return text.strip("-")


def _short_id(osm_id):
    """A short, stable suffix derived from the OSM id, for slug collisions."""
    return hashlib.sha1(osm_id.encode("utf-8")).hexdigest()[:6]


def _osm_id(element):
    return "{}/{}".format(element["type"], element["id"])


def _coordinates(element):
    if element.get("type") == "node":
        return element.get("lat"), element.get("lon")
    center = element.get("center") or {}
    return center.get("lat"), center.get("lon")


def _assemble_address(tags):
    house = tags.get("addr:housenumber")
    street = tags.get("addr:street")
    city = tags.get("addr:city")
    line1 = " ".join(part for part in (house, street) if part)
    parts = [part for part in (line1, city) if part]
    return ", ".join(parts) if parts else None


def _facilities_from_tags(tags):
    """Map OSM tags to the three-state facilities dict.

    A missing tag is "unknown", never "no" - OSM tagging is volunteer-supplied
    and sparse, so an untagged pub must not be rendered as lacking a facility.

    food:    "yes" if tags["food"] == "yes" or a "cuisine" tag is present;
             "no" if tags["food"] == "no"; otherwise "unknown".
    garden:  the first of "outdoor_seating", "beer_garden", "garden" that is
             tagged "yes" or "no"; otherwise "unknown".
    parking: "no" if tags["parking"] == "no"; "yes" if the "parking" tag is
             present with any other value; otherwise "unknown".
    """
    food = tags.get("food")
    if food == "yes" or "cuisine" in tags:
        food_state = "yes"
    elif food == "no":
        food_state = "no"
    else:
        food_state = "unknown"

    garden_state = "unknown"
    for key in ("outdoor_seating", "beer_garden", "garden"):
        value = tags.get(key)
        if value == "yes":
            garden_state = "yes"
            break
        if value == "no":
            garden_state = "no"
            break

    parking = tags.get("parking")
    if parking is None:
        parking_state = "unknown"
    elif parking == "no":
        parking_state = "no"
    else:
        parking_state = "yes"

    return {"food": food_state, "garden": garden_state, "parking": parking_state}


def normalise_pubs(elements):
    """Normalise raw Overpass elements into the pubs.json record shape,
    sorted by slug.
    """
    named = []
    for element in elements:
        tags = element.get("tags") or {}
        if tags.get("amenity") != "pub":
            continue
        name = (tags.get("name") or "").strip()
        if not name:
            continue
        lat, lon = _coordinates(element)
        if lat is None or lon is None:
            continue
        named.append((_osm_id(element), name, tags, lat, lon))

    base_slugs = [_slugify(name) for _, name, _, _, _ in named]
    slug_counts = Counter(base_slugs)

    pubs = []
    for (osm_id, name, tags, lat, lon), base_slug in zip(named, base_slugs):
        if slug_counts[base_slug] > 1:
            slug = "{}-{}".format(base_slug, _short_id(osm_id))
        else:
            slug = base_slug
        pubs.append(
            {
                "id": osm_id,
                "slug": slug,
                "name": name,
                "lat": lat,
                "lon": lon,
                "address": _assemble_address(tags),
                "postcode": tags.get("addr:postcode") or None,
                "website": tags.get("website") or tags.get("contact:website") or None,
                "facilities": _facilities_from_tags(tags),
                "osm_url": "https://www.openstreetmap.org/{}".format(osm_id),
            }
        )

    pubs.sort(key=lambda pub: pub["slug"])
    return pubs


def build_dataset(elements, generated_from):
    return {
        "attribution": ATTRIBUTION,
        "generated_from": generated_from,
        "pubs": normalise_pubs(elements),
    }


def fetch_overpass(query):
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    request = urllib.request.Request(
        OVERPASS_URL,
        data=data,
        headers={"User-Agent": "ai-app-factory-cov-pubs/refresh_pubs.py"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.load(response)


def write_dataset(dataset, out_path):
    text = json.dumps(dataset, indent=2, ensure_ascii=False) + "\n"
    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write(text)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out", default="data/pubs.json", help="Path to write the normalised dataset to."
    )
    parser.add_argument(
        "--from-json",
        metavar="FILE",
        help="Normalise a saved Overpass JSON response instead of fetching one.",
    )
    args = parser.parse_args(argv)

    if args.from_json:
        with open(args.from_json, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
        generated_from = args.from_json
    else:
        raw = fetch_overpass(OVERPASS_QUERY)
        generated_from = OVERPASS_URL

    dataset = build_dataset(raw.get("elements", []), generated_from)
    write_dataset(dataset, args.out)


if __name__ == "__main__":
    main()
