import yfinance as yf
import pandas as pd
import time
import os
import re
from datetime import datetime, timedelta, timezone

def get_stock_data():
    manual_data = {}
    csv_path = 'data/stock_data.csv'
    
    # 1. 既存データの読み込み（手入力項目の保護）
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

    # 2. 銘柄リスト読み込み
    ticker_list = []
    if not os.path.exists('tickers.txt'):
        print("tickers.txt が見つかりません。")
        return
    
    with open('tickers.txt', 'r', encoding='utf-8') as f:
        for line in f:
            for p in line.split(','):
                symbol = p.strip().upper()
                if re.fullmatch(r'[A-Z0-9\.-]+', symbol):
                    ticker_list.append(symbol)

    ticker_list = list(dict.fromkeys(ticker_list))
    results = []

    # 日本時間（JST）の設定
    jst = timezone(timedelta(hours=+9), 'JST')
    current_time = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")

    for symbol in ticker_list:
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            if not info or ('currentPrice' not in info and 'regularMarketPrice' not in info):
                continue

            # --- 財務データの取得 ---
            financials = stock.financials
            
            # 売上高と純利益の取得（info優先、なければfinancialsから）
            revenue = info.get("totalRevenue")
            net_income = info.get("netIncome")
            
            if financials is not None and not financials.empty:
                if 'Total Revenue' in financials.index:
                    rev_history = financials.loc['Total Revenue'].fillna(0).tolist()
                    if not revenue: revenue = rev_history[0]
                else:
                    rev_history = []

                if 'Net Income' in financials.index and not net_income:
                    net_income = financials.loc['Net Income'].iloc[0]
            else:
                rev_history = []

            # --- 売上増加率の計算 (過去3期分) ---
            growth_rates = []
            for i in range(len(rev_history) - 1):
                curr = rev_history[i]
                prev = rev_history[i+1]
                if prev > 0:
                    growth = (curr - prev) / prev
                    growth_rates.append(f"{growth:.2%}")
                else:
                    growth_rates.append("-")

            # --- 指標の計算 ---
            # 利益率
            margin = "-"
            if net_income and revenue and float(revenue) > 0:
                margin = f"{(float(net_income) / float(revenue)):.2%}"

            # 配当利回り (yfinanceは小数表記なので100をかけずに表示)
            dy_raw = info.get('dividendYield')
            dividend_yield = f"{float(dy_raw):.2%}" if dy_raw not in [None, ""] else "0.00%"

            # 自己資本比率 (純資産 / 総資産)
            total_assets = info.get('totalAssets')
            total_equity = info.get('totalStockholderEquity')
            equity_ratio = "N/A"
            if total_assets and total_equity:
                equity_ratio = f"{(total_equity / total_assets):.2%}"

            # フェアバリュー判定 (グレアム数ベース)
            eps = info.get("forwardEps")
            bps = info.get("bookValue")
            price = info.get("currentPrice") or info.get("regularMarketPrice")
            fv = (22.5 * eps * bps) ** 0.5 if (eps and bps and eps > 0 and bps > 0) else None
            
            status = "-"
            if fv and price:
                ratio = price / fv
                if ratio < 0.7: status = "超割安"
                elif ratio < 1.0: status = "割安"
                elif ratio < 1.3: status = "適正"
                else: status = "割高"

            # 手入力データの統合
            m_info = manual_data.get(symbol, {"⑮自作シグナル": "-", "⑯保有": "-"})

            # 結果の格納
            results.append({
                "No.": len(results) + 1,
                "Ticker": symbol,
                "①総株式数": info.get("sharesOutstanding"),
                "②自己資本比率": equity_ratio,
                "③営業CF": info.get("operatingCashflow"),
                "⑤業界/セクター": f"{info.get('sector', '')} / {info.get('industry', '')}",
                "⑧当期売上高": revenue,
                "成長率(最新期)": growth_rates[0] if len(growth_rates) > 0 else "-",
                "成長率(1期前)": growth_rates[1] if len(growth_rates) > 1 else "-",
                "成長率(2期前)": growth_rates[2] if len(growth_rates) > 2 else "-",
                "⑨当期純利益": net_income,
                "利益率": margin,
                "配当率": dividend_yield,
                "⑩来期予想EPS": eps,
                "⑪1株純資産(BPS)": bps,
                "⑫時価総額": info.get("marketCap"),
                "⑬フェアバリュー": round(fv, 2) if fv else "-",
                "⑭判定": status,
                "⑮自作シグナル": m_info["⑮自作シグナル"],
                "⑯保有": m_info["⑯保有"],
                "更新日時": current_time
            })
            print(f"Success: {symbol}")
            time.sleep(1.2)  # サーバー負荷軽減
            
        except Exception as e:
            print(f"Error {symbol}: {e}")

    # 3. CSVへの保存
    if results:
        df = pd.DataFrame(results)
        os.makedirs('data', exist_ok=True)
        # Excelで開いても文字化けしないよう utf-8-sig を使用
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"\n保存完了: {csv_path}")

if __name__ == "__main__":
    get_stock_data()
