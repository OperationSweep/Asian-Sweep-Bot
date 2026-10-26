"""
Pure order-book arithmetic for arbitrage measurement. No I/O, no exchange access.

Conventions
    A book side is a list of [price, qty] levels, best first.
    Asks ascend in price, bids descend.
    Fees are fractions (0.001 == 0.10 %), charged as taker on every leg.
    Slippage is never added separately: it is already inside the depth walk.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

Level = Sequence[float]
Side = Sequence[Level]


def buy_with_quote(asks: Side, quote_amount: float) -> Tuple[float, float]:
    """Spend up to `quote_amount` walking the asks. Returns (base_bought, quote_spent)."""
    base = 0.0
    spent = 0.0
    remaining = quote_amount
    for price, qty in asks:
        if remaining <= 0:
            break
        level_cost = price * qty
        if level_cost <= remaining:
            base += qty
            spent += level_cost
            remaining -= level_cost
        else:
            take = remaining / price
            base += take
            spent += remaining
            remaining = 0.0
    return base, spent


def sell_base(bids: Side, base_amount: float) -> Tuple[float, float]:
    """Sell up to `base_amount` walking the bids. Returns (quote_received, base_sold)."""
    received = 0.0
    sold = 0.0
    remaining = base_amount
    for price, qty in bids:
        if remaining <= 0:
            break
        take = min(qty, remaining)
        received += take * price
        sold += take
        remaining -= take
    return received, sold


def buy_base(asks: Side, base_amount: float) -> Tuple[float, float]:
    """Buy exactly up to `base_amount` walking the asks. Returns (quote_spent, base_bought)."""
    spent = 0.0
    bought = 0.0
    remaining = base_amount
    for price, qty in asks:
        if remaining <= 0:
            break
        take = min(qty, remaining)
        spent += take * price
        bought += take
        remaining -= take
    return spent, bought


@dataclass
class CrossResult:
    notional: float          # quote budget requested
    base_qty: float          # base actually traded on both legs
    cost: float              # quote paid on the buy venue incl. fee
    proceeds: float          # quote received on the sell venue net of fee
    net: float               # proceeds - cost
    net_bps: float           # net / cost in basis points
    complete: bool           # False if either book was too thin for the full size


def cross_venue(buy_asks: Side, sell_bids: Side, notional: float,
                buy_fee: float, sell_fee: float) -> Optional[CrossResult]:
    """
    Inventory-based cross-venue arbitrage: buy `notional` worth on venue A (spending
    quote already held there) and simultaneously sell the same base quantity on venue B
    (from base already held there). No transfer happens inside the trade.
    """
    if not buy_asks or not sell_bids or notional <= 0:
        return None
    base, spent = buy_with_quote(buy_asks, notional)
    if base <= 0:
        return None
    received, sold = sell_base(sell_bids, base)
    complete = spent >= notional * 0.999999 and sold >= base * 0.999999
    if sold < base:
        # Sell book too thin: only count the matched quantity on both legs.
        spent, base = buy_base(buy_asks, sold)
    cost = spent * (1 + buy_fee)
    proceeds = received * (1 - sell_fee)
    net = proceeds - cost
    return CrossResult(notional, base, cost, proceeds, net,
                       (net / cost * 1e4) if cost else 0.0, complete)


def max_profitable_cross(buy_asks: Side, sell_bids: Side, buy_fee: float,
                         sell_fee: float) -> Tuple[float, float]:
    """
    Largest base quantity for which every marginal unit is still profitable after fees,
    and the total net quote profit at that size. Returns (base_qty, net_quote).
    """
    i = j = 0
    a_left = buy_asks[0][1] if buy_asks else 0.0
    b_left = sell_bids[0][1] if sell_bids else 0.0
    qty = 0.0
    net = 0.0
    while i < len(buy_asks) and j < len(sell_bids):
        ask = buy_asks[i][0]
        bid = sell_bids[j][0]
        edge = bid * (1 - sell_fee) - ask * (1 + buy_fee)
        if edge <= 0:
            break
        take = min(a_left, b_left)
        qty += take
        net += take * edge
        a_left -= take
        b_left -= take
        if a_left <= 1e-15:
            i += 1
            a_left = buy_asks[i][1] if i < len(buy_asks) else 0.0
        if b_left <= 1e-15:
            j += 1
            b_left = sell_bids[j][1] if j < len(sell_bids) else 0.0
    return qty, net


Books = Dict[str, Dict[str, Side]]   # symbol "BASE/QUOTE" -> {"bids": [...], "asks": [...]}


def convert(books: Books, amount: float, src: str, dst: str, fee: float) -> Optional[float]:
    """
    Convert `amount` of asset `src` into `dst` on one venue, walking whichever market
    exists (dst/src = buy base with quote, src/dst = sell base for quote). Taker fee is
    deducted from the output. Returns None if no market exists or the book is too thin.
    """
    direct = f"{dst}/{src}"
    inverse = f"{src}/{dst}"
    if direct in books:
        asks = books[direct].get("asks") or []
        out, spent = buy_with_quote(asks, amount)
        if spent < amount * 0.999999:
            return None
    elif inverse in books:
        bids = books[inverse].get("bids") or []
        out, sold = sell_base(bids, amount)
        if sold < amount * 0.999999:
            return None
    else:
        return None
    return out * (1 - fee)


def cycle_return(books: Books, path: List[str], notional: float, fee: float) -> Optional[float]:
    """
    Run `notional` of path[0] around the cycle path[0] -> path[1] -> ... -> path[0].
    Returns the net ending amount minus the starting amount (in path[0] units), or None.
    """
    amount = notional
    hops = list(zip(path, path[1:] + path[:1]))
    for src, dst in hops:
        nxt = convert(books, amount, src, dst, fee)
        if nxt is None:
            return None
        amount = nxt
    return amount - notional
