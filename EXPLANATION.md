# Technical Explanation

This document explains key design decisions with focus on **Scalability, Performance, and Edge Case Handling**.

---

## 1. Concurrency & Data Integrity

To prevent race conditions (e.g., multiple approvals or simultaneous stock updates), I implemented **pessimistic locking** at the database level.

- Used `transaction.atomic()` to ensure the entire transfer process executes as a single unit (all-or-nothing).
- Used `select_for_update()` in the `ApproveTransferView` to lock the involved `Stock` rows during the transaction.

This ensures:
- No double deduction of stock
- No inconsistent stock states
- Safe handling of concurrent requests

Additionally:
- Stock availability is validated both during **transfer creation** and again during **approval**, ensuring correctness even under concurrent operations.

---

## 2. Query Optimization

To ensure performance and scalability:

### 🔹 N+1 Query Prevention
- Used `select_related()` in:
  - `StockTransferView`
  - `BranchStockSummarySerializer`
- This reduces multiple database hits by performing SQL joins.

### 🔹 Pagination
- Implemented `PageNumberPagination` for all list APIs.
- Ensures consistent response time regardless of dataset size.

### 🔹 Indexing
- Added database indexes on frequently queried fields:
  - `product`
  - `branch`
  - `sku`
- Improves lookup and filtering performance.

---

## 3. Edge Case Handling

Handled critical edge cases including:

- Preventing transfers between the same branch
- Rejecting negative or invalid quantities
- Handling insufficient stock scenarios
- Preventing duplicate approvals of the same transfer
- Validating active status of product and branches
- Graceful error handling for invalid inputs

---

## 4. Unfinished Work & Next Steps

Due to time constraints, the following improvements are identified:

### 🔹 Transfer Log APIs (Important)

Currently:
- Transfer logs are stored in `StockTransferLog` for audit purposes

Missing:
- API to retrieve logs

### Planned API:
GET /api/transfers/{id}/logs/
[
  {
    "action": "created",
    "performed_by": {
        "id": 2,
        "username": "xyz",
        "is_staff: False
    },
    "message" : "...",
    "created_at": "..."
  },
  {
    "action": "approved",
    "performed_by": {
        "id": 2,
        "username": "admin",
        "is_staff: True
    },
    "message" : "...",
    "created_at": "..."
  }
]

Future Enhancements:
- Add filtering (by action/date)
- Add pagination for logs
- Improve audit visibility for managers