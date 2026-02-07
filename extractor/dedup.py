from __future__ import annotations

import hashlib
import json
import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from followthemoney import model

logger = logging.getLogger(__name__)


DEDUP_SCHEMATA: Tuple[str, ...] = (
    "Person",
    "Company",
    "Address",
    "Email",
    "BankAccount",
    "Vehicle",
    "Vessel",
    "Airplane",
)


def _norm_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, list):
        value = value[0] if value else None
    if not isinstance(value, str):
        value = str(value)
    value = " ".join(value.strip().split())
    if not value:
        return None
    return value.casefold()


def _first_prop(props: Dict[str, Any], prop: str) -> Optional[Any]:
    value = props.get(prop)
    if isinstance(value, list):
        return value[0] if value else None
    return value


def _canon_key(schema: str, props: Dict[str, Any]) -> Optional[str]:
    if schema in ("Person", "Company"):
        return _norm_text(_first_prop(props, "name"))

    if schema == "Address":
        return _norm_text(_first_prop(props, "full") or _first_prop(props, "name"))

    if schema == "Email":
        return _norm_text(_first_prop(props, "email") or _first_prop(props, "name"))

    if schema == "BankAccount":
        return _norm_text(
            _first_prop(props, "iban")
            or _first_prop(props, "accountNumber")
            or _first_prop(props, "name")
        )

    if schema == "Vehicle":
        return _norm_text(_first_prop(props, "registrationNumber") or _first_prop(props, "vin") or _first_prop(props, "name"))

    if schema == "Vessel":
        return _norm_text(_first_prop(props, "imoNumber") or _first_prop(props, "mmsi") or _first_prop(props, "name"))

    if schema == "Airplane":
        return _norm_text(_first_prop(props, "registrationNumber") or _first_prop(props, "tailNumber") or _first_prop(props, "name"))

    return None


def _canon_id(schema: str, key: str) -> str:
    h = hashlib.sha1(f"{schema}|{key}".encode("utf-8", errors="ignore")).hexdigest()
    return f"canon-{h}"


def _is_entity_prop(schema_name: str, prop: str) -> bool:
    schema = model.get(schema_name)
    p = schema.get(prop)
    if p is None:
        return False
    # `p.type.name` is typically e.g. 'entity', 'string', 'date'
    return getattr(getattr(p, "type", None), "name", None) == "entity"


@dataclass
class CanonAgg:
    schema: str
    canon_id: str
    values: Dict[str, Dict[str, Any]]

    def add_value(self, prop: str, value: Any) -> None:
        if value is None:
            return
        if isinstance(value, list):
            for v in value:
                self.add_value(prop, v)
            return

        try:
            key = json.dumps(value, sort_keys=True, ensure_ascii=False)
        except Exception:
            key = str(value)

        bucket = self.values.setdefault(prop, {})
        bucket.setdefault(key, value)

    def to_entity_dict(self) -> Dict[str, Any]:
        ent = model.make_entity(self.schema)
        ent.id = self.canon_id

        for prop, bucket in self.values.items():
            if ent.schema.get(prop) is None:
                continue
            for v in bucket.values():
                ent.add(prop, v)

        return ent.to_dict()


def dedup_stream(
    in_path: Path,
    out_path: Path,
    dedup_schemata: Iterable[str] = DEDUP_SCHEMATA,
    verbose: bool = False,
) -> int:
    in_path = Path(in_path)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not in_path.exists():
        logger.error("missing input NDJSON: %s", in_path)
        return 2

    dedup_set = set(dedup_schemata)

    canon: Dict[str, CanonAgg] = {}
    id_map: Dict[str, str] = {}

    # First pass: build canonical aggregates and an old->canonical id map.
    # Spool non-dedupbed entities to disk for a second pass rewrite.
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        delete=False,
        prefix="ftm-dedup-spool-",
        suffix=".ndjson",
        dir=str(out_path.parent),
    ) as spool:
        spool_path = Path(spool.name)

        with in_path.open("r", encoding="utf-8", errors="ignore") as fh:
            for i, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                try:
                    ent = json.loads(line)
                except Exception:
                    continue

                schema = ent.get("schema")
                ent_id = ent.get("id")
                props = ent.get("properties") or {}
                if not schema or not ent_id or not isinstance(props, dict):
                    continue

                if schema in dedup_set:
                    key = _canon_key(schema, props)
                    if not key:
                        spool.write(line)
                        continue

                    cid = _canon_id(schema, key)
                    id_map[str(ent_id)] = cid
                    agg = canon.get(cid)
                    if agg is None:
                        agg = CanonAgg(schema=schema, canon_id=cid, values={})
                        canon[cid] = agg

                    for prop, val in props.items():
                        agg.add_value(prop, val)

                else:
                    spool.write(line)

                if verbose and i % 10000 == 0:
                    logger.info("pass1 lines=%d canon=%d", i, len(canon))

    # Second pass: write canonical entities, then rewrite spooled entities.
    written = 0
    with out_path.open("w", encoding="utf-8", buffering=1) as out:
        for cid in sorted(canon.keys()):
            out.write(json.dumps(canon[cid].to_entity_dict(), ensure_ascii=False) + "\n")
            written += 1

        with spool_path.open("r", encoding="utf-8", errors="ignore") as fh:
            for i, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                try:
                    ent = json.loads(line)
                except Exception:
                    continue

                schema = ent.get("schema")
                props = ent.get("properties") or {}
                if not schema or not isinstance(props, dict):
                    continue

                for prop, val in list(props.items()):
                    if not _is_entity_prop(schema, prop):
                        continue

                    if isinstance(val, list):
                        props[prop] = [id_map.get(str(v), v) for v in val]
                    else:
                        props[prop] = id_map.get(str(val), val)

                ent["properties"] = props
                out.write(json.dumps(ent, ensure_ascii=False) + "\n")
                written += 1

                if verbose and i % 10000 == 0:
                    logger.info("pass2 spooled=%d written=%d", i, written)

    try:
        spool_path.unlink(missing_ok=True)
    except Exception:
        pass

    if verbose:
        logger.info("wrote %s (entities=%d canon=%d)", out_path, written, len(canon))

    return 0
