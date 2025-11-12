from __future__ import annotations

import json
from pathlib import Path

import pytest

from BGLApp_Refactor.core.config import constants
from BGLApp_Refactor.core.pdf import generator
from BGLApp_Refactor.core.pdf.models import BankModel, LetterModel


def test_letter_model_from_payload():
    payload = {
        "contractor_name": " ACME ",
        "guarantee_number": " G-123 ",
        "amount": "10000",
        "bank_name": "Test Bank",
        "notes": "Hello",
    }
    letter = LetterModel.from_payload(payload)
    assert letter.contractor_name == "ACME"
    assert letter.guarantee_number == "G-123"
    assert letter.notes == "Hello"


def test_build_bank_model(monkeypatch, tmp_path):
    data = [
        {"arabic": "Test Bank", "aliases": ["TB"], "email": "test@example.com"},
    ]
    ref = tmp_path / "banks.json"
    ref.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def fake_loader():
        return json.loads(ref.read_text(encoding="utf-8"))

    monkeypatch.setattr(constants, "get_bank_reference", fake_loader)
    bank = constants.build_bank_model("TB")
    assert isinstance(bank, BankModel)
    assert bank.email == "test@example.com"


def test_build_letter_context_includes_bank(monkeypatch, tmp_path):
    bank_entry = {"arabic": "Test Bank", "aliases": [], "email": "bank@example.com"}
    monkeypatch.setattr(constants, "get_bank_reference", lambda: [bank_entry])
    letter = LetterModel("ACME", "G-1", "1000", "Test Bank")

    context = generator.build_letter_context(letter)
    assert context["bank"]["email"] == "bank@example.com"


def test_render_letter_html_injects_assets(monkeypatch):
    monkeypatch.setattr(constants, "get_bank_reference", lambda: [])
    html = generator.render_letter_html({"bank_name": "Test Bank"})
    assert "AL-Mohanad.ttf" in html
