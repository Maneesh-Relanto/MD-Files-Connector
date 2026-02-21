# REST API Reference

Base URL: `https://api.acme.example.com/v2`

All requests must include an `Authorization: Bearer <token>` header.

---

## Authentication

### POST /auth/token

Exchange credentials for a JWT.

**Request body:**
```json
{
  "username": "alice",
  "password": "s3cret"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "expires_in": 3600
}
```

---

## Users

### GET /users

Returns a paginated list of users.

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | int | Page number (default: 1) |
| `per_page` | int | Results per page (max: 100) |

### GET /users/{id}

Returns a single user by ID.

### PATCH /users/{id}

Update user fields. Supports partial updates.

### DELETE /users/{id}

Soft-deletes a user. Deleted users retain data for 30 days.

---

## Jobs

### POST /jobs

Submit a background job.

### GET /jobs/{id}/status

Poll job status. Returns `pending`, `running`, `done`, or `failed`.

---

## Rate Limiting

Requests are limited to **1000 per minute** per API key.
Exceeded requests receive HTTP 429 with a `Retry-After` header.
