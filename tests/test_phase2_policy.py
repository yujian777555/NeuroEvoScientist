"""Phase-2 policy tests: action rules, model selection, tie-breaks,
SIMPLE-FEAT thresholds, and the F0 NO-GO / F1 PASS gate. Tiny synthetic data."""

import os
import sys

import numpy as np

REPO = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(REPO, "src"))

from phase2 import policy as P  # noqa: E402


def _mk_util_from_features(X, n):
    """Utility where B0 is strongly linear in the given feature matrix."""
    U = np.zeros((n, 5))
    U[:, 1] = 0.5 + 2.0 * X[:, 0]
    U[:, 2] = 0.05 * X[:, 1]
    U[:, 3] = 0.05 * X[:, 0]
    U[:, 4] = 0.02 * X[:, 1]
    U[:, 0] = 0.1
    return U


# --- action rule -----------------------------------------------------------------

def test_action_rule_gating():
    sv = np.array([0.0, 0.5, 0.3, 0.1, 0.2])  # B0 best (index 1)
    assert P.choose_action(sv, delta=0.01, shift_score=0.0, tau=10.0) == 1
    # shift above tau -> fall back to B1
    assert P.choose_action(sv, delta=0.01, shift_score=5.0, tau=1.0) == 0
    # max score not above delta -> B1
    assert P.choose_action(np.array([0.0, -0.1, -0.2, -0.3, -0.4]),
                           delta=0.0, shift_score=0.0, tau=10.0) == 0


def test_argmax_tie_broken_by_config_order():
    # exact score tie between B1(0) and B0(1) -> smallest index (B1)
    assert P.argmax_config(np.array([0.5, 0.5, 0.1, 0.2, 0.3])) == 0
    # B3(2) and REF(3) tie -> B3
    assert P.argmax_config(np.array([0.0, 0.1, 0.7, 0.7, 0.2])) == 2


def test_best_action_tie_prefers_lower_tokens_then_order():
    U = np.array([[0.5, 0.5, 0.5, 0.1, 0.2]])       # B1,B0,B3 tie on utility
    tokens = np.array([[300, 100, 200, 100, 100]])   # B0 has fewest among ties
    assert P.best_actions(U, tokens)[0] == 1          # lower tokens wins
    tokens2 = np.array([[100, 100, 200, 100, 100]])  # B1 & B0 tie on tokens too
    assert P.best_actions(U, tokens2)[0] == 0         # then config order (B1)


# --- grid and tie-break ordering -------------------------------------------------

def test_grid_has_10_candidates():
    cands = P.grid_candidates()
    assert len(cands) == 10
    assert sum(c.cls == "ridge" for c in cands) == 3
    assert sum(c.cls == "logistic" for c in cands) == 3
    assert sum(c.cls == "gbt" for c in cands) == 4


def test_tie_key_preference_order():
    ridge_small = P.CandidateSpec("ridge", {"alpha": 0.1}, "ridge|alpha=0.1")
    ridge_big = P.CandidateSpec("ridge", {"alpha": 10.0}, "ridge|alpha=10")
    logi = P.CandidateSpec("logistic", {"C": 1.0}, "logistic|C=1")
    gbt = P.CandidateSpec("gbt", {"n_estimators": 50, "max_depth": 1}, "gbt|n=50|d=1")
    # equal score -> ridge < logistic < gbt; within ridge larger alpha preferred
    scored = [(logi, 1.0), (gbt, 1.0), (ridge_small, 1.0), (ridge_big, 1.0)]
    best = min(scored, key=lambda t: (-t[1],) + P._tie_key(t[0]) + (t[0].grid_key,))
    assert best[0] is ridge_big


# --- model selection --------------------------------------------------------------

def _fit_data(seed=0, n=30):
    rng = np.random.RandomState(seed)
    X0 = rng.randn(n, 2)
    X1 = np.concatenate([X0, rng.randn(n, 384)], axis=1)
    U = _mk_util_from_features(X0, n)
    tokens = rng.randint(100, 200, (n, 5)).astype(float)
    folds = np.arange(n) % 5
    return X0, X1, U, tokens, folds


def test_select_model_deterministic_and_valid():
    X0, X1, U, tokens, folds = _fit_data()
    sel1 = P.select_model(X0, X1, folds, U, tokens)
    sel2 = P.select_model(X0, X1, folds, U, tokens)
    assert sel1 is not None
    assert sel1.selected in P.grid_candidates()
    # deterministic across runs
    assert sel1.selected.grid_key == sel2.selected.grid_key
    assert sel1.score == sel2.score
    # selected candidate has the max (S(F0)+S(F1))/2 among survivors
    assert sel1.score == max(s for _, s, _ in sel1.table)


def test_logistic_excluded_when_fold_lacks_a_class():
    # best action only ever B0 -> every logistic fold is missing classes -> fail
    rng = np.random.RandomState(3)
    n = 25
    X0 = rng.randn(n, 2)
    X1 = np.concatenate([X0, rng.randn(n, 384)], axis=1)
    U = np.zeros((n, 5))
    U[:, 1] = 1.0 + X0[:, 0]          # B0 always the unique best action
    tokens = rng.randint(100, 200, (n, 5)).astype(float)
    folds = np.arange(n) % 5
    sel = P.select_model(X0, X1, folds, U, tokens)
    assert sel is not None
    assert sel.selected.cls != "logistic"
    assert all(spec.cls != "logistic" for spec, _, _ in sel.table)


# --- BEST-FIXED and MAJORITY -------------------------------------------------------

def test_best_fixed_tie_prefers_lower_tokens_then_order():
    U = np.array([[0.9, 0.9, 0.2, 0.1, 0.3]])          # B1 and B0 tie on utility
    tokens_low_b0 = np.array([[500, 100, 100, 100, 100]])
    assert P.CONFIG_ORDER[P.best_fixed(U, tokens_low_b0)] == "B0"   # fewer tokens
    tokens_tie = np.array([[100, 100, 100, 100, 100]])
    assert P.CONFIG_ORDER[P.best_fixed(U, tokens_tie)] == "B1"      # then order


def test_majority_frequency_tie_prefers_first_in_frozen_order():
    # row0 best=B1, row1 best=B0 -> frequency tie -> first in (B1,B0,...) -> B1
    U = np.array([[0.9, 0.5, 0.2, 0.1, 0.3],
                  [0.5, 0.9, 0.2, 0.1, 0.3]])
    tokens = np.array([[100, 100, 100, 100, 100],
                       [100, 100, 100, 100, 100]])
    assert P.CONFIG_ORDER[P.majority_action(U, tokens)] == "B1"
    # a clear winner is returned as-is
    U2 = np.array([[0.1, 0.9, 0.2, 0.3, 0.4],
                   [0.1, 0.9, 0.2, 0.3, 0.4]])
    assert P.CONFIG_ORDER[P.majority_action(U2, tokens)] == "B0"


# --- SIMPLE-FEAT thresholds and the F0/F1 gate -------------------------------------

def _tune_data(seed=7, n=25):
    rng = np.random.RandomState(seed)
    X0 = rng.randn(n, 2)
    emb = rng.randn(n, 384)
    X1 = np.concatenate([X0, emb], axis=1)
    U = np.zeros((n, 5))
    U[:, 1] = 0.5 + 2.0 * emb[:, 0]   # signal lives in the embedding
    U[:, 2] = 0.05 * emb[:, 1]
    U[:, 0] = 0.1
    tokens = rng.randint(100, 200, (n, 5)).astype(float)
    return X0, emb, X1, U, tokens


def test_simple_feat_thresholds_from_f0_grids():
    X0, emb, X1, U, tokens = _tune_data()
    rng = np.random.RandomState(11)
    Xf0 = rng.randn(30, 2)
    Uf = _mk_util_from_features(Xf0, 30)
    tf = rng.randint(100, 200, (30, 5)).astype(float)
    spec = P.CandidateSpec("ridge", {"alpha": 1.0}, "ridge|alpha=1")
    pol_f0 = P.final_refit(spec, Xf0, Uf, tf)
    det_f0 = P.ShiftDetector().fit(Xf0)
    delta, tau = P.simple_feat_thresholds(pol_f0, det_f0, X0, U, tokens)
    assert delta in P.DELTA_GRID
    assert tau in P.tau_candidates(det_f0.score(X0))
    # deterministic
    assert P.simple_feat_thresholds(pol_f0, det_f0, X0, U, tokens) == (delta, tau)


def test_run_candidate_selection_nogo_when_f0_wins():
    rng = np.random.RandomState(1)
    nf, nt = 40, 25
    Xf0 = rng.randn(nf, 2)
    Xf1 = np.concatenate([Xf0, rng.randn(nf, 384)], axis=1)  # embedding = noise
    Xt0 = rng.randn(nt, 2)
    Xt1 = np.concatenate([Xt0, rng.randn(nt, 384)], axis=1)
    Uf = _mk_util_from_features(Xf0, nf)
    Ut = _mk_util_from_features(Xt0, nt)
    tf = rng.randint(100, 200, (nf, 5)).astype(float)
    tt = rng.randint(100, 200, (nt, 5)).astype(float)
    res = P.run_candidate_selection(Xf0, Xf1, np.arange(nf) % 5, Uf, tf,
                                    Xt0, Xt1, Ut, tt)
    assert res.status == P.STATUS_NO_GO_SIMPLE_FEAT
    assert res.feature_set == "F0"
    assert res.candidate is None  # no frozen candidate on a NO-GO


def test_run_candidate_selection_pass_when_f1_wins():
    rng = np.random.RandomState(2)
    nf, nt = 40, 25
    Xf0 = rng.randn(nf, 2)
    embf = rng.randn(nf, 384)
    Xf1 = np.concatenate([Xf0, embf], axis=1)
    Xt0 = rng.randn(nt, 2)
    embt = rng.randn(nt, 384)
    Xt1 = np.concatenate([Xt0, embt], axis=1)
    # utility depends on embedding dim 0 -> only F1 can exploit it
    Uf = np.zeros((nf, 5)); Uf[:, 1] = 0.5 + 2.0 * embf[:, 0]; Uf[:, 0] = 0.1
    Ut = np.zeros((nt, 5)); Ut[:, 1] = 0.5 + 2.0 * embt[:, 0]; Ut[:, 0] = 0.1
    tf = rng.randint(100, 200, (nf, 5)).astype(float)
    tt = rng.randint(100, 200, (nt, 5)).astype(float)
    res = P.run_candidate_selection(Xf0, Xf1, np.arange(nf) % 5, Uf, tf,
                                    Xt0, Xt1, Ut, tt)
    assert res.status == P.STATUS_PASS
    assert res.feature_set == "F1"
    assert res.delta in P.DELTA_GRID
    assert isinstance(res.candidate, P.PolicyModel)
    # frozen candidate scores TUNE items to a 5-dim vector with B1 == 0
    scores = res.candidate.scores(Xt1)
    assert scores.shape == (nt, 5)
    assert np.all(scores[:, 0] == 0.0)
    # SIMPLE-FEAT keeps F0 and its own thresholds; baselines resolved
    assert res.simple_feat["feature_set"] == "F0"
    assert res.simple_feat["delta"] in P.DELTA_GRID
    assert res.best_fixed in P.CONFIG_ORDER
    assert res.majority in P.CONFIG_ORDER
