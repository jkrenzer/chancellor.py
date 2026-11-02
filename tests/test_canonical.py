"""Canonicalization and digest form (0.1.0:D0006)."""

from decimal import Decimal

import pytest

from chancellor.canonical import (
    PREFIX,
    canonical_bytes,
    digest_of,
    is_current,
    normalize,
)


def test_key_order_does_not_matter() -> None:
    assert canonical_bytes({"b": 1, "a": [1, 2]}) == canonical_bytes(
        {"a": [1, 2], "b": 1}
    )


def test_crlf_and_cr_hash_like_lf() -> None:
    assert digest_of({"t": "a\r\nb\rc"}) == digest_of({"t": "a\nb\nc"})


def test_nfc_normalization() -> None:
    decomposed = "Mu\u0308nchen"
    assert digest_of(decomposed) == digest_of("M\u00fcnchen")


def test_trailing_whitespace_is_kept() -> None:
    assert digest_of("text ") != digest_of("text")
    assert digest_of("line\n") != digest_of("line")


def test_null_is_kept_and_differs_from_absent() -> None:
    assert canonical_bytes({"a": None}) == b'{"a":null}'
    assert digest_of({"a": None}) != digest_of({})


def test_floats_are_refused_unless_allowed() -> None:
    with pytest.raises(TypeError, match="floats"):
        canonical_bytes({"x": [1.5]})
    assert canonical_bytes(1.5, allow_float=True) == b"1.5"


def test_non_json_values_are_refused() -> None:
    with pytest.raises(TypeError):
        normalize({"x": Decimal("1.0")})
    with pytest.raises(TypeError):
        normalize({1: "x"})


def test_jcs_bytes() -> None:
    assert canonical_bytes({"b": True, "a": "ä"}) == '{"a":"ä","b":true}'.encode()


def test_digest_form() -> None:
    value = digest_of({"a": 1})
    assert value.startswith("c1:sha256:") and value.startswith(PREFIX)
    assert len(value) == len(PREFIX) + 64 and value == value.lower()
    assert is_current(value)
    assert not is_current("sha256:" + "0" * 64)
    assert not is_current("c2:sha256:" + "0" * 64)
    assert not is_current(None)
