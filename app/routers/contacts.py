from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.company import Company
from app.models.contact import Contact
from app.schemas.contact import ContactCreate, ContactRead, ContactUpdate


router = APIRouter(
    prefix="/contacts",
    tags=["Contacts"],
)


@router.post(
    "",
    response_model=ContactRead,
    status_code=status.HTTP_201_CREATED,
)
def create_contact(
    contact_data: ContactCreate,
    db: Session = Depends(get_db),
):
    company = db.get(Company, contact_data.company_id)

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found.",
        )

    normalized_email = str(contact_data.email).lower()

    existing_contact = db.scalar(
        select(Contact).where(Contact.email == normalized_email)
    )

    if existing_contact:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A contact with this email already exists.",
        )

    contact_values = contact_data.model_dump()
    contact_values["email"] = normalized_email

    contact = Contact(**contact_values)
    db.add(contact)

    try:
        db.commit()
        db.refresh(contact)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to create the contact.",
        ) from error

    return contact
@router.get("", response_model=list[ContactRead])
def list_contacts(
    company_id: int | None = Query(default=None, gt=0),
    email: str | None = Query(default=None, min_length=3),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    statement = select(Contact).order_by(Contact.id)

    if company_id is not None:
        statement = statement.where(Contact.company_id == company_id)

    if email is not None:
        normalized_email = email.strip().lower()
        statement = statement.where(
            func.lower(Contact.email) == normalized_email
        )

    statement = statement.offset(offset).limit(limit)

    return db.scalars(statement).all()
@router.get("/{contact_id}", response_model=ContactRead)
def get_contact(
    contact_id: int,
    db: Session = Depends(get_db),
):
    contact = db.get(Contact, contact_id)

    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found.",
        )

    return contact
@router.patch("/{contact_id}", response_model=ContactRead)
def update_contact(
    contact_id: int,
    contact_data: ContactUpdate,
    db: Session = Depends(get_db),
):
    contact = db.get(Contact, contact_id)

    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found.",
        )

    update_data = contact_data.model_dump(exclude_unset=True)

    required_fields = {
        "company_id",
        "first_name",
        "last_name",
        "email",
    }

    for field in required_fields:
        if field in update_data and update_data[field] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{field} cannot be null.",
            )

    if "company_id" in update_data:
        company = db.get(Company, update_data["company_id"])

        if company is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found.",
            )

    if "email" in update_data:
        normalized_email = str(update_data["email"]).lower()
        update_data["email"] = normalized_email

        existing_contact = db.scalar(
            select(Contact).where(
                Contact.email == normalized_email,
                Contact.id != contact_id,
            )
        )

        if existing_contact:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A contact with this email already exists.",
            )

    for field, value in update_data.items():
        setattr(contact, field, value)

    try:
        db.commit()
        db.refresh(contact)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to update the contact.",
        ) from error

    return contact
@router.delete(
    "/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
):
    contact = db.get(Contact, contact_id)

    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found.",
        )

    db.delete(contact)

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contact cannot be deleted because it has linked records.",
        ) from error