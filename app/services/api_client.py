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
            # Log request body but mask sensitive fields for security
            safe_json = {k: (v if k != "password" else "***" * len(str(v))) for k, v in json_data.items()}
            logger.debug(f"   JSON: {safe_json}")
            logger.info(f"   Request body keys: {list(json_data.keys())}")
        
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
    
    async def get_template(self, key: str, lang: str = "en") -> Dict[str, Any]:
        """Get template by key and language (with fallback to English)."""
        response = await self._request("GET", "config/template", params={"key": key, "lang": lang})
        return response.json()
    
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
                # Fix API typo: bankNamee -> bankName (if present)
                if "bankNamee" in bank_data and "bankName" not in bank_data:
                    bank_data["bankName"] = bank_data.pop("bankNamee")
                    logger.debug(f"   Fixed typo: bankNamee -> bankName")
                
                # Ensure isActive has a default
                if "isActive" not in bank_data:
                    bank_data["isActive"] = True
                
                # Validate required fields
                if "id" not in bank_data or "bankName" not in bank_data:
                    logger.warning(f"⚠️ Skipping deposit bank with missing id or bankName: {bank_data}")
                    continue
                
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
                # Fix API typo: bankNamee -> bankName
                if "bankNamee" in bank_data and "bankName" not in bank_data:
                    bank_data["bankName"] = bank_data.pop("bankNamee")
                    logger.debug(f"   Fixed typo: bankNamee -> bankName")
                
                # Ensure isActive has a default
                if "isActive" not in bank_data:
                    bank_data["isActive"] = True
                
                # Parse requiredFields if it's a JSON string
                if "requiredFields" in bank_data:
                    required_fields = bank_data["requiredFields"]
                    if isinstance(required_fields, str):
                        # It's a JSON string, parse it
                        import json
                        try:
                            bank_data["requiredFields"] = json.loads(required_fields)
                            logger.debug(f"   Parsed requiredFields from JSON string to list: {len(bank_data['requiredFields'])} fields")
                        except json.JSONDecodeError as e:
                            logger.warning(f"⚠️ Failed to parse requiredFields JSON: {e}")
                            bank_data["requiredFields"] = []
                    elif not isinstance(required_fields, list):
                        logger.warning(f"⚠️ requiredFields is neither string nor list, setting to empty: {type(required_fields)}")
                        bank_data["requiredFields"] = []
                else:
                    # Ensure requiredFields exists
                    bank_data["requiredFields"] = []
                    logger.debug(f"   Added default requiredFields: []")
                
                # Validate required fields
                if "id" not in bank_data or "bankName" not in bank_data:
                    logger.warning(f"⚠️ Skipping bank with missing id or bankName: {bank_data}")
                    continue
                
                banks.append(WithdrawalBank(**bank_data))
            except Exception as e:
                logger.warning(f"⚠️ Skipping invalid withdrawal bank data: {bank_data}, error: {e}")
        
        logger.info(f"✅ Parsed {len(banks)} valid withdrawal banks")
        return banks
    
    async def get_betting_sites(self, is_active: bool = True) -> List[BettingSite]:
        """Get betting sites. Only returns sites where isActive = true."""
        params = {"isActive": str(is_active).lower()} if is_active else {}
        response = await self._request("GET", "config/betting-sites", params=params)
        data = response.json()
        
        # Parse all sites first
        all_sites = [BettingSite(**site) for site in data.get("bettingSites", [])]
        
        # Filter to only return active sites (client-side safety check)
        if is_active:
            active_sites = [site for site in all_sites if site.isActive]
            logger.debug(f"📊 Filtered betting sites: {len(active_sites)} active from {len(all_sites)} total")
            return active_sites
        
        return all_sites
    
    # Authentication endpoints
    
    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """Login user and get access token."""
        payload = {
            "username": username,
            "password": password,
        }
        logger.info(f"🔐 Login request payload: username='{username}', password_length={len(password)}")
        logger.debug(f"   Full payload: {payload}")
        try:
            response = await self._request("POST", "auth/login", json_data=payload)
            result = response.json()
            logger.info(f"✅ Login response received: {list(result.keys())}")
            return result
        except Exception as e:
            logger.error(f"❌ Login request failed: {e}")
            logger.error(f"   Username: {username}")
            logger.error(f"   Password length: {len(password)}")
            raise

    async def telegram_login(
        self,
        phone: str,
        telegram_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Login or register via Telegram contact."""
        payload = {
            "phone": phone,
            "telegramId": telegram_id,
            "firstName": first_name,
            "lastName": last_name,
            "username": username,
        }
        logger.info(f"📱 Telegram login request for user {telegram_id} (phone: {phone})")
        
        response = await self._request("POST", "auth/telegram-login", json_data=payload)
        result = response.json()
        logger.info(f"✅ Telegram login success for user {telegram_id}")
        return result
    
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
    
    # Admin endpoints
    
    async def get_admin_transactions(
        self,
        access_token: str,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
        transaction_type: Optional[str] = None,
        agent_id: Optional[int] = None,
        date_range: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get all transactions (admin only)."""
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"page": page, "limit": limit}
        if status:
            params["status"] = status
        if transaction_type:
            params["type"] = transaction_type
        if agent_id:
            params["agent"] = agent_id
        if date_range:
            params["dateRange"] = date_range
        
        response = await self._request("GET", "admin/transactions", params=params, headers=headers)
        return response.json()
    
    async def assign_transaction_to_agent(
        self,
        access_token: str,
        transaction_id: int,
        agent_id: int,
    ) -> Dict[str, Any]:
        """Assign transaction to agent (admin only)."""
        headers = {"Authorization": f"Bearer {access_token}"}
        json_data = {"agentId": agent_id}
        response = await self._request(
            "PUT",
            f"admin/transactions/{transaction_id}/assign",
            json_data=json_data,
            headers=headers,
        )
        return response.json()
    
    async def update_transaction_status(
        self,
        access_token: str,
        transaction_id: int,
        status: str,
        admin_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update transaction status (admin only)."""
        headers = {"Authorization": f"Bearer {access_token}"}
        json_data = {"status": status}
        if admin_notes:
            json_data["adminNotes"] = admin_notes
        response = await self._request(
            "PUT",
            f"admin/transactions/{transaction_id}/status",
            json_data=json_data,
            headers=headers,
        )
        return response.json()
    
    async def get_agents(self, access_token: str) -> Dict[str, Any]:
        """Get all agents with statistics (admin only)."""
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await self._request("GET", "admin/agents", headers=headers)
        return response.json()
    
    # Agent endpoints
    
    async def get_agent_tasks(
        self,
        access_token: str,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
        date_range: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get assigned tasks for agent."""
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"page": page, "limit": limit}
        if status:
            params["status"] = status
        if date_range:
            params["dateRange"] = date_range
        
        response = await self._request("GET", "agent/tasks", params=params, headers=headers)
        return response.json()
    
    async def process_transaction(
        self,
        access_token: str,
        transaction_id: int,
        status: str,
        agent_notes: Optional[str] = None,
        evidence_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process/update transaction (agent only)."""
        headers = {"Authorization": f"Bearer {access_token}"}
        json_data = {"status": status}
        if agent_notes:
            json_data["agentNotes"] = agent_notes
        if evidence_url:
            json_data["evidenceUrl"] = evidence_url
        
        response = await self._request(
            "PUT",
            f"agent/transactions/{transaction_id}/process",
            json_data=json_data,
            headers=headers,
        )
        return response.json()
    
    async def get_agent_stats(self, access_token: str) -> Dict[str, Any]:
        """Get agent statistics."""
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await self._request("GET", "agent/stats", headers=headers)
        return response.json()

