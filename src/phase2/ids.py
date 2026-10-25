"""Canonical IDs, deterministic hash ordering, and partition/subset/fold locks.

Implements protocol v5 section 1 (R4-F / R5-B). Every canonical ID carries
exactly one namespace prefix:

- Source ID:   ``src:`` + normalized source scalar.
- Fallback ID: ``q:`` + lowercase hex SHA-256 of the UTF-8 bytes of
  ``"question\\0" + normalized_question_text``. The ``q:`` prefix is applied
  exactly once (to the digest, never to the question text and then again).

Normalization is Unicode NFC, strip leading/trailing whitespace, and collapse
every internal whitespace run to one ASCII space. Empty normalized values and
duplicate canonical IDs are preflight FAILURES (raised, never repaired).

All ordering is by ``(digest, norm_id)`` where
``digest = SHA256(UTF8(norm_id + "|" + namespace_tag))`` with no trailing
newline; the second key makes even an equal-digest tie deterministic.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata

# --- Locked namespace tags (protocol section 1.2) ---------------------------
PARTITION_TAG = "phase2-partition-v1"
SUBSET_TAG = "phase2-subset-v1"
FOLD_TAG = "phase2-fold-v1"

# --- Locked counts (protocol section 1.2) -----------------------------------
# Order matters: the partition sort is sliced in this fixed sequence.
PARTITION_ORDER = ("BANK", "FIT", "TUNE", "LEVAL")
PARTITION_COUNTS = {"BANK": 2989, "FIT": 1868, "TUNE": 1121, "LEVAL": 1495}
TOTAL_ITEMS = 7473  # sum(PARTITION_COUNTS.values())
SUBSET_SIZES = {"FIT": 500, "TUNE": 200, "LEVAL": 300}  # BANK has no pilot subset
N_FOLDS = 5

_SRC_NS = "src"
_FALLBACK_NS = "q"
_WS_RE = re.compile(r"\s+")


class IDError(ValueError):
    """Raised on empty normalized values or duplicate canonical IDs."""


def normalize_text(text):
    """Unicode NFC, strip ends, collapse internal whitespace runs to one space."""
    text = unicodedata.normalize("NFC", str(text))
    text = text.strip()
    return _WS_RE.sub(" ", text)


def _source_scalar(value):
    """Return the canonical scalar string for a usable source ID, else None.

    Strings are used directly; integers/floats use their JSON scalar
    representation. ``None``, booleans, arrays, and objects are unusable.
    (bool is checked before int because bool subclasses int.)
    """
    if isinstance(value, str):
        return value
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return json.dumps(value, ensure_ascii=False)
    return None  # arrays, objects, and any other type are unusable


def fallback_id(question):
    """`q:` + sha256 hex of UTF-8 bytes of ``"question\\0" + normalized``.

    The ``q:`` namespace prefix is applied exactly once. Raises IDError when
    the normalized question is empty.
    """
    norm = normalize_text(question)
    if norm == "":
        raise IDError("fallback ID requires non-empty normalized question")
    digest = hashlib.sha256(("question\0" + norm).encode("utf-8")).hexdigest()
    return _FALLBACK_NS + ":" + digest


def canonical_id(source_id, question):
    """Return the unique canonical ID (``src:`` or ``q:`` namespace).

    A source ID is usable when it is a string/int/float that normalizes to a
    non-empty value; otherwise the question-text fallback is used.
    """
    scalar = _source_scalar(source_id)
    if scalar is not None:
        norm = normalize_text(scalar)
        if norm != "":
            return _SRC_NS + ":" + norm
    return fallback_id(question)


def digest_bytes(norm_id, namespace_tag):
    """SHA256 of UTF8(``norm_id + "|" + namespace_tag``); no trailing newline."""
    payload = (norm_id + "|" + namespace_tag).encode("utf-8")
    return hashlib.sha256(payload).digest()


def sort_key(norm_id, namespace_tag):
    """Deterministic ascending sort key ``(digest, norm_id)``."""
    return (digest_bytes(norm_id, namespace_tag), norm_id)


def ordered_ids(norm_ids, namespace_tag):
    """Return ``norm_ids`` sorted ascending by the deterministic sort key."""
    return sorted(norm_ids, key=lambda x: sort_key(x, namespace_tag))


def validate_unique(norm_ids):
    """Raise IDError on empty values or duplicate canonical IDs."""
    seen = set()
    for nid in norm_ids:
        if not isinstance(nid, str) or nid == "":
            raise IDError("empty canonical ID")
        if nid in seen:
            raise IDError("duplicate canonical ID: %r" % nid)
        seen.add(nid)
    return True


def assign_partitions(norm_ids, counts=None, namespace_tag=PARTITION_TAG):
    """Sort all items and slice into BANK/FIT/TUNE/LEVAL in fixed order.

    ``counts`` defaults to the locked 2989/1868/1121/1495 split. The number of
    IDs must equal the sum of the counts exactly.
    """
    if counts is None:
        counts = PARTITION_COUNTS
    norm_ids = list(norm_ids)
    validate_unique(norm_ids)
    total = sum(counts[name] for name in PARTITION_ORDER)
    if len(norm_ids) != total:
        raise IDError("partition input has %d IDs, expected %d"
                      % (len(norm_ids), total))
    ordered = ordered_ids(norm_ids, namespace_tag)
    out, pos = {}, 0
    for name in PARTITION_ORDER:
        out[name] = ordered[pos:pos + counts[name]]
        pos += counts[name]
    return out


def assign_subsets(partitions, sizes=None, namespace_tag=SUBSET_TAG):
    """Independently sort within each partition and take the pilot subsets.

    Only partitions named in ``sizes`` (default FIT/TUNE/LEVAL = 500/200/300)
    get a subset; BANK is never subsampled as an evaluation target.
    """
    if sizes is None:
        sizes = SUBSET_SIZES
    out = {}
    for name, size in sizes.items():
        ordered = ordered_ids(partitions[name], namespace_tag)
        if len(ordered) < size:
            raise IDError("partition %s has %d IDs, subset needs %d"
                          % (name, len(ordered), size))
        out[name] = ordered[:size]
    return out


def assign_fold(norm_id, n_folds=N_FOLDS, namespace_tag=FOLD_TAG):
    """FIT cross-validation fold: ``int.from_bytes(digest[:4], "big") % n_folds``.

    Fixed before model fitting; independent of outcomes.
    """
    return int.from_bytes(digest_bytes(norm_id, namespace_tag)[:4], "big") % n_folds


def assign_folds(norm_ids, n_folds=N_FOLDS, namespace_tag=FOLD_TAG):
    """Vector of fold assignments for an ordered list of canonical IDs."""
    return [assign_fold(n, n_folds, namespace_tag) for n in norm_ids]
