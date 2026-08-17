# Strategy Specification
## Asian Session Liquidity Sweep + BOS Bot — v1 Mechanical Rules

## 1. Objective
Trade at most **one London-session reversal setup per day** on **EURUSD** when all of the following are true:

1. Higher-timeframe bias is clear
2. Asian session range is defined
3. Liquidity is swept against the bias first
4. Reversal is confirmed by a valid M5 BOS
5. Execution quality filters are satisfied

If any of the above is missing, the correct action is **no trade**.

## 2. Instrument and sessions
- Instrument: `EURUSD`
- Bias timeframe: `H4`
- Setup timeframe: `M5`
- Asian range window: `19:00` to `00:00` New York time
- Trade scan window: `09:00` to `13:00` Dubai time
- Force close: `13:00` Dubai time

## 3. Bias rules
Use the last **3 fully closed H4 candles**.

### Bullish bias
Bias = `BULLISH` only if:
- highs strictly increase across the last 3 closed candles
- lows strictly increase across the last 3 closed candles

### Bearish bias
Bias = `BEARISH` only if:
- highs strictly decrease across the last 3 closed candles
- lows strictly decrease across the last 3 closed candles

### Neutral
If neither bullish nor bearish conditions are true, bias = `NEUTRAL` and no trade is allowed.

### Structure-size filter
Bias is invalid if the total H4 structure across those candles is too small.
Configurable field:
- `MIN_H4_STRUCTURE_PIPS`

## 4. Asian range rules
Using all **closed M5 candles** in the Asian window:
- `asian_high` = highest wick high
- `asian_low` = lowest wick low

The range is fixed for the rest of the day after setup completes.

## 5. Sweep rules
### Bearish setup
If bias = `BEARISH`, price must sweep **above** the Asian high first.
Valid sweep condition:
- closed M5 candle high > `asian_high`
- optional buffer: candle high >= `asian_high + MIN_SWEEP_BUFFER_PIPS`

### Bullish setup
If bias = `BULLISH`, price must sweep **below** the Asian low first.
Valid sweep condition:
- closed M5 candle low < `asian_low`
- optional buffer: candle low <= `asian_low - MIN_SWEEP_BUFFER_PIPS`

### Sweep record
Store:
- sweep type
- sweep timestamp
- sweep candle high/low
- sweep extreme

For v1, only the **first valid sweep of the day** is used.

## 6. Invalid day rules
### Bearish bias invalidation
If price closes below `asian_low` before a valid high sweep occurs, no trade is allowed that day.

### Bullish bias invalidation
If price closes above `asian_high` before a valid low sweep occurs, no trade is allowed that day.

These invalidations apply only to **closed M5 candles** during the trade scan window.

## 7. Swing rules
Use a fractal swing definition on closed M5 candles.

### Swing high
A candle is a swing high if its high is greater than the highs of the previous `N` candles and the next `N` candles.

### Swing low
A candle is a swing low if its low is lower than the lows of the previous `N` candles and the next `N` candles.

For v1:
- `N = 2`

## 8. BOS rules
### Bearish BOS
After a valid `HIGH_SWEEP`, identify the most recent confirmed M5 swing low formed before the sweep.
A BOS is confirmed only when a **closed M5 candle** closes strictly below that swing low.

### Bullish BOS
After a valid `LOW_SWEEP`, identify the most recent confirmed M5 swing high formed before the sweep.
A BOS is confirmed only when a **closed M5 candle** closes strictly above that swing high.

### BOS invalid conditions
Reject BOS if:
- no valid prior swing exists
- BOS occurs outside the scan window
- BOS occurs too near the force-close time

## 9. Entry rules
### Bearish entry
If bearish bias, valid high sweep, and bearish BOS are all true:
- place `SELL` market order immediately after BOS confirmation

### Bullish entry
If bullish bias, valid low sweep, and bullish BOS are all true:
- place `BUY` market order immediately after BOS confirmation

### Entry logging requirement
Log both:
- BOS candle close (signal price)
- actual fill price

## 10. Stop loss rules
### Bearish
- SL = sweep high + `SL_BUFFER_PIPS`

### Bullish
- SL = sweep low - `SL_BUFFER_PIPS`

## 11. Take profit rules
Use fixed `2R` target.
- `R = abs(entry - stop_loss)`
- bullish TP = `entry + 2R`
- bearish TP = `entry - 2R`

No partials in v1.

## 12. Break-even rule
Move stop to break-even once price reaches `+1R`.
Only do this once per trade.

## 13. Re-entry rule
For v1:
- no re-entry
- maximum one trade per day

## 14. Trade filters
Reject trade if any of these fail:
- spread > `MAX_SPREAD_PIPS`
- stop distance < `MIN_STOP_PIPS`
- stop distance > `MAX_STOP_PIPS`
- minutes remaining until force-close < `MIN_MINUTES_BEFORE_FORCE_CLOSE`

## 15. Session close rule
At `13:00` Dubai time:
- close all strategy positions
- exit reason = `TIME_EXIT`

## 16. State requirements
Persist at least:
- date
- bias
- asian range
- sweep detected state
- sweep type/time/extreme
- BOS level/time
- trade open state
- ticket / entry / SL / TP
- break-even status
- invalidation reason
- exit result

## 17. Journaling requirements
Maintain:
- event log
- daily signal journal
- trade journal

## 18. Deployment/testing discipline
Order of use:
1. dry-run / signal-only mode
2. demo account validation
3. tiny live pilot only after evidence exists

This strategy is a research candidate, not a proven edge by default.
