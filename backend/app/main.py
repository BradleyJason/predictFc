from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import matches_router, predictions_router, smart_ticket_router

app = FastAPI(
    title="PredictFC API",
    version="0.1.0",
    description="Prédictions de matchs de football basées sur des modèles statistiques. Ces prédictions ne sont pas garanties. Jouez responsablement."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(matches_router, prefix="/api/v1")
app.include_router(predictions_router, prefix="/api/v1")
app.include_router(smart_ticket_router, prefix="/api/v1")

@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "version": "0.1.0", "env": "development"}

@app.get("/", tags=["system"])
def root():
    return {"message": "PredictFC API", "docs": "/docs"}
