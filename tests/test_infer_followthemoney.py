import json
from pathlib import Path

import extractor.inference as inf


class DummyClient:
    def __init__(self, host=None):
        self.host = host

    def generate(self, model, prompt):
        # Minimal contract: JSON array only
        return {
            "response": json.dumps(
                [
                    {
                        "schema": "Person",
                        "properties": {"name": "Hickens"},
                        "confidence": 0.55,
                        "evidence": "Hickens",
                    },
                    {
                        "schema": "Address",
                        "properties": {"name": "Little St. James Island"},
                        "confidence": 0.8,
                        "evidence": "Little St. James Island",
                    },
                    {
                        "schema": "Event",
                        "properties": {
                            "name": "Log Entry 31E-NY-302351",
                            "startDate": "2019-09-11",
                            "location": "Little St. James Island",
                            "involved": ["Hickens"],
                        },
                        "confidence": 0.6,
                        "evidence": "9/11/2019",
                    },
                    {
                        "schema": "Payment",
                        "properties": {},
                        "confidence": 0.2,
                        "evidence": "",
                    },
                ]
            )
        }


def test_infer_stream_from_image_description(tmp_path, monkeypatch):
    factual = tmp_path / "followthemoney.ndjson"
    out = tmp_path / "followthemoney.inferred.ndjson"

    img_id = "img-abc"

    factual.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "id": img_id,
                        "schema": "Image",
                        "properties": {"description": ["Persons: Hickens\nLocations: Little St. James Island\nDates: 9/11/2019"]},
                    }
                )
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(inf, "load_config", lambda *a, **k: {"enrichment": {"ollama_host": "http://x", "description_model": "m"}})
    monkeypatch.setattr(inf.ollama, "Client", DummyClient)

    rc = inf.infer_stream(factual_ndjson=factual, out_path=out)
    assert rc == 0

    lines = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines() if l.strip()]
    schemata = {e["schema"] for e in lines}
    assert {"Person", "Address", "Event"}.issubset(schemata)

    # All inferred entities should proof-link back to the image ID
    for ent in lines:
        props = ent.get("properties", {})
        assert img_id in (props.get("proof") or [])

    # Event should link to person + address entities by ID
    people = {e["id"] for e in lines if e["schema"] == "Person"}
    addrs = {e["id"] for e in lines if e["schema"] == "Address"}
    event = next(e for e in lines if e["schema"] == "Event")

    assert any(pid in (event["properties"].get("involved") or []) for pid in people)
    assert any(aid in (event["properties"].get("addressEntity") or []) for aid in addrs)
