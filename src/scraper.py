import yfinance as yf
import pandas as pd
import time
import os
import re
from datetime import datetime, timedelta, timezone

def get_stock_data():
    csv_path = 'data/stock_data.csv'
    manual_data = {}
    
    # 既存データの読み込み（手入力項目の保護）
    if os.path.exists(csv_path):
        try:
            df_old = pd.read_csv(csv_path, dtype=str)
            for _, row in df_old.iterrows():
                ticker = str(row['Ticker']).strip().upper()
                manual_data[ticker] = {
                    "⑮自作シグナル": row.get('⑮自作シグナル', '-'),
                    "⑯保有": row.get('⑯保有', '-')
                }
        except Exception as e:
            print(f"Read error: {e}")

    # 銘柄リスト読み込み
    if not os.path.exists('tickers.txt'):
        print("tickers.txt が見つかりません。")
        return
    
    with open('tickers.txt', 'r', encoding='utf-8') as f:
        ticker_list = [p.strip().upper() for line in f for p in line.split(',') 
                       if re.fullmatch(r'[A-Z0-9\.-]+', p.strip().upper())]
    ticker_list = list(dict.fromkeys(ticker_list))
    results = []

    jst = timezone(timedelta(hours=+9), 'JST')
    current_time = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")

    for symbol in ticker_list:
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            if not info or ('currentPrice' not in info and 'regularMarketPrice' not in info):
                continue

            # 財務データの取得
            financials = stock.financials
            rev_history = []
            if financials is not None and not financials.empty and 'Total Revenue' in financials.index:
                rev_history = financials.loc['Total Revenue'].fillna(0).tolist()

            # 売上成長率の計算 (取得できた最大分)
            growth_rates = []
            for i in range(len(rev_history) - 1):
                curr, prev = rev_history[i], rev_history[i+1]
                growth_rates.append(f"{(curr - prev) / prev:.2%}" if prev > 0 else "-")

            # 各種指標
            revenue = info.get("totalRevenue") or (rev_history[0] if rev_history else 0)
            net_income = info.get("netIncome")
            margin = f"{(net_income / revenue):.2%}" if net_income and revenue and revenue > 0 else "-"
            
            dy_raw = info.get('dividendYield')
            dividend_yield = f"{(float(dy_raw) / 100):.2%}" if dy_raw not in [None, ""] else "0.00%"

            total_assets = info.get('totalAssets')
            total_equity = info.get('totalStockholderEquity')
            equity_ratio = f"{(total_equity / total_assets):.2%}" if total_assets and total_equity else "N/A"

            # フェアバリュー
            eps, bps = info.get("forwardEps"), info.get("bookValue")
            price = info.get("currentPrice") or info.get("regularMarketPrice")
            fv = (22.5 * eps * bps) ** 0.5 if (eps and bps and eps > 0 and bps > 0) else None
            
            status = "-"
            if fv and price:
                ratio = price / fv
                if ratio < 0.7: status = "超割安"
                elif ratio < 1.0: status = "割安"
                elif ratio < 1.3: status = "適正"
                else: status = "割高"

            m_info = manual_data.get(symbol, {"⑮自作シグナル": "-", "⑯保有": "-"})

            results.append({
                "No.": len(results) + 1,
                "Ticker": symbol,
                "②自己資本比率": equity_ratio,
                "⑤業界/セクター": f"{info.get('sector', '')} / {info.get('industry', '')}",
                "⑧当期売上高": revenue,
                "成長率(最新)": growth_rates[0] if len(growth_rates) > 0 else "-",
                "成長率(1期前)": growth_rates[1] if len(growth_rates) > 1 else "-",
                "成長率(2期前)": growth_rates[2] if len(growth_rates) > 2 else "-",
                "⑨当期純利益": net_income,
                "利益率": margin,
                "配当率": dividend_yield,
                "⑬フェアバリュー": round(fv, 2) if fv else "-",
                "⑭判定": status,
                "⑮自作シグナル": m_info["⑮自作シグナル"],
                "⑯保有": m_info["⑯保有"],
                "更新日時": current_time
            })
            print(f"Success: {symbol}")
            time.sleep(1.0)
        except Exception as e:
            print(f"Error {symbol}: {e}")

    if results:
        df = pd.DataFrame(results)
        os.makedirs('data', exist_ok=True)
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')

if __name__ == "__main__":
    get_stock_data()
