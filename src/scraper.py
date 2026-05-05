import yfinance as yf
import pandas as pd
import datetime
import time
import os
import re

def get_stock_data():
    ticker_list = []
    if not os.path.exists('tickers.txt'):
        print("Error: tickers.txt が見つかりません。")
        return

    # ティッカーの抽出ロジック（日本語スルー対応）
    with open('tickers.txt', 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.split(',')
            for p in parts:
                symbol = p.strip()
                if re.fullmatch(r'[A-Z0-9\.-]+', symbol):
                    ticker_list.append(symbol)

    ticker_list = list(dict.fromkeys(ticker_list))[:100]
    
    results = []
    print(f"有効なティッカーを {len(ticker_list)} 件確認しました。取得を開始します...")

    for symbol in ticker_list:
        try:
            print(f"取得中: {symbol}...")
            stock = yf.Ticker(symbol)
            info = stock.info
            
            # 財務諸表の取得
            financials = stock.financials 
            
            # 売上高履歴の安全な取得
            # .iloc[0] が最新になるよう、日付でソートを確認
            rev_history = []
            if 'Total Revenue' in financials.index:
                # 日付の新しい順に並び替え
                sorted_financials = financials.sort_index(axis=1, ascending=False)
                rev_history = sorted_financials.loc['Total Revenue'].tolist()

            row = {
                "No.": len(results) + 1,
                "Ticker": symbol,
                "①総株式数": info.get("sharesOutstanding"),
                "②自己資本比率": f"{(info.get('totalCashFromOperatingActivities', 0) / info.get('totalAssets', 1)):.2%}" if info.get('totalAssets') else "N/A",
                "③営業CF": info.get("operatingCashflow"),
                "⑤業界/セクター": f"{info.get('sector', '')} / {info.get('industry', '')}",
                "⑧当期売上高": info.get("totalRevenue"),
                "⑧-1 前年売上高": rev_history[1] if len(rev_history) > 1 else None,
                "⑧-2 前々年売上高": rev_history[2] if len(rev_history) > 2 else None,
                "⑨当期純利益": info.get("netIncome"),
                "⑩来期予想EPS": info.get("forwardEps"),
                "⑪1株純資産(BPS)": info.get("bookValue"),
                "⑫時価総額": info.get("marketCap"),
                "更新日時": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            results.append(row)
            
            # 100社取得時は少し長めに待機するとエラー（429 Too Many Requests）を防げます
            time.sleep(1.0) 
            
        except Exception as e:
            print(f"Failed to fetch {symbol}: {e}")

    # CSV保存
    df = pd.DataFrame(results)
    os.makedirs('data', exist_ok=True)
    output_path = 'data/stock_data.csv'
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"完了！ {output_path} に保存されました。")

if __name__ == "__main__":
    get_stock_data()
