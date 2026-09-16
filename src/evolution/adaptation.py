"""Candidate substrate adaptation for ENSS (Phase-17, Task 3).

Every candidate gets the same small, fixed adaptation budget for its
trainable memory substrate; the LLM backbone stays frozen.

Protocol (configs/phase17_adaptation.yaml):
- calibration split: benchmark TRAIN split only (no test leakage)
- N optimizer steps, same for every candidate
- fixed optimizer / learning rate / seed across candidates
- objective: next-experience embedding prediction over the calibration
  stream (recurrent substrate objective)

Recorded per candidate: pre/post adaptation loss, wall-clock cost,
trainable parameter count — this is what makes the inheritance comparison
(inherited vs scratch init, equal budget) scientifically meaningful.
"""

import time

import torch

from evaluator.memory import hashed_embedding


class AdaptationConfig:
    def __init__(self, calibration_samples=48, adaptation_steps=30,
                 learning_rate=1e-3, weight_decay=0.01,
                 sequence_window=16, seed=0):
        self.calibration_samples = calibration_samples
        self.adaptation_steps = adaptation_steps
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
        self.sequence_window = sequence_window
        self.seed = seed

    @classmethod
    def from_yaml(cls, path):
        try:
            import yaml
        except ImportError:
            return cls()
        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        return cls(
            calibration_samples=cfg.get("calibration_samples", 48),
            adaptation_steps=cfg.get("adaptation_steps", 30),
            learning_rate=cfg.get("learning_rate", 1e-3),
            weight_decay=cfg.get("weight_decay", 0.01),
            sequence_window=cfg.get("sequence_window", 16),
            seed=cfg.get("seed", 0),
        )


def _calibration_embeddings(samples, dim):
    return [hashed_embedding(s["question"] + " " + s["answer"], dim)
            for s in samples]


def _sequence_loss(substrate, embeddings, window):
    """Next-embedding prediction loss over one calibration window."""
    seq = torch.stack(embeddings).unsqueeze(0)  # (1, n, dim)
    out = substrate.forward_sequence(seq)       # (1, n, dim)
    pred = out[:, :-1]
    target = seq[:, 1:]
    return torch.nn.functional.mse_loss(pred, target)


def adapt_substrate(memory_controller, calibration_samples,
                    config: AdaptationConfig, dim=64):
    """Adapt a candidate's trainable substrate on the calibration stream.

    Returns a record dict; the controller's substrate is updated in place.
    Non-trainable substrates (recency/retrieval/hybrid without mamba2)
    return a zero-cost record.
    """
    substrate = getattr(memory_controller, "substrate", None)
    if substrate is None:
        return {"trainable": False, "pre_loss": None, "post_loss": None,
                "steps": 0, "wall_time_sec": 0.0, "trainable_params": 0}

    torch.manual_seed(config.seed)  # identical optimizer trajectory per budget
    embeddings = _calibration_embeddings(
        calibration_samples[: config.calibration_samples], dim)
    windows = [
        embeddings[i:i + config.sequence_window + 1]
        for i in range(0, len(embeddings) - config.sequence_window,
                       config.sequence_window)
    ]

    device = "cuda" if torch.cuda.is_available() else "cpu"
    substrate.to(device)

    with torch.no_grad():
        pre = sum(_sequence_loss(substrate,
                                 [e.to(device) for e in w], 0).item()
                  for w in windows) / max(1, len(windows))

    opt = torch.optim.AdamW(substrate.parameters(),
                            lr=config.learning_rate,
                            weight_decay=config.weight_decay)
    start = time.time()
    step = 0
    for step in range(config.adaptation_steps):
        window = [e.to(device) for e in windows[step % len(windows)]]
        seq = torch.stack(window).unsqueeze(0)
        out = substrate.forward_sequence(seq)
        loss = torch.nn.functional.mse_loss(out[:, :-1], seq[:, 1:])
        opt.zero_grad()
        loss.backward()
        opt.step()
    wall_time = time.time() - start

    with torch.no_grad():
        post = sum(_sequence_loss(substrate,
                                  [e.to(device) for e in w], 0).item()
                   for w in windows) / max(1, len(windows))

    substrate.to("cpu")
    # Weights changed: any cached memory state is now stale.
    if hasattr(memory_controller, "invalidate_state_cache"):
        memory_controller.invalidate_state_cache()
    return {
        "trainable": True,
        "pre_loss": pre,
        "post_loss": post,
        "steps": config.adaptation_steps,
        "wall_time_sec": wall_time,
        "trainable_params": sum(p.numel() for p in substrate.parameters()),
    }
