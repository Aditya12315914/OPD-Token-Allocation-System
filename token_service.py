from datetime import datetime
from database import get_database

PRIORITY_MAP = {
    "emergency": 1,
    "paid_priority": 2,
    "online_booking": 3,
    "follow_up": 4,
    "walk_in": 5
}

async def get_priority(source_type):
    return PRIORITY_MAP.get(source_type, 5)

async def allocate_token(doctor_id, slot_time, source):
    db = get_database()
    
    doctor = await db.doctors.find_one({"doctor_id": doctor_id})
    if not doctor:
        return {"error": "Doctor not found"}
    
    slot_info = None
    for slot in doctor.get("time_slots", []):
        if slot["slot_time"] == slot_time:
            slot_info = slot
            break
    
    if not slot_info:
        return {"error": "Invalid time slot"}
    
    existing_tokens = await db.tokens.find({
        "doctor_id": doctor_id,
        "slot_time": slot_time,
        "status": "active"
    }).to_list(length=100)
    
    if len(existing_tokens) >= slot_info["max_capacity"]:
        return {"error": "Slot is full"}
    
    if len(existing_tokens) == 0:
        token_number = 1
    else:
        token_number = max([t["token_number"] for t in existing_tokens]) + 1
    
    priority = await get_priority(source.type)
    
    token_data = {
        "token_number": token_number,
        "doctor_id": doctor_id,
        "slot_time": slot_time,
        "patient_name": source.patient_name,
        "patient_id": source.patient_id,
        "contact": source.contact,
        "source_type": source.type,
        "priority_level": priority,
        "status": "active",
        "created_at": datetime.now()
    }
    
    result = await db.tokens.insert_one(token_data)
    token_data["_id"] = str(result.inserted_id)
    
    return token_data

async def cancel_token(token_number, doctor_id, slot_time, reason="cancelled"):
    db = get_database()
    
    result = await db.tokens.update_one(
        {
            "token_number": token_number,
            "doctor_id": doctor_id,
            "slot_time": slot_time,
            "status": "active"
        },
        {
            "$set": {
                "status": "cancelled",
                "cancelled_at": datetime.now(),
                "cancel_reason": reason
            }
        }
    )
    
    if result.modified_count == 0:
        return {"error": "Token not found or already cancelled"}
    
    return {"message": "Token cancelled successfully"}

async def reallocate_tokens(doctor_id, slot_time):
    db = get_database()
    
    tokens = await db.tokens.find({
        "doctor_id": doctor_id,
        "slot_time": slot_time,
        "status": "active"
    }).sort("priority_level", 1).to_list(length=100)
    
    for index, token in enumerate(tokens):
        new_token_number = index + 1
        await db.tokens.update_one(
            {"_id": token["_id"]},
            {"$set": {"token_number": new_token_number}}
        )
    
    return {"message": "Tokens reallocated", "total_tokens": len(tokens)}

async def get_slot_status(doctor_id, slot_time):
    db = get_database()
    
    doctor = await db.doctors.find_one({"doctor_id": doctor_id})
    if not doctor:
        return {"error": "Doctor not found"}
    
    slot_info = None
    for slot in doctor.get("time_slots", []):
        if slot["slot_time"] == slot_time:
            slot_info = slot
            break
    
    if not slot_info:
        return {"error": "Invalid slot"}
    
    active_tokens = await db.tokens.find({
        "doctor_id": doctor_id,
        "slot_time": slot_time,
        "status": "active"
    }).sort("token_number", 1).to_list(length=100)
    
    return {
        "doctor_id": doctor_id,
        "slot_time": slot_time,
        "max_capacity": slot_info["max_capacity"],
        "current_tokens": len(active_tokens),
        "available_slots": slot_info["max_capacity"] - len(active_tokens),
        "tokens": active_tokens
    }
