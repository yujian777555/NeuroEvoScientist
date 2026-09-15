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
                 use_chat_template=None):
        self.model_name = model_name
        self.max_new_tokens = max_new_tokens
        self.device = device
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
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        device_map = "auto" if self.device == "auto" else None
        model = AutoModelForCausalLM.from_pretrained(
            self.model_name, torch_dtype=dtype, device_map=device_map)
        if device_map is None and isinstance(self.device, int) \
                and self.device >= 0 and torch.cuda.is_available():
            model = model.to("cuda:%d" % self.device)
        self._pipe = model

    def _format_prompt(self, prompt):
        if (self.use_chat_template and self._tokenizer is not None
                and getattr(self._tokenizer, "chat_template", None)):
            messages = [{"role": "user", "content": prompt}]
            return self._tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True)
        return prompt

    def __call__(self, prompt, genome):
        if self._pipe is None:
            self._load()
        text = self._format_prompt(prompt)
        inputs = self._tokenizer(text, return_tensors="pt").to(
            self._pipe.device)
        out = self._pipe.generate(
            **inputs,
            max_new_tokens=self.max_new_tokens,
            do_sample=False,
            pad_token_id=self._tokenizer.eos_token_id,
        )
        generated = out[0][inputs["input_ids"].shape[1]:]
        return self._tokenizer.decode(generated, skip_special_tokens=True)


class QwenBackend(HFTransformersBackend):
    """Qwen2.5 backend preset (A800 default)."""

    def __init__(self, model_name="Qwen/Qwen2.5-1.5B-Instruct", **kwargs):
        kwargs.setdefault("device", "auto")
        super().__init__(model_name, **kwargs)
