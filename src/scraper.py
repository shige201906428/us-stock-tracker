import yfinance as yf
import pandas as pd
import datetime
import time
import os
import re

def get_stock_data():
    ticker_list = []
    if not os.path.exists('tickers.txt'):
        print("Error: tickers.txt not found.")
        return

    # ティッカー抽出（日本語混じり対応）
    with open('tickers.txt', 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.split(',')
            for p in parts:
                symbol = p.strip()
                if re.fullmatch(r'[A-Z0-9\.-]+', symbol):
                    ticker_list.append(symbol)

    ticker_list = list(dict.fromkeys(ticker_list))[:100]
    results = []
    print(f"{len(ticker_list)}銘柄の取得を開始...")

    for symbol in ticker_list:
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            financials = stock.financials
            
            # 売上履歴の取得（新しい順にソート）
            rev_history = []
            if 'Total Revenue' in financials.index:
                sorted_fin = financials.sort_index(axis=1, ascending=False)
                rev_history = sorted_fin.loc['Total Revenue'].tolist()

            # --- ここから追加：純利益の確実な取得 ---
            net_income = info.get("netIncome")
            # infoで取れない場合、財務諸表(financials)から最新の値を抜き出す
            if not net_income and 'Net Income' in financials.index:
                sorted_fin = financials.sort_index(axis=1, ascending=False)
                net_income = sorted_fin.loc['Net Income'].iloc[0]
            # --- ここまで追加 ---

            # フェアバリュー計算 (グレアム数: √(22.5 * EPS * BPS))
            eps = info.get("forwardEps")
            bps = info.get("bookValue")
            price = info.get("currentPrice")
            fv = (22.5 * eps * bps) ** 0.5 if (eps and bps and eps > 0 and bps > 0) else None
            
            status = "-"
            if fv and price:
                ratio = price / fv
                if ratio < 0.7: status = "超割安"
                elif ratio < 1.0: status = "割安"
                elif ratio < 1.3: status = "適正"
                else: status = "割高"

            results.append({
                "No.": len(results) + 1,
                "Ticker": symbol,
                "①総株式数": info.get("sharesOutstanding"),
                "②自己資本比率": f"{(info.get('totalCashFromOperatingActivities', 0) / info.get('totalAssets', 1)):.2%}" if info.get('totalAssets') else "N/A",
                "③営業CF": info.get("operatingCashflow"),
                "⑤業界/セクター": f"{info.get('sector', '')} / {info.get('industry', '')}",
                "⑧当期売上高": info.get("totalRevenue"),
                "⑧-1 前年売上高": rev_history[1] if len(rev_history) > 1 else None,
                "⑧-2 前々年売上高": rev_history[2] if len(rev_history) > 2 else None,
                "⑨当期純利益": net_income,
                "利益率": f"{info.get('profitMargins', 0):.2%}" if info.get('profitMargins') else "-", # 追加
                "配当率": f"{info.get('dividendYield', 0):.2%}" if info.get('dividendYield') else "0.00%", # 追加
                "⑩来期予想EPS": eps,
                "⑪1株純資産(BPS)": bps,
                "⑫時価総額": info.get("marketCap"),
                "⑬フェアバリュー": round(fv, 2) if fv else "-",
                "⑭判定": status,
                "更新日時": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            time.sleep(1.0) # 負荷軽減
        except Exception as e:
            print(f"Error {symbol}: {e}")

    df = pd.DataFrame(results)
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/stock_data.csv', index=False, encoding='utf-8-sig')
    print("CSV更新完了")

if __name__ == "__main__":
    get_stock_data()
