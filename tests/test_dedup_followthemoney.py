import json
from pathlib import Path

from extractor.dedup import dedup_stream


def _ndjson(path: Path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def test_dedup_merges_people_and_rewrites_event(tmp_path):
    in_path = tmp_path / "inferred.ndjson"
    out_path = tmp_path / "dedup.ndjson"

    img1 = "img-1"
    img2 = "img-2"

    p1 = {
        "id": "ment-p1",
        "schema": "Person",
        "properties": {"name": ["Hickens"], "proof": [img1]},
    }
    p2 = {
        "id": "ment-p2",
        "schema": "Person",
        "properties": {"name": ["Hickens"], "proof": [img2]},
    }
    c1 = {
        "id": "ment-c1",
        "schema": "Company",
        "properties": {"name": ["FedEx"], "proof": [img1]},
    }
    c2 = {
        "id": "ment-c2",
        "schema": "Company",
        "properties": {"name": ["FedEx"], "proof": [img2]},
    }
    ev = {
        "id": "ment-e1",
        "schema": "Event",
        "properties": {"name": ["Test"], "involved": ["ment-p1"], "proof": [img1]},
    }

    in_path.write_text(
        "\n".join(json.dumps(x) for x in [p1, p2, c1, c2, ev]) + "\n",
        encoding="utf-8",
    )

    rc = dedup_stream(in_path=in_path, out_path=out_path)
    assert rc == 0

    ents = _ndjson(out_path)

    # Mention-level Person/Company should be collapsed into one each
    assert all(e["id"] not in {"ment-p1", "ment-p2", "ment-c1", "ment-c2"} for e in ents)

    people = [e for e in ents if e["schema"] == "Person"]
    companies = [e for e in ents if e["schema"] == "Company"]
    assert len(people) == 1
    assert len(companies) == 1

    person_id = people[0]["id"]
    proofs = set(people[0]["properties"].get("proof") or [])
    assert {img1, img2}.issubset(proofs)

    # Event should remain, but reference rewritten to canonical person id
    event = next(e for e in ents if e["schema"] == "Event")
    assert person_id in (event["properties"].get("involved") or [])
