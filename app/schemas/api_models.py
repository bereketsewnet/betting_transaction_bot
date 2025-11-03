"""Pydantic models matching API request/response formats."""
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator


class Language(BaseModel):
    """Language model."""
    code: str
    name: str
    isActive: bool = True  # Default to True if not provided


class WelcomeResponse(BaseModel):
    """Welcome message response."""
    message: str
    languageCode: str


class DepositBank(BaseModel):
    """Deposit bank model."""
    id: int
    bankName: str
    accountNumber: str
    accountName: str
    notes: Optional[str] = None
    isActive: bool = True  # Default to True if not provided


class RequiredField(BaseModel):
    """Required field for withdrawal banks."""
    name: str
    label: str
    type: str
    required: bool


class WithdrawalBank(BaseModel):
    """Withdrawal bank model."""
    id: int
    bankName: str
    requiredFields: Optional[List[RequiredField]] = []
    notes: Optional[str] = None
    isActive: bool = True  # Default to True if not provided


class BettingSite(BaseModel):
    """Betting site model."""
    id: int
    name: str
    description: Optional[str] = None
    website: Optional[str] = None
    isActive: bool


class PlayerCreateRequest(BaseModel):
    """Player creation request."""
    telegramId: str
    telegramUsername: Optional[str] = None
    languageCode: str


class PlayerRegisterRequest(BaseModel):
    """Player registration request."""
    telegramId: str
    telegramUsername: Optional[str] = None
    languageCode: str
    username: str
    email: str
    password: str
    displayName: str
    phone: Optional[str] = None


class Player(BaseModel):
    """Player model."""
    id: int
    playerUuid: str
    telegramId: Optional[str] = None
    telegramUsername: Optional[str] = None
    languageCode: Optional[str] = None
    isTemporary: Optional[bool] = False


class PlayerResponse(BaseModel):
    """Player API response."""
    message: Optional[str] = None
    player: Player


class TransactionCreateRequest(BaseModel):
    """Transaction creation request."""
    playerUuid: str
    type: str = Field(..., pattern="^(DEPOSIT|WITHDRAW)$")
    amount: float
    currency: str = "ETB"
    depositBankId: Optional[int] = None
    withdrawalBankId: Optional[int] = None
    withdrawalAddress: Optional[str] = None
    bettingSiteId: int
    playerSiteId: str
    screenshotUrl: Optional[str] = None


class Transaction(BaseModel):
    """Transaction model."""
    id: int
    transactionUuid: str
    type: str
    amount: Union[str, int, float]  # Accept int, float, or str
    currency: str
    status: str
    depositBank: Optional[DepositBank] = None
    withdrawalBank: Optional[WithdrawalBank] = None
    withdrawalAddress: Optional[str] = None
    screenshotUrl: Optional[str] = None
    bettingSiteId: Optional[int] = None
    playerSiteId: Optional[str] = None
    requestedAt: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    
    @field_validator('amount', mode='before')
    @classmethod
    def convert_amount_to_string(cls, v):
        """Convert amount to string if it's int or float."""
        if isinstance(v, (int, float)):
            return str(v)
        return v


class TransactionResponse(BaseModel):
    """Transaction API response."""
    message: Optional[str] = None
    transaction: Transaction


class TransactionListResponse(BaseModel):
    """Transaction list response."""
    transactions: List[Transaction]
    pagination: Dict[str, Any]


class UploadConfigResponse(BaseModel):
    """Upload configuration response."""
    maxFileSize: int
    allowedMimeTypes: List[str]
    uploadPath: str
    storageType: str


class UploadResponse(BaseModel):
    """File upload response."""
    message: str
    file: Dict[str, Any]
    url: Optional[str] = None
    filename: Optional[str] = None


class ApiError(BaseModel):
    """API error response."""
    error: str
    message: Optional[str] = None
    details: Optional[List[str]] = None

