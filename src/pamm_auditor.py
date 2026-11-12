"""
PAMM Allocation Mathematical Auditor & Follower Verifier
"""

from typing import List, Dict, Any
from src.config import Config
from src.api_client import PlatformAPIClient


class PAMMAuditor:
    def __init__(self, client: PlatformAPIClient = None):
        self.client = client or PlatformAPIClient()

    def audit_master_allocations(self, master_token: str) -> List[Dict[str, Any]]:
        res = self.client.get_pamm_allocations(master_token, role="master", limit=500, instance=Config.DEFAULT_INSTANCE)
        return res.get("allocations", [])

    def audit_follower(self, idx: int) -> Dict[str, Any]:
        email = f"{Config.FOLLOWER_PREFIX}{idx}@{Config.FOLLOWER_DOMAIN}"
        password = Config.FOLLOWER_PASSWORD
        try:
            token = self.client.login_client(email, password)
            allocs = self.client.get_pamm_allocations(token, instance=Config.DEFAULT_INSTANCE).get("allocations", [])
            follows = self.client.get_pamm_follows(token, instance=Config.DEFAULT_INSTANCE)
            sub = follows.get("subscriptions", [{}])[0] if follows.get("subscriptions") else {}

            return {
                "index": idx,
                "email": email,
                "status": sub.get("status", "unknown"),
                "deposit": sub.get("deposit", 0.0),
                "running_pnl": sub.get("running_pnl", 0.0),
                "allocations_count": len(allocs),
                "allocations": allocs,
            }
        except Exception as e:
            return {"index": idx, "email": email, "error": str(e), "allocations_count": 0}

    def audit_sample_followers(self, indices: List[int] = None) -> List[Dict[str, Any]]:
        indices = indices or [1, 10, 25, 50, 75, 100]
        print(f"[*] Auditing Sample Follower Accounts: {indices}...")
        results = []
        for idx in indices:
            res = self.audit_follower(idx)
            results.append(res)
            print(f"  [+] #{idx:03d} {res['email']} | Deposit: ${res.get('deposit', 0):,.2f} | Running PnL: ${res.get('running_pnl', 0):+.4f} | Allocations: {res['allocations_count']}")
        return results

