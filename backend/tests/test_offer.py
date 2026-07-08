"""Offer page application intake."""
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from backend.app.models.offer import OfferInquiry


def test_offer_inquiry_persists(client: TestClient, session: Session):
    r = client.post("/api/offer/inquiry", json={
        "full_name": "Jordan Lee",
        "email": "jordan@meridian.co",
        "company": "Meridian Growth Co.",
        "revenue_band": "₹5L–10L/mo",
        "primary_worry": "Referrals unpredictable",
        "message": "6-person agency",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["id"] >= 1
    assert "received" in data["message"].lower()

    row = session.exec(select(OfferInquiry).where(OfferInquiry.email == "jordan@meridian.co")).first()
    assert row is not None
    assert row.company == "Meridian Growth Co."
    assert row.revenue_band == "₹5L–10L/mo"


def test_offer_inquiry_rejects_empty_name(client: TestClient):
    r = client.post("/api/offer/inquiry", json={
        "full_name": "  ",
        "email": "a@b.co",
        "company": "Acme",
    })
    assert r.status_code == 422


def test_offer_inquiry_rejects_invalid_band(client: TestClient):
    r = client.post("/api/offer/inquiry", json={
        "full_name": "Test",
        "email": "a@b.co",
        "company": "Acme",
        "revenue_band": "₹999/mo",
    })
    assert r.status_code == 422


def test_spa_serves_offer_route(client: TestClient):
    r = client.get("/offer")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]