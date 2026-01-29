# OPD Token Allocation System

Production-ready backend API for hospital OPD token management.

## Features
- Token allocation from multiple sources (online, walk-in, emergency, etc.)
- Priority-based token assignment
- Dynamic reallocation on cancellations
- Real-time slot capacity management

## Setup

### Prerequisites
- Python 3.8+
- MongoDB (local or Atlas)

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure `.env`:
```env
MONGODB_URL=your_mongodb_connection_string
DATABASE_NAME=opd_system
```

3. Run:
```bash
python main.py
```

API: http://localhost:8000  
Docs: http://localhost:8000/docs

## Endpoints

### Doctors
- `POST /doctors/` - Create doctor
- `GET /doctors/` - List doctors  
- `GET /doctors/{doctor_id}` - Get doctor

### Tokens
- `POST /tokens/allocate` - Allocate token
- `POST /tokens/cancel` - Cancel token
- `POST /tokens/emergency` - Emergency token
- `GET /tokens/doctor/{doctor_id}` - Doctor tokens

### Slots
- `GET /slots/{doctor_id}/{slot_time}` - Slot status

## Priority

1. Emergency
2. Paid Priority  
3. Online Booking
4. Follow-up
5. Walk-in
