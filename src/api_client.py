"""
Unified Platform API Client for BlackTrader / BlackFX
Handles Admin Backoffice & Client OMS interactions.
"""

import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional
from src.config import Config


class PlatformAPIClient:
    def __init__(self, base_url: str = Config.BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.user_agent = Config.USER_AGENT
        self._admin_token = None

    def _request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        token: Optional[str] = None,
        cookie: Optional[str] = None,
        timeout: int = 15,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if cookie:
            headers["Cookie"] = cookie

        encoded_data = None
        if data is not None:
            headers["Content-Type"] = "application/json"
            encoded_data = json.dumps(data).encode("utf-8")

        req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read().decode("utf-8")
            set_cookie = resp.headers.get("Set-Cookie")
            parsed = json.loads(content) if content else {}
            if set_cookie and isinstance(parsed, dict):
                parsed["_cookie"] = set_cookie.split(";")[0]
            return parsed

    # --------------------------------------------------------------------------
    # Admin API (Back-Office)
    # --------------------------------------------------------------------------
    def get_admin_token(self) -> str:
        if self._admin_token:
            return self._admin_token
        res = self._request(
            "/admin/api/login",
            method="POST",
            data={
                "email": Config.BLACKADMIN_EMAIL,
                "password": Config.BLACKADMIN_PASSWORD,
                "remember": True,
            },
        )
        self._admin_token = res.get("token")
        return self._admin_token

    def create_member(self, email: str, password: str, name: str = "Pam Follower") -> Dict[str, Any]:
        token = self.get_admin_token()
        return self._request(
            "/admin/api/members",
            method="POST",
            data={"email": email, "password": password, "name": name},
            token=token,
        )

    def set_member_balance(
        self, member_id: str, balance: float, instance: str = "paper", remark: str = "Seed"
    ) -> Dict[str, Any]:
        token = self.get_admin_token()
        return self._request(
            f"/admin/api/members/{member_id}/balance",
            method="POST",
            data={"instance": instance, "balance": balance, "remark": remark},
            token=token,
        )

    # --------------------------------------------------------------------------
    # Client Portal & OMS Authentication
    # --------------------------------------------------------------------------
    def login_client(self, email: str, password: str) -> str:
        """Logs into Trader portal and returns OMS User Token."""
        login_res = self._request(
            "/api/auth/login",
            method="POST",
            data={"email": email, "password": password, "remember": True},
        )
        cookie = login_res.get("_cookie")
        token_res = self._request("/api/auth/chart-token", method="POST", cookie=cookie)
        return token_res.get("token")

    # --------------------------------------------------------------------------
    # PAMM & OMS Endpoints
    # --------------------------------------------------------------------------
    def get_pamm_masters(self, token: str, instance: str = "paper") -> Dict[str, Any]:
        return self._request(f"/v1/oms/{instance}/pamm/masters", token=token)

    def get_pamm_follows(self, token: str, instance: str = "paper") -> Dict[str, Any]:
        return self._request(f"/v1/oms/{instance}/pamm/follows", token=token)

    def join_pamm_pool(
        self, token: str, master_client_id: str, deposit: float, op_key: str, instance: str = "paper"
    ) -> Dict[str, Any]:
        return self._request(
            f"/v1/oms/{instance}/pamm/join",
            method="POST",
            data={"master_client_id": master_client_id, "deposit": deposit, "operation_key": op_key},
            token=token,
        )

    def get_pamm_allocations(
        self, token: str, role: Optional[str] = None, limit: int = 500, instance: str = "paper"
    ) -> Dict[str, Any]:
        q = f"?limit={limit}"
        if role:
            q += f"&role={role}"
        return self._request(f"/v1/oms/{instance}/pamm/allocations{q}", token=token)

    def get_trade_history(self, token: str, limit: int = 100, instance: str = "paper") -> Dict[str, Any]:
        return self._request(f"/v1/oms/{instance}/history?limit={limit}", token=token)

    def place_order(
        self, token: str, symbol: str, side: str, qty: float, order_type: str = "MARKET", instance: str = "paper"
    ) -> Dict[str, Any]:
        return self._request(
            f"/v1/oms/{instance}/orders",
            method="POST",
            data={"symbol": symbol, "side": side, "qty": qty, "type": order_type},
            token=token,
        )

    def get_positions(self, token: str, instance: str = "paper") -> Dict[str, Any]:
        return self._request(f"/v1/oms/{instance}/positions", token=token)

    def squareoff_position(self, token: str, market_order_id: str, instance: str = "paper") -> Dict[str, Any]:
        return self._request(
            f"/v1/oms/{instance}/positions/{market_order_id}/squareoff",
            method="POST",
            data={},
            token=token,
        )

