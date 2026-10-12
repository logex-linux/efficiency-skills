#!/usr/bin/env python3
"""Send one typed judgment request to Jev through OpenRouter."""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


ENDPOINT = "https://openrouter.ai/api/alpha/decisions"
DEFAULT_MODEL = "~typesafe/jev-latest"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    api_key = os.environ.get("OPRT_API_KEY")
    if not api_key:
        parser.error("OPRT_API_KEY is not set in this shell")

    try:
        request_data = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        parser.error("stdin must contain valid JSON: {}".format(exc.msg))

    if not isinstance(request_data, dict) or "state" not in request_data:
        parser.error("JSON input must be an object with a state field")
    questions = request_data.get("questions")
    if not isinstance(questions, dict) or not questions:
        parser.error("JSON input must include a non-empty questions object")

    payload = {
        "model": args.model,
        "state": request_data["state"],
        "questions": questions,
    }
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        parser.error("OpenRouter returned HTTP {}".format(exc.code))
    except urllib.error.URLError:
        parser.error("Could not reach OpenRouter")
    except json.JSONDecodeError:
        parser.error("OpenRouter returned an invalid JSON response")

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
