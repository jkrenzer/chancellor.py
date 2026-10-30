"""Canonical bytes and digests (0.1.0:D0006).

One function makes the bytes behind every digest: record data, the configuration, a model's
emitted JSON Schema and a provider manifest. The bytes are JCS (RFC 8785) produced by
`rfc8785`, over input that is first normalized:

- strings are NFC, and line breaks inside them are LF, so a CRLF checkout cannot move a
  digest; trailing whitespace is kept, so content and digest cannot diverge;
- floats are refused unless the caller allows them, because hashed fields carry integers;
  `Decimal` arrives as a string from a JSON-mode dump;
- nulls are kept, so a key absent with a null default and an explicit null hash alike.

The caller passes the validated dump with defaults filled, never raw parsed YAML.

A digest is written `c1:sha256:<hex>`. The tag names the canonicalization spec; a digest with
another tag is never compared against bytes made under these rules.
"""

import hashlib
import unicodedata
from collections.abc import Mapping, Sequence
from typing import Any

import rfc8785

TAG = "c1"
"""Name of this canonicalization spec; bump it when the rules above change."""

PREFIX = f"{TAG}:sha256:"


def normalize(value: Any, *, allow_float: bool = False, _path: str = "") -> Any:
    """Return `value` with strings in NFC and LF; reject floats and non-JSON types."""
    if isinstance(value, str):
        text = value.replace("\r\n", "\n").replace("\r", "\n")
        return unicodedata.normalize("NFC", text)
    if value is None or isinstance(value, bool | int):
        return value
    if isinstance(value, float):
        if allow_float:
            return value
        raise TypeError(f"{_path or 'value'}: floats are not allowed in hashed data")
    if isinstance(value, Mapping):
        result = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{_path or 'value'}: mapping keys must be strings")
            result[normalize(key)] = normalize(
                item, allow_float=allow_float, _path=f"{_path}.{key}"
            )
        return result
    if isinstance(value, Sequence) and not isinstance(value, bytes | bytearray):
        return [
            normalize(item, allow_float=allow_float, _path=f"{_path}[{index}]")
            for index, item in enumerate(value)
        ]
    raise TypeError(f"{_path or 'value'}: {type(value).__name__} is not JSON data")


def canonical_bytes(value: Any, *, allow_float: bool = False) -> bytes:
    """JCS bytes of normalized `value`."""
    return rfc8785.dumps(normalize(value, allow_float=allow_float))


def digest(data: bytes) -> str:
    """Digest of bytes, written `c1:sha256:<hex>`."""
    return PREFIX + hashlib.sha256(data).hexdigest()


def digest_of(value: Any, *, allow_float: bool = False) -> str:
    """Digest of the canonical bytes of `value`."""
    return digest(canonical_bytes(value, allow_float=allow_float))


def is_current(value: str | None) -> bool:
    """Whether a stored digest was made under this spec and can be compared."""
    return isinstance(value, str) and value.startswith(PREFIX)
