"""Duplicate-group audit and atomic partition (R1, CPU only).

The detector is deliberately reused, not re-tuned:
- token-set Jaccard from ``preflight._norm_tokens`` (lowercase alphanumeric
  tokens), threshold ``preflight.NEAR_DUP_THRESHOLD`` (0.9), already frozen
  in the previous failed preflight and its manifest;
- sequence ratio from ``difflib.SequenceMatcher`` on the original question
  text, the same calculation used for the Josie/Amanda evidence.

All length-compatible sample pairs are evaluated; the length filter only
removes pairs whose Jaccard cannot reach the frozen threshold (it is an
exact upper bound, not sampling). Groups are connected components of the
near-duplicate graph. A component that is not a clique is a potential
transitive-chain over-merge and is a hard stop rather than a silently
accepted partition. No answer or evaluator-private field is used.
"""

from __future__ import annotations

import difflib
import hashlib
import json
from collections import Counter, defaultdict

from . import ids, preflight

DETECTOR_VERSION = "token-jaccard-v1"
GROUP_ALGORITHM_VERSION = "connected-components-clique-guard-v1"
PARTITION_ALGORITHM_VERSION = "atomic-groups-exact-counts-v1"
GROUP_PARTITION_TAG = "phase2-group-partition-v1"
GROUP_ID_PREFIX = "dg:"


class DuplicateAuditError(ValueError):
    """Base class for fail-closed duplicate audit errors."""


class DetectorContractError(DuplicateAuditError):
    """The frozen detector threshold/version is missing or inconsistent."""


class AmbiguousGroupError(DuplicateAuditError):
    """A group may be a transitive-chain or otherwise ambiguous merge."""


class PartitionToleranceError(DuplicateAuditError):
    """Exact frozen partition counts cannot be met without splitting groups."""


class LockValidationError(DuplicateAuditError):
    """A lock, source hash, or manifest does not match the real artifacts."""


def detector_contract():
    """Return the frozen, traceable detector contract or fail closed."""
    threshold = getattr(preflight, "NEAR_DUP_THRESHOLD", None)
    if not isinstance(threshold, (int, float)) or not 0 < threshold < 1:
        raise DetectorContractError("missing/invalid frozen Jaccard threshold")
    if DETECTOR_VERSION != "token-jaccard-v1" or not GROUP_ALGORITHM_VERSION:
        raise DetectorContractError("missing detector/group algorithm version")
    return {
        "detector_version": DETECTOR_VERSION,
        "jaccard_threshold": threshold,
        "jaccard_tokens": "frozenset(re.findall(r'[a-z0-9]+', text.lower()))",
        "sequence_ratio": "difflib.SequenceMatcher(None, question_a, question_b).ratio() on original question text",
        "normalization": "lowercase alphanumeric tokenization only; no name stripping; no punctuation/name-specific rewriting",
        "threshold_source": "src/phase2/preflight.py NEAR_DUP_THRESHOLD and phase2/pilot/preflight_manifest.json",
        "group_algorithm_version": GROUP_ALGORITHM_VERSION,
        "partition_algorithm_version": PARTITION_ALGORITHM_VERSION,
        "group_id": "dg: + sha256(newline-joined sorted canonical member IDs)",
        "allowed_fields": ["question text and canonical ID only"],
    }


def _tokens(text):
    return preflight._norm_tokens(text)


def near_duplicate_pairs(rows, threshold=None):
    """Evaluate every length-compatible pair and return all edges >= threshold.

    For token sets A and B, ``min(|A|,|B|)/max(|A|,|B|)`` is an upper bound
    on their Jaccard. Pairs below the threshold by that bound are skipped as
    provably non-matches; every other pair is explicitly scored.
    """
    contract = detector_contract()
    threshold = contract["jaccard_threshold"] if threshold is None else threshold
    if threshold != contract["jaccard_threshold"]:
        raise DetectorContractError("attempt to change frozen threshold")
    n = len(rows)
    sets = [_tokens(r["question"]) for r in rows]
    lengths = [len(s) for s in sets]
    edges = []
    scored = 0
    skipped_by_bound = 0
    for i in range(n):
        if not lengths[i]:
            for j in range(i + 1, n):
                if not lengths[j]:
                    a, b = rows[i], rows[j]
                    edges.append(_edge(i, j, a, b, 1.0))
                    scored += 1
                else:
                    skipped_by_bound += 1
            continue
        for j in range(i + 1, n):
            if not lengths[j]:
                skipped_by_bound += 1
                continue
            lo, hi = sorted((lengths[i], lengths[j]))
            if lo / hi < threshold:
                skipped_by_bound += 1
                continue
            scored += 1
            jaccard = lo and (len(sets[i] & sets[j]) / len(sets[i] | sets[j]))
            if jaccard >= threshold:
                edges.append(_edge(i, j, rows[i], rows[j], jaccard))
    stats = {
        "total_pairs": n * (n - 1) // 2,
        "pairs_scored": scored,
        "pairs_rejected_by_length_upper_bound": skipped_by_bound,
        "candidate_edges": len(edges),
        "candidate_pairs_are_not_sampled": True,
    }
    return edges, stats


def _edge(i, j, row_a, row_b, jaccard):
    return {
        "i": i, "j": j,
        "id_a": row_a["canonical_id"], "id_b": row_b["canonical_id"],
        "partition_a": row_a.get("original_partition"),
        "partition_b": row_b.get("original_partition"),
        "jaccard": float(jaccard),
        "sequence_ratio": difflib.SequenceMatcher(
            None, row_a["question"], row_b["question"]).ratio(),
    }


class _DSU:
    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a == b:
            return
        if self.size[a] < self.size[b]:
            a, b = b, a
        self.parent[b] = a
        self.size[a] += self.size[b]


def _group_id(member_ids):
    payload = "\n".join(sorted(member_ids)).encode("utf-8")
    return GROUP_ID_PREFIX + hashlib.sha256(payload).hexdigest()


def build_groups(rows, edges):
    """Build clique-checked connected components from near-duplicate edges."""
    dsu = _DSU(len(rows))
    for edge in edges:
        dsu.union(edge["i"], edge["j"])
    components = defaultdict(list)
    for i in range(len(rows)):
        components[dsu.find(i)].append(i)
    edge_set = {(min(e["i"], e["j"]), max(e["i"], e["j"])): e for e in edges}
    groups = []
    for members in components.values():
        members = sorted(members)
        member_ids = [rows[i]["canonical_id"] for i in members]
        internal = []
        missing = []
        for a in range(len(members)):
            for b in range(a + 1, len(members)):
                key = (members[a], members[b])
                if key in edge_set:
                    internal.append(edge_set[key]["jaccard"])
                else:
                    missing.append([member_ids[a], member_ids[b]])
        ambiguities = []
        if missing:
            ambiguities.append("CHAIN_NON_CLIQUE")
        groups.append({
            "group_id": _group_id(member_ids),
            "member_ids": member_ids,
            "size": len(members),
            "internal_edge_count": len(internal),
            "min_internal_jaccard": min(internal) if internal else None,
            "max_internal_jaccard": max(internal) if internal else None,
            "is_clique": not missing,
            "missing_clique_edges": missing,
            "ambiguities": ambiguities,
        })
    groups.sort(key=lambda g: (-g["size"], ids.sort_key(g["group_id"], GROUP_PARTITION_TAG)))
    return groups


def assert_unambiguous(groups):
    ambiguous = [g for g in groups if g["ambiguities"]]
    if ambiguous:
        raise AmbiguousGroupError(
            "ambiguous duplicate groups require review: %s"
            % [(g["group_id"], g["size"], g["ambiguities"])
               for g in ambiguous[:5]])


def group_size_distribution(groups):
    return dict(sorted(Counter(g["size"] for g in groups).items()))


def partition_groups(rows, groups, counts=None):
    """Assign whole groups to exact frozen counts without splitting or deletion."""
    counts = counts or dict(ids.PARTITION_COUNTS)
    if sum(counts.values()) != len(rows):
        raise LockValidationError("source row count differs from target total")
    assert_unambiguous(groups)
    remaining = dict(counts)
    assignment = {}
    multi = [g for g in groups if g["size"] > 1]
    multi.sort(key=lambda g: (-g["size"], ids.sort_key(g["group_id"], GROUP_PARTITION_TAG)))
    for group in multi:
        feasible = [name for name in ids.PARTITION_ORDER
                    if remaining[name] >= group["size"]]
        if not feasible:
            raise PartitionToleranceError(
                "group %s of size %d cannot fit any partition"
                % (group["group_id"], group["size"]))
        name = max(feasible, key=lambda n: (remaining[n],
                                            -ids.PARTITION_ORDER.index(n)))
        assignment[group["group_id"]] = name
        remaining[name] -= group["size"]
    for group in groups:
        if group["size"] != 1:
            continue
        name = max(ids.PARTITION_ORDER,
                   key=lambda n: (remaining[n], -ids.PARTITION_ORDER.index(n)))
        assignment[group["group_id"]] = name
        remaining[name] -= 1
    if any(v != 0 for v in remaining.values()):
        raise PartitionToleranceError(
            "atomic groups cannot meet exact frozen counts; deviation=%s" % remaining)

    partitions = {name: [] for name in ids.PARTITION_ORDER}
    group_by_id = {g["group_id"]: g for g in groups}
    for group in groups:
        partitions[assignment[group["group_id"]]].extend(group["member_ids"])
    for name, members in partitions.items():
        if len(members) != counts[name]:
            raise PartitionToleranceError("internal partition count mismatch")
        if len(set(members)) != len(members):
            raise LockValidationError("duplicate assignment in %s" % name)
    flat = [nid for name in ids.PARTITION_ORDER for nid in partitions[name]]
    if len(flat) != len(set(flat)):
        raise LockValidationError("sample assigned more than once")
    if set(flat) != {r["canonical_id"] for r in rows}:
        raise LockValidationError("source IDs changed or samples missing")
    return {
        "partitions": partitions,
        "group_assignment": assignment,
        "counts": {name: len(partitions[name]) for name in ids.PARTITION_ORDER},
        "deviation": {name: 0 for name in ids.PARTITION_ORDER},
        "tolerance": "exact frozen counts required; no positive tolerance was found in protocol v6",
    }


def canonical_group_entry(group):
    """Canonical serialization of one duplicate-group entry.

    Group-list order is contractual (``build_groups`` is deterministic), while
    member IDs and missing clique edges are sorted here so their content can be
    compared independently of their original serialization order. Every field
    used by the duplicate-group audit is checked, not just the assignment.
    """
    if not isinstance(group, dict):
        raise LockValidationError("group entry is not an object")
    required = {"group_id", "member_ids", "size", "internal_edge_count",
                "min_internal_jaccard", "max_internal_jaccard", "is_clique",
                "missing_clique_edges", "ambiguities"}
    if set(group) != required:
        raise LockValidationError("group entry fields mismatch")
    member_ids = group["member_ids"]
    if (not isinstance(member_ids, list)
            or any(not isinstance(nid, str) or not nid for nid in member_ids)):
        raise LockValidationError("invalid group member IDs")
    if len(member_ids) != group["size"] or len(set(member_ids)) != len(member_ids):
        raise LockValidationError("group size/member mismatch")
    if not isinstance(group["group_id"], str) or not group["group_id"]:
        raise LockValidationError("invalid group ID")
    if not isinstance(group["internal_edge_count"], int):
        raise LockValidationError("invalid internal edge count")
    if not isinstance(group["is_clique"], bool):
        raise LockValidationError("invalid clique flag")
    if not isinstance(group["ambiguities"], list):
        raise LockValidationError("invalid ambiguity flags")
    missing = []
    for pair in group["missing_clique_edges"]:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise LockValidationError("invalid missing clique edge")
        missing.append(sorted(pair))
    return {
        "group_id": group["group_id"],
        "member_ids": sorted(member_ids),
        "size": group["size"],
        "internal_edge_count": group["internal_edge_count"],
        "min_internal_jaccard": group["min_internal_jaccard"],
        "max_internal_jaccard": group["max_internal_jaccard"],
        "is_clique": group["is_clique"],
        "missing_clique_edges": sorted(missing),
        "ambiguities": list(group["ambiguities"]),
    }


def canonical_group_list(groups):
    """Canonicalize the contractual group list and reject duplicate group IDs."""
    if not isinstance(groups, list):
        raise LockValidationError("embedded groups is not a list")
    canonical = [canonical_group_entry(g) for g in groups]
    group_ids = [g["group_id"] for g in canonical]
    if len(set(group_ids)) != len(group_ids):
        raise LockValidationError("duplicate group ID in embedded groups")
    return canonical


def validate_lock(lock, rows, groups, source_sha256):
    """Recompute and validate a lock; reject tampering/hash or lock mismatch."""
    if not isinstance(source_sha256, str) or len(source_sha256) != 64:
        raise LockValidationError("invalid source hash")
    if lock.get("source", {}).get("sha256") != source_sha256:
        raise LockValidationError("source data hash mismatch")
    if lock.get("detector", {}).get("jaccard_threshold") != detector_contract()["jaccard_threshold"]:
        raise LockValidationError("detector threshold mismatch")
    if canonical_group_list(lock.get("groups")) != canonical_group_list(groups):
        raise LockValidationError("embedded duplicate-group structure mismatch")
    expected = partition_groups(rows, groups)
    if lock.get("group_assignment") != expected["group_assignment"]:
        raise LockValidationError("group assignment does not match deterministic recomputation")
    if lock.get("counts") != expected["counts"]:
        raise LockValidationError("partition counts mismatch")
    for name, members in lock["partitions"].items():
        if preflight.ordered_id_list_hash(members) != lock["partition_hashes"][name]:
            raise LockValidationError("partition hash mismatch: " + name)
        if set(members) != set(expected["partitions"][name]):
            raise LockValidationError("partition membership mismatch: " + name)
    return True


def bank_label_audit(partitions, historical_ids):
    """BANK labels must come only from train, never from historical eval splits."""
    bank = set(partitions["BANK"])
    overlaps = {name: len(bank & set(values)) for name, values in historical_ids.items()}
    if any(overlaps.values()):
        raise LockValidationError("BANK contains prohibited evaluation labels: %s" % overlaps)
    return {
        "bank_answer_label_source": "GSM8K train only",
        "prohibited_overlap": overlaps,
        "bank_contains_fit_tune_leval_or_test_labels": False,
    }


def make_lock(rows, groups, result, detector, source, historical_ids):
    """Create a deterministic lock payload from real rows/groups/results."""
    partitions = result["partitions"]
    return {
        "protocol": "phase2-duplicate-group-split-r1",
        "source": source,
        "detector": detector,
        "counts": result["counts"],
        "deviation": result["deviation"],
        "tolerance": result["tolerance"],
        "partitions": partitions,
        "partition_hashes": {
            name: preflight.ordered_id_list_hash(partitions[name])
            for name in ids.PARTITION_ORDER
        },
        "group_assignment": result["group_assignment"],
        "groups": groups,
        "bank_label_isolation": bank_label_audit(partitions, historical_ids),
    }
