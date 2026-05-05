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
