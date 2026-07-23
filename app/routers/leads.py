from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.company import Company
from app.models.contact import Contact
from app.models.lead import Lead
from app.schemas.lead import LeadCreate, LeadRead, LeadStatus, LeadUpdate


router = APIRouter(
    prefix="/leads",
    tags=["Leads"],
)


@router.post(
    "",
    response_model=LeadRead,
    status_code=status.HTTP_201_CREATED,
)
def create_lead(
    lead_data: LeadCreate,
    db: Session = Depends(get_db),
):
    if lead_data.external_id is not None:
        existing_lead = db.scalar(
            select(Lead).where(
                Lead.external_id == lead_data.external_id
            )
        )

        if existing_lead:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A lead with this external_id already exists.",
            )

    company = db.get(Company, lead_data.company_id)

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found.",
        )

    if lead_data.contact_id is not None:
        contact = db.get(Contact, lead_data.contact_id)

        if contact is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found.",
            )

        if contact.company_id != lead_data.company_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The contact does not belong to this company.",
            )

    lead_values = lead_data.model_dump()
    lead_values["status"] = lead_data.status.value

    lead = Lead(**lead_values)
    db.add(lead)

    try:
        db.commit()
        db.refresh(lead)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to create the lead.",
        ) from error

    return lead

@router.get("", response_model=list[LeadRead])
def list_leads(
    company_id: int | None = Query(default=None, gt=0),
    contact_id: int | None = Query(default=None, gt=0),
    external_id: str | None = Query(default=None, min_length=1),
    lead_status: LeadStatus | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    statement = select(Lead).order_by(Lead.id)

    if company_id is not None:
        statement = statement.where(Lead.company_id == company_id)

    if contact_id is not None:
        statement = statement.where(Lead.contact_id == contact_id)

    if external_id is not None:
        statement = statement.where(Lead.external_id == external_id.strip())

    if lead_status is not None:
        statement = statement.where(Lead.status == lead_status.value)

    statement = statement.offset(offset).limit(limit)

    return db.scalars(statement).all()
@router.get("/{lead_id}", response_model=LeadRead)
def get_lead(
    lead_id: int,
    db: Session = Depends(get_db),
):
    lead = db.get(Lead, lead_id)

    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found.",
        )

    return lead
@router.patch("/{lead_id}", response_model=LeadRead)
def update_lead(
    lead_id: int,
    lead_data: LeadUpdate,
    db: Session = Depends(get_db),
):
    lead = db.get(Lead, lead_id)

    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found.",
        )

    update_data = lead_data.model_dump(exclude_unset=True)

    required_fields = {
        "company_id",
        "title",
        "status",
        "estimated_value",
        "currency",
    }

    for field in required_fields:
        if field in update_data and update_data[field] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{field} cannot be null.",
            )

    effective_company_id = update_data.get(
        "company_id",
        lead.company_id,
    )

    company = db.get(Company, effective_company_id)

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found.",
        )

    effective_contact_id = update_data.get(
        "contact_id",
        lead.contact_id,
    )

    if effective_contact_id is not None:
        contact = db.get(Contact, effective_contact_id)

        if contact is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found.",
            )

        if contact.company_id != effective_company_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The contact does not belong to this company.",
            )

    if "external_id" in update_data and update_data["external_id"] is not None:
        existing_lead = db.scalar(
            select(Lead).where(
                Lead.external_id == update_data["external_id"],
                Lead.id != lead_id,
            )
        )

        if existing_lead:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A lead with this external_id already exists.",
            )

    if "status" in update_data:
        update_data["status"] = lead_data.status.value

    for field, value in update_data.items():
        setattr(lead, field, value)

    try:
        db.commit()
        db.refresh(lead)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to update the lead.",
        ) from error

    return lead
@router.delete(
    "/{lead_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db),
):
    lead = db.get(Lead, lead_id)

    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found.",
        )

    db.delete(lead)

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Lead cannot be deleted because it has linked records.",
        ) from error