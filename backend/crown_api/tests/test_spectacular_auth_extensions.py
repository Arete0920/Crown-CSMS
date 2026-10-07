from crown_api.spectacular_extensions import (
    AADBearerAuthenticationExtension,
    CrownAccessTokenAuthenticationExtension,
)


def test_crown_access_token_authentication_extension_contract():
    extension = CrownAccessTokenAuthenticationExtension()
    assert (
        extension.target_class
        == "crown_api.auth_middleware.CrownAccessTokenAuthentication"
    )
    assert extension.name == "CrownAccessTokenAuthentication"
    definition = extension.get_security_definition(None)
    assert definition["type"] == "http"
    assert definition["scheme"] == "bearer"
    assert "CROWN" in definition["bearerFormat"]


def test_aad_extension_remains_registered():
    extension = AADBearerAuthenticationExtension()
    assert extension.target_class == "core.auth.authentication.AADBearerAuthentication"
    assert extension.name == "AADBearerAuthentication"
