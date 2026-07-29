"""Evidências produzidas fora do motor computacional."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")


@dataclass(frozen=True, slots=True)
class ExternalEvidence:
    document_id: str
    revision: str
    responsible_engineer: str
    professional_registration: str
    date: date
    file_hash: str
    checked_items: tuple[str, ...]

    def __post_init__(self) -> None:
        required = {
            "document_id": self.document_id,
            "revision": self.revision,
            "responsible_engineer": self.responsible_engineer,
            "professional_registration": self.professional_registration,
        }
        missing = [name for name, value in required.items() if not value.strip()]
        if missing:
            raise ValueError(f"Campos obrigatórios vazios: {', '.join(missing)}.")
        if not _SHA256.fullmatch(self.file_hash):
            raise ValueError("file_hash deve ser um SHA-256 hexadecimal com 64 caracteres.")
        if not self.checked_items or any(not item.strip() for item in self.checked_items):
            raise ValueError("checked_items deve identificar ao menos uma verificação.")

