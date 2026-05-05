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

    with open('tickers.txt', 'r', encoding='utf-8') as f:
        for line in f:
            # 1. カンマで分割
            parts = line.split(',')
            for p in parts:
                symbol = p.strip()
                # 2. 正規表現で「英大文字・数字・一部記号(ハイフン等)」のみの単語かチェック
                # これにより「■ 生活必需品」などの日本語を完全に無視します
                if re.fullmatch(r'[A-Z0-9\.-]+', symbol):
                    ticker_list.append(symbol)

    # 重複を除去
    ticker_list = list(dict.fromkeys(ticker_list))[:100]
    
    results = []
    print(f"有効なティッカーを {len(ticker_list)} 件確認しました。取得を開始します...")

    # --- 以下、データ取得ロジック（変更なし） ---
    for symbol in ticker_list:
        try:
            print(f"取得中: {symbol}...")
            stock = yf.Ticker(symbol)
            info = stock.info
            
            row = {
                "No.": len(results) + 1,
                "Ticker": symbol,
                "①総株式数": info.get("sharesOutstanding"),
                "②自己資本比率": f"{(info.get('totalCashFromOperatingActivities', 0) / info.get('totalAssets', 1)):.2%}" if 'totalAssets' in info else "N/A",
                "③営業CF": info.get("operatingCashflow"),
                "④主要株主": "Major Holders Tab",
                "⑤業界/セクター": f"{info.get('sector', '')} / {info.get('industry', '')}",
                "⑧当期売上高": info.get("totalRevenue"),
                "⑨当期純利益": info.get("netIncome"),
                "⑩来期1株あたり純利益(予想EPS)": info.get("forwardEps"),
                "⑪1株あたり純資産(BPS)": info.get("bookValue"),
                "⑫時価総額": info.get("marketCap"),
                "更新日時": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            results.append(row)
            time.sleep(0.5) 
            
        except Exception as e:
            print(f"Failed to fetch {symbol}: {e}")

    df = pd.DataFrame(results)
    os.makedirs('data', exist_ok=True)
    output_path = 'data/stock_data.csv'
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"完了！ {output_path} に保存されました。")

if __name__ == "__main__":
    get_stock_data()
