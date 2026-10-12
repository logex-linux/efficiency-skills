#!/usr/bin/env python3
"""Offline, structured decisions using the installed Nox 4B MLX model."""

import argparse
import contextlib
import json
import os
from pathlib import Path
import sys
import time

RUNTIME = Path("/Users/linnx/Documents/开发/quick-decision")
PYTHON = RUNTIME / ".venv/bin/python"
MODEL = RUNTIME / "models/Decision-2.0-Nox-4B-MLX-4bit"


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False))


def validate(request):
    if not isinstance(request, dict) or set(request) != {"state", "questions"}:
        raise ValueError("Each request must contain exactly state and questions")
    state, questions = request["state"], request["questions"]
    if not isinstance(state, (str, dict, list)) or state in ("", {}, []):
        raise ValueError("state must be nonempty text, an object, or an array")
    if not isinstance(questions, dict) or not questions:
        raise ValueError("questions must be a nonempty object")
    for qid, question in questions.items():
        if not isinstance(qid, str) or not qid:
            raise ValueError("Question IDs must be nonempty strings")
        if not isinstance(question, dict):
            raise ValueError(f"{qid}: question must be an object")
        kind = question.get("type")
        if kind not in {"choice", "noul", "score"}:
            raise ValueError(f"{qid}: type must be choice, noul, or score")
        if not isinstance(question.get("instructions"), str) or not question["instructions"].strip():
            raise ValueError(f"{qid}: instructions must be nonempty text")
        criteria = question.get("criteria")
        if kind == "choice":
            if not isinstance(criteria, dict) or not 2 <= len(criteria) <= 255:
                raise ValueError(f"{qid}: choice needs 2..255 described options")
            if any(not k or not isinstance(v, str) or not v.strip() for k, v in criteria.items()):
                raise ValueError(f"{qid}: choice descriptions must be nonempty text")
        elif kind == "score":
            if not isinstance(criteria, list) or not 2 <= len(criteria) <= 10:
                raise ValueError(f"{qid}: score needs 2..10 ordered levels")
            if any(not isinstance(v, str) or not v.strip() for v in criteria):
                raise ValueError(f"{qid}: score levels must be nonempty text")
        elif criteria is not None:
            if not isinstance(criteria, dict) or set(criteria) != {"false", "true"}:
                raise ValueError(f"{qid}: noul criteria must describe false and true")
            if any(not isinstance(v, str) or not v.strip() for v in criteria.values()):
                raise ValueError(f"{qid}: noul descriptions must be nonempty text")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="-", help="Request JSON file, or - for stdin; accepts an array of requests")
    parser.add_argument("--output", type=Path, help="Also save the JSON result to this path")
    parser.add_argument("--check", action="store_true", help="Check installation without loading weights")
    args = parser.parse_args()
    if sys.prefix != str(RUNTIME / ".venv"):
        if not PYTHON.is_file():
            raise FileNotFoundError(f"Local Python environment is missing: {PYTHON}")
        os.execv(str(PYTHON), [str(PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]])
    # Set before importing libraries: all inference reads local files only.
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["DECISION_PREFIX_CACHE"] = "0"
    os.environ["DECISION_BATCH_TOKENS"] = "4096"
    needed = ["mlx_decision.py", "config.json", "model.safetensors", "tokenizer.json",
              "decision/decision_head.safetensors", "decision/tokenizer.json"]
    missing = [name for name in needed if not (MODEL / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Local model files missing: {', '.join(missing)}")
    if args.check:
        from importlib.metadata import version
        import mlx.core as mx
        emit({"status": "ok", "runtime": str(RUNTIME), "model_path": str(MODEL),
              "metal_available": mx.metal.is_available(),
              "versions": {p: version(p) for p in ["mlx", "mlx-lm", "torch", "transformers"]},
              "source": json.loads((RUNTIME / "model-source.json").read_text())})
        return 0
    text = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
    payload = json.loads(text, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"Invalid JSON constant: {value}")))
    requests = payload if isinstance(payload, list) else [payload]
    if not requests:
        raise ValueError("Request array must not be empty")
    for request in requests:
        validate(request)
    sys.path.insert(0, str(MODEL))
    with contextlib.redirect_stdout(sys.stderr):
        started = time.perf_counter()
        from mlx_decision import MLXDecision
        import mlx.core as mx
        engine = MLXDecision()
        load_ms = round((time.perf_counter() - started) * 1000, 2)
        outputs = []
        for request in requests:
            started = time.perf_counter()
            answers, tokens = engine.system_one(request["state"], request["questions"])
            outputs.append({"model": engine.name, "backend": "mlx", "quantization_bits": 4,
                            "prefix_cache": False, "answers": answers,
                            "usage": {"input_tokens": tokens, "output_tokens": 0},
                            "timing": {"load_ms": load_ms, "inference_ms": round((time.perf_counter() - started) * 1000, 2)},
                            "mlx_peak_memory_gb": round(mx.get_peak_memory() / 1e9, 3)})
    result = outputs if isinstance(payload, list) else outputs[0]
    if args.output:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    emit(result)
    return 2 if any("error" in a for output in outputs for a in output["answers"].values()) else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
