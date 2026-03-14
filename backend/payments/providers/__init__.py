from .compuwerx import CompuwerxGateway
from .stripe_connect import StripeConnect


def get_gateway(provider_code: str):
	if provider_code == "compuwerx":
		return CompuwerxGateway()
	raise ValueError(f"Unsupported payment gateway provider: {provider_code}")


__all__ = ["CompuwerxGateway", "StripeConnect", "get_gateway"]
