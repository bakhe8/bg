from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class LetterModel:
    contractor_name: str
    guarantee_number: str
    amount: str
    bank_name: str
    notes: Optional[str] = None
