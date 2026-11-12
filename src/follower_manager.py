"""
Follower Account Lifecycle & Pool Onboarding Manager
"""

import json
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from src.config import Config
from src.api_client import PlatformAPIClient


class FollowerManager:
    def __init__(self, client: PlatformAPIClient = None):
        self.client = client or PlatformAPIClient()

    def provision_follower(self, idx: int) -> Dict[str, Any]:
        email = f"{Config.FOLLOWER_PREFIX}{idx}@{Config.FOLLOWER_DOMAIN}"
        password = Config.FOLLOWER_PASSWORD
        deposit = float(500 + (idx * 25))
        wallet_bal = 10000.0

        # 1. Admin Create Member
        member_id = None
        try:
            res_create = self.client.create_member(email, password, name="Pam Follower")
            member_id = res_create.get("member", {}).get("member_id")
        except Exception as e:
            err = str(e)
            if "already registered" not in err and "already exists" not in err:
                return {"index": idx, "email": email, "status": "FAILED_CREATE", "error": err}

        # 2. Fund Paper Balance if new member
        if member_id:
            try:
                self.client.set_member_balance(member_id, balance=wallet_bal, instance=Config.DEFAULT_INSTANCE)
            except Exception:
                pass

        # 3. Follower Login & Mint OMS Token
        try:
            token = self.client.login_client(email, password)

            # Check if already following
            try:
                follows = self.client.get_pamm_follows(token, instance=Config.DEFAULT_INSTANCE)
                for sub in follows.get("subscriptions", []):
                    if sub.get("master_client_id") == Config.MASTER_CLIENT_ID and sub.get("status") == "active":
                        return {
                            "index": idx,
                            "email": email,
                            "deposit": sub.get("deposit", deposit),
                            "pamm_id": sub.get("pamm_id"),
                            "status": "SUCCESS",
                        }
            except Exception:
                pass

            # 4. Join Master PAMM Pool
            op_key = f"join_{idx}_{uuid.uuid4().hex[:8]}"
            res_join = self.client.join_pamm_pool(
                token,
                master_client_id=Config.MASTER_CLIENT_ID,
                deposit=deposit,
                op_key=op_key,
                instance=Config.DEFAULT_INSTANCE,
            )
            return {
                "index": idx,
                "email": email,
                "deposit": deposit,
                "pamm_id": res_join.get("subscription", {}).get("pamm_id"),
                "status": "SUCCESS",
            }
        except Exception as e:
            err = str(e)
            if "already have an active subscription" in err:
                return {
                    "index": idx,
                    "email": email,
                    "deposit": deposit,
                    "pamm_id": "active_existing",
                    "status": "SUCCESS",
                }
            return {"index": idx, "email": email, "status": "FAILED_JOIN", "error": err}

    def provision_all(self, count: int = Config.FOLLOWER_COUNT, max_workers: int = 6) -> List[Dict[str, Any]]:
        print(f"[*] Provisioning {count} Follower Accounts ({Config.FOLLOWER_PREFIX}1..{count})...")
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.provision_follower, i): i for i in range(1, count + 1)}
            for f in as_completed(futures):
                res = f.result()
                results.append(res)
                idx = res["index"]
                if res["status"] == "SUCCESS":
                    print(f"  [+] #{idx:03d} {res['email']} joined with ${res['deposit']:,.2f}")
                else:
                    print(f"  [!] #{idx:03d} {res['email']} - {res['status']}: {res.get('error')}")

        results.sort(key=lambda x: x["index"])
        Config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(Config.STATE_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        successes = sum(1 for r in results if r["status"] == "SUCCESS")
        print(f"[+] Provisioning Complete: {successes}/{count} active followers in pool.")
        return results

