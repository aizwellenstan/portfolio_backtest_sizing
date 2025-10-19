import pandas as pd
import math

# Load and preprocess
df = pd.read_csv("tradelist.csv")
df['Symbol'] = df['Symbol'].fillna('').astype(str)

def normalize_symbol(symbol):
    if 'MNQ' in symbol or 'NQ' in symbol:
        return 'MNQ', 0.5, 0.25
    elif 'MYM' in symbol or 'YM' in symbol:
        return 'MYM', 0.5, 1
    elif 'MES' in symbol or 'ES' in symbol:
        return 'MES', 1.25, 0.25
    elif 'MGC' in symbol or 'GC' in symbol:
        return 'MGC', 1, 1
    else:
        return 'UNKNOWN', 0, 0

df[['NormalizedSymbol', 'TickValue', 'TickSize']] = df['Symbol'].apply(normalize_symbol).apply(pd.Series)
df = df.dropna(subset=['Entry Price', 'Exit Price'])

def calc_profit(row):
    entry = row['Entry Price']
    exit = row['Exit Price']
    direction = row['Trade Type']
    tick_val = row['TickValue']
    tick_size = row['TickSize']
    if tick_val == 0 or tick_size == 0:
        return 0
    price_diff = exit - entry if direction == 'Long' else entry - exit
    ticks = price_diff / tick_size
    return ticks * tick_val

df['ProfitPerContract'] = df.apply(calc_profit, axis=1)

# === Backtest combinations ===
start_balance = 4500
best_score = -float('inf')
best_combo = (0, 0)

for risk_pct in [i / 1000 for i in range(1, 300)]:
    for min_contracts in range(1, 20):
        balance = start_balance
        trade_profits = []

        for ppc in df['ProfitPerContract']:
            if ppc == 0:
                contracts = 0
            else:
                dynamic_contracts = math.floor((balance * risk_pct) / abs(ppc))
                contracts = max(min_contracts, dynamic_contracts)
            trade_profit = contracts * ppc
            balance += trade_profit
            trade_profits.append(trade_profit)

        wins = [r for r in trade_profits if r > 0]
        losses = [r for r in trade_profits if r < 0]
        win_rate = len(wins) / len(trade_profits) if trade_profits else 0
        avg_win = sum(wins) / len(wins) if wins else 0
        avg_loss = abs(sum(losses) / len(losses)) if losses else 0
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)

        if expectancy > best_score:
            best_score = expectancy
            best_combo = (risk_pct, min_contracts)
            best_profits = trade_profits

# === Evaluate best combo ===
balance = start_balance
equity_curve = []
for profit in best_profits:
    balance += profit
    equity_curve.append(balance)

final_profit = balance - start_balance
peak = start_balance
mdd = 0
for equity in equity_curve:
    if equity > peak:
        peak = equity
    drawdown = peak - equity
    if drawdown > mdd:
        mdd = drawdown

# === Output ===
print(f"Expectancy Optimization")
print(f"Optimal risk_pct: {best_combo[0]:.3f}, min_contracts: {best_combo[1]}")
print(f"Expectancy: ${best_score:.2f} per trade")
print(f"Final Profit: ${final_profit:.2f}")
print(f"Max Drawdown: ${mdd:.2f}")
