import json
from typing import Any


def _extract_first_json_object(text: str) -> str:
    start_index = text.find("{")
    if start_index == -1:
        raise ValueError("No JSON object found in response.")

    depth = 0
    for index in range(start_index, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start_index : index + 1]

    raise ValueError("Could not find the end of the JSON object.")


def parse_json_response(raw_text: str) -> Any:
    if not raw_text:
        raise ValueError("Empty LLM response.")

    normalized = raw_text.strip()
    if normalized.startswith("```"):
        normalized = normalized.strip("`")
        if normalized.lower().startswith("json"):
            normalized = normalized[4:].strip()

    try:
        return json.loads(normalized)
    except json.JSONDecodeError:
        json_slice = _extract_first_json_object(normalized)
        return json.loads(json_slice)
