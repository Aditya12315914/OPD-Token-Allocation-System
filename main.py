from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from database import connect_db, close_db, get_database
from models import Doctor, TokenRequest, Token, CancelTokenRequest
from token_service import (
    allocate_token,
    cancel_token,
    reallocate_tokens,
    get_slot_status
)
from contextlib import asynccontextmanager

# Startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    connect_db()
    yield
    # Shutdown
    close_db()

app = FastAPI(
    title="OPD Token Allocation System",
    description="Token allocation system for hospital OPD with dynamic capacity management",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    return {"message": "OPD Token Allocation System", "status": "active"}

@app.post("/doctors/", tags=["Doctors"])
async def create_doctor(doctor: Doctor):
    """Add a new doctor to the system"""
    db = get_database()
    
    existing = await db.doctors.find_one({"doctor_id": doctor.doctor_id})
    if existing:
        raise HTTPException(status_code=400, detail="Doctor already exists")
    
    doctor_dict = doctor.model_dump()
    result = await db.doctors.insert_one(doctor_dict)
    
    return {"message": "Doctor created successfully", "doctor_id": doctor.doctor_id}

@app.get("/doctors/", tags=["Doctors"])
async def get_doctors():
    """Get list of all doctors"""
    db = get_database()
    doctors = await db.doctors.find().to_list(length=100)
    
    for doc in doctors:
        doc["_id"] = str(doc["_id"])
    
    return {"doctors": doctors}

@app.get("/doctors/{doctor_id}", tags=["Doctors"])
async def get_doctor(doctor_id: str):
    """Get specific doctor details"""
    db = get_database()
    doctor = await db.doctors.find_one({"doctor_id": doctor_id})
    
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    doctor["_id"] = str(doctor["_id"])
    return doctor

@app.post("/tokens/allocate", tags=["Tokens"])
async def create_token(request: TokenRequest):
    """Allocate a new token to a patient"""
    result = await allocate_token(
        request.doctor_id,
        request.slot_time,
        request.source
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {"message": "Token allocated successfully", "token": result}

@app.post("/tokens/cancel", tags=["Tokens"])
async def cancel_token_endpoint(request: CancelTokenRequest):
    """Cancel an existing token"""
    result = await cancel_token(
        request.token_number,
        request.doctor_id,
        request.slot_time,
        request.reason or "cancelled"
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    await reallocate_tokens(request.doctor_id, request.slot_time)
    
    return result

@app.get("/slots/{doctor_id}/{slot_time}", tags=["Slots"])
async def get_slot_info(doctor_id: str, slot_time: str):
    """Get current status of a time slot"""
    result = await get_slot_status(doctor_id, slot_time)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result

@app.get("/tokens/doctor/{doctor_id}", tags=["Tokens"])
async def get_doctor_tokens(doctor_id: str):
    """Get all tokens for a specific doctor"""
    db = get_database()
    
    tokens = await db.tokens.find({
        "doctor_id": doctor_id,
        "status": "active"
    }).sort("slot_time", 1).to_list(length=200)
    
    for token in tokens:
        token["_id"] = str(token["_id"])
    
    return {"doctor_id": doctor_id, "tokens": tokens, "total": len(tokens)}

@app.post("/tokens/emergency", tags=["Tokens"])
async def add_emergency_token(request: TokenRequest):
    """Add emergency patient - gets highest priority"""
    request.source.type = "emergency"
    
    result = await allocate_token(
        request.doctor_id,
        request.slot_time,
        request.source
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    await reallocate_tokens(request.doctor_id, request.slot_time)
    
    return {"message": "Emergency token added", "token": result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
