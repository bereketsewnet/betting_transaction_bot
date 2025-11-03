"""HTTP client for API integration."""
import httpx
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging
from app.config import config

logger = logging.getLogger(__name__)
from app.schemas.api_models import (
    Language,
    WelcomeResponse,
    DepositBank,
    WithdrawalBank,
    BettingSite,
    PlayerResponse,
    TransactionResponse,
    TransactionListResponse,
    UploadConfigResponse,
    UploadResponse,
    ApiError,
)

logger = logging.getLogger(__name__)


class APIClient:
    """Async HTTP client for Betting Payment Manager API."""
    
    def __init__(self, base_url: str = None, timeout: float = 30.0):
        self.base_url = base_url or config.API_BASE_URL
        self.timeout = httpx.Timeout(timeout)
        self.client = httpx.AsyncClient(timeout=self.timeout, follow_redirects=True)
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> httpx.Response:
        """Make HTTP request with error handling."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        # Parse URL to show host details
        from urllib.parse import urlparse
        parsed = urlparse(url)
        
        # Log the full URL and host being called
        logger.info(f"🌐 API Request: {method} {url}")
        logger.info(f"   Host: {parsed.netloc}")
        logger.info(f"   Path: {parsed.path}")
        if params:
            logger.debug(f"   Params: {params}")
        if json_data:
            logger.debug(f"   JSON: {json_data}")
        
        try:
            response = await self.client.request(
                method=method,
                url=url,
                json=json_data,
                files=files,
                params=params,
                headers=headers,
            )
            logger.info(f"📡 API Response: {method} {url} - Status: {response.status_code}")
            if response.status_code >= 400:
                logger.error(f"   Response body: {response.text[:500]}")
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ API Error {e.response.status_code}: {method} {url}")
            logger.error(f"   Host: {parsed.netloc}")
            logger.error(f"   Response: {e.response.text[:500]}")
            logger.error(f"   Headers: {dict(e.response.headers)}")
            raise
        except httpx.RequestError as e:
            logger.error(f"❌ Request Error: {method} {url}")
            logger.error(f"   Host: {parsed.netloc}")
            logger.error(f"   Error: {e}")
            raise
    
    # Configuration endpoints
    
    async def get_languages(self) -> List[Language]:
        """Get available languages."""
        response = await self._request("GET", "config/languages")
        data = response.json()
        logger.debug(f"📋 Languages response: {data}")
        languages = []
        for lang in data.get("languages", []):
            try:
                languages.append(Language(**lang))
            except Exception as e:
                logger.warning(f"⚠️ Skipping invalid language data: {lang}, error: {e}")
                # Try with default isActive
                lang_with_default = {**lang, "isActive": lang.get("isActive", True)}
                languages.append(Language(**lang_with_default))
        return languages
    
    async def get_welcome(self, lang: str) -> WelcomeResponse:
        """Get welcome message for language."""
        response = await self._request("GET", f"config/welcome", params={"lang": lang})
        return WelcomeResponse(**response.json())
    
    async def get_deposit_banks(self) -> List[DepositBank]:
        """Get deposit banks."""
        response = await self._request("GET", "config/deposit-banks")
        data = response.json()
        logger.debug(f"📦 Deposit banks API response: {type(data)}")
        
        # Handle different response structures
        banks_list = []
        if isinstance(data, list):
            # Direct array response
            banks_list = data
        elif isinstance(data, dict):
            # Object with depositBanks key
            banks_list = data.get("depositBanks", [])
            # Also try "banks" or "data" keys as fallback
            if not banks_list:
                banks_list = data.get("banks", data.get("data", []))
        
        logger.info(f"📊 Found {len(banks_list)} deposit banks in response")
        
        # Parse banks with error handling
        banks = []
        for bank_data in banks_list:
            try:
                # Ensure isActive has a default
                if "isActive" not in bank_data:
                    bank_data["isActive"] = True
                banks.append(DepositBank(**bank_data))
            except Exception as e:
                logger.warning(f"⚠️ Skipping invalid deposit bank data: {bank_data}, error: {e}")
        
        logger.info(f"✅ Parsed {len(banks)} valid deposit banks")
        return banks
    
    async def get_withdrawal_banks(self) -> List[WithdrawalBank]:
        """Get withdrawal banks."""
        response = await self._request("GET", "config/withdrawal-banks")
        data = response.json()
        logger.debug(f"📦 Withdrawal banks API response: {type(data)}")
        
        # Handle different response structures
        banks_list = []
        if isinstance(data, list):
            # Direct array response
            banks_list = data
        elif isinstance(data, dict):
            # Object with withdrawalBanks key
            banks_list = data.get("withdrawalBanks", [])
            # Also try "banks" or "data" keys as fallback
            if not banks_list:
                banks_list = data.get("banks", data.get("data", []))
        
        logger.info(f"📊 Found {len(banks_list)} withdrawal banks in response")
        
        # Parse banks with error handling
        banks = []
        for bank_data in banks_list:
            try:
                # Ensure isActive has a default
                if "isActive" not in bank_data:
                    bank_data["isActive"] = True
                # Ensure requiredFields exists
                if "requiredFields" not in bank_data:
                    bank_data["requiredFields"] = []
                banks.append(WithdrawalBank(**bank_data))
            except Exception as e:
                logger.warning(f"⚠️ Skipping invalid withdrawal bank data: {bank_data}, error: {e}")
        
        logger.info(f"✅ Parsed {len(banks)} valid withdrawal banks")
        return banks
    
    async def get_betting_sites(self, is_active: bool = True) -> List[BettingSite]:
        """Get betting sites."""
        params = {"isActive": str(is_active).lower()} if is_active else {}
        response = await self._request("GET", "config/betting-sites", params=params)
        data = response.json()
        return [BettingSite(**site) for site in data.get("bettingSites", [])]
    
    # Authentication endpoints
    
    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """Login user and get access token."""
        payload = {
            "username": username,
            "password": password,
        }
        response = await self._request("POST", "auth/login", json_data=payload)
        return response.json()
    
    async def logout(self) -> Dict[str, Any]:
        """Logout user."""
        response = await self._request("POST", "auth/logout", json_data={})
        return response.json()
    
    async def get_player_by_user_id(self, user_id: int) -> PlayerResponse:
        """Get player by user ID (after login)."""
        response = await self._request("GET", f"players/user/{user_id}")
        return PlayerResponse(**response.json())
    
    # Player endpoints
    
    async def create_player(
        self,
        telegram_id: str,
        telegram_username: Optional[str] = None,
        language_code: str = "en",
    ) -> PlayerResponse:
        """Create temporary/guest player."""
        payload = {
            "telegramId": telegram_id,
            "telegramUsername": telegram_username,
            "languageCode": language_code,
        }
        response = await self._request("POST", "players", json_data=payload)
        return PlayerResponse(**response.json())
    
    async def register_player(
        self,
        telegram_id: str,
        telegram_username: Optional[str],
        language_code: str,
        username: str,
        email: str,
        password: str,
        display_name: str,
        phone: Optional[str] = None,
    ) -> PlayerResponse:
        """Register player with full account using /players/register endpoint."""
        # Build payload for /players/register endpoint
        payload = {
            "username": email,  # Email is used as username
            "email": email,
            "password": password,
            "displayName": display_name,
            "languageCode": language_code,
        }
        if phone:
            payload["phone"] = phone
        
        logger.info(f"🔄 Registering player: email={email}, languageCode={language_code}")
        
        # Register player via /players/register
        response = await self._request("POST", "players/register", json_data=payload)
        player_data = response.json()
        logger.info(f"✅ Player registered: {player_data.get('player', {}).get('playerUuid')}")
        
        return PlayerResponse(**player_data)
    
    async def get_player(self, player_uuid: str) -> PlayerResponse:
        """Get player by UUID."""
        response = await self._request("GET", f"players/{player_uuid}")
        return PlayerResponse(**response.json())
    
    # Transaction endpoints
    
    async def create_transaction(
        self,
        player_uuid: str,
        transaction_type: str,
        amount: float,
        currency: str,
        betting_site_id: int,
        player_site_id: str,
        deposit_bank_id: Optional[int] = None,
        withdrawal_bank_id: Optional[int] = None,
        withdrawal_address: Optional[str] = None,
        screenshot_path: Optional[Path] = None,
    ) -> TransactionResponse:
        """Create transaction with optional file upload."""
        if screenshot_path and screenshot_path.exists():
            # Multipart upload
            data = {
                "playerUuid": player_uuid,
                "type": transaction_type,
                "amount": str(amount),
                "currency": currency,
                "bettingSiteId": str(betting_site_id),
                "playerSiteId": player_site_id,
            }
            if deposit_bank_id:
                data["depositBankId"] = str(deposit_bank_id)
            if withdrawal_bank_id:
                data["withdrawalBankId"] = str(withdrawal_bank_id)
            if withdrawal_address:
                data["withdrawalAddress"] = withdrawal_address
            
            # Open file and upload
            with open(screenshot_path, "rb") as f:
                files_data = {
                    "screenshot": (screenshot_path.name, f, "image/jpeg")
                }
                # Use multipart form data
                response = await self.client.post(
                    f"{self.base_url}/transactions",
                    files=files_data,
                    data=data,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return TransactionResponse(**response.json())
        else:
            # JSON upload
            payload = {
                "playerUuid": player_uuid,
                "type": transaction_type,
                "amount": amount,
                "currency": currency,
                "bettingSiteId": betting_site_id,
                "playerSiteId": player_site_id,
            }
            if deposit_bank_id:
                payload["depositBankId"] = deposit_bank_id
            if withdrawal_bank_id:
                payload["withdrawalBankId"] = withdrawal_bank_id
            if withdrawal_address:
                payload["withdrawalAddress"] = withdrawal_address
            
            response = await self._request("POST", "transactions", json_data=payload)
            return TransactionResponse(**response.json())
    
    async def get_transactions(
        self,
        player_uuid: str,
        page: int = 1,
        limit: int = 10,
    ) -> TransactionListResponse:
        """Get player transactions."""
        params = {
            "playerUuid": player_uuid,
            "page": page,
            "limit": limit,
        }
        response = await self._request("GET", "transactions", params=params)
        return TransactionListResponse(**response.json())
    
    async def get_transaction(
        self,
        transaction_id: str,
        player_uuid: Optional[str] = None,
    ) -> TransactionResponse:
        """Get transaction details."""
        params = {"player_uuid": player_uuid} if player_uuid else {}
        response = await self._request("GET", f"transactions/{transaction_id}", params=params)
        return TransactionResponse(**response.json())
    
    # File upload endpoints
    
    async def get_upload_config(self) -> UploadConfigResponse:
        """Get file upload configuration."""
        response = await self._request("GET", "uploads/config")
        return UploadConfigResponse(**response.json())
    
    async def upload_file(self, file_path: Path) -> UploadResponse:
        """Upload file to backend."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, "rb") as f:
            files_data = {"file": (file_path.name, f, "image/jpeg")}
            response = await self.client.post(
                f"{self.base_url}/uploads",
                files=files_data,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return UploadResponse(**response.json())

