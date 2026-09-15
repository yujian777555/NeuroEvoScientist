"""Pluggable inference backends for real benchmark evaluation (Phase-14).

A backend is any callable ``(prompt: str, genome) -> str``. Backends never
fabricate scores — they only wrap real model inference.

Recommended first model for A800 experiments: Qwen/Qwen2.5-1.5B-Instruct
(low cost, fast iteration, easy scaling to larger sizes later).

Requirements (A800 environment): torch>=2.1, transformers>=4.40.
The Phase-12/13 dev box (torch 1.10 / transformers 4.29) cannot load
Qwen2.5 — use the scripted/mock backends there.
"""

import os

# Model families whose checkpoints expect a chat template.
_CHAT_MODEL_HINTS = ("instruct", "chat")


class HFTransformersBackend:
    """Lazy Hugging Face text-generation backend (real inference).

    Args:
        model_name:     HF hub id or local path.
        max_new_tokens: generation cap per prompt.
        device:         -1 for CPU, or GPU index / "auto" device map.
        use_chat_template: force chat-template wrapping; default auto-detects
                        Instruct/Chat models and applies tokenizer template.
    """

    def __init__(self, model_name, max_new_tokens=256, device=-1,
                 use_chat_template=None, batch_size=16):
        self.model_name = model_name
        self.max_new_tokens = max_new_tokens
        self.device = device
        self.batch_size = batch_size
        if use_chat_template is None:
            name = os.path.basename(str(model_name)).lower()
            use_chat_template = any(h in name for h in _CHAT_MODEL_HINTS)
        self.use_chat_template = use_chat_template
        self._pipe = None
        self._tokenizer = None

    def _load(self):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        use_cuda = torch.cuda.is_available() and self.device != -1
        dtype = torch.float16 if use_cuda else torch.float32
        device_map = "auto" if (use_cuda and str(self.device) == "auto") else None
        # transformers>=5 renamed torch_dtype -> dtype; stay compatible.
        try:
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name, dtype=dtype, device_map=device_map)
        except TypeError:
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name, torch_dtype=dtype, device_map=device_map)
        if device_map is None and use_cuda:
            target = "cuda:0" if str(self.device) == "auto" \
                else "cuda:%d" % int(self.device)
            model = model.to(target)
        self._pipe = model

    def _format_prompt(self, prompt):
        if (self.use_chat_template and self._tokenizer is not None
                and getattr(self._tokenizer, "chat_template", None)):
            messages = [{"role": "user", "content": prompt}]
            return self._tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True)
        return prompt

    def __call__(self, prompt, genome):
        return self.batch_generate([prompt], genome)[0]

    def batch_generate(self, prompts, genome, batch_size=None):
        """Batched real inference (left-padded). ~20-40x faster than
        per-prompt generation for benchmark evaluation."""
        if self._pipe is None:
            self._load()
        batch_size = batch_size or self.batch_size
        tok = self._tokenizer
        if tok.pad_token_id is None:
            tok.pad_token = tok.eos_token
        old_padding_side = tok.padding_side
        tok.padding_side = "left"

        outputs = []
        try:
            for i in range(0, len(prompts), batch_size):
                chunk = [self._format_prompt(p)
                         for p in prompts[i:i + batch_size]]
                inputs = tok(chunk, return_tensors="pt", padding=True).to(
                    self._pipe.device)
                out = self._pipe.generate(
                    **inputs,
                    max_new_tokens=self.max_new_tokens,
                    do_sample=False,
                    pad_token_id=tok.pad_token_id,
                )
                generated = out[:, inputs["input_ids"].shape[1]:]
                outputs.extend(
                    tok.decode(row, skip_special_tokens=True)
                    for row in generated
                )
        finally:
            tok.padding_side = old_padding_side
        return outputs


class QwenBackend(HFTransformersBackend):
    """Qwen2.5 backend preset.

    Defaults to a single visible GPU (device=0): on shared multi-GPU boxes,
    pin the card with CUDA_VISIBLE_DEVICES instead of device_map="auto",
    which would spread onto busy neighbors.
    """

    def __init__(self, model_name="Qwen/Qwen2.5-1.5B-Instruct", **kwargs):
        kwargs.setdefault("device", 0)
        super().__init__(model_name, **kwargs)
