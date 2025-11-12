from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BankModel:
    name: str
    address: str
    email: str
