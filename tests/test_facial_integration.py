import json

import extractor.inference as inf


class DummyClient:
    def __init__(self, host=None):
        self.host = host

    def generate(self, model, prompt):
        return {"response": "[]"}


def test_infer_stream_omits_faces_when_disabled(tmp_path, monkeypatch):
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    img_path = images_dir / "img1.png"
    img_path.write_bytes(b"fake_image_data")

    factual = tmp_path / "followthemoney.ndjson"
    out = tmp_path / "followthemoney.inferred.ndjson"

    factual.write_text(
        json.dumps(
            {
                "id": "img-1",
                "schema": "Image",
                "properties": {"fileName": ["img1.png"], "sourceUrl": [img_path.as_uri()]},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        inf,
        "load_config",
        lambda *a, **k: {"enrichment": {"ollama_host": "http://x", "description_model": "m"}},
    )
    monkeypatch.setattr(inf.ollama, "Client", DummyClient)

    from unittest.mock import patch

    with patch("extractor.enrichment_engine.EnrichmentEngine") as MockEnrich, patch(
        "extractor.facial_engine.FacialEngine"
    ) as MockFacial:
        enrich = MockEnrich.return_value
        enrich.describe_image.return_value = "Mock Description"
        enrich.embed_image.return_value = {"dino": [0.1], "clip": [0.2]}
        enrich.ollama_host = "http://x"
        enrich.description_model = "m"
        enrich.embedding_model_dino_id = "d"
        enrich.embedding_model_clip_id = "c"

        facial = MockFacial.return_value
        facial.enabled = False

        rc = inf.infer_stream(factual_ndjson=factual, out_path=out)
        assert rc == 0

        facial.detect_faces.assert_not_called()

    enrich_path = images_dir / "image_enrichment.json"
    data = json.loads(enrich_path.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert "faces" not in data[0]
