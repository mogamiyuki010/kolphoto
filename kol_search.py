import os
import json
import requests
from duckduckgo_search import DDGS
from datetime import datetime

# --- 設定區 ---
# 從清洗後的 JSON 讀取 KOL 名單
with open(r'd:\google antigravity\kolphoto\kol_list_cleaned.json', 'r', encoding='utf-8') as f:
    kol_data_raw = json.load(f)

# 使用 display_name 作為搜尋和顯示名稱
KOL_NAMES = [(kol['display_name'], kol['name']) for kol in kol_data_raw]
DOWNLOAD_DIR = "kol_avatars"
HTML_FILENAME = "index.html"

# 確保資料夾存在
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def download_image(name, url):
    """下載圖片並儲存到本地"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            # 取得副檔名，預設為 jpg
            ext = ".jpg"
            filename = f"{name}{ext}"
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return filepath
    except Exception as e:
        print(f"下載 {name} 失敗: {e}")
    return None

def search_and_save_kols():
    kol_data = []
    total = len(KOL_NAMES)
    
    with DDGS() as ddgs:
        for idx, (display_name, clean_name) in enumerate(KOL_NAMES, 1):
            print(f"[{idx}/{total}] 正在搜尋 {display_name} 的頭像...")
            # 搜尋關鍵字加上 'profile picture' 提高精確度
            search_query = f"{display_name} KOL profile picture portrait"
            try:
                results = ddgs.images(search_query, max_results=1)
                
                if results:
                    image_url = results[0]['image']
                    # 使用 clean_name 作為檔名（避免特殊字元）
                    safe_filename = clean_name.replace('/', '_').replace('\\', '_').replace(':', '_')
                    local_path = download_image(safe_filename, image_url)
                    if local_path:
                        kol_data.append({"name": display_name, "path": local_path})
                        print(f"    ✓ 成功儲存: {display_name}")
                else:
                    print(f"    ✗ 找不到 {display_name} 的圖片")
            except Exception as e:
                print(f"    ✗ 搜尋 {display_name} 時發生錯誤: {e}")
                
    return kol_data

def generate_html(kol_data):
    """生成格狀卡片 HTML"""
    css_style = """
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f9; padding: 40px; }
        .grid-container {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 20px;
        }
        .card {
            background: white;
            border-radius: 15px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            overflow: hidden;
            text-align: center;
            transition: transform 0.3s;
        }
        .card:hover { transform: translateY(-5px); }
        .card img {
            width: 100%;
            height: 200px;
            object-fit: cover;
        }
        .card h3 { padding: 10px; margin: 0; color: #333; }
    </style>
    """
    
    cards_html = ""
    for kol in kol_data:
        cards_html += f"""
        <div class="card">
            <img src="{kol['path']}" alt="{kol['name']}">
            <h3>{kol['name']}</h3>
        </div>
        """
        
    full_html = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <title>KOL 名單</title>
        {css_style}
    </head>
    <body>
        <h1 style="text-align:center;">我的 KOL 追蹤名單</h1>
        <div class="grid-container">
            {cards_html}
        </div>
    </body>
    </html>
    """
    
    with open(HTML_FILENAME, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"\nHTML 已生成：{HTML_FILENAME}")

if __name__ == "__main__":
    data = search_and_save_kols()
    if data:
        generate_html(data)
    else:
        print("未抓取到任何資料。")
