from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

import ollama
from followthemoney import model

from .utils import load_config

logger = logging.getLogger(__name__)


SCHEMA_WHITELIST: Tuple[str, ...] = (
    "Address",
    "Airplane",
    "BankAccount",
    "Call",
    "Company",
    "CourtCase",
    "Email",
    "Event",
    "Payment",
    "Person",
    "Trip",
    "Vehicle",
    "Vessel",
)


@dataclass(frozen=True)
class Evidence:
    proof_id: str
    kind: str  # "Document" or "Image"
    text: str


def _first_prop(entity: Dict[str, Any], prop: str) -> Optional[str]:
    try:
        values = (entity.get("properties") or {}).get(prop) or []
        if isinstance(values, list) and values:
            return str(values[0])
        if isinstance(values, str):
            return values
    except Exception:
        return None
    return None


def iter_factual_evidence(
    factual_ndjson: Path,
    max_chars: int = 8000,
    image_description: Optional[Callable[[Dict[str, Any]], Optional[str]]] = None,
) -> Iterator[Evidence]:
    factual_ndjson = Path(factual_ndjson)
    with factual_ndjson.open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                ent = json.loads(line)
            except Exception:
                continue

            schema = ent.get("schema")
            ent_id = ent.get("id")
            if not schema or not ent_id:
                continue

            if schema == "Image":
                desc = _first_prop(ent, "description")
                if not desc and image_description is not None:
                    try:
                        desc = image_description(ent)
                    except Exception:
                        desc = None
                if not desc:
                    continue
                yield Evidence(proof_id=str(ent_id), kind="Image", text=desc[:max_chars])

            elif schema == "Document":
                body = _first_prop(ent, "bodyText")
                if not body:
                    continue
                yield Evidence(proof_id=str(ent_id), kind="Document", text=body[:max_chars])


def _extract_json_array(text: str) -> Optional[str]:
    text = text.strip()
    if text.startswith("[") and text.endswith("]"):
        return text

    m = re.search(r"\[.*\]", text, flags=re.DOTALL)
    if m:
        return m.group(0)
    return None


def _stable_mention_id(proof_id: str, schema: str, key: str) -> str:
    h = hashlib.sha1(f"{proof_id}|{schema}|{key}".encode("utf-8", errors="ignore")).hexdigest()
    return f"ment-{h}"


def _normalize_person(props: Dict[str, Any]) -> None:
    name = props.get("name")
    if isinstance(name, list) and name:
        name = name[0]
    if not isinstance(name, str) or not name.strip():
        return

    name = name.strip()
    props.setdefault("name", name)

    if props.get("firstName") or props.get("lastName"):
        return

    parts = name.split()
    if len(parts) == 1:
        props.setdefault("lastName", parts[0])
        return

    props.setdefault("firstName", " ".join(parts[:-1]))
    props.setdefault("lastName", parts[-1])


def _normalize_address(props: Dict[str, Any]) -> None:
    full = props.get("full")
    name = props.get("name")

    if isinstance(full, list) and full:
        full = full[0]
    if isinstance(name, list) and name:
        name = name[0]

    if not full and isinstance(name, str) and name.strip():
        props["full"] = name.strip()
    if not name and isinstance(full, str) and full.strip():
        props["name"] = full.strip()


def _add_props_safe(entity, props: Dict[str, Any]) -> None:
    schema = entity.schema
    for prop, value in props.items():
        if schema.get(prop) is None:
            continue
        if value is None:
            continue

        values: Sequence[Any]
        if isinstance(value, list):
            values = value
        else:
            values = [value]

        for v in values:
            if v is None:
                continue
            entity.add(prop, v)


def _add_one_safe(entity, prop: str, value: Any) -> None:
    if value is None:
        return
    if entity.schema.get(prop) is None:
        return
    entity.add(prop, value)


def _add_inference_meta(entity, meta: Dict[str, Any]) -> None:
    text = json.dumps(meta, ensure_ascii=False)
    if entity.schema.get("notes") is not None:
        entity.add("notes", text)
        return
    if entity.schema.get("description") is not None:
        entity.add("description", text)
        return
    if entity.schema.get("summary") is not None:
        entity.add("summary", text)


def _infer_raw(
    client: ollama.Client,
    model_name: str,
    evidence: Evidence,
    verbose: bool = False,
) -> List[Dict[str, Any]]:
    prompt = (
        "You are an information extraction system.\n"
        "Extract FollowTheMoney entities from the input text.\n\n"
        f"Allowed schemata: {', '.join(SCHEMA_WHITELIST)}\n"
        "Return ONLY a JSON array. Each item must be an object with keys:\n"
        "- schema: one of the allowed schemata\n"
        "- properties: an object of FtM properties for that schema\n"
        "- confidence: number 0..1\n"
        "- evidence: short quote from the input (string)\n\n"
        "Guidance:\n"
        "- Person: include name; if possible also firstName/lastName.\n"
        "- Address: prefer full.\n"
        "- Event: use name, startDate (ISO), location (string), involved (list of names).\n\n"
        f"Input kind: {evidence.kind}\n"
        "Input text:\n"
        f"{evidence.text}\n"
    )

    if verbose:
        logger.debug(
            "ollama.generate start kind=%s proof=%s chars=%d",
            evidence.kind,
            evidence.proof_id,
            len(evidence.text or ""),
        )

    try:
        resp = client.generate(model=model_name, prompt=prompt)
    except Exception as exc:
        if verbose:
            logger.exception(
                "ollama.generate failed kind=%s proof=%s: %s",
                evidence.kind,
                evidence.proof_id,
                exc,
            )
        else:
            logger.error(
                "ollama.generate failed kind=%s proof=%s: %s",
                evidence.kind,
                evidence.proof_id,
                exc,
            )
        return []
    raw = (resp or {}).get("response", "")

    if verbose:
        max_log = 20000
        snippet = raw if len(raw) <= max_log else (raw[:max_log] + "\n... [truncated]")
        logger.debug(
            "ollama.generate response kind=%s proof=%s chars=%d\n%s",
            evidence.kind,
            evidence.proof_id,
            len(raw),
            snippet,
        )

    json_text = _extract_json_array(raw)
    if not json_text:
        return []

    try:
        data = json.loads(json_text)
    except Exception:
        return []

    return data if isinstance(data, list) else []


def infer_stream(
    factual_ndjson: Path,
    out_path: Path,
    ollama_host: Optional[str] = None,
    model_name: Optional[str] = None,
    max_chars: int = 8000,
    verbose: bool = False,
    image_enrichment: bool = True,
) -> int:
    cfg = load_config()
    enrichment = cfg.get("enrichment", {})

    if ollama_host is None:
        ollama_host = enrichment.get("ollama_host", "http://localhost:11434")
    if model_name is None:
        model_name = enrichment.get("description_model", "llava")

    if verbose:
        logger.info("factual=%s", Path(factual_ndjson))
        logger.info("out=%s", Path(out_path))
        logger.info("ollama_host=%s model=%s", ollama_host, model_name)

    client = ollama.Client(host=ollama_host)

    image_description_cb: Optional[Callable[[Dict[str, Any]], Optional[str]]] = None
    if image_enrichment:
        from datetime import datetime
        from urllib.parse import urlparse, unquote

        from .enrichment_engine import EnrichmentEngine
        from .facial_engine import FacialEngine

        enrichment_engine = EnrichmentEngine(cfg)
        facial_engine = FacialEngine(cfg)

        cache: Dict[Path, Dict[str, Any]] = {}

        def _path_from_source_url(url: str) -> Optional[Path]:
            try:
                if not url.startswith("file:"):
                    return None
                parsed = urlparse(url)
                return Path(unquote(parsed.path))
            except Exception:
                return None

        def _load_enrichment(images_dir: Path) -> List[Dict[str, Any]]:
            enrich_path = images_dir / "image_enrichment.json"
            if images_dir in cache:
                return cache[images_dir]["data"]
            data: List[Dict[str, Any]] = []
            if enrich_path.exists():
                try:
                    data = json.loads(enrich_path.read_text(encoding="utf-8"))
                except Exception:
                    data = []
            cache[images_dir] = {"data": data, "path": enrich_path}
            return data

        def _save_enrichment(images_dir: Path) -> None:
            entry = cache.get(images_dir)
            if not entry:
                return
            enrich_path = entry["path"]
            enrich_path.write_text(json.dumps(entry["data"], ensure_ascii=False, indent=2), encoding="utf-8")

        def image_description(ent: Dict[str, Any]) -> Optional[str]:
            img_id = str(ent.get("id") or "")
            src_url = _first_prop(ent, "sourceUrl")
            file_name = _first_prop(ent, "fileName")

            img_path = None
            if isinstance(src_url, str):
                img_path = _path_from_source_url(src_url)
            if img_path is None and isinstance(file_name, str) and file_name:
                # best-effort fallback: can't resolve without sourceUrl
                return None
            if img_path is None:
                return None

            images_dir = img_path.parent
            data = _load_enrichment(images_dir)

            for item in data:
                if not isinstance(item, dict):
                    continue
                if img_id and item.get("id") == img_id and item.get("description"):
                    return str(item.get("description"))
                if file_name and item.get("filename") == file_name and item.get("description"):
                    return str(item.get("description"))

            if verbose:
                logger.info("enriching image=%s", img_path)

            desc = enrichment_engine.describe_image(img_path)
            embeddings = enrichment_engine.embed_image(img_path)
            faces = facial_engine.detect_faces(img_path) if facial_engine.enabled else []

            rec: Dict[str, Any] = {
                "id": img_id or None,
                "filename": file_name or img_path.name,
                "path": str(img_path),
                "sourceUrl": src_url,
                "generatedAt": datetime.now().isoformat(),
                "ollamaHost": enrichment_engine.ollama_host,
                "descriptionModel": enrichment_engine.description_model,
                "embeddingModelDino": enrichment_engine.embedding_model_dino_id,
                "embeddingModelClip": enrichment_engine.embedding_model_clip_id,
                "description": desc,
                "embeddings": embeddings,
            }
            if faces:
                rec["faces"] = faces

            data.append(rec)
            _save_enrichment(images_dir)
            return desc

        image_description_cb = image_description

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    factual_ndjson = Path(factual_ndjson)
    if not factual_ndjson.exists():
        logger.error("missing factual NDJSON: %s", factual_ndjson)
        return 2

    evidence_count = 0
    entity_count = 0

    # Create output file immediately and stream-write results as they are generated.
    with out_path.open("w", encoding="utf-8", buffering=1) as out:
        for evidence in iter_factual_evidence(
            factual_ndjson, max_chars=max_chars, image_description=image_description_cb
        ):
            evidence_count += 1

            raw_items = _infer_raw(client, model_name, evidence, verbose=verbose)
            if verbose and evidence_count <= 3:
                logger.info("received %d inferred items for proof=%s", len(raw_items), evidence.proof_id)

            local: Dict[str, Any] = {}

            # per-proof local caches to allow Event linking by name
            persons: Dict[str, str] = {}
            addresses: Dict[str, str] = {}

            def ensure_person(name: str) -> str:
                key = name.strip()
                ent_id = persons.get(key)
                if ent_id:
                    return ent_id

                props: Dict[str, Any] = {"name": key}
                _normalize_person(props)
                ent_id = _stable_mention_id(evidence.proof_id, "Person", props.get("name") or key)

                if ent_id not in local:
                    ent = model.make_entity("Person")
                    ent.id = ent_id
                    _add_props_safe(ent, props)
                    _add_one_safe(ent, "proof", evidence.proof_id)
                    _add_inference_meta(
                        ent,
                        {
                            "stream": "inferred",
                            "source": "ollama",
                            "confidence": None,
                            "evidence": None,
                            "proof": evidence.proof_id,
                        },
                    )
                    local[ent_id] = ent

                persons[key] = ent_id
                return ent_id

            def ensure_address(full: str) -> str:
                key = full.strip()
                ent_id = addresses.get(key)
                if ent_id:
                    return ent_id

                props: Dict[str, Any] = {"full": key, "name": key}
                _normalize_address(props)
                ent_id = _stable_mention_id(evidence.proof_id, "Address", props.get("full") or key)

                if ent_id not in local:
                    ent = model.make_entity("Address")
                    ent.id = ent_id
                    _add_props_safe(ent, props)
                    _add_one_safe(ent, "proof", evidence.proof_id)
                    _add_inference_meta(
                        ent,
                        {
                            "stream": "inferred",
                            "source": "ollama",
                            "confidence": None,
                            "evidence": None,
                            "proof": evidence.proof_id,
                        },
                    )
                    local[ent_id] = ent

                addresses[key] = ent_id
                return ent_id

            for item in raw_items:
                if not isinstance(item, dict):
                    continue
                schema = item.get("schema")
                if schema not in SCHEMA_WHITELIST:
                    continue

                props = item.get("properties") or {}
                if not isinstance(props, dict):
                    continue

                confidence = item.get("confidence")
                evidence_quote = item.get("evidence")

                if schema == "Person":
                    _normalize_person(props)
                    key = str(props.get("name") or "").strip()
                    if not key:
                        continue
                    ent_id = _stable_mention_id(evidence.proof_id, schema, key)
                    ent = model.make_entity(schema)
                    ent.id = ent_id
                    _add_props_safe(ent, props)
                    _add_one_safe(ent, "proof", evidence.proof_id)

                elif schema == "Address":
                    _normalize_address(props)
                    key = str(props.get("full") or props.get("name") or "").strip()
                    if not key:
                        continue
                    ent_id = _stable_mention_id(evidence.proof_id, schema, key)
                    ent = model.make_entity(schema)
                    ent.id = ent_id
                    _add_props_safe(ent, props)
                    _add_one_safe(ent, "proof", evidence.proof_id)

                elif schema == "Event":
                    key = str(props.get("name") or "").strip() or f"event@{evidence.proof_id}"
                    ent_id = _stable_mention_id(evidence.proof_id, schema, key)
                    ent = model.make_entity(schema)
                    ent.id = ent_id

                    # Link out involved/location if they are strings
                    involved = props.get("involved")
                    if isinstance(involved, list):
                        inv_ids = [ensure_person(str(v)) for v in involved if isinstance(v, str) and v.strip()]
                        props["involved"] = inv_ids

                    loc = props.get("location")
                    if isinstance(loc, str) and loc.strip():
                        addr_id = ensure_address(loc)
                        props["addressEntity"] = [addr_id]

                    _add_props_safe(ent, props)
                    _add_one_safe(ent, "proof", evidence.proof_id)

                else:
                    key = str(props.get("name") or props.get("id") or props.get("full") or "").strip()
                    if not key:
                        key = f"{schema}@{evidence.proof_id}"
                    ent_id = _stable_mention_id(evidence.proof_id, schema, key)
                    ent = model.make_entity(schema)
                    ent.id = ent_id
                    _add_props_safe(ent, props)
                    _add_one_safe(ent, "proof", evidence.proof_id)

                _add_inference_meta(
                    ent,
                    {
                        "stream": "inferred",
                        "source": "ollama",
                        "confidence": confidence,
                        "evidence": evidence_quote,
                        "proof": evidence.proof_id,
                        "kind": evidence.kind,
                    },
                )

                local[ent_id] = ent

            # Write this evidence batch immediately.
            for ent in sorted(local.values(), key=lambda e: (e.schema.name, e.id)):
                out.write(json.dumps(ent.to_dict(), ensure_ascii=False) + "\n")
                entity_count += 1

            out.flush()

            if verbose and evidence_count % 25 == 0:
                logger.info("processed evidence=%d wrote_entities=%d", evidence_count, entity_count)

    if verbose:
        logger.info("wrote %s (entities=%d evidence=%d)", out_path, entity_count, evidence_count)

    return 0
