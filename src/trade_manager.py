"""
Master Trade Execution & Real-Time Settlement Manager
"""

import time
from typing import Dict, Any, Optional
from src.config import Config
from src.api_client import PlatformAPIClient


class TradeManager:
    def __init__(self, client: PlatformAPIClient = None):
        self.client = client or PlatformAPIClient()
        self.master_token = None

    def authenticate_master(self) -> str:
        if not self.master_token:
            self.master_token = self.client.login_client(Config.MASTER_EMAIL, Config.MASTER_PASSWORD)
        return self.master_token

    def execute_and_settle(
        self,
        symbol: str = Config.DEFAULT_SYMBOL,
        side: str = "BUY",
        qty: float = 2.0,
        target_pnl: Optional[float] = None,
        max_wait_seconds: int = 15,
    ) -> Dict[str, Any]:
        token = self.authenticate_master()

        # 1. Place Market Order
        print(f"[*] Master executing {side} {qty} {symbol}...")
        order_res = self.client.place_order(token, symbol=symbol, side=side, qty=qty, instance=Config.DEFAULT_INSTANCE)
        order = order_res.get("order", {})
        market_order_id = order.get("market_order_id")
        fill_price = order.get("avg_fill_price")
        print(f"  [+] Filled: {market_order_id} at price {fill_price}")

        # 2. Wait or monitor target PnL
        start = time.time()
        while time.time() - start < max_wait_seconds:
            time.sleep(0.5)
            if target_pnl is not None:
                pos_res = self.client.get_positions(token, instance=Config.DEFAULT_INSTANCE)
                positions = pos_res.get("positions", [])
                if positions:
                    cur_pnl = positions[0].get("unrealized_pnl", 0.0)
                    if (target_pnl > 0 and cur_pnl >= target_pnl) or (target_pnl < 0 and cur_pnl <= target_pnl):
                        print(f"  [*] Target PnL reached: ${cur_pnl:+.2f}")
                        break

        # 3. Squareoff Position
        print(f"[*] Master squaring off position {market_order_id}...")
        close_res = self.client.squareoff_position(token, market_order_id=market_order_id, instance=Config.DEFAULT_INSTANCE)
        realized_pnl = close_res.get("realized_pnl", 0.0)
        exit_price = close_res.get("exit_price")
        print(f"  [+] Closed: Realized PnL = ${realized_pnl:+.4f} (Exit: {exit_price})")

        return {
            "order_id": market_order_id,
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "fill_price": fill_price,
            "exit_price": exit_price,
            "realized_pnl": realized_pnl,
        }

