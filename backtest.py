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
best_sharpe = -float('inf')
best_combo = (0, 0)
results = []

for risk_pct in [i / 100 for i in range(1, 51)]:  # 0.01 to 0.50
    for min_contracts in range(1, 51):  # 1 to 50
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

        mean_return = pd.Series(trade_profits).mean()
        std_return = pd.Series(trade_profits).std()
        sharpe = mean_return / std_return if std_return != 0 else 0
        results.append((risk_pct, min_contracts, sharpe))

        if sharpe > best_sharpe:
            best_sharpe = sharpe
            best_combo = (risk_pct, min_contracts)

# Output best result
print(f"Best Sharpe ratio: {best_sharpe:.4f}")
print(f"Optimal risk_pct: {best_combo[0]:.3f}, min_contracts: {best_combo[1]}")
