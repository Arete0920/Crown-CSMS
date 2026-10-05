"""Closed, opt-in OpenAI transport for maintained generic adult guidance."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from urllib.parse import urlsplit

from django.conf import settings
import redis
import requests

from .assistance_catalog import ASSISTANCE, CATALOG_VERSION
from .guidance import GUIDANCE, POLICY_VERSION, build_external_payload, local_guidance

ENDPOINT = "https://api.openai.com/v1/responses"
MAX_RESPONSE_BYTES = 65536
MAX_OUTPUT_TOKENS = 1024
PROVIDER_POLICY_VERSION = "solomon-provider-v1"
FIELDS = {"title", "guidance", "steps", "draft"}
SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "title": {"type": "string"}, "guidance": {"type": "string"},
        "steps": {"type": "array", "items": {"type": "string"}},
        "draft": {"type": "string"},
    },
    "required": sorted(FIELDS),
}
INSTRUCTIONS = (
    "Prepare a general adult-facing CROWN draft using only the supplied maintained source. "
    "Explain or reword its checklist and template. Preserve placeholders. Do not invent school "
    "facts, citations, dates, legal or medical conclusions, or individual profiles. Do not make "
    "admissions, grading, discipline, health, financial aid, pastoral or other consequential "
    "decisions. School-specific strategy belongs to school leadership and Arete Advisory Group. "
    "The result requires human verification and is not an instruction to act."
)
QUOTA_SCRIPT = """
local count = tonumber(redis.call('GET', KEYS[1]) or '0')
if count >= tonumber(ARGV[1]) then return 0 end
local next = redis.call('INCR', KEYS[1])
if next == 1 then redis.call('EXPIRE', KEYS[1], 90000) end
return 1
"""


class ProviderUnavailable(Exception):
    """A generic failure boundary; never expose vendor responses or credentials."""


def release_fingerprint(model, limit):
    material = {
        "model": model, "daily_limit": limit, "policy": POLICY_VERSION,
        "provider_policy": PROVIDER_POLICY_VERSION, "catalog": CATALOG_VERSION,
        "guidance": dict(GUIDANCE), "resources": dict(ASSISTANCE),
        "endpoint": ENDPOINT, "output_cap": MAX_OUTPUT_TOKENS,
        "schema": SCHEMA, "instructions": INSTRUCTIONS,
    }
    return sha256(json.dumps(material, sort_keys=True).encode("utf-8")).hexdigest()


def release_configuration():
    if (getattr(settings, "CROWN_SOLOMON_EXTERNAL_ENABLED", False) is not True
            or getattr(settings, "CROWN_SOLOMON_RELEASE_APPROVED", False) is not True):
        raise ProviderUnavailable
    for name in ("CONTRACT", "RETENTION", "EVALUATION", "BUDGET", "CORPUS"):
        reference = getattr(settings, f"CROWN_SOLOMON_{name}_REVIEW_REF", "")
        if type(reference) is not str or not reference.strip():
            raise ProviderUnavailable
    config = {
        "model": getattr(settings, "CROWN_SOLOMON_MODEL", ""),
        "key": getattr(settings, "OPENAI_API_KEY", ""),
        "namespace": getattr(settings, "CROWN_SOLOMON_QUOTA_NAMESPACE", ""),
        "limit": getattr(settings, "CROWN_SOLOMON_DAILY_REQUEST_LIMIT", 0),
        "quota_url": getattr(settings, "CROWN_SOLOMON_QUOTA_REDIS_URL", ""),
    }
    if (type(config["model"]) is not str
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}", config["model"])
            or type(config["key"]) is not str or not config["key"]
            or any(character.isspace() for character in config["key"])
            or type(config["namespace"]) is not str
            or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", config["namespace"])
            or type(config["limit"]) is not int or not 1 <= config["limit"] <= 1000):
        raise ProviderUnavailable
    try:
        url = urlsplit(config["quota_url"])
        if url.scheme != "rediss" or not url.hostname or url.query or url.fragment:
            raise ProviderUnavailable
    except (ValueError, TypeError):
        raise ProviderUnavailable from None
    if getattr(settings, "CROWN_SOLOMON_RELEASE_FINGERPRINT", "") != release_fingerprint(config["model"], config["limit"]):
        raise ProviderUnavailable
    return config


def build_request(selection, model):
    approved = build_external_payload(selection)
    resource = local_guidance(selection)
    source = {**approved["source"], "steps": resource["steps"], "draft": resource["draft"]}
    body = {
        "model": model, "store": False, "background": False, "stream": False,
        "tools": [], "tool_choice": "none", "max_output_tokens": MAX_OUTPUT_TOKENS,
        "instructions": INSTRUCTIONS,
        "input": json.dumps({"topic": approved["topic"], "source": source}, ensure_ascii=False),
        "text": {"format": {"type": "json_schema", "name": "solomon_assistance",
                            "strict": True, "schema": SCHEMA}},
    }
    if len(json.dumps(body).encode("utf-8")) > 16384:
        raise ProviderUnavailable
    return body


def reserve_request(config):
    connection = None
    try:
        connection = redis.Redis.from_url(
            config["quota_url"], ssl_cert_reqs="required",
            socket_connect_timeout=2, socket_timeout=2,
        )
        day = datetime.now(timezone.utc).date().isoformat()
        key = f"solomon:external:{config['namespace']}:{day}"
        if connection.eval(QUOTA_SCRIPT, 1, key, config["limit"]) != 1:
            raise ProviderUnavailable
    except Exception:
        raise ProviderUnavailable from None
    finally:
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass


def send_request(body, key):
    try:
        with requests.Session() as session:
            session.trust_env = False
            with session.post(
                ENDPOINT, json=body, headers={"Authorization": f"Bearer {key}"},
                timeout=(3, 10), allow_redirects=False, stream=True, verify=True,
            ) as response:
                if response.status_code != 200 or not response.headers.get("Content-Type", "").startswith("application/json"):
                    raise ProviderUnavailable
                raw = response.raw.read(MAX_RESPONSE_BYTES + 1, decode_content=True)
                if len(raw) > MAX_RESPONSE_BYTES:
                    raise ProviderUnavailable
                return json.loads(raw.decode("utf-8"))
    except Exception:
        raise ProviderUnavailable from None


def validate_result(response):
    try:
        if response.get("status") != "completed" or response.get("error") or response.get("incomplete_details"):
            raise ValueError
        texts = []
        for item in response["output"]:
            if item.get("type") == "reasoning":
                continue
            if item.get("type") != "message" or item.get("role") != "assistant":
                raise ValueError
            for content in item["content"]:
                if content.get("type") != "output_text":
                    raise ValueError
                texts.append(content["text"])
        if len(texts) != 1 or type(texts[0]) is not str or len(texts[0]) > 10000:
            raise ValueError
        data = json.loads(texts[0])
        if type(data) is not dict or set(data) != FIELDS:
            raise ValueError
        for field, maximum in (("title", 150), ("guidance", 2400), ("draft", 5000)):
            if type(data[field]) is not str or len(data[field]) > maximum:
                raise ValueError
        if not data["title"].strip() or not data["guidance"].strip():
            raise ValueError
        if (type(data["steps"]) is not list or len(data["steps"]) > 6
                or any(type(step) is not str or not step.strip() or len(step) > 300 for step in data["steps"])):
            raise ValueError
        return data
    except (KeyError, TypeError, ValueError, AttributeError):
        raise ProviderUnavailable from None


def generate(selection, config):
    body = build_request(selection, config["model"])
    # Reservations are not refunded: an interrupted request may still incur cost.
    reserve_request(config)
    return validate_result(send_request(body, config["key"]))
