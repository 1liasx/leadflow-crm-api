from fastapi import FastAPI
from app.routers.contacts import router as contacts_router
from app.routers.companies import router as companies_router
from app.routers.leads import router as leads_router
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from app.schemas.lead import LeadCreate, LeadRead, LeadStatus

app = FastAPI(title="LeadFlow CRM API")

app.include_router(companies_router)
app.include_router(contacts_router)
app.include_router(leads_router)


@app.get("/health")
def health_check():
    return {"status": "healthy"}