"""
重新生成 HTML - 包含所有已有圖片的 KOL
"""

import os
import json
import re
from datetime import datetime

DOWNLOAD_DIR = "kol_avatars"
HTML_FILENAME = "index.html"
KOL_DATA_FILE = r'd:\google antigravity\kolphoto\kol_list_cleaned.json'

def safe_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name)

# 讀取 KOL 資料
with open(KOL_DATA_FILE, 'r', encoding='utf-8') as f:
    kol_list = json.load(f)

# 取得所有已有的圖片
existing_images = {}
for f in os.listdir(DOWNLOAD_DIR):
    name = os.path.splitext(f)[0]
    existing_images[name] = os.path.join(DOWNLOAD_DIR, f)

print(f"找到 {len(existing_images)} 張圖片")

# 建立多種匹配索引
name_to_kol = {}
display_to_kol = {}
for kol in kol_list:
    name_to_kol[safe_filename(kol['name'])] = kol
    display_to_kol[safe_filename(kol['display_name'])] = kol

# 匹配 KOL 與圖片
results = []
matched_images = set()

for img_name, img_path in existing_images.items():
    kol = None
    
    # 優先用 name 匹配
    if img_name in name_to_kol:
        kol = name_to_kol[img_name]
    # 其次用 display_name 匹配
    elif img_name in display_to_kol:
        kol = display_to_kol[img_name]
    else:
        # 部分匹配：檢查圖片名稱是否包含 KOL name 或反之
        for k in kol_list:
            safe_name = safe_filename(k['name'])
            safe_display = safe_filename(k['display_name'])
            if (safe_name in img_name or img_name in safe_name or 
                safe_display in img_name or img_name in safe_display):
                kol = k
                break
    
    if kol:
        social_link = kol.get('social_link', '').lower()
        platform = 'Manual'
        if 'instagram' in social_link:
            platform = 'Instagram'
        elif 'facebook' in social_link:
            platform = 'Facebook'
        elif 'youtube' in social_link:
            platform = 'YouTube'
        
        results.append({
            'display_name': kol['display_name'],
            'clean_name': kol['name'],
            'path': img_path,
            'platform': platform
        })
        matched_images.add(img_name)
    else:
        # 未匹配的圖片，用圖片名稱作為顯示名稱
        results.append({
            'display_name': img_name,
            'clean_name': img_name,
            'path': img_path,
            'platform': 'Manual'
        })
        print(f"  [新增] {img_name} (無 JSON 資料，使用圖片名稱)")

print(f"匹配成功 {len(results)} 位 KOL")

# A區優先名單
priority_list = [
    "丁菱娟",
    "冏星人",
    "馬克說書",
    "周慕姿",
    "尚瑞君",
    "心理師想跟你說",
    "愛瑞克",
    "科技工作講",
    "施 定男",
    "李柏鋒",
    "林奇芬",
    "閱讀人",
    "陳志恆諮商心理師",
]

# 排序函數：A區優先
def get_priority(kol):
    display = kol['display_name']
    clean = kol['clean_name']
    for i, name in enumerate(priority_list):
        if name in display or name in clean:
            return (0, i)  # A區，按名單順序
    return (1, display)  # B區，按名稱排序

results.sort(key=get_priority)

# 分區結果
a_zone = [k for k in results if get_priority(k)[0] == 0]
b_zone = [k for k in results if get_priority(k)[0] == 1]
print(f"A區: {len(a_zone)} 位, B區: {len(b_zone)} 位")

# 生成 HTML
css_style = """
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { 
        font-family: 'Segoe UI', 'Microsoft JhengHei', sans-serif; 
        background: #f5f5f7;
        min-height: 100vh;
        padding: 40px 20px; 
    }
    h1 {
        text-align: center;
        color: #1d1d1f;
        font-size: 2.2em;
        font-weight: 600;
        margin-bottom: 10px;
    }
    .stats {
        text-align: center;
        color: #86868b;
        margin-bottom: 30px;
        font-size: 1em;
    }
    .section-title {
        max-width: 1200px;
        margin: 30px auto 15px;
        padding: 10px 0;
        font-size: 1.3em;
        font-weight: 600;
        color: #1d1d1f;
        border-bottom: 2px solid #e0e0e0;
    }
    .section-title:first-of-type {
        margin-top: 0;
    }
    .grid-container {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
        gap: 20px;
        max-width: 1200px;
        margin: 0 auto;
    }
    .card {
        background: white;
        border-radius: 16px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        overflow: hidden;
        text-align: center;
        transition: all 0.3s ease;
    }
    .card:hover { 
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.12);
    }
    .card .img-wrapper {
        width: 100%;
        aspect-ratio: 1 / 1;
        overflow: hidden;
    }
    .card img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        object-position: center top;
    }
    .card-body {
        padding: 12px 10px;
    }
    .card h3 { 
        font-size: 0.85em;
        font-weight: 600;
        color: #1d1d1f; 
        margin-bottom: 2px;
        line-height: 1.3;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .card .real-name {
        font-size: 0.7em;
        color: #86868b;
        margin-bottom: 6px;
    }
    .platform-badge {
        display: inline-block;
        font-size: 0.65em;
        padding: 3px 8px;
        border-radius: 12px;
        color: white;
        font-weight: 500;
    }
    .platform-instagram { background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888); }
    .platform-facebook { background: #1877f2; }
    .platform-youtube { background: #ff0000; }
    .platform-manual { background: #86868b; }

    /* 搜尋框樣式 */
    .search-container {
        max-width: 500px;
        margin: 0 auto 30px;
        position: relative;
    }
    .search-input {
        width: 100%;
        padding: 14px 20px 14px 50px;
        border: 2px solid #e0e0e0;
        border-radius: 30px;
        font-size: 1em;
        outline: none;
        transition: all 0.3s ease;
    }
    .search-input:focus {
        border-color: #667eea;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
    }
    .search-icon {
        position: absolute;
        left: 18px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 1.2em;
        color: #86868b;
    }
    .card.hidden { display: none; }
    .no-results {
        text-align: center;
        color: #86868b;
        padding: 40px;
        grid-column: 1 / -1;
    }

    @media (max-width: 768px) {
        body { padding: 20px 12px; }
        h1 { font-size: 1.6em; }
        .grid-container {
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }
        .card { border-radius: 12px; }
        .card-body { padding: 10px 8px; }
        .card h3 { font-size: 0.8em; }
    }
    
    @media (max-width: 400px) {
        .grid-container {
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }
    }
</style>
"""


def generate_card_html(kol):
    platform = kol.get('platform', 'Manual')
    platform_class = f"platform-{platform.lower()}"
    display_name = kol['display_name']
    clean_name = kol['clean_name']
    
    if clean_name and clean_name != display_name:
        name_html = f"<h3>{display_name}</h3><p class='real-name'>({clean_name})</p>"
    else:
        name_html = f"<h3>{display_name}</h3>"
    
    return f"""
    <div class="card" data-name="{display_name} {clean_name}">
        <div class="img-wrapper">
            <img src="{kol['path']}" alt="{display_name}" loading="lazy">
        </div>
        <div class="card-body">
            {name_html}
            <span class="platform-badge {platform_class}">{platform}</span>
        </div>
    </div>
    """

# 生成 A區 卡片
a_zone_cards = ""
for kol in a_zone:
    a_zone_cards += generate_card_html(kol)

# 生成 B區 卡片
b_zone_cards = ""
for kol in b_zone:
    b_zone_cards += generate_card_html(kol)


full_html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KOL 名單 - {datetime.now().strftime('%Y/%m/%d')}</title>
    {css_style}
</head>
<body>
    <h1>樊登新書發佈會創作者</h1>
    <p class="stats">共 {len(results)} 位創作者（A區 {len(a_zone)} 位 / B區 {len(b_zone)} 位）</p>
    <div class="search-container">
        <span class="search-icon">🔍</span>
        <input type="text" class="search-input" id="searchInput" placeholder="輸入姓名或社群名稱搜尋..." oninput="filterCards()">
    </div>
    <h2 class="section-title">⭐ A區</h2>
    <div class="grid-container" id="cardContainer">
        {a_zone_cards}
    </div>
    <h2 class="section-title">📚 B區</h2>
    <div class="grid-container">
        {b_zone_cards}
    </div>
    <script>
        function filterCards() {{
            const query = document.getElementById('searchInput').value.toLowerCase();
            const cards = document.querySelectorAll('.card');
            let visibleCount = 0;
            
            cards.forEach(card => {{
                const name = card.getAttribute('data-name').toLowerCase();
                if (name.includes(query)) {{
                    card.classList.remove('hidden');
                    visibleCount++;
                }} else {{
                    card.classList.add('hidden');
                }}
            }});
            
            // 顯示無結果提示
            let noResults = document.querySelector('.no-results');
            if (visibleCount === 0 && query) {{
                if (!noResults) {{
                    noResults = document.createElement('div');
                    noResults.className = 'no-results';
                    noResults.textContent = '找不到符合的創作者';
                    document.getElementById('cardContainer').appendChild(noResults);
                }}
            }} else if (noResults) {{
                noResults.remove();
            }}
        }}
    </script>
</body>
</html>"""

with open(HTML_FILENAME, "w", encoding="utf-8") as f:
    f.write(full_html)

print(f"HTML 已生成：{HTML_FILENAME}")
