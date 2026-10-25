"""Preflight guards and lock/manifest writers (protocol v5 sections 1.3, 6).

Pure, dependency-injected helpers. The loaders take an explicit path so tests
exercise them on tiny synthetic JSONL only; this module never opens the real
dataset by itself. The lock/manifest writers serialize deterministically
(``sort_keys``) to a caller-provided path — they are provided for a separately
authorized CPU preflight and are not invoked here on repository paths.

Overlap guards are fail-closed: any exact canonical-ID collision or any
normalized near-duplicate across partitions (or against a historical split)
is a preflight FAILURE that blocks the pilot.
"""

from __future__ import annotations

import hashlib
import json
import re

from .ids import PARTITION_ORDER, canonical_id, validate_unique

# Locked calibration-bank depth (matches GSM8KEvaluator default).
BANK_EXEMPLAR_COUNT = 48

# Near-duplicate token-Jaccard threshold (planning guard; exact match always).
NEAR_DUP_THRESHOLD = 0.9

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class PreflightError(ValueError):
    """Raised on a fail-closed preflight violation (overlap, duplicate, bad row)."""


def load_gsm8k_jsonl(path):
    """Load a GSM8K-format JSONL file into ``{"question", "answer"}`` dicts.

    Every non-empty line must be a JSON object with a string ``question``;
    anything else is a preflight failure. Returns canonical IDs too, so the
    caller can run the ID audit without re-deriving them.
    """
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                raise PreflightError("line %d: invalid JSON (%s)" % (lineno, e))
            if not isinstance(obj, dict) or not isinstance(obj.get("question"), str):
                raise PreflightError("line %d: missing string 'question'" % lineno)
            rows.append({"question": obj["question"],
                         "answer": obj.get("answer"),
                         "source_id": obj.get("id")})
    return rows


def canonical_ids(rows):
    """Canonical `src:`/`q:` IDs for loaded rows; duplicates are a FAILURE."""
    ids = [canonical_id(r.get("source_id"), r["question"]) for r in rows]
    validate_unique(ids)
    return ids


def _norm_tokens(text):
    return frozenset(_TOKEN_RE.findall(str(text).lower()))


def exact_overlap_guard(ids_a, ids_b, label_a="A", label_b="B"):
    """Fail-closed exact canonical-ID overlap check between two ID sets."""
    inter = sorted(set(ids_a) & set(ids_b))
    if inter:
        raise PreflightError(
            "exact ID overlap between %s and %s: %d shared (e.g. %s)"
            % (label_a, label_b, len(inter), inter[0]))
    return True


def near_duplicate_guard(texts_a, texts_b, threshold=NEAR_DUP_THRESHOLD,
                         label_a="A", label_b="B"):
    """Fail-closed near-duplicate check via token-Jaccard similarity.

    Any cross pair with Jaccard >= ``threshold`` (or an exact normalized-token
    match) blocks the pilot. Intended for small pilot partitions; returns True
    when clean.
    """
    toks_a = [(t, _norm_tokens(t)) for t in texts_a]
    toks_b = [(t, _norm_tokens(t)) for t in texts_b]
    for ta, sa in toks_a:
        for tb, sb in toks_b:
            if not sa or not sb:
                continue
            j = len(sa & sb) / float(len(sa | sb))
            if j >= threshold:
                raise PreflightError(
                    "near-duplicate between %s and %s (Jaccard=%.3f): %r ~ %r"
                    % (label_a, label_b, j, ta[:40], tb[:40]))
    return True


def pairwise_partition_guard(partitions):
    """Every partition pair must be disjoint by canonical ID (must be empty)."""
    names = [n for n in PARTITION_ORDER if n in partitions]
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            exact_overlap_guard(partitions[names[i]], partitions[names[j]],
                                names[i], names[j])
    return True


def bank_first48_id_hash(bank_ids):
    """SHA-256 of the first-48 BANK exemplar canonical IDs (newline-joined).

    Locks the exemplar-bank content identity for the manifest. Raises when the
    bank has fewer than 48 IDs.
    """
    bank_ids = list(bank_ids)
    if len(bank_ids) < BANK_EXEMPLAR_COUNT:
        raise PreflightError("BANK has %d IDs, need first %d"
                             % (len(bank_ids), BANK_EXEMPLAR_COUNT))
    first = bank_ids[:BANK_EXEMPLAR_COUNT]
    return hashlib.sha256("\n".join(first).encode("utf-8")).hexdigest()


def ordered_id_list_hash(ids):
    """SHA-256 of an ordered canonical-ID list (newline-joined)."""
    return hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()


def write_json(payload, path):
    """Deterministically write a JSON artifact (sorted keys, trailing newline)."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    return path


def build_lock(partitions, subsets, source):
    """Assemble the partition/subset lock payload (NOT written here).

    ``source`` records provenance (path/revision/sha256) supplied by the
    authorized preflight caller. Per-partition and per-subset ordered ID lists
    plus their hashes are included; pairwise intersections are verified empty.
    """
    pairwise_partition_guard(partitions)
    lock = {"source": source,
            "partitions": {}, "subsets": {}}
    for name, ids in partitions.items():
        lock["partitions"][name] = {"n": len(ids), "ids": list(ids),
                                    "ids_sha256": ordered_id_list_hash(ids)}
    for name, ids in subsets.items():
        lock["subsets"][name] = {"n": len(ids), "ids": list(ids),
                                 "ids_sha256": ordered_id_list_hash(ids)}
    if "BANK" in partitions:
        lock["bank_first48_ids_sha256"] = bank_first48_id_hash(partitions["BANK"])
    return lock


def build_manifest(lock, extra=None):
    """Assemble a run manifest payload from a lock plus caller-supplied fields."""
    manifest = {"lock": lock}
    if extra:
        manifest.update(extra)
    return manifest
