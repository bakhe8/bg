from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


@dataclass(slots=True)
class LetterModel:
    contractor_name: str
    guarantee_number: str
    amount: str
    bank_name: str
    notes: Optional[str] = None

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "LetterModel":
        return cls(
            contractor_name=str(payload.get("contractor_name", "")).strip(),
            guarantee_number=str(payload.get("guarantee_number", "")).strip(),
            amount=str(payload.get("amount", "")).strip(),
            bank_name=str(payload.get("bank_name", "")).strip(),
            notes=payload.get("notes"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class BankModel:
    name: str
    address: str = ""
    email: str = ""
    phone: str | None = None

    @classmethod
    def from_mapping(cls, mapping: Dict[str, Any]) -> "BankModel":
        return cls(
            name=str(mapping.get("arabic") or mapping.get("name") or "").strip(),
            address=str(mapping.get("address", "")).strip(),
            email=str(mapping.get("email", "")).strip(),
            phone=(mapping.get("phone") or None),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


__all__ = ["LetterModel", "BankModel"]
