# ERP Inventory & Stock Transfer System

A robust Django REST Framework backend for managing multi-branch inventory and atomic stock transfers.

## Features
- **Custom ID System**: Human-readable IDs (e.g., `prd_`, `brn_`).
- **Atomic Transfers**: Transactions ensure data integrity during stock movements.
- **Concurrency Protection**: Row-level locking to prevent race conditions.
- **Audit Logging**: Every transfer is tracked with a status history.

## Setup Instructions   
```bash
git clone <your-repo-url>
cd inventory_system

python -m venv venv
venv\Scripts\activate   # Windows

pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

Authentication (JWT)
Get Token
POST /api/token
Request Body
{
  "username": "admin",
  "password": "1234"
}
Use Token
Authorization: Bearer <token>


API Endpoints

User APIs
1. Create User
POST /api/create-user
Request Body
{
  "username": "admin",
  "password": "1234",
  "is_staff": true
}

Branch APIs
2. Create Branch
POST /api/branch
Request Body
{
  "name": "Branch A",
  "location": "Bhubaneswar"
}
3. List Branches
GET /api/branch

Product APIs
4. Create Product
POST /api/product
Request Body
{
  "name": "Laptop",
  "sku": "LP1001"
}
5. List Products
GET /api/product
Optional Query Params
?name=lap

Stock APIs
6. Create / Update Stock
POST /api/stock
Request Body
{
  "product": "prd_xxx",
  "branch": "brn_xxx",
  "quantity": 100
}
7. Branch Stock Summary
GET /api/branches/{branch_id}/stock-summary/
Response - {
  "branch": {
    "id": "brn_xxx",
    "name": "Branch A",
    "location": "Bhubaneswar",
    "is_active": true
  },
  "products": [
    {
      "id": "prd_xxx",
      "name": "Laptop",
      "sku": "LP1001",
      "quantity": 100
    }
  ]
}

Transfer APIs
8. Create Transfer Request
POST /api/transfers/
Request Body
{
  "product": "prd_xxx",
  "source_branch": "brn_1",
  "destination_branch": "brn_2",
  "quantity": 10
}

9. Approve Transfer (Staff Only)
POST /api/transfers/{transfer_id}/approve/
Notes
Only users with is_staff = true can approve
This operation is:
atomic
concurrency-safe
audit logged
10. List Transfers
GET /api/transfers/


🧪 Run Tests
python manage.py test

Audit Logging
Each transfer generates logs for:
• Created
• Approved
• Failed


Limitations / Future Improvements
🔹 Transfer Log APIs (Not Implemented)
Currently logs are created internally but no API is provided to fetch them.

➡️ Planned API
GET /api/transfers/{id}/logs/
Would return:
[
  {
    "action": "created",
    "performed_by": {
        "id": 2,
        "username": "xyz",
        "is_staff: False
    },
    "message": "...",
    "created_at": "..."
  },
  {
    "action": "approved",
    "performed_by": {
        "id": 2,
        "username": "admin",
        "is_staff: True
    },
    "message": "...",
    "created_at": "..."
  }
]

****
Architecture Overview
Django REST Framework (Monolithic)
SQLite (Development)
JWT Authentication
Relational DB design

****
Scaling Strategy
PostgreSQL for production
Redis caching for stock queries
Celery for async processing

****
Security Considerations
JWT authentication
Role-based access (is_staff)
Input validation
Transaction-safe operations