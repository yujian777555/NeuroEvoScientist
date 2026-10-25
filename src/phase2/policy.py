"""Unified policy contract and model selection (protocol v5 section 3, R4/R5).

Every candidate produces, from pre-inference question features only, a score
vector ``s_i(c)`` with the B1 score anchored to zero, hence a deterministic
action:

    c_star   = argmax_c s_i(c)         (ties broken by the fixed config order)
    action_i = c_star if max_c s_i(c) > delta and shift_score(x_i) <= tau else B1

Model classes (independent grids):
- Ridge regression (one regressor per non-B1 action), target ``u_i(c)-u_i(B1)``;
- Multinomial logistic regression over the best action, score ``p(c)-p(B1)``;
- GradientBoostingRegressor (one regressor per non-B1 action), same Delta-u target.

Classes are compared by the realized utility of the resulting action at the
locked lambda=0.1, never by an R^2 that is meaningless for a classifier. All
selection is FIT cross-validation then TUNE feature-set/threshold selection,
with deterministic tie-breaks and a final FIT-only refit. If TUNE selects F0
the run is NO-GO_IDENTICAL_TO_SIMPLE-FEAT before any LEVAL output.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, Ridge

from .features import FEATURE_SETS, ShiftDetector
from .stats import (LAMBDA, S0, STATUS_INCOMPLETE_INVALID,
                    STATUS_NO_GO_SIMPLE_FEAT, STATUS_PASS, quantile_type7)

# --- Locked action set and order (protocol section 2) ------------------------
CONFIG_ORDER = ("B1", "B0", "B3", "REF", "B2")
B1_INDEX = 0
CONFIG_INDEX = {name: i for i, name in enumerate(CONFIG_ORDER)}
NON_B1_ACTIONS = tuple(c for c in CONFIG_ORDER if c != "B1")
NON_B1_INDEX = tuple(CONFIG_INDEX[c] for c in NON_B1_ACTIONS)
N_CONFIGS = len(CONFIG_ORDER)

# --- Locked independent hyperparameter grids (section 3.2) -------------------
RIDGE_ALPHAS = (0.1, 1.0, 10.0)
LOGISTIC_CS = (0.1, 1.0, 10.0)
GBT_N_ESTIMATORS = (50, 100)
GBT_MAX_DEPTHS = (1, 3)
GBT_LEARNING_RATE = 0.05
GBT_SUBSAMPLE = 1.0
LOGISTIC_MAX_ITER = 1000

# --- Locked TUNE grids (sections 3.3, R5-A) ----------------------------------
DELTA_GRID = (0.0, 0.005, 0.01, 0.02)
TAU_PERCENTILES = (90, 95, 99)

CLASS_RANK = {"ridge": 0, "logistic": 1, "gbt": 2}  # tie preference order


@dataclass(frozen=True)
class CandidateSpec:
    """One class + hyperparameter candidate (10 total across the grids)."""
    cls: str
    params: dict
    grid_key: str


@dataclass
class Selection:
    selected: CandidateSpec
    score: float
    table: list = field(default_factory=list)


@dataclass
class FeatureSelection:
    feature_set: str
    delta: float
    tau: float
    table: list = field(default_factory=list)


@dataclass
class CandidateResult:
    status: str
    feature_set: str = None
    delta: float = None
    tau: float = None
    selection: Selection = None
    simple_feat: dict = None
    best_fixed: str = None
    majority: str = None
    candidate: object = None


def grid_candidates():
    """The 10 class/hyperparameter candidates (3 ridge + 3 logistic + 4 GBT)."""
    cands = [CandidateSpec("ridge", {"alpha": a}, "ridge|alpha=%g" % a)
             for a in RIDGE_ALPHAS]
    cands += [CandidateSpec("logistic", {"C": c}, "logistic|C=%g" % c)
              for c in LOGISTIC_CS]
    cands += [CandidateSpec("gbt", {"n_estimators": n, "max_depth": d},
                            "gbt|n=%d|d=%d" % (n, d))
              for n in GBT_N_ESTIMATORS for d in GBT_MAX_DEPTHS]
    return cands


def _tie_key(spec):
    """Deterministic FIT tie-break: ridge<logistic<GBT; larger alpha/C;
    shallower then fewer GBT trees. Only compared within equal class rank."""
    if spec.cls == "ridge":
        return (CLASS_RANK["ridge"], (-spec.params["alpha"],))
    if spec.cls == "logistic":
        return (CLASS_RANK["logistic"], (-spec.params["C"],))
    return (CLASS_RANK["gbt"],
            (spec.params["max_depth"], spec.params["n_estimators"]))


def argmax_config(values, tokens=None):
    """Index of the max score; exact ties -> lower total tokens -> config order.

    The fixed config order is CONFIG_ORDER, so among remaining ties the
    smallest index wins. ``tokens`` (per-config totals) is used only for the
    best-action tie rule of section 2.
    """
    values = np.asarray(values, dtype=float)
    best = np.max(values)
    cand = np.flatnonzero(values == best)
    if tokens is not None:
        tok = np.asarray(tokens, dtype=float)
        cand = cand[tok[cand] == np.min(tok[cand])]
    return int(np.min(cand))


def choose_action(score_vec, delta, shift_score, tau):
    """The gated action rule; returns a config index."""
    c_star = argmax_config(score_vec)
    if score_vec[c_star] > delta and shift_score <= tau:
        return c_star
    return B1_INDEX


def best_actions(U, tokens):
    """Per-item best action a*_i = argmax_c u_i(c) with section-2 tie rules."""
    U = np.asarray(U, dtype=float)
    tokens = np.asarray(tokens, dtype=float)
    return np.array([argmax_config(U[i], tokens[i]) for i in range(len(U))],
                    dtype=int)


class PolicyModel:
    """A fitted policy: maps feature vectors to a 5-dim score vector, B1 == 0."""

    def __init__(self, spec, estimators=None, clf=None, classes=None):
        self.spec = spec
        self.estimators = estimators or {}   # ridge/GBT: {config_index: reg}
        self.clf = clf                       # logistic: multinomial classifier
        self.classes = classes               # sorted label indices of clf

    def scores(self, X):
        X = np.atleast_2d(np.asarray(X, dtype=np.float64))
        n = X.shape[0]
        out = np.zeros((n, N_CONFIGS), dtype=np.float64)
        if self.clf is not None:
            proba = self.clf.predict_proba(X)
            p_b1 = proba[:, list(self.classes).index(B1_INDEX)]
            for pos, cls_idx in enumerate(self.classes):
                if cls_idx == B1_INDEX:
                    continue
                out[:, cls_idx] = proba[:, pos] - p_b1
        else:
            for a, reg in self.estimators.items():
                out[:, a] = reg.predict(X)
        out[:, B1_INDEX] = 0.0
        return out


def fit_policy(spec, X, U, tokens):
    """Fit one candidate; return a PolicyModel, or None on a failed fit.

    A logistic fit that lacks any action class (including B1) fails and is
    excluded deterministically. Regressors fit one model per non-B1 action.
    """
    X = np.asarray(X, dtype=np.float64)
    U = np.asarray(U, dtype=np.float64)
    tokens = np.asarray(tokens, dtype=np.float64)
    try:
        if spec.cls == "logistic":
            labels = best_actions(U, tokens)
            if set(np.unique(labels).tolist()) != set(range(N_CONFIGS)):
                return None
            clf = LogisticRegression(C=spec.params["C"], solver="lbfgs",
                                     max_iter=LOGISTIC_MAX_ITER)
            clf.fit(X, labels)
            return PolicyModel(spec, clf=clf, classes=clf.classes_)
        base = U[:, B1_INDEX]
        est = {}
        for a in NON_B1_INDEX:
            target = U[:, a] - base
            if spec.cls == "ridge":
                # SVD solver: deterministic and avoids the cholesky/scipy path.
                reg = Ridge(alpha=spec.params["alpha"], fit_intercept=True,
                            solver="svd")
            elif spec.cls == "gbt":
                reg = GradientBoostingRegressor(
                    loss="squared_error",
                    n_estimators=spec.params["n_estimators"],
                    max_depth=spec.params["max_depth"],
                    learning_rate=GBT_LEARNING_RATE,
                    subsample=GBT_SUBSAMPLE, random_state=S0)
            else:
                return None
            reg.fit(X, target)
            est[a] = reg
        return PolicyModel(spec, estimators=est)
    except Exception:
        return None


def cv_mean_utility(spec, X, folds, U, tokens):
    """FIT cross-validation realized utility under neutral gating.

    Fit on four folds, evaluate on the held-out fold with ``delta=0``,
    ``tau=+inf`` (action = argmax score). Returns None if the fit fails on any
    fold (that candidate is then excluded).
    """
    X = np.asarray(X, dtype=np.float64)
    U = np.asarray(U, dtype=np.float64)
    tokens = np.asarray(tokens, dtype=np.float64)
    folds = np.asarray(folds)
    utils = []
    for f in sorted(set(folds.tolist())):
        tr, te = folds != f, folds == f
        model = fit_policy(spec, X[tr], U[tr], tokens[tr])
        if model is None:
            return None
        scores = model.scores(X[te])
        for i in range(scores.shape[0]):
            a = choose_action(scores[i], delta=0.0, shift_score=0.0,
                              tau=float("inf"))
            utils.append(U[te][i, a])
    return float(np.mean(utils)) if utils else None


def select_model(X_f0, X_f1, folds, U, tokens):
    """FIT model choice: select class/hyperparameters by mean CV utility.

    The class/hyperparameter score is ``(S(F0) + S(F1)) / 2``. Deterministic
    ties prefer ridge < logistic < GBT, larger alpha/C, shallower then fewer
    GBT trees, then the lexicographic grid key. Returns None when every
    candidate fails on a fold (model selection is INVALID and stops).
    """
    scored = []
    for spec in grid_candidates():
        s0 = cv_mean_utility(spec, X_f0, folds, U, tokens)
        s1 = cv_mean_utility(spec, X_f1, folds, U, tokens)
        if s0 is None or s1 is None:
            continue
        scored.append((spec, 0.5 * (s0 + s1), {"F0": s0, "F1": s1}))
    if not scored:
        return None
    best = min(scored, key=lambda t: (-t[1],) + _tie_key(t[0]) + (t[0].grid_key,))
    return Selection(selected=best[0], score=best[1], table=scored)


def _realized_utility(scores, shift, U, delta, tau):
    U = np.asarray(U, dtype=np.float64)
    tot = 0.0
    for i in range(scores.shape[0]):
        tot += U[i, choose_action(scores[i], delta, shift[i], tau)]
    return tot / scores.shape[0]


def tau_candidates(shift_scores, percentiles=TAU_PERCENTILES):
    """Tau grid from TUNE shift-score percentiles (90/95/99), type-7."""
    ordered = sorted(float(s) for s in shift_scores)
    return [quantile_type7(ordered, p / 100.0) for p in percentiles]


def select_feature_and_thresholds(policies, detectors, X_tune, U_tune, tokens_tune):
    """TUNE-only selection of feature set, delta, tau by realized utility.

    Ties prefer F0, then smaller delta, then smaller tau. ``policies`` /
    ``detectors`` / ``X_tune`` are dicts keyed by feature set ("F0"/"F1").
    """
    U_tune = np.asarray(U_tune, dtype=np.float64)
    combos = []
    for fs in FEATURE_SETS:
        shift = detectors[fs].score(X_tune[fs])
        scores = policies[fs].scores(X_tune[fs])
        for delta in DELTA_GRID:
            for tau in tau_candidates(shift):
                u = _realized_utility(scores, shift, U_tune, delta, tau)
                combos.append(((fs, delta, tau), u))
    best = min(combos, key=lambda t: (-t[1], 0 if t[0][0] == "F0" else 1,
                                      t[0][1], t[0][2]))
    (fs, delta, tau), _ = best
    return FeatureSelection(feature_set=fs, delta=delta, tau=tau, table=combos)


def best_fixed(U, tokens):
    """BEST-FIXED: fixed config with highest mean FIT realized utility.

    Exact ties use lower total tokens, then the fixed config order. Returns a
    config index.
    """
    U = np.asarray(U, dtype=np.float64)
    tokens = np.asarray(tokens, dtype=np.float64)
    mean_u = U.mean(axis=0)
    tot_tok = tokens.sum(axis=0)
    cand = np.flatnonzero(mean_u == np.max(mean_u))
    cand = cand[tot_tok[cand] == np.min(tot_tok[cand])]
    return int(np.min(cand))


def majority_action(U, tokens):
    """MAJORITY: most frequent observed best action on FIT.

    Frequency ties choose the first config in the frozen order
    (B1, B0, B3, REF, B2) == the smallest index (R5-F).
    """
    best = best_actions(U, tokens)
    freq = np.bincount(best, minlength=N_CONFIGS)
    top = np.flatnonzero(freq == np.max(freq))
    return int(np.min(top))


def simple_feat_thresholds(policy_f0, detector_f0, X_tune_f0, U_tune, tokens_tune):
    """SIMPLE-FEAT's own F0 thresholds (R5-A), independent of the F1 candidate.

    Select delta from the frozen grid and tau from the F0-specific TUNE
    shift-score percentiles by realized utility at lambda=0.1. Ties prefer
    smaller delta then smaller tau. Returns ``(delta, tau)``.
    """
    U_tune = np.asarray(U_tune, dtype=np.float64)
    shift = detector_f0.score(X_tune_f0)
    scores = policy_f0.scores(X_tune_f0)
    combos = []
    for delta in DELTA_GRID:
        for tau in tau_candidates(shift):
            combos.append(((delta, tau),
                           _realized_utility(scores, shift, U_tune, delta, tau)))
    (delta, tau), _ = min(combos, key=lambda t: (-t[1], t[0][0], t[0][1]))
    return delta, tau


def final_refit(spec, X, U, tokens):
    """Final FIT-only refit and freeze; None (INVALID) on any fit failure."""
    return fit_policy(spec, X, U, tokens)


def run_candidate_selection(X_fit_f0, X_fit_f1, folds_fit, U_fit, tokens_fit,
                            X_tune_f0, X_tune_f1, U_tune, tokens_tune):
    """The single ordered selection procedure of section 3.3 (steps 1-7).

    Returns a CandidateResult. Status is STATUS_PASS only when TUNE selects F1
    and the frozen F1 candidate is refit; STATUS_NO_GO_SIMPLE_FEAT when TUNE
    selects F0 (stop before any LEVAL output); STATUS_INCOMPLETE_INVALID when
    model selection or a refit fails.
    """
    sel = select_model(X_fit_f0, X_fit_f1, folds_fit, U_fit, tokens_fit)
    if sel is None:
        return CandidateResult(status=STATUS_INCOMPLETE_INVALID)

    pol_f0 = final_refit(sel.selected, X_fit_f0, U_fit, tokens_fit)
    pol_f1 = final_refit(sel.selected, X_fit_f1, U_fit, tokens_fit)
    if pol_f0 is None or pol_f1 is None:
        return CandidateResult(status=STATUS_INCOMPLETE_INVALID,
                               selection=sel)

    det_f0 = ShiftDetector().fit(X_fit_f0)
    det_f1 = ShiftDetector().fit(X_fit_f1)
    fs = select_feature_and_thresholds(
        {"F0": pol_f0, "F1": pol_f1}, {"F0": det_f0, "F1": det_f1},
        {"F0": X_tune_f0, "F1": X_tune_f1}, U_tune, tokens_tune)

    if fs.feature_set == "F0":
        # Degeneracy guard: identical to the simple-feature comparator.
        return CandidateResult(status=STATUS_NO_GO_SIMPLE_FEAT,
                               feature_set="F0", selection=sel)

    candidate = final_refit(sel.selected, X_fit_f1, U_fit, tokens_fit)
    if candidate is None:
        return CandidateResult(status=STATUS_INCOMPLETE_INVALID,
                               feature_set="F1", selection=sel)

    sf_delta, sf_tau = simple_feat_thresholds(pol_f0, det_f0, X_tune_f0,
                                              U_tune, tokens_tune)
    return CandidateResult(
        status=STATUS_PASS,
        feature_set="F1", delta=fs.delta, tau=fs.tau, selection=sel,
        simple_feat={"delta": sf_delta, "tau": sf_tau, "feature_set": "F0"},
        best_fixed=CONFIG_ORDER[best_fixed(U_fit, tokens_fit)],
        majority=CONFIG_ORDER[majority_action(U_fit, tokens_fit)],
        candidate=candidate,
    )
