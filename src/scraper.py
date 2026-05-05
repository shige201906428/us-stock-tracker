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
# --- src/scraper.py のデータ取得ループ内を以下のように修正 ---

            stock = yf.Ticker(symbol)
            info = stock.info
            financials = stock.financials # 損益計算書のデータを取得
            
            # 売上高（Total Revenue）の履歴を取得
            # financialsのインデックスは [0]が直近, [1]が1年前, [2]が2年前
            rev_history = financials.loc['Total Revenue'] if 'Total Revenue' in financials.index else []
            
            row = {
                "No.": len(results) + 1,
                "Ticker": symbol,
                "①総株式数": info.get("sharesOutstanding"),
                "②自己資本比率": f"{(info.get('totalCashFromOperatingActivities', 0) / info.get('totalAssets', 1)):.2%}" if 'totalAssets' in info else "N/A",
                "③営業CF": info.get("operatingCashflow"),
                "⑤業界/セクター": f"{info.get('sector', '')} / {info.get('industry', '')}",
                "⑧当期売上高": info.get("totalRevenue"),
                "⑧-1 前年売上高": rev_history[1] if len(rev_history) > 1 else None, # 追加
                "⑧-2 前々年売上高": rev_history[2] if len(rev_history) > 2 else None, # 追加
                "⑨当期純利益": info.get("netIncome"),
                "⑩来期予想EPS": info.get("forwardEps"),
                "⑪1株純資産(BPS)": info.get("bookValue"),
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
