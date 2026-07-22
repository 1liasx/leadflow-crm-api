COMPANY_PAYLOAD = {
    "industry": "Technology",
}

LEAD_PAYLOAD = {
    "title": "Automatisation du traitement des leads",
    "description": "Intégration n8n et FastAPI",
    "status": "new",
    "source": "LinkedIn",
    "estimated_value": 8000,
    "currency": "MAD",
}


def create_company(client, name="Atlas Digital"):
    payload = {
        **COMPANY_PAYLOAD,
        "name": name,
    }

    response = client.post("/companies", json=payload)

    return response.json()["id"]


def create_contact(client, company_id):
    payload = {
        "company_id": company_id,
        "first_name": "Sara",
        "last_name": "Amrani",
        "email": "sara@example.com",
    }

    response = client.post("/contacts", json=payload)

    return response.json()["id"]


def create_lead(client, company_id, contact_id=None):
    payload = {
        **LEAD_PAYLOAD,
        "company_id": company_id,
        "contact_id": contact_id,
    }

    return client.post("/leads", json=payload)


def test_create_lead(client):
    company_id = create_company(client)
    contact_id = create_contact(client, company_id)

    response = create_lead(
        client,
        company_id,
        contact_id,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["company_id"] == company_id
    assert data["contact_id"] == contact_id
    assert data["status"] == "new"
    assert data["currency"] == "MAD"


def test_reject_unknown_company(client):
    response = create_lead(
        client,
        company_id=999,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Company not found."


def test_reject_contact_from_another_company(client):
    first_company_id = create_company(
        client,
        name="Atlas Digital",
    )

    second_company_id = create_company(
        client,
        name="RiadFlow",
    )

    contact_id = create_contact(
        client,
        first_company_id,
    )

    response = create_lead(
        client,
        second_company_id,
        contact_id,
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "The contact does not belong to this company."
    )


def test_list_filter_and_update_lead(client):
    company_id = create_company(client)

    create_response = create_lead(
        client,
        company_id,
    )

    lead_id = create_response.json()["id"]

    list_response = client.get(
        "/leads",
        params={
            "company_id": company_id,
            "status": "new",
        },
    )

    update_response = client.patch(
        f"/leads/{lead_id}",
        json={
            "status": "qualified",
            "estimated_value": 10000,
        },
    )

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    assert update_response.status_code == 200
    assert update_response.json()["status"] == "qualified"


def test_deleting_contact_preserves_lead(client):
    company_id = create_company(client)
    contact_id = create_contact(client, company_id)

    lead_response = create_lead(
        client,
        company_id,
        contact_id,
    )

    lead_id = lead_response.json()["id"]

    delete_response = client.delete(
        f"/contacts/{contact_id}"
    )

    get_response = client.get(
        f"/leads/{lead_id}"
    )

    assert delete_response.status_code == 204
    assert get_response.status_code == 200
    assert get_response.json()["contact_id"] is None


def test_company_with_lead_cannot_be_deleted(client):
    company_id = create_company(client)

    lead_response = create_lead(
        client,
        company_id,
    )

    lead_id = lead_response.json()["id"]

    blocked_response = client.delete(
        f"/companies/{company_id}"
    )

    delete_lead_response = client.delete(
        f"/leads/{lead_id}"
    )

    delete_company_response = client.delete(
        f"/companies/{company_id}"
    )

    assert blocked_response.status_code == 409
    assert delete_lead_response.status_code == 204
    assert delete_company_response.status_code == 204