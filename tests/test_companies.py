COMPANY_PAYLOAD = {
    "name": "Atlas Digital",
    "industry": "Technology",
    "website": "https://atlas.example",
    "phone": "+212600000000",
}


def test_create_company(client):
    response = client.post(
        "/companies",
        json=COMPANY_PAYLOAD,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Atlas Digital"
    assert data["industry"] == "Technology"
    assert data["id"] > 0
    assert "created_at" in data


def test_reject_duplicate_company(client):
    client.post("/companies", json=COMPANY_PAYLOAD)

    response = client.post(
        "/companies",
        json=COMPANY_PAYLOAD,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "A company with this name already exists."
    )


def test_list_and_get_company(client):
    create_response = client.post(
        "/companies",
        json=COMPANY_PAYLOAD,
    )

    company_id = create_response.json()["id"]

    list_response = client.get("/companies")
    get_response = client.get(f"/companies/{company_id}")

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Atlas Digital"


def test_update_company(client):
    create_response = client.post(
        "/companies",
        json=COMPANY_PAYLOAD,
    )

    company_id = create_response.json()["id"]

    response = client.patch(
        f"/companies/{company_id}",
        json={"industry": "AI Automation"},
    )

    assert response.status_code == 200
    assert response.json()["industry"] == "AI Automation"
    assert response.json()["name"] == "Atlas Digital"


def test_delete_company(client):
    create_response = client.post(
        "/companies",
        json=COMPANY_PAYLOAD,
    )

    company_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/companies/{company_id}"
    )

    get_response = client.get(
        f"/companies/{company_id}"
    )

    assert delete_response.status_code == 204
    assert get_response.status_code == 404