# Betting Payment Manager API - Complete Examples

Complete API documentation with all endpoints, request/response examples, and error cases.

**Base URL:** `http://localhost:3000/api/v1`

---

## Table of Contents
1. [Authentication](#authentication)
2. [Public Configuration](#public-configuration)
3. [Player Management](#player-management)
4. [Transaction Management](#transaction-management)
5. [Admin - Transaction Management](#admin---transaction-management)
6. [Admin - User Management](#admin---user-management)
7. [Admin - Configuration Management](#admin---configuration-management)
8. [Admin - Betting Sites Management](#admin---betting-sites-management)
9. [Agent Operations](#agent-operations)
10. [File Upload](#file-upload)
11. [Error Responses](#error-responses)

---

## Authentication

### 1. Login (Admin/Agent)

**Endpoint:** `POST /auth/login`

**Request Body:**
```json
{
  "username": "admin@example.com",
  "password": "AdminPass123!"
}
```

**Success Response (200):**
```json
{
  "message": "Login successful",
  "user": {
    "id": 11,
    "username": "admin@example.com",
    "email": "admin@example.com",
    "displayName": "System Administrator",
    "role": "admin"
  },
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "550e8400-e29b-41d4-a716-446655440000",
  "expiresIn": 2592000
}
```

**Error Response (401):**
```json
{
  "error": "Invalid credentials"
}
```

**Error Response (400):**
```json
{
  "error": "Validation failed",
  "details": ["\"username\" is required"]
}
```

---

### 2. Refresh Token

**Endpoint:** `POST /auth/refresh`

**Request Body:**
```json
{
  "refreshToken": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Success Response (200):**
```json
{
  "message": "Token refreshed successfully",
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expiresIn": 2592000
}
```

**Error Response (401):**
```json
{
  "error": "Invalid or expired refresh token"
}
```

---

### 3. Logout

**Endpoint:** `POST /auth/logout`

**Request Body:**
```json
{
  "refreshToken": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Success Response (200):**
```json
{
  "message": "Logged out successfully"
}
```

---

### 4. Get Profile

**Endpoint:** `GET /auth/profile`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Success Response (200):**
```json
{
  "user": {
    "id": 11,
    "username": "admin@example.com",
    "email": "admin@example.com",
    "displayName": "System Administrator",
    "role": "admin",
    "isActive": true,
    "createdAt": "2025-10-25T11:56:17.000Z"
  }
}
```

**Error Response (401):**
```json
{
  "error": "Access token required"
}
```

---

### 5. Change Password

**Endpoint:** `PUT /auth/change-password`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Request Body:**
```json
{
  "currentPassword": "AdminPass123!",
  "newPassword": "NewAdminPass123!"
}
```

**Success Response (200):**
```json
{
  "message": "Password changed successfully"
}
```

**Error Response (401):**
```json
{
  "error": "Current password is incorrect"
}
```

---

## Public Configuration

### 1. Get Welcome Message

**Endpoint:** `GET /config/welcome?lang=en`

**Success Response (200):**
```json
{
  "message": "Welcome to Betting Payment Manager! Please choose your preferred language to continue.",
  "languageCode": "en"
}
```

---

### 2. Get Deposit Banks

**Endpoint:** `GET /config/deposit-banks`

**Success Response (200):**
```json
{
  "depositBanks": [
    {
      "id": 1,
      "bankName": "Chase Bank",
      "accountNumber": "1234567890",
      "accountName": "Betting Payment Manager",
      "notes": "Primary deposit account",
      "isActive": true
    }
  ]
}
```

---

### 3. Get Withdrawal Banks

**Endpoint:** `GET /config/withdrawal-banks`

**Success Response (200):**
```json
{
  "withdrawalBanks": [
    {
      "id": 1,
      "bankName": "Chase Bank",
      "requiredFields": [
        {
          "name": "account_number",
          "label": "Account Number",
          "type": "text",
          "required": true
        }
      ],
      "notes": "Primary withdrawal bank",
      "isActive": true
    }
  ]
}
```

---

### 4. Get Languages

**Endpoint:** `GET /config/languages`

**Success Response (200):**
```json
{
  "languages": [
    {
      "code": "en",
      "name": "English",
      "isActive": true
    },
    {
      "code": "es",
      "name": "Spanish",
      "isActive": true
    }
  ]
}
```

---

### 5. Get Betting Sites

**Endpoint:** `GET /config/betting-sites`

**Query Parameters:**
- `isActive` (optional): Filter by active status (true/false)

**Success Response (200):**
```json
{
  "bettingSites": [
    {
      "id": 1,
      "name": "Arada Betting",
      "description": "Arada Betting Platform - Sports betting and casino games",
      "website": "https://arada-betting.com",
      "isActive": true,
      "createdAt": "2025-10-25T11:22:13.000Z",
      "updatedAt": "2025-10-25T11:22:13.000Z"
    },
    {
      "id": 2,
      "name": "Bética Betting",
      "description": "Bética Betting Platform - Online sports betting",
      "website": "https://betica-betting.com",
      "isActive": true,
      "createdAt": "2025-10-25T11:22:13.000Z",
      "updatedAt": "2025-10-25T11:22:13.000Z"
    }
  ],
  "total": 2
}
```

---

## Player Management

### 1. Create Player Profile

**Endpoint:** `POST /players`

**Request Body:**
```json
{
  "telegramId": "123456789",
  "telegramUsername": "player123",
  "languageCode": "en"
}
```

**Success Response (201):**
```json
{
  "message": "Player profile created successfully",
  "player": {
    "id": 1,
    "playerUuid": "e804346f-e513-4ae2-9cfa-7584c3ea1698",
    "telegramId": "123456789",
    "telegramUsername": "player123",
    "languageCode": "en",
    "lastActive": "2025-10-25T12:00:00.000Z",
    "createdAt": "2025-10-25T12:00:00.000Z",
    "updatedAt": "2025-10-25T12:00:00.000Z"
  }
}
```

**Error Response (409):**
```json
{
  "error": "Player already exists",
  "message": "A player with this Telegram ID already exists"
}
```

**Error Response (400):**
```json
{
  "error": "Validation failed",
  "details": ["\"telegramId\" is required"]
}
```

---

### 2. Get Player by UUID

**Endpoint:** `GET /players/:playerUuid`

**Success Response (200):**
```json
{
  "player": {
    "id": 1,
    "playerUuid": "e804346f-e513-4ae2-9cfa-7584c3ea1698",
    "telegramId": "123456789",
    "telegramUsername": "player123",
    "languageCode": "en",
    "lastActive": "2025-10-25T12:00:00.000Z",
    "createdAt": "2025-10-25T12:00:00.000Z",
    "updatedAt": "2025-10-25T12:00:00.000Z"
  }
}
```

**Error Response (404):**
```json
{
  "error": "Player not found"
}
```

---

### 3. Update Player Profile

**Endpoint:** `PUT /players/:playerUuid`

**Request Body:**
```json
{
  "telegramUsername": "updatedplayer",
  "languageCode": "es"
}
```

**Success Response (200):**
```json
{
  "message": "Player profile updated successfully",
  "player": {
    "id": 1,
    "playerUuid": "e804346f-e513-4ae2-9cfa-7584c3ea1698",
    "telegramId": "123456789",
    "telegramUsername": "updatedplayer",
    "languageCode": "es",
    "lastActive": "2025-10-25T12:00:00.000Z",
    "updatedAt": "2025-10-25T12:05:00.000Z"
  }
}
```

**Error Response (404):**
```json
{
  "error": "Player not found"
}
```

---

## Player Operations

### 1. Extended Player Registration

**Endpoint:** `POST /players/register`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "telegramId": "123456789",
  "telegramUsername": "player123",
  "languageCode": "en",
  "username": "player123",
  "email": "player@example.com",
  "password": "password123",
  "displayName": "Player Name",
  "phone": "+1234567890"
}
```

**Success Response (201):**
```json
{
  "message": "Player registered successfully",
  "player": {
    "id": 5,
    "playerUuid": "84153609-76d1-4414-819b-c469b6651d9f",
    "userId": 16,
    "telegramId": "123456789",
    "telegramUsername": "player123",
    "displayName": "Player Name",
    "email": "player@example.com",
    "phone": "+1234567890",
    "isTemporary": false,
    "languageCode": "en",
    "createdAt": "2025-10-26T14:00:00.000Z"
  }
}
```

**Error Response (400 - Validation Error):**
```json
{
  "error": "Validation error",
  "details": "\"email\" is required when \"username\" is provided"
}
```

---

### 2. Get Player by User ID

**Endpoint:** `GET /players/user/:userId`

**Path Parameters:**
- `userId` (required): The user ID from the authentication response

**Success Response (200):**
```json
{
  "player": {
    "id": 12,
    "playerUuid": "84153609-76d1-4414-819b-c469b6651d9f",
    "userId": 16,
    "telegramId": "temp_1761487642921",
    "telegramUsername": "temp_player_4a7ifnwdv",
    "languageCode": "fr",
    "lastActive": "2025-10-26T14:07:22.000Z",
    "user": {
      "id": 16,
      "username": "player3@example.com",
      "email": "player3@example.com",
      "roleId": 9,
      "displayName": "Bereket Sewnet2",
      "phone": "+251912757376",
      "isActive": true,
      "createdAt": "2025-10-26T14:07:23.000Z",
      "updatedAt": "2025-10-26T14:07:23.000Z"
    }
  }
}
```

**Error Response (404):**
```json
{
  "error": "Player profile not found for this user"
}
```

---

### 3. Temp ID Transaction Lookup

**Endpoint:** `GET /transactions/temp`

**Query Parameters:**
- `tempId` (required): Temporary ID to lookup transactions
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 10)

**Success Response (200):**
```json
{
  "message": "Transactions retrieved successfully",
  "transactions": [
    {
      "id": 1,
      "transactionUuid": "98bc140c-99ed-4406-b803-f8a0051f0693",
      "type": "DEPOSIT",
      "amount": "100.00",
      "currency": "USD",
      "status": "Pending",
      "depositBank": {
        "id": 1,
        "bankName": "Chase Bank",
        "accountNumber": "1234567890"
      },
      "withdrawalBank": null,
      "withdrawalAddress": null,
      "screenshotUrl": null,
      "bettingSiteId": 1,
      "playerSiteId": "player123",
      "requestedAt": "2025-10-25T12:00:00.000Z",
      "assignedAgent": null,
      "adminNotes": null,
      "agentNotes": null,
      "rating": null,
      "createdAt": "2025-10-25T12:00:00.000Z",
      "updatedAt": "2025-10-25T12:00:00.000Z"
    }
  ],
  "pagination": {
    "total": 1,
    "page": 1,
    "limit": 10,
    "pages": 1
  },
  "playerInfo": {
    "playerUuid": "e804346f-e513-4ae2-9cfa-7584c3ea1698",
    "telegramUsername": "temp_player_abc123",
    "isTemporary": true
  }
}
```

**Error Response (404):**
```json
{
  "error": "No transactions found",
  "message": "No transactions found for this temporary ID"
}
```

---

### 4. Advanced Transaction Filtering

**Endpoint:** `GET /transactions`

**Query Parameters:**
- `playerUuid` (required): Player UUID
- `type` (optional): Transaction type (DEPOSIT, WITHDRAW)
- `status` (optional): Transaction status (PENDING, IN_PROGRESS, SUCCESS, FAILED)
- `bettingSiteId` (optional): Filter by betting site ID
- `minAmount` (optional): Minimum transaction amount
- `maxAmount` (optional): Maximum transaction amount
- `startDate` (optional): Start date (YYYY-MM-DD)
- `endDate` (optional): End date (YYYY-MM-DD)
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)

**Example Request:**
```
GET /transactions?playerUuid=61014869-9a8a-43d0-9f1e-28bc6e418cdc&type=DEPOSIT&minAmount=50&maxAmount=200&bettingSiteId=1&startDate=2025-10-01&endDate=2025-10-31
```

**Success Response (200):**
```json
{
  "message": "Transactions retrieved successfully",
  "transactions": [
    {
      "id": 1,
      "transactionUuid": "98bc140c-99ed-4406-b803-f8a0051f0693",
      "type": "DEPOSIT",
      "amount": "100.00",
      "currency": "USD",
      "status": "Pending",
      "depositBank": {
        "id": 1,
        "bankName": "Chase Bank",
        "accountNumber": "1234567890"
      },
      "withdrawalBank": null,
      "withdrawalAddress": null,
      "screenshotUrl": null,
      "bettingSiteId": 1,
      "playerSiteId": "player123",
      "requestedAt": "2025-10-25T12:00:00.000Z",
      "assignedAgent": null,
      "adminNotes": null,
      "agentNotes": null,
      "rating": null,
      "createdAt": "2025-10-25T12:00:00.000Z",
      "updatedAt": "2025-10-25T12:00:00.000Z"
    }
  ],
  "pagination": {
    "total": 1,
    "page": 1,
    "limit": 20,
    "pages": 1
  },
  "filters": {
    "type": "DEPOSIT",
    "status": null,
    "bettingSiteId": "1",
    "minAmount": "50",
    "maxAmount": "200",
    "startDate": "2025-10-01",
    "endDate": "2025-10-31"
  },
  "playerInfo": {
    "playerUuid": "61014869-9a8a-43d0-9f1e-28bc6e418cdc",
    "telegramUsername": "player123",
    "isTemporary": false
  }
}
```

**Error Response (400):**
```json
{
  "error": "Query validation failed",
  "details": ["\"playerUuid\" is required"]
}
```

**Error Response (404):**
```json
{
  "error": "Player profile not found",
  "message": "No player found with this UUID"
}
```

---

### 5. Basic Player Registration (Legacy)

**Endpoint:** `POST /players`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "telegramId": "123456789",
  "telegramUsername": "player123",
  "languageCode": "en"
}
```

**Success Response (201):**
```json
{
  "message": "Player created successfully",
  "player": {
    "id": 1,
    "playerUuid": "e804346f-e513-4ae2-9cfa-7584c3ea1698",
    "telegramId": "123456789",
    "telegramUsername": "player123",
    "languageCode": "en",
    "lastActive": "2025-10-25T12:00:00.000Z"
  }
}
```

---

### 6. Get Player by UUID

**Endpoint:** `GET /players/:playerUuid`

**Success Response (200):**
```json
{
  "player": {
    "id": 1,
    "playerUuid": "e804346f-e513-4ae2-9cfa-7584c3ea1698",
    "telegramId": "123456789",
    "telegramUsername": "player123",
    "languageCode": "en",
    "lastActive": "2025-10-25T12:00:00.000Z",
    "createdAt": "2025-10-25T12:00:00.000Z",
    "updatedAt": "2025-10-25T12:00:00.000Z"
  }
}
```

**Error Response (404):**
```json
{
  "error": "Player profile not found"
}
```

---

### 7. Update Player Profile

**Endpoint:** `PUT /players/:playerUuid`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "telegramId": "987654321",
  "telegramUsername": "updatedplayer",
  "languageCode": "es"
}
```

**Success Response (200):**
```json
{
  "message": "Player profile updated successfully",
  "player": {
    "id": 1,
    "playerUuid": "e804346f-e513-4ae2-9cfa-7584c3ea1698",
    "telegramId": "987654321",
    "telegramUsername": "updatedplayer",
    "languageCode": "es",
    "lastActive": "2025-10-25T12:00:00.000Z"
  }
}
```

---

## Transaction Management

### 1. Create Deposit Transaction (JSON)

**Endpoint:** `POST /transactions`

**Request Body:**
```json
{
  "playerUuid": "e804346f-e513-4ae2-9cfa-7584c3ea1698",
  "type": "DEPOSIT",
  "amount": 100.00,
  "currency": "USD",
  "depositBankId": 1,
  "bettingSiteId": 1,
  "playerSiteId": "player123"
}
```

**Success Response (201):**
```json
{
  "message": "Transaction created successfully",
  "transaction": {
    "id": 1,
    "transactionUuid": "98bc140c-99ed-4406-b803-f8a0051f0693",
    "type": "DEPOSIT",
    "amount": "100.00",
    "currency": "USD",
    "status": "Pending",
    "screenshotUrl": null,
    "bettingSiteId": 1,
    "playerSiteId": "player123",
    "requestedAt": "2025-10-25T12:00:00.000Z",
    "createdAt": "2025-10-25T12:00:00.000Z",
    "updatedAt": "2025-10-25T12:00:00.000Z"
  }
}
```

**Error Response (404):**
```json
{
  "error": "Player not found"
}
```

**Error Response (400):**
```json
{
  "error": "Validation failed",
  "details": [
    "\"bettingSiteId\" is required",
    "\"playerSiteId\" is required"
  ]
}
```

---

### 2. Create Withdrawal Transaction

**Endpoint:** `POST /transactions`

**Request Body:**
```json
{
  "playerUuid": "e804346f-e513-4ae2-9cfa-7584c3ea1698",
  "type": "WITHDRAW",
  "amount": 50.00,
  "currency": "USD",
  "withdrawalBankId": 1,
  "withdrawalAddress": "test-address-123",
  "bettingSiteId": 1,
  "playerSiteId": "player123"
}
```

**Success Response (201):**
```json
{
  "message": "Transaction created successfully",
  "transaction": {
    "id": 2,
    "transactionUuid": "24068d99-fea9-412d-b4b1-01e3087bf4e2",
    "type": "WITHDRAW",
    "amount": "50.00",
    "currency": "USD",
    "status": "Pending",
    "screenshotUrl": null,
    "bettingSiteId": 1,
    "playerSiteId": "player123",
    "requestedAt": "2025-10-25T12:00:00.000Z",
    "createdAt": "2025-10-25T12:00:00.000Z",
    "updatedAt": "2025-10-25T12:00:00.000Z"
  }
}
```

**Error Response (400):**
```json
{
  "error": "Validation failed",
  "details": [
    "\"withdrawalBankId\" is required",
    "\"withdrawalAddress\" is required",
    "\"bettingSiteId\" is required",
    "\"playerSiteId\" is required"
  ]
}
```

---

### 3. Create Transaction with File Upload

**Endpoint:** `POST /transactions`

**Content-Type:** `multipart/form-data`

**Form Data:**
- `playerUuid`: e804346f-e513-4ae2-9cfa-7584c3ea1698
- `type`: DEPOSIT
- `amount`: 100.00
- `currency`: USD
- `depositBankId`: 1
- `bettingSiteId`: 1
- `playerSiteId`: player123
- `screenshot`: [PNG/JPG/JPEG file]

**Success Response (201):**
```json
{
  "message": "Transaction created successfully",
  "transaction": {
    "id": 3,
    "transactionUuid": "98bc140c-99ed-4406-b803-f8a0051f0694",
    "type": "DEPOSIT",
    "amount": "100.00",
    "currency": "USD",
    "status": "Pending",
    "screenshotUrl": "http://localhost:3000/uploads/screenshot-1234567890.png",
    "bettingSiteId": 1,
    "playerSiteId": "player123",
    "requestedAt": "2025-10-25T12:00:00.000Z",
    "createdAt": "2025-10-25T12:00:00.000Z"
  }
}
```

**Error Response (400):**
```json
{
  "error": "Invalid file type. Only PNG, JPG, and JPEG files are allowed."
}
```

---

### 4. Get Player Transactions

**Endpoint:** `GET /transactions?playerUuid=:playerUuid&page=1&limit=10`

**Query Parameters:**
- `playerUuid` (required): Player UUID
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 10)
- `type` (optional): DEPOSIT or WITHDRAW
- `status` (optional): Transaction status

**Success Response (200):**
```json
{
  "transactions": [
    {
      "id": 2,
      "transactionUuid": "24068d99-fea9-412d-b4b1-01e3087bf4e2",
      "type": "WITHDRAW",
      "amount": "50.00",
      "currency": "USD",
      "status": "Pending",
      "depositBank": null,
      "withdrawalBank": {
        "id": 1,
        "bankName": "Chase Bank"
      },
      "withdrawalAddress": "test-address-123",
      "screenshotUrl": null,
      "requestedAt": "2025-10-25T12:00:00.000Z",
      "assignedAgent": null,
      "createdAt": "2025-10-25T12:00:00.000Z",
      "updatedAt": "2025-10-25T12:00:00.000Z"
    },
    {
      "id": 1,
      "transactionUuid": "98bc140c-99ed-4406-b803-f8a0051f0693",
      "type": "DEPOSIT",
      "amount": "100.00",
      "currency": "USD",
      "status": "Pending",
      "depositBank": {
        "id": 1,
        "bankName": "Chase Bank"
      },
      "withdrawalBank": null,
      "screenshotUrl": null,
      "bettingSiteId": 1,
      "playerSiteId": "player123",
      "requestedAt": "2025-10-25T12:00:00.000Z",
      "assignedAgent": null,
      "createdAt": "2025-10-25T12:00:00.000Z",
      "updatedAt": "2025-10-25T12:00:00.000Z"
    }
  ],
  "pagination": {
    "total": 2,
    "page": 1,
    "limit": 10,
    "pages": 1
  }
}
```

**Error Response (400):**
```json
{
  "error": "Validation failed",
  "details": ["\"playerUuid\" is required"]
}
```

---

### 5. Get Transaction Details

**Endpoint:** `GET /transactions/:id?player_uuid=:playerUuid`

**Query Parameters:**
- `player_uuid` (optional): Player UUID for verification

**Success Response (200):**
```json
{
  "transaction": {
    "id": 1,
    "transactionUuid": "98bc140c-99ed-4406-b803-f8a0051f0693",
    "type": "DEPOSIT",
    "amount": "100.00",
    "currency": "USD",
    "status": "Pending",
    "depositBank": {
      "id": 1,
      "bankName": "Chase Bank",
      "accountNumber": "1234567890",
      "accountName": "Betting Payment Manager"
    },
    "withdrawalBank": null,
    "screenshotUrl": null,
    "bettingSiteId": 1,
    "playerSiteId": "player123",
    "bettingSite": {
      "id": 1,
      "name": "Arada Betting",
      "website": "https://arada-betting.com"
    },
    "requestedAt": "2025-10-25T12:00:00.000Z",
    "assignedAgent": null,
    "adminNotes": null,
    "agentNotes": null,
    "rating": null,
    "createdAt": "2025-10-25T12:00:00.000Z",
    "updatedAt": "2025-10-25T12:00:00.000Z"
  }
}
```

**Error Response (404):**
```json
{
  "error": "Transaction not found"
}
```

---

## Admin - Transaction Management

### 1. Get All Transactions

**Endpoint:** `GET /admin/transactions`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)
- `status` (optional): Filter by status
- `type` (optional): Filter by type (DEPOSIT/WITHDRAW)
- `agent` (optional): Filter by assigned agent ID
- `playerUuid` (optional): Filter by player UUID

**Success Response (200):**
```json
{
  "transactions": [
    {
      "id": 1,
      "transactionUuid": "98bc140c-99ed-4406-b803-f8a0051f0693",
      "type": "DEPOSIT",
      "amount": "100.00",
      "currency": "USD",
      "status": "Pending",
      "depositBank": {
        "id": 1,
        "bankName": "Chase Bank",
        "accountNumber": "1234567890"
      },
      "withdrawalBank": null,
      "withdrawalAddress": null,
      "screenshotUrl": null,
      "bettingSiteId": 1,
      "playerSiteId": "player123",
      "bettingSite": {
        "id": 1,
        "name": "Arada Betting",
        "description": "Arada Betting Platform - Sports betting and casino games",
        "website": "https://arada-betting.com",
        "isActive": true
      },
      "requestedAt": "2025-10-25T12:00:00.000Z",
      "assignedAgent": null,
      "adminNotes": null,
      "agentNotes": null,
      "rating": null,
      "playerProfile": {
        "id": 1,
        "playerUuid": "e804346f-e513-4ae2-9cfa-7584c3ea1698",
        "telegramUsername": "player123"
      },
      "createdAt": "2025-10-25T12:00:00.000Z",
      "updatedAt": "2025-10-25T12:00:00.000Z"
    }
  ],
  "pagination": {
    "total": 1,
    "page": 1,
    "limit": 20,
    "pages": 1
  }
}
```

**Error Response (401):**
```json
{
  "error": "Access token required"
}
```

**Error Response (403):**
```json
{
  "error": "Access denied. Admin role required."
}
```

---

### 2. Assign Transaction to Agent

**Endpoint:** `PUT /admin/transactions/:id/assign`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Request Body:**
```json
{
  "agentId": 12
}
```

**Success Response (200):**
```json
{
  "message": "Transaction assigned successfully",
  "transaction": {
    "id": 1,
    "transactionUuid": "98bc140c-99ed-4406-b803-f8a0051f0693",
    "assignedAgentId": 12,
    "assignedAgent": {
      "id": 12,
      "username": "agent@example.com",
      "displayName": "Support Agent"
    }
  }
}
```

**Error Response (404):**
```json
{
  "error": "Transaction not found"
}
```

**Error Response (404):**
```json
{
  "error": "Agent not found"
}
```

---

### 3. Update Transaction Status

**Endpoint:** `PUT /admin/transactions/:id/status`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Request Body:**
```json
{
  "status": "SUCCESS",
  "adminNotes": "Transaction completed successfully"
}
```

**Success Response (200):**
```json
{
  "message": "Transaction status updated successfully",
  "transaction": {
    "id": 1,
    "transactionUuid": "98bc140c-99ed-4406-b803-f8a0051f0693",
    "status": "Success",
    "adminNotes": "Transaction completed successfully",
    "updatedAt": "2025-10-25T12:10:00.000Z"
  }
}
```

**Error Response (404):**
```json
{
  "error": "Transaction not found"
}
```

**Error Response (404):**
```json
{
  "error": "Status not found"
}
```

---

### 4. Get Agents with Statistics

**Endpoint:** `GET /admin/agents`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Success Response (200):**
```json
{
  "agents": [
    {
      "id": 12,
      "username": "agent@example.com",
      "displayName": "Support Agent",
      "isActive": true,
      "stats": {
        "totalAssigned": 5,
        "pending": 2,
        "inProgress": 1,
        "completed": 2,
        "failed": 0,
        "averageRating": 4.5
      }
    }
  ]
}
```

---

## Admin - User Management

### 1. Get All Roles

**Endpoint:** `GET /admin/roles`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Success Response (200):**
```json
{
  "roles": [
    {
      "id": 7,
      "name": "admin"
    },
    {
      "id": 8,
      "name": "agent"
    },
    {
      "id": 9,
      "name": "player"
    }
  ]
}
```

---

### 2. Get User Statistics

**Endpoint:** `GET /admin/users/statistics`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Success Response (200):**
```json
{
  "statistics": {
    "totalUsers": 2,
    "activeUsers": 2,
    "inactiveUsers": 0,
    "recentUsers": 2,
    "roleDistribution": [
      {
        "role": "admin",
        "count": 1
      },
      {
        "role": "agent",
        "count": 1
      }
    ]
  }
}
```

---

### 3. Register New User

**Endpoint:** `POST /admin/users`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Request Body:**
```json
{
  "username": "newadmin@example.com",
  "password": "NewAdminPass123!",
  "displayName": "New Administrator",
  "email": "newadmin@example.com",
  "phone": "+1234567892",
  "roleId": 7,
  "isActive": true
}
```

**Success Response (201):**
```json
{
  "message": "User created successfully",
  "user": {
    "id": 13,
    "username": "newadmin@example.com",
    "email": "newadmin@example.com",
    "displayName": "New Administrator",
    "phone": "+1234567892",
    "roleId": 7,
    "isActive": true,
    "createdAt": "2025-10-25T12:00:00.000Z",
    "updatedAt": "2025-10-25T12:00:00.000Z"
  }
}
```

**Error Response (409):**
```json
{
  "error": "User already exists",
  "message": "A user with this username already exists"
}
```

**Error Response (400):**
```json
{
  "error": "Validation failed",
  "details": [
    "\"password\" is required",
    "\"roleId\" is required"
  ]
}
```

---

### 4. Get All Users

**Endpoint:** `GET /admin/users`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)
- `role` (optional): Filter by role ID (7=admin, 8=agent, 9=player)
- `search` (optional): Search by username or display name
- `isActive` (optional): Filter by active status (true/false)

**Success Response (200):**
```json
{
  "users": [
    {
      "id": 11,
      "username": "admin@example.com",
      "email": "admin@example.com",
      "displayName": "System Administrator",
      "phone": "+1234567890",
      "isActive": true,
      "role": {
        "id": 7,
        "name": "admin"
      },
      "createdAt": "2025-10-25T11:56:17.000Z",
      "updatedAt": "2025-10-25T11:56:17.000Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1,
    "pages": 1
  }
}
```

---

### 5. Get User by ID

**Endpoint:** `GET /admin/users/:id`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Success Response (200):**
```json
{
  "user": {
    "id": 11,
    "username": "admin@example.com",
    "email": "admin@example.com",
    "displayName": "System Administrator",
    "phone": "+1234567890",
    "isActive": true,
    "role": {
      "id": 7,
      "name": "admin"
    },
    "createdAt": "2025-10-25T11:56:17.000Z",
    "updatedAt": "2025-10-25T11:56:17.000Z"
  }
}
```

**Error Response (404):**
```json
{
  "error": "User not found"
}
```

---

### 6. Update User

**Endpoint:** `PUT /admin/users/:id`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Request Body:**
```json
{
  "username": "updatedadmin@example.com",
  "displayName": "Updated Administrator",
  "email": "updatedadmin@example.com",
  "phone": "+1234567893",
  "roleId": 7,
  "isActive": true
}
```

**Success Response (200):**
```json
{
  "message": "User updated successfully",
  "user": {
    "id": 13,
    "username": "updatedadmin@example.com",
    "email": "updatedadmin@example.com",
    "displayName": "Updated Administrator",
    "phone": "+1234567893",
    "roleId": 7,
    "isActive": true,
    "updatedAt": "2025-10-25T12:10:00.000Z"
  }
}
```

**Error Response (404):**
```json
{
  "error": "User not found"
}
```

---

### 7. Change User Password (Admin)

**Endpoint:** `PUT /admin/users/:id/password`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Request Body:**
```json
{
  "newPassword": "NewSecurePassword123!"
}
```

**Success Response (200):**
```json
{
  "message": "Password changed successfully"
}
```

**Error Response (404):**
```json
{
  "error": "User not found"
}
```

---

### 8. Toggle User Status

**Endpoint:** `PUT /admin/users/:id/toggle-status`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Success Response (200):**
```json
{
  "message": "User deactivated successfully",
  "user": {
    "id": 13,
    "username": "updatedadmin@example.com",
    "isActive": false,
    "updatedAt": "2025-10-25T12:15:00.000Z"
  }
}
```

**Error Response (404):**
```json
{
  "error": "User not found"
}
```

---

### 9. Delete User

**Endpoint:** `DELETE /admin/users/:id`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Success Response (200):**
```json
{
  "message": "User deleted successfully"
}
```

**Error Response (404):**
```json
{
  "error": "User not found"
}
```

---

## Admin - Configuration Management

### 1. Get Deposit Banks (Admin)

**Endpoint:** `GET /admin/deposit-banks`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Success Response (200):**
```json
{
  "depositBanks": [
    {
      "id": 1,
      "bankName": "Chase Bank",
      "accountNumber": "1234567890",
      "accountName": "Betting Payment Manager",
      "notes": "Primary deposit account",
      "isActive": true,
      "createdAt": "2025-10-25T11:17:41.000Z",
      "updatedAt": "2025-10-25T11:17:41.000Z"
    }
  ]
}
```

---

### 2. Create Deposit Bank

**Endpoint:** `POST /admin/deposit-banks`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Request Body:**
```json
{
  "bankName": "New Bank",
  "accountNumber": "9876543210",
  "accountName": "Betting Payment Manager",
  "notes": "New deposit account",
  "isActive": true
}
```

**Success Response (201):**
```json
{
  "message": "Deposit bank created successfully",
  "depositBank": {
    "id": 4,
    "bankName": "New Bank",
    "accountNumber": "9876543210",
    "accountName": "Betting Payment Manager",
    "notes": "New deposit account",
    "isActive": true,
    "createdAt": "2025-10-25T12:00:00.000Z",
    "updatedAt": "2025-10-25T12:00:00.000Z"
  }
}
```

**Error Response (400):**
```json
{
  "error": "Validation failed",
  "details": ["\"bankName\" is required"]
}
```

---

### 3. Update Deposit Bank

**Endpoint:** `PUT /admin/deposit-banks/:id`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Request Body:**
```json
{
  "bankName": "Updated Bank Name",
  "accountNumber": "9876543210",
  "accountName": "Updated Account Name",
  "notes": "Updated notes",
  "isActive": true
}
```

**Success Response (200):**
```json
{
  "message": "Deposit bank updated successfully",
  "depositBank": {
    "id": 1,
    "bankName": "Updated Bank Name",
    "accountNumber": "9876543210",
    "accountName": "Updated Account Name",
    "notes": "Updated notes",
    "isActive": true,
    "updatedAt": "2025-10-25T12:05:00.000Z"
  }
}
```

**Error Response (404):**
```json
{
  "error": "Deposit bank not found"
}
```

---

### 4. Delete Deposit Bank

**Endpoint:** `DELETE /admin/deposit-banks/:id`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Success Response (200):**
```json
{
  "message": "Deposit bank deleted successfully"
}
```

**Error Response (404):**
```json
{
  "error": "Deposit bank not found"
}
```

---

### 5. Get Withdrawal Banks (Admin)

**Endpoint:** `GET /admin/withdrawal-banks`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Success Response (200):**
```json
{
  "withdrawalBanks": [
    {
      "id": 1,
      "bankName": "Chase Bank",
      "requiredFields": [
        {
          "name": "account_number",
          "label": "Account Number",
          "type": "text",
          "required": true
        }
      ],
      "notes": "Primary withdrawal bank",
      "isActive": true,
      "createdAt": "2025-10-25T11:17:41.000Z",
      "updatedAt": "2025-10-25T11:17:41.000Z"
    }
  ]
}
```

---

### 6. Create Withdrawal Bank

**Endpoint:** `POST /admin/withdrawal-banks`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Request Body:**
```json
{
  "bankName": "New Withdrawal Bank",
  "requiredFields": [
    {
      "name": "account_number",
      "label": "Account Number",
      "type": "text",
      "required": true
    },
    {
      "name": "routing_number",
      "label": "Routing Number",
      "type": "text",
      "required": true
    }
  ],
  "notes": "New withdrawal bank",
  "isActive": true
}
```

**Success Response (201):**
```json
{
  "message": "Withdrawal bank created successfully",
  "withdrawalBank": {
    "id": 4,
    "bankName": "New Withdrawal Bank",
    "requiredFields": [
      {
        "name": "account_number",
        "label": "Account Number",
        "type": "text",
        "required": true
      },
      {
        "name": "routing_number",
        "label": "Routing Number",
        "type": "text",
        "required": true
      }
    ],
    "notes": "New withdrawal bank",
    "isActive": true,
    "createdAt": "2025-10-25T12:00:00.000Z",
    "updatedAt": "2025-10-25T12:00:00.000Z"
  }
}
```

---

### 7. Update Withdrawal Bank

**Endpoint:** `PUT /admin/withdrawal-banks/:id`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Request Body:**
```json
{
  "bankName": "Updated Withdrawal Bank",
  "requiredFields": [
    {
      "name": "account_number",
      "label": "Account Number",
      "type": "text",
      "required": true
    }
  ],
  "notes": "Updated notes",
  "isActive": true
}
```

**Success Response (200):**
```json
{
  "message": "Withdrawal bank updated successfully",
  "withdrawalBank": {
    "id": 1,
    "bankName": "Updated Withdrawal Bank",
    "requiredFields": [...],
    "notes": "Updated notes",
    "isActive": true,
    "updatedAt": "2025-10-25T12:05:00.000Z"
  }
}
```

**Error Response (404):**
```json
{
  "error": "Withdrawal bank not found"
}
```

---

### 8. Delete Withdrawal Bank

**Endpoint:** `DELETE /admin/withdrawal-banks/:id`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Success Response (200):**
```json
{
  "message": "Withdrawal bank deleted successfully"
}
```

**Error Response (404):**
```json
{
  "error": "Withdrawal bank not found"
}
```

---

### 9. Get Templates (Admin)

**Endpoint:** `GET /admin/templates`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Query Parameters:**
- `languageCode` (optional): Filter by language code

**Success Response (200):**
```json
{
  "templates": [
    {
      "id": 1,
      "languageCode": "en",
      "keyName": "welcome_message",
      "content": "Welcome to Betting Payment Manager!",
      "createdAt": "2025-10-25T11:17:41.000Z",
      "updatedAt": "2025-10-25T11:17:41.000Z"
    }
  ]
}
```

---

### 10. Create Template

**Endpoint:** `POST /admin/templates`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Request Body:**
```json
{
  "languageCode": "en",
  "keyName": "custom_message",
  "content": "This is a custom message template"
}
```

**Success Response (201):**
```json
{
  "message": "Template created successfully",
  "template": {
    "id": 5,
    "languageCode": "en",
    "keyName": "custom_message",
    "content": "This is a custom message template",
    "createdAt": "2025-10-25T12:00:00.000Z",
    "updatedAt": "2025-10-25T12:00:00.000Z"
  }
}
```

**Error Response (409):**
```json
{
  "error": "Template already exists",
  "message": "A template with this key already exists for this language"
}
```

---

### 11. Update Template

**Endpoint:** `PUT /admin/templates/:id`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Request Body:**
```json
{
  "content": "Updated template content"
}
```

**Success Response (200):**
```json
{
  "message": "Template updated successfully",
  "template": {
    "id": 1,
    "languageCode": "en",
    "keyName": "welcome_message",
    "content": "Updated template content",
    "updatedAt": "2025-10-25T12:05:00.000Z"
  }
}
```

**Error Response (404):**
```json
{
  "error": "Template not found"
}
```

---

### 12. Delete Template

**Endpoint:** `DELETE /admin/templates/:id`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Success Response (200):**
```json
{
  "message": "Template deleted successfully"
}
```

**Error Response (404):**
```json
{
  "error": "Template not found"
}
```

---

### 13. Get Languages (Admin)

**Endpoint:** `GET /admin/languages`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Success Response (200):**
```json
{
  "languages": [
    {
      "code": "en",
      "name": "English",
      "isActive": true,
      "createdAt": "2025-10-25T11:17:41.000Z",
      "updatedAt": "2025-10-25T11:17:41.000Z"
    }
  ]
}
```

---

### 14. Create Language

**Endpoint:** `POST /admin/languages`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Request Body:**
```json
{
  "code": "de",
  "name": "German",
  "isActive": true
}
```

**Success Response (201):**
```json
{
  "message": "Language created successfully",
  "language": {
    "code": "de",
    "name": "German",
    "isActive": true,
    "createdAt": "2025-10-25T12:00:00.000Z",
    "updatedAt": "2025-10-25T12:00:00.000Z"
  }
}
```

**Error Response (409):**
```json
{
  "error": "Language already exists"
}
```

---

### 15. Update Language

**Endpoint:** `PUT /admin/languages/:code`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Deutsch",
  "isActive": true
}
```

**Success Response (200):**
```json
{
  "message": "Language updated successfully",
  "language": {
    "code": "de",
    "name": "Deutsch",
    "isActive": true,
    "updatedAt": "2025-10-25T12:05:00.000Z"
  }
}
```

**Error Response (404):**
```json
{
  "error": "Language not found"
}
```

---

### 16. Delete Language

**Endpoint:** `DELETE /admin/languages/:code`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Success Response (200):**
```json
{
  "message": "Language deleted successfully"
}
```

**Error Response (404):**
```json
{
  "error": "Language not found"
}
```

---

## Admin - Betting Sites Management

### 1. Get All Betting Sites (Admin)

**Endpoint:** `GET /admin/betting-sites`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Query Parameters:**
- `isActive` (optional): Filter by active status (true/false)

**Success Response (200):**
```json
{
  "bettingSites": [
    {
      "id": 1,
      "name": "Arada Betting",
      "description": "Arada Betting Platform - Sports betting and casino games",
      "website": "https://arada-betting.com",
      "isActive": true,
      "createdAt": "2025-10-25T11:22:13.000Z",
      "updatedAt": "2025-10-25T11:22:13.000Z"
    }
  ],
  "total": 1
}
```

---

### 2. Get Betting Site by ID (Admin)

**Endpoint:** `GET /admin/betting-sites/:id`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Success Response (200):**
```json
{
  "bettingSite": {
    "id": 1,
    "name": "Arada Betting",
    "description": "Arada Betting Platform - Sports betting and casino games",
    "website": "https://arada-betting.com",
    "isActive": true,
    "createdAt": "2025-10-25T11:22:13.000Z",
    "updatedAt": "2025-10-25T11:22:13.000Z"
  }
}
```

**Error Response (404):**
```json
{
  "error": "Betting site not found"
}
```

---

### 3. Create Betting Site

**Endpoint:** `POST /admin/betting-sites`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "New Betting Site",
  "description": "A new betting platform for sports and casino games",
  "website": "https://new-betting-site.com",
  "isActive": true
}
```

**Success Response (201):**
```json
{
  "message": "Betting site created successfully",
  "bettingSite": {
    "id": 9,
    "name": "New Betting Site",
    "description": "A new betting platform for sports and casino games",
    "website": "https://new-betting-site.com",
    "isActive": true,
    "createdAt": "2025-10-25T12:00:00.000Z",
    "updatedAt": "2025-10-25T12:00:00.000Z"
  }
}
```

**Error Response (409):**
```json
{
  "error": "Betting site already exists",
  "message": "A betting site with this name already exists"
}
```

**Error Response (400):**
```json
{
  "error": "Validation failed",
  "details": ["\"name\" is required"]
}
```

---

### 4. Update Betting Site

**Endpoint:** `PUT /admin/betting-sites/:id`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Updated Betting Site",
  "description": "Updated description for the betting platform",
  "website": "https://updated-betting-site.com",
  "isActive": true
}
```

**Success Response (200):**
```json
{
  "message": "Betting site updated successfully",
  "bettingSite": {
    "id": 1,
    "name": "Updated Betting Site",
    "description": "Updated description for the betting platform",
    "website": "https://updated-betting-site.com",
    "isActive": true,
    "updatedAt": "2025-10-25T12:05:00.000Z"
  }
}
```

**Error Response (404):**
```json
{
  "error": "Betting site not found"
}
```

**Error Response (409):**
```json
{
  "error": "Betting site name already exists",
  "message": "A betting site with this name already exists"
}
```

---

### 5. Toggle Betting Site Status

**Endpoint:** `PUT /admin/betting-sites/:id/toggle-status`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Success Response (200):**
```json
{
  "message": "Betting site deactivated successfully",
  "bettingSite": {
    "id": 1,
    "name": "Arada Betting",
    "isActive": false,
    "updatedAt": "2025-10-25T12:10:00.000Z"
  }
}
```

**Error Response (404):**
```json
{
  "error": "Betting site not found"
}
```

---

### 6. Delete Betting Site

**Endpoint:** `DELETE /admin/betting-sites/:id`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Success Response (200):**
```json
{
  "message": "Betting site deleted successfully"
}
```

**Error Response (404):**
```json
{
  "error": "Betting site not found"
}
```

---

## Agent Operations

### 1. Get Assigned Tasks

**Endpoint:** `GET /agent/tasks`

**Headers:**
```
Authorization: Bearer AGENT_ACCESS_TOKEN
```

**Query Parameters:**
- `status` (optional): Filter by status (PENDING, IN_PROGRESS, SUCCESS, FAILED)
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)

**Success Response (200):**
```json
{
  "tasks": [
    {
      "id": 1,
      "transactionUuid": "98bc140c-99ed-4406-b803-f8a0051f0693",
      "type": "DEPOSIT",
      "amount": "100.00",
      "currency": "USD",
      "status": "Pending",
      "depositBank": {
        "id": 1,
        "bankName": "Chase Bank",
        "accountNumber": "1234567890"
      },
      "withdrawalBank": null,
      "withdrawalAddress": null,
      "screenshotUrl": null,
      "bettingSiteId": 1,
      "playerSiteId": "player123",
      "requestedAt": "2025-10-25T12:00:00.000Z",
      "adminNotes": null,
      "agentNotes": null,
      "rating": null,
      "playerProfile": {
        "id": 1,
        "playerUuid": "e804346f-e513-4ae2-9cfa-7584c3ea1698",
        "telegramUsername": "player123"
      },
      "evidence": [],
      "createdAt": "2025-10-25T12:00:00.000Z",
      "updatedAt": "2025-10-25T12:00:00.000Z"
    }
  ],
  "pagination": {
    "total": 1,
    "page": 1,
    "limit": 20,
    "pages": 1
  }
}
```

**Error Response (401):**
```json
{
  "error": "Agent ID not found"
}
```

**Error Response (500):**
```json
{
  "error": "Failed to get tasks",
  "message": "Internal server error while fetching agent tasks",
  "details": "Database connection failed"
}
```

---

### 2. Process Transaction

**Endpoint:** `PUT /agent/transactions/:id/process`

**Headers:**
```
Authorization: Bearer AGENT_ACCESS_TOKEN
Content-Type: application/json
```

**Request Body:**
```json
{
  "status": "SUCCESS",
  "agentNotes": "Payment verified and processed",
  "evidenceUrl": "https://example.com/receipt.jpg"
}
```

**Success Response (200):**
```json
{
  "message": "Transaction processed successfully",
  "transaction": {
    "id": 1,
    "transactionUuid": "98bc140c-99ed-4406-b803-f8a0051f0693",
    "status": "Success",
    "agentNotes": "Payment verified and processed",
    "evidenceUrl": "https://example.com/receipt.jpg",
    "updatedAt": "2025-10-25T12:10:00.000Z"
  }
}
```

**Error Response (403):**
```json
{
  "error": "Access denied. This transaction is not assigned to you.",
  "message": "You can only process transactions assigned to you"
}
```

**Error Response (404):**
```json
{
  "error": "Transaction not found",
  "message": "The requested transaction does not exist"
}
```

**Error Response (400):**
```json
{
  "error": "Invalid status",
  "message": "The provided status is not valid",
  "validStatuses": ["PENDING", "IN_PROGRESS", "SUCCESS", "FAILED", "CANCELLED"]
}
```

**Error Response (500):**
```json
{
  "error": "Failed to process transaction",
  "message": "Internal server error while processing transaction",
  "details": "Database connection failed"
}
```

---

### 3. Upload Evidence

**Endpoint:** `POST /agent/evidence`

**Headers:**
```
Authorization: Bearer AGENT_ACCESS_TOKEN
```

**Content-Type:** `multipart/form-data`

**Form Data:**
- `file`: [PNG/JPG/JPEG file]

**Success Response (200):**
```json
{
  "message": "Evidence uploaded successfully",
  "fileUrl": "http://localhost:3000/uploads/evidence-1234567890.png",
  "filename": "evidence-1234567890.png",
  "file": {
    "filename": "evidence-1234567890.png",
    "originalName": "receipt.png",
    "mimetype": "image/png",
    "size": 102400,
    "url": "http://localhost:3000/uploads/evidence-1234567890.png"
  }
}
```

**Error Response (400):**
```json
{
  "error": "No file uploaded",
  "message": "Please select a file to upload"
}
```

**Error Response (400):**
```json
{
  "error": "Invalid file type. Only PNG, JPG, and JPEG files are allowed."
}
```

**Error Response (500):**
```json
{
  "error": "Failed to upload evidence",
  "message": "Internal server error while uploading file",
  "details": "File system error"
}
```

---

### 4. Get Agent Statistics

**Endpoint:** `GET /agent/stats`

**Headers:**
```
Authorization: Bearer AGENT_ACCESS_TOKEN
```

**Success Response (200):**
```json
{
  "stats": {
    "totalAssigned": 10,
    "pending": 3,
    "inProgress": 2,
    "completed": 5,
    "failed": 0,
    "averageRating": 4.5,
    "totalAmount": "1500.00",
    "recentActivity": 8
  },
  "recentTransactions": [
    {
      "id": 1,
      "transactionUuid": "98bc140c-99ed-4406-b803-f8a0051f0693",
      "type": "DEPOSIT",
      "amount": "100.00",
      "currency": "USD",
      "status": "Success",
      "createdAt": "2025-10-25T12:00:00.000Z"
    }
  ]
}
```

**Error Response (401):**
```json
{
  "error": "Agent ID not found"
}
```

**Error Response (500):**
```json
{
  "error": "Failed to get agent statistics",
  "message": "Internal server error while fetching agent statistics",
  "details": "Database connection failed"
}
```

---

## File Upload

### 1. Upload File

**Endpoint:** `POST /uploads`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Content-Type:** `multipart/form-data`

**Form Data:**
- `file`: [PNG/JPG/JPEG file, max 5MB]

**Success Response (200):**
```json
{
  "message": "File uploaded successfully",
  "file": {
    "filename": "upload-1234567890.png",
    "originalName": "screenshot.png",
    "mimetype": "image/png",
    "size": 102400,
    "url": "http://localhost:3000/uploads/upload-1234567890.png"
  }
}
```

**Error Response (400):**
```json
{
  "error": "Invalid file type. Only PNG, JPG, and JPEG files are allowed."
}
```

**Error Response (400):**
```json
{
  "error": "File too large. Maximum size is 5MB."
}
```

---

### 2. Get File

**Endpoint:** `GET /uploads/:filename`

**Success Response (200):**
- Returns the file content with appropriate Content-Type header

**Error Response (404):**
```json
{
  "error": "File not found"
}
```

---

### 3. Delete File

**Endpoint:** `DELETE /uploads/:filename`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Success Response (200):**
```json
{
  "message": "File deleted successfully"
}
```

**Error Response (404):**
```json
{
  "error": "File not found"
}
```

---

### 4. Get Upload Configuration

**Endpoint:** `GET /uploads/config`

**Success Response (200):**
```json
{
  "maxFileSize": 5242880,
  "allowedMimeTypes": [
    "image/png",
    "image/jpeg",
    "image/jpg"
  ],
  "uploadPath": "/uploads",
  "storageType": "local"
}
```

---

## Error Responses

### Common Error Codes

#### 400 - Bad Request
```json
{
  "error": "Validation failed",
  "details": [
    "\"amount\" is required",
    "\"type\" must be one of [DEPOSIT, WITHDRAW]"
  ]
}
```

#### 401 - Unauthorized
```json
{
  "error": "Access token required"
}
```

```json
{
  "error": "Invalid or expired token"
}
```

```json
{
  "error": "Invalid credentials"
}
```

#### 403 - Forbidden
```json
{
  "error": "Access denied. Admin role required."
}
```

```json
{
  "error": "Access denied. This transaction is not assigned to you."
}
```

#### 404 - Not Found
```json
{
  "error": "Resource not found"
}
```

```json
{
  "error": "Player not found"
}
```

```json
{
  "error": "Transaction not found"
}
```

```json
{
  "error": "User not found"
}
```

```json
{
  "error": "Betting site not found"
}
```

#### 409 - Conflict
```json
{
  "error": "User already exists",
  "message": "A user with this username already exists"
}
```

```json
{
  "error": "Player already exists",
  "message": "A player with this Telegram ID already exists"
}
```

```json
{
  "error": "Betting site already exists",
  "message": "A betting site with this name already exists"
}
```

#### 429 - Too Many Requests
```json
{
  "error": "Too many requests, please try again later."
}
```

#### 500 - Internal Server Error
```json
{
  "error": "Internal server error",
  "message": "An unexpected error occurred"
}
```

```json
{
  "error": "Failed to create transaction",
  "message": "Internal server error",
  "details": "Database connection failed"
}
```

---

## Notes

### Authentication
- All admin endpoints require `Authorization: Bearer YOUR_ACCESS_TOKEN` header
- All agent endpoints require `Authorization: Bearer AGENT_ACCESS_TOKEN` header
- Access tokens expire after 30 days (2592000 seconds)
- Use refresh token to get a new access token

### Role IDs
- **Admin**: Role ID = 7
- **Agent**: Role ID = 8
- **Player**: Role ID = 9

### Default Credentials
- **Admin**: `admin@example.com` / `AdminPass123!`
- **Agent**: `agent@example.com` / `AgentPass123!`

### Transaction Types
- **DEPOSIT**: Requires `depositBankId`, `bettingSiteId`, and `playerSiteId`
- **WITHDRAW**: Requires `withdrawalBankId`, `withdrawalAddress`, `bettingSiteId`, and `playerSiteId`

### Transaction Statuses
- **PENDING**: Initial status
- **IN_PROGRESS**: Agent is processing
- **SUCCESS**: Completed successfully
- **FAILED**: Failed to process
- **CANCELLED**: Cancelled by admin

### File Upload
- Supported formats: PNG, JPG, JPEG
- Maximum file size: 5MB
- Files are stored locally in `/uploads` directory
- S3 storage is available if configured

### Betting Sites
- 8 pre-configured betting sites available
- Required for all DEPOSIT transactions
- Agents can see betting site details when processing transactions

### Rate Limiting
- Auth endpoints: 50 requests per 15 minutes
- Transaction endpoints: 100 requests per 15 minutes
- Public endpoints: 100 requests per 15 minutes

### Pagination
- Default page: 1
- Default limit: 10 (transactions), 20 (users)
- Maximum limit: 100

### Timestamps
- All timestamps are in ISO 8601 format
- Timezone: UTC
- Example: `2025-10-25T12:00:00.000Z`

### Currency
- Default currency: USD
- Amounts are returned as strings to preserve precision
- Example: `"100.00"` instead of `100`
