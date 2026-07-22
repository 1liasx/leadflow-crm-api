from fastapi import FastAPI
app = FastAPI(title="LeadFlow CRM API")
@app.get("/health")
def health_check():
    return {"status": "healthy"}