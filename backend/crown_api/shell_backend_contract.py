"""Shell/backend wizard contract declarations derived from wizard_registry."""

from __future__ import annotations

from typing import TypedDict

from crown_api.wizard_registry import WIZARDS


class WizardContractRow(TypedDict):
    slug: str
    title: str
    backendUrlPrefix: str
    backendModule: str


def get_backend_wizard_contract_rows() -> list[WizardContractRow]:
    rows: list[WizardContractRow] = []
    for wizard in WIZARDS:
        rows.append(
            {
                "slug": wizard["url_prefix"].split("/")[2],
                "title": wizard["name"],
                "backendUrlPrefix": wizard["url_prefix"],
                "backendModule": wizard["urls_module"],
            }
        )
    rows.sort(key=lambda row: row["slug"])
    return rows
