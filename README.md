# BlackTrader / BlackFX PAMM Automated Test Suite

Professional automated testing and verification suite for the **Percent Allocation Management Module (PAMM)** architecture on **BlackTrader / BlackFX** (`https://lpadmin.blackfx.com`).

---

## 1. PAMM Business Logic & Verified Rules

* **Master Account Capital:** **$0.00** personal seed capital (trades purely on pooled follower equity).
* **Pool Architecture:** Follower capital is enrolled into the Master strategy (`Alpha Pool`, ID: `mem_fb2ee87f7645878a2f`).
* **Asymmetric Risk Sharing:**
  * **On Loss:** Master absorbs **$0.00 loss**; 100% of loss is distributed proportionally across active followers according to their deposit share.
  * **On Profit:** Master automatically earns a **20% performance fee** on follower net profits; followers receive 80% net gain.
* **100 Real Follower Accounts:** Provisioned sequentially (`pamfollower1@mailinator.com` through `pamfollower100@mailinator.com`, password `Password123!`).

---

## 2. Project Directory Structure

```text
├── .env                        # Live credentials (configured & git-ignored)
├── .env.example                # Configuration template
├── run_pamm_suite.py           # Unified CLI test runner (entry point)
├── README.md                   # Documentation & execution guide
│
├── src/                        # Modular test architecture
│   ├── config.py               # Centralized configuration loader
│   ├── api_client.py           # BlackTrader Admin & Client OMS API client
│   ├── follower_manager.py     # Batch account provisioning & pool enrollment
│   ├── trade_manager.py        # Master order execution & squareoff
│   ├── pamm_auditor.py         # Allocation verification & random follower auditing
│   └── report_generator.py     # Generates CSV & interactive HTML dashboard
│
└── reports/                    # Output reports & state
    ├── pamm_100_audit.csv      # Complete 100-follower audit spreadsheet
    ├── pamm_audit_dashboard.html # Interactive visual dashboard
    └── followers_state.json    # Provisioned accounts & subscription IDs
```

---

## 3. How to Run the Tests

The entire PAMM test suite is controlled via `run_pamm_suite.py`:

### A. Live Audit & Report Generation (Default)
Queries the live platform database, audits the Master pool, verifies random follower accounts, and updates all reports:
```bash
python3 run_pamm_suite.py
```
*(or explicitly: `python3 run_pamm_suite.py --audit`)*

### B. Place Master Trades
Places and settles real market test orders (winning and losing trades) on `BINANCE:BTCUSDT` to trigger PAMM pool allocations:
```bash
python3 run_pamm_suite.py --trade
```

### C. Batch Provision 100 Followers
Provisions and funds `pamfollower1` to `pamfollower100` and joins them into the Master pool:
```bash
python3 run_pamm_suite.py --provision
```

### D. Full Lifecycle Test
Executes the full test pipeline (Provision $\rightarrow$ Trade $\rightarrow$ Audit $\rightarrow$ Report):
```bash
python3 run_pamm_suite.py --full
```

---

## 4. Manual Verification via Browser

You can manually verify all executions in your browser anytime:

### 1. Verify Master Account & Orders
* **URL:** `https://lpadmin.blackfx.com/dashboard`
* **Email:** `dhanya@mailinator.com` | **Password:** `test1234`
* **History Tab:** View executed trade tickets (e.g. `ord_acbf133ccfce7d813a`, `ord_593a53d009f1eaf452`) with fill prices and realized PnL.
* **PAMM Tab:** Inspect **Alpha Pool** to view the 100 followers and $177,175.00 total pooled fund.

### 2. Verify Random Follower Account
* **URL:** `https://lpadmin.blackfx.com/dashboard`
* **Email:** `pamfollower{1..100}@mailinator.com` (e.g. `pamfollower25@mailinator.com`)
* **Password:** `Password123!`
* **PAMM Allocations:** View individual allocations matching their exact proportional share of the Master's trades.

---

## 5. Reports & Deliverables

* **Interactive HTML Dashboard:** [pamm_audit_dashboard.html](pamm_audit_dashboard.html) (Searchable, filterable by deposit tier with live KPI cards).
* **CSV Audit Export:** [pamm_100_audit.csv](pamm_100_audit.csv) (Contains all 100 follower emails, passwords, PAMM IDs, deposits, and exact PnL breakdown).
