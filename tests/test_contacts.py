COMPANY_PAYLOAD = {
    "name": "Atlas Digital",
    "industry": "Technology",
}

CONTACT_PAYLOAD = {
    "first_name": "Sara",
    "last_name": "Amrani",
    "email": "sara@example.com",
    "phone": "+212611111111",
    "job_title": "Operations Manager",
}


def create_company(client):
    response = client.post(
        "/companies",
        json=COMPANY_PAYLOAD,
    )

    return response.json()["id"]


def create_contact(client, company_id):
    payload = {
        **CONTACT_PAYLOAD,
        "company_id": company_id,
    }

    return client.post("/contacts", json=payload)


def test_create_contact(client):
    company_id = create_company(client)

    response = create_contact(client, company_id)

    assert response.status_code == 201

    data = response.json()

    assert data["first_name"] == "Sara"
    assert data["company_id"] == company_id
    assert data["email"] == "sara@example.com"


def test_reject_unknown_company(client):
    payload = {
        **CONTACT_PAYLOAD,
        "company_id": 999,
    }

    response = client.post("/contacts", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Company not found."


def test_reject_duplicate_email(client):
    company_id = create_company(client)

    create_contact(client, company_id)

    duplicate_payload = {
        **CONTACT_PAYLOAD,
        "company_id": company_id,
        "email": "SARA@EXAMPLE.COM",
    }

    response = client.post(
        "/contacts",
        json=duplicate_payload,
    )

    assert response.status_code == 409


def test_list_filter_and_update_contact(client):
    company_id = create_company(client)

    create_response = create_contact(client, company_id)
    contact_id = create_response.json()["id"]

    list_response = client.get(
        "/contacts",
        params={"company_id": company_id},
    )

    update_response = client.patch(
        f"/contacts/{contact_id}",
        json={"job_title": "AI Automation Manager"},
    )

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    assert update_response.status_code == 200
    assert update_response.json()["job_title"] == (
        "AI Automation Manager"
    )


def test_company_with_contact_cannot_be_deleted(client):
    company_id = create_company(client)
    create_contact(client, company_id)

    response = client.delete(
        f"/companies/{company_id}"
    )

    assert response.status_code == 409


def test_delete_contact_then_company(client):
    company_id = create_company(client)

    contact_response = create_contact(client, company_id)
    contact_id = contact_response.json()["id"]

    delete_contact_response = client.delete(
        f"/contacts/{contact_id}"
    )

    delete_company_response = client.delete(
        f"/companies/{company_id}"
    )

    assert delete_contact_response.status_code == 204
    assert delete_company_response.status_code == 204