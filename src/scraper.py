<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>US Stock Screener | 米国株100社</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/PapaParse/5.3.2/papaparse.min.js"></script>
    <style>
        :root {
            --bg: #f5f7fa;
            --card-bg: #ffffff;
            --primary: #3498db;
            --text: #2c3e50;
            --border: #e1e8ed;
        }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: var(--bg); color: var(--text); margin: 0; padding: 0; }
        header { background: #2c3e50; color: white; padding: 1.5rem; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .main-container { max-width: 1400px; margin: 20px auto; padding: 0 20px; }
        .controls { display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 20px; background: var(--card-bg); padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); align-items: center; }
        .search-box { flex-grow: 1; min-width: 250px; }
        input[type="text"] { width: 100%; padding: 10px; border: 1px solid var(--border); border-radius: 4px; box-sizing: border-box; }
        .table-wrapper { background: var(--card-bg); border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); overflow: hidden; }
        .scroll-container { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; min-width: 1200px; }
        th { background: #f8f9fa; color: #7f8c8d; font-weight: 600; text-transform: uppercase; font-size: 12px; padding: 12px 15px; border-bottom: 2px solid var(--border); cursor: pointer; position: sticky; top: 0; z-index: 10; }
        th:hover { background: #edf2f7; color: var(--primary); }
        td { padding: 12px 15px; border-bottom: 1px solid var(--border); font-size: 14px; white-space: nowrap; text-align: right; }
        td:nth-child(2), td:nth-child(7) { text-align: left; } /* Tickerと業界は左寄せ */
        tr:hover { background-color: #f1f9ff; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; background: #e0e0e0; color: #444; }
        .footer-info { margin-top: 10px; font-size: 12px; color: #95a5a6; display: flex; justify-content: space-between; }
        .loading { text-align: center; padding: 100px; font-size: 1.2rem; }
    </style>
</head>
<body>

<header>
    <h1>US Stock Financial Screener</h1>
</header>

<div class="main-container">
    <div class="controls">
        <div class="search-box">
            <input type="text" id="filterInput" placeholder="銘柄名、ティッカー、業種で絞り込み..." onkeyup="filterData()">
        </div>
        <div id="statCount" style="font-weight: bold; color: var(--primary);"></div>
    </div>

    <div class="table-wrapper">
        <div id="loader" class="loading">データを読み込み中...</div>
        <div class="scroll-container">
            <table id="stockTable" style="display:none;">
                <thead id="tableHead"></thead>
                <tbody id="tableBody"></tbody>
            </table>
        </div>
    </div>

    <div class="footer-info">
        <div id="updateStamp"></div>
        <div>※列名クリックでソート。金額は Million Dollar (M$) 単位。</div>
    </div>
</div>

<script>
    let allData = [];
    let currentSort = { col: null, asc: true };

    // 数値を Million 単位のカンマ区切りにする関数
    function formatMillion(val, headerName) {
        const targets = ["⑧当期売上高", "⑨当期純利益", "⑫時価総額", "③営業CF"];
        if (targets.includes(headerName)) {
            const num = parseFloat(val);
            if (!isNaN(num)) {
                return (num / 1000000).toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                }) + " M$";
            }
        }
        return val;
    }

    async function loadCSV() {
        try {
            const response = await fetch('data/stock_data.csv');
            const csvText = await response.text();
            Papa.parse(csvText, {
                header: true,
                skipEmptyLines: true,
                complete: function(results) {
                    allData = results.data;
                    document.getElementById('loader').style.display = 'none';
                    document.getElementById('stockTable').style.display = 'table';
                    renderTable(allData);
                    if(allData.length > 0) {
                        document.getElementById('updateStamp').innerText = "最終更新(JST): " + allData[0]['更新日時'];
                    }
                }
            });
        } catch (e) {
            document.getElementById('loader').innerText = "読み込みエラー。GitHub Actionsが完了しているか確認してください。";
        }
    }

    function renderTable(data) {
        if (data.length === 0) return;
        const headers = Object.keys(data[0]);
        const head = document.getElementById('tableHead');
        const body = document.getElementById('tableBody');

        head.innerHTML = `<tr>${headers.map(h => `<th onclick="sortTable('${h}')">${h}</th>`).join('')}</tr>`;

        body.innerHTML = data.map(row => {
            return `<tr>${headers.map(h => {
                let val = row[h] || '-';
                val = formatMillion(val, h); // 金額項目をM$化
                if(h === "⑤業界/セクター") return `<td><span class="badge">${val}</span></td>`;
                return `<td>${val}</td>`;
            }).join('')}</tr>`;
        }).join('');
        document.getElementById('statCount').innerText = `${data.length} 銘柄を表示中`;
    }

    function filterData() {
        const query = document.getElementById('filterInput').value.toLowerCase();
        const filtered = allData.filter(row => {
            return Object.values(row).some(v => String(v).toLowerCase().includes(query));
        });
        renderTable(filtered);
    }

    function sortTable(column) {
        currentSort.asc = (currentSort.col === column) ? !currentSort.asc : true;
        currentSort.col = column;
        const sorted = [...allData].sort((a, b) => {
            const cleanNum = (s) => parseFloat(String(s).replace(/[^-0.9.]/g, ''));
            const numA = cleanNum(a[column]);
            const numB = cleanNum(b[column]);
            if (!isNaN(numA) && !isNaN(numB)) {
                return currentSort.asc ? numA - numB : numB - numA;
            }
            return currentSort.asc ? String(a[column]).localeCompare(String(b[column])) : String(b[column]).localeCompare(String(a[column]));
        });
        renderTable(sorted);
    }

    loadCSV();
</script>
</body>
</html>
