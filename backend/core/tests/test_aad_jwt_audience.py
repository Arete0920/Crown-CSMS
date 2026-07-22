from unittest.mock import patch

import pytest
from django.test import override_settings

jwt = pytest.importorskip("jwt")

from core.auth.aad_jwt import decode_and_validate_bearer


@pytest.mark.parametrize("audience", ["", "   ", None])
def test_decode_rejects_missing_server_audience_configuration_before_jwks(settings, audience):
    settings.AAD_TENANT_ID = "tenant-id"
    settings.AAD_API_AUDIENCE = audience

    with patch("core.auth.aad_jwt._get_jwks") as jwks_mock:
        with pytest.raises(ValueError, match="AAD_API_AUDIENCE is not configured"):
            decode_and_validate_bearer("token")

    jwks_mock.assert_not_called()


@override_settings(AAD_TENANT_ID="", AAD_API_AUDIENCE="api://crown")
@patch("core.auth.aad_jwt._get_jwks")
def test_decode_rejects_missing_tenant_configuration_before_jwks(jwks_mock):
    with pytest.raises(ValueError, match="AAD_TENANT_ID is not configured"):
        decode_and_validate_bearer("token")
    jwks_mock.assert_not_called()


@override_settings(AAD_TENANT_ID="  tenant-id  ", AAD_API_AUDIENCE="api://crown")
@patch("core.auth.aad_jwt._get_jwks", return_value={"keys": [{"kid": "key-1"}]})
@patch("jwt.get_unverified_header", return_value={"kid": "key-1"})
@patch("jwt.algorithms.RSAAlgorithm.from_jwk", return_value="public-key")
@patch("jwt.decode", return_value={"aud": "api://crown", "sub": "user"})
def test_decode_uses_normalized_tenant_for_jwks_and_issuer(
    decode_mock,
    _from_jwk,
    _header,
    jwks_mock,
):
    claims = decode_and_validate_bearer("token")

    assert claims["sub"] == "user"
    jwks_mock.assert_called_once_with("tenant-id")
    decode_mock.assert_called_once_with(
        "token",
        key="public-key",
        algorithms=["RS256"],
        audience="api://crown",
        issuer="https://login.microsoftonline.com/tenant-id/v2.0",
        options={"verify_exp": True, "verify_aud": True},
    )


@override_settings(AAD_TENANT_ID="tenant-id", AAD_API_AUDIENCE="api://crown")
@patch("core.auth.aad_jwt._get_jwks", return_value={"keys": [{"kid": "key-1"}]})
@patch("jwt.get_unverified_header", return_value={"kid": "key-1"})
@patch("jwt.algorithms.RSAAlgorithm.from_jwk", return_value="public-key")
@patch("jwt.decode", return_value={"aud": "api://crown", "sub": "user"})
def test_decode_requires_exact_configured_audience(
    decode_mock,
    _from_jwk,
    _header,
    _jwks,
):
    claims = decode_and_validate_bearer("token")

    assert claims["aud"] == "api://crown"
    decode_mock.assert_called_once_with(
        "token",
        key="public-key",
        algorithms=["RS256"],
        audience="api://crown",
        issuer="https://login.microsoftonline.com/tenant-id/v2.0",
        options={"verify_exp": True, "verify_aud": True},
    )


@override_settings(AAD_TENANT_ID="tenant-id", AAD_API_AUDIENCE="api://crown")
@patch("core.auth.aad_jwt._get_jwks", return_value={"keys": [{"kid": "key-1"}]})
@patch("jwt.get_unverified_header", return_value={"kid": "key-1"})
@patch("jwt.algorithms.RSAAlgorithm.from_jwk", return_value="public-key")
@patch("jwt.decode", side_effect=jwt.InvalidAudienceError("Audience doesn't match"))
def test_decode_rejects_foreign_audience(
    _decode,
    _from_jwk,
    _header,
    _jwks,
):
    with pytest.raises(jwt.InvalidAudienceError):
        decode_and_validate_bearer("token")


@override_settings(AAD_TENANT_ID="tenant-id", AAD_API_AUDIENCE="api://crown")
@patch("core.auth.aad_jwt._get_jwks", return_value={"keys": [{"kid": "key-1"}]})
@patch("jwt.get_unverified_header", return_value={"kid": "key-1"})
@patch("jwt.algorithms.RSAAlgorithm.from_jwk", return_value="public-key")
@patch("jwt.decode", side_effect=jwt.MissingRequiredClaimError("aud"))
def test_decode_rejects_missing_audience_claim(
    _decode,
    _from_jwk,
    _header,
    _jwks,
):
    with pytest.raises(jwt.MissingRequiredClaimError):
        decode_and_validate_bearer("token")


@override_settings(AAD_TENANT_ID="tenant-id", AAD_API_AUDIENCE="api://crown")
@patch("core.auth.aad_jwt._get_jwks", return_value={"keys": [{"kid": "key-1"}]})
@patch("jwt.get_unverified_header", return_value={"kid": "key-1"})
@patch("jwt.algorithms.RSAAlgorithm.from_jwk", return_value="public-key")
@patch("jwt.decode", side_effect=jwt.InvalidIssuerError("Invalid issuer"))
def test_decode_rejects_foreign_issuer(
    _decode,
    _from_jwk,
    _header,
    _jwks,
):
    with pytest.raises(jwt.InvalidIssuerError):
        decode_and_validate_bearer("token")
