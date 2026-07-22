from fastapi import FastAPI
from app.routers.contacts import router as contacts_router
from app.routers.companies import router as companies_router


app = FastAPI(title="LeadFlow CRM API")

app.include_router(companies_router)
app.include_router(contacts_router)


@app.get("/health")
def health_check():
    return {"status": "healthy"}