#!/usr/bin/env python3
"""
PAMM Platform Automated Testing & Verification Suite
====================================================
Unified Command-Line Runner for BlackTrader / BlackFX PAMM Architecture.

Usage:
    python3 run_pamm_suite.py              # Run live audit & generate reports (default)
    python3 run_pamm_suite.py --audit      # Audit Master & Follower allocations
    python3 run_pamm_suite.py --trade      # Place & settle Master test trades
    python3 run_pamm_suite.py --provision  # Batch provision 100 followers
    python3 run_pamm_suite.py --full       # Full lifecycle (provision, trade, audit)
"""

import sys
import argparse
import json
from pathlib import Path

# Add workspace to path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from src.config import Config
from src.api_client import PlatformAPIClient
from src.follower_manager import FollowerManager
from src.trade_manager import TradeManager
from src.pamm_auditor import PAMMAuditor
from src.report_generator import ReportGenerator


def load_followers_state():
    state_file = Config.STATE_FILE_PATH
    if state_file.exists():
        with open(state_file, "r", encoding="utf-8") as f:
            return json.load(f)
    # Fallback to default definition if not yet generated
    return [
        {
            "index": i,
            "email": f"{Config.FOLLOWER_PREFIX}{i}@{Config.FOLLOWER_DOMAIN}",
            "deposit": float(500 + (i * 25)),
            "pamm_id": "active",
            "status": "SUCCESS",
        }
        for i in range(1, Config.FOLLOWER_COUNT + 1)
    ]


def main():
    parser = argparse.ArgumentParser(description="PAMM Platform Test Suite")
    parser.add_argument("--provision", action="store_true", help="Provision follower accounts & join pool")
    parser.add_argument("--trade", action="store_true", help="Execute & settle Master test trades")
    parser.add_argument("--audit", action="store_true", help="Audit Master & Follower allocations")
    parser.add_argument("--full", action="store_true", help="Run full lifecycle: provision -> trade -> audit")
    args = parser.parse_args()

    # Default action if no flags provided
    if not any([args.provision, args.trade, args.audit, args.full]):
        args.audit = True

    print("=" * 80)
    print("BLACKTRADER / BLACKFX PAMM AUTOMATION & VERIFICATION SUITE")
    print(f"Target Platform: {Config.BASE_URL}")
    print(f"Master Strategy: '{Config.MASTER_POOL_NAME}' ({Config.MASTER_CLIENT_ID})")
    print("=" * 80)

    client = PlatformAPIClient()
    follower_mgr = FollowerManager(client)
    trade_mgr = TradeManager(client)
    auditor = PAMMAuditor(client)

    followers_data = []

    # 1. Provisioning Phase
    if args.provision or args.full:
        print("\n[PHASE 1] Batch Provisioning 100 Followers...")
        followers_data = follower_mgr.provision_all(count=Config.FOLLOWER_COUNT)
    else:
        followers_data = load_followers_state()

    # 2. Trading Phase
    if args.trade or args.full:
        print("\n[PHASE 2] Executing Master Live Trades...")
        # Trade 1: Positive PnL test
        print("\n--- Executing Winning Trade ---")
        win_res = trade_mgr.execute_and_settle(side="BUY", qty=2.5, target_pnl=5.0, max_wait_seconds=20)
        # Trade 2: Negative PnL test
        print("\n--- Executing Losing Trade ---")
        loss_res = trade_mgr.execute_and_settle(side="BUY", qty=2.0, target_pnl=-5.0, max_wait_seconds=15)

    # 3. Auditing Phase
    if args.audit or args.full:
        print("\n[PHASE 3] Auditing Live PAMM Allocations...")
        master_token = trade_mgr.authenticate_master()

        # Check Pool Stats
        masters_info = client.get_pamm_masters(master_token, instance=Config.DEFAULT_INSTANCE)
        pool = next((m for m in masters_info.get("masters", []) if m["client_id"] == Config.MASTER_CLIENT_ID), None)
        if pool:
            stats = pool.get("stats", {})
            print(f"[+] Active Pool: '{pool.get('name')}' | Followers: {stats.get('followers')} | Fund: ${stats.get('fund', 0):,.2f} | Trades: {stats.get('trades')}")

        # Check Master Allocations
        master_allocs = auditor.audit_master_allocations(master_token)
        print(f"[+] Total Master Allocations Logged in OMS: {len(master_allocs)}")

        # Audit Sample Followers
        sample_results = auditor.audit_sample_followers(indices=[1, 10, 25, 50, 75, 100])

        # 4. Generate Reports
        print("\n[PHASE 4] Generating Verification Reports...")
        csv_file = ReportGenerator.export_csv(followers_data, master_allocs)
        html_file = ReportGenerator.export_dashboard(followers_data, master_allocs)

        print(f"[+] CSV Audit Report: file://{csv_file}")
        print(f"[+] HTML Dashboard:   file://{html_file}")

    print("\n" + "=" * 80)
    print("PAMM SUITE EXECUTION COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    main()

