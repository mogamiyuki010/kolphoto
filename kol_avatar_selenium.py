"""
KOL 社群頭像抓取工具 v2
使用 Selenium 抓取 Facebook 頭像，提高成功率
"""

import os
import re
import json
import time
import requests
from urllib.parse import urlparse, unquote
from datetime import datetime

# --- 設定區 ---
DOWNLOAD_DIR = "kol_avatars"
HTML_FILENAME = "index.html"
KOL_DATA_FILE = r'd:\google antigravity\kolphoto\kol_list_cleaned.json'

# 確保資料夾存在
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# 請求 headers（模擬瀏覽器）
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
}

# Selenium driver 全域變數
_selenium_driver = None

def get_selenium_driver():
    """取得 Selenium driver（Chrome headless）"""
    global _selenium_driver
    if _selenium_driver is None:
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            from webdriver_manager.chrome import ChromeDriverManager
            
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            chrome_options.add_argument("--lang=zh-TW")
            
            service = Service(ChromeDriverManager().install())
            _selenium_driver = webdriver.Chrome(service=service, options=chrome_options)
            print("    [Selenium] Chrome driver 初始化成功")
        except Exception as e:
            print(f"    [Selenium] 初始化失敗: {e}")
            return None
    return _selenium_driver

def close_selenium_driver():
    """關閉 Selenium driver"""
    global _selenium_driver
    if _selenium_driver:
        _selenium_driver.quit()
        _selenium_driver = None

def safe_filename(name):
    """產生安全的檔案名稱"""
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def download_image(name, url):
    """下載圖片並儲存到本地"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            if 'png' in content_type:
                ext = '.png'
            elif 'gif' in content_type:
                ext = '.gif'
            elif 'webp' in content_type:
                ext = '.webp'
            else:
                ext = '.jpg'
            
            filename = f"{safe_filename(name)}{ext}"
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return filepath
    except Exception as e:
        print(f"    下載失敗: {e}")
    return None

# ==================== Instagram ====================

def extract_instagram_username(url):
    """從 Instagram URL 提取用戶名"""
    patterns = [
        r'instagram\.com/([^/?]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            username = match.group(1).strip()
            if username not in ['p', 'reel', 'stories', 'explore', 'accounts', 'about']:
                return username
    return None

_insta_loader = None

def get_instaloader():
    """取得 instaloader 實例"""
    global _insta_loader
    if _insta_loader is None:
        try:
            import instaloader
            _insta_loader = instaloader.Instaloader()
            try:
                _insta_loader.login('kingway_publishing', 'Cmoney1234')
                print("    [IG] 登入成功")
            except Exception as e:
                print(f"    [IG] 登入失敗: {e}")
        except ImportError:
            return None
    return _insta_loader

def fetch_instagram_avatar(url):
    """從 Instagram 抓取頭像"""
    username = extract_instagram_username(url)
    if not username:
        return None
    
    try:
        loader = get_instaloader()
        if loader:
            import instaloader
            profile = instaloader.Profile.from_username(loader.context, username)
            return profile.profile_pic_url
    except:
        pass
    return None

# ==================== Facebook (Selenium) ====================

def fetch_facebook_avatar_selenium(url):
    """使用 Selenium 從 Facebook 抓取頭像"""
    driver = get_selenium_driver()
    if not driver:
        return None
    
    try:
        driver.get(url)
        time.sleep(3)  # 等待頁面載入
        
        # 方法1: 找 profile picture image
        from selenium.webdriver.common.by import By
        
        # 嘗試多種選擇器
        selectors = [
            'img[data-imgperflogname="profileCoverPhoto"]',
            'image[preserveAspectRatio="xMidYMid slice"]',
            'svg[aria-label] image',
            'img.x1lq5wgf',  # 常見的 FB 頭像 class
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    src = elem.get_attribute('xlink:href') or elem.get_attribute('src')
                    if src and ('fbcdn' in src or 'facebook' in src):
                        return src
            except:
                continue
        
        # 方法2: 從頁面源碼找 og:image
        page_source = driver.page_source
        match = re.search(r'"profilePicLarge":\{"uri":"([^"]+)"', page_source)
        if match:
            return match.group(1).replace('\\/', '/')
        
        match = re.search(r'<meta property="og:image" content="([^"]+)"', page_source)
        if match:
            return match.group(1)
            
    except Exception as e:
        print(f"    [FB Selenium] 錯誤: {e}")
    
    return None

# ==================== YouTube ====================

def fetch_youtube_avatar(url):
    """從 YouTube 抓取頭像"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            match = re.search(r'"avatar":\{"thumbnails":\[\{"url":"([^"]+)"', response.text)
            if match:
                return match.group(1).replace('\\u0026', '&')
            match = re.search(r'<link rel="image_src" href="([^"]+)"', response.text)
            if match:
                return match.group(1)
    except:
        pass
    return None

# ==================== 主程序 ====================

def fetch_avatar_by_platform(social_link):
    """根據平台類型選擇對應的抓取方法"""
    if not social_link or not social_link.startswith('http'):
        return None, None
    
    url_lower = social_link.lower()
    
    if 'instagram.com' in url_lower:
        return fetch_instagram_avatar(social_link), 'Instagram'
    elif 'facebook.com' in url_lower:
        return fetch_facebook_avatar_selenium(social_link), 'Facebook'
    elif 'youtube.com' in url_lower:
        return fetch_youtube_avatar(social_link), 'YouTube'
    
    return None, None

def main():
    # 讀取 KOL 資料
    with open(KOL_DATA_FILE, 'r', encoding='utf-8') as f:
        kol_list = json.load(f)
    
    # 篩選有社群連結的 KOL
    kol_with_links = [k for k in kol_list if k.get('social_link', '').startswith('http')]
    
    print(f"載入 {len(kol_list)} 位 KOL，其中 {len(kol_with_links)} 位有社群連結")
    print("="*60)
    
    results = []
    stats = {'instagram': 0, 'facebook': 0, 'youtube': 0, 'failed': 0}
    
    # 先載入已經成功的結果
    existing_files = set()
    if os.path.exists(DOWNLOAD_DIR):
        for f in os.listdir(DOWNLOAD_DIR):
            name = os.path.splitext(f)[0]
            existing_files.add(name)
    
    for idx, kol in enumerate(kol_with_links, 1):
        name = kol['display_name']
        clean_name = kol['name']
        social_link = kol.get('social_link', '')
        
        # 檢查是否已經下載過
        if safe_filename(clean_name) in existing_files:
            print(f"[{idx}/{len(kol_with_links)}] {name} - 已存在，跳過")
            # 找到現有檔案
            for f in os.listdir(DOWNLOAD_DIR):
                if f.startswith(safe_filename(clean_name)):
                    platform = 'Existing'
                    if 'instagram' in social_link.lower():
                        platform = 'Instagram'
                    elif 'facebook' in social_link.lower():
                        platform = 'Facebook'
                    elif 'youtube' in social_link.lower():
                        platform = 'YouTube'
                    results.append({
                        'display_name': name,
                        'clean_name': clean_name,
                        'path': os.path.join(DOWNLOAD_DIR, f),
                        'platform': platform
                    })
                    break
            continue
        
        print(f"[{idx}/{len(kol_with_links)}] {name}")
        
        avatar_url, platform = fetch_avatar_by_platform(social_link)
        
        if avatar_url:
            print(f"    ✓ 從 {platform} 取得頭像 URL")
            local_path = download_image(clean_name, avatar_url)
            if local_path:
                results.append({
                    'display_name': name,
                    'clean_name': clean_name,
                    'path': local_path,
                    'platform': platform
                })
                if platform == 'Instagram':
                    stats['instagram'] += 1
                elif platform == 'Facebook':
                    stats['facebook'] += 1
                elif platform == 'YouTube':
                    stats['youtube'] += 1
                print(f"    ✓ 下載成功")
            else:
                stats['failed'] += 1
                print(f"    ✗ 下載失敗")
        else:
            stats['failed'] += 1
            print(f"    ✗ 無法取得頭像")
        
        # 每 5 個休息一下
        if idx % 5 == 0:
            time.sleep(1)
    
    # 關閉 Selenium
    close_selenium_driver()
    
    print("\n" + "="*60)
    print("本次抓取統計:")
    print(f"  Instagram: {stats['instagram']}")
    print(f"  Facebook:  {stats['facebook']}")
    print(f"  YouTube:   {stats['youtube']}")
    print(f"  失敗:      {stats['failed']}")
    print(f"  總成功:    {len(results)}/{len(kol_with_links)} (有連結者)")
    
    return results

def generate_html(kol_data):
    """生成格狀卡片 HTML"""
    css_style = """
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', 'Microsoft JhengHei', sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px; 
        }
        h1 {
            text-align: center;
            color: white;
            font-size: 2.5em;
            margin-bottom: 40px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .stats {
            text-align: center;
            color: rgba(255,255,255,0.9);
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        .grid-container {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 25px;
            max-width: 1400px;
            margin: 0 auto;
        }
        .card {
            background: white;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
            text-align: center;
            transition: all 0.3s ease;
        }
        .card:hover { 
            transform: translateY(-10px) scale(1.02);
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        }
        .card img {
            width: 100%;
            height: 180px;
            object-fit: cover;
        }
        .card-body {
            padding: 15px;
        }
        .card h3 { 
            font-size: 0.9em;
            color: #333; 
            margin-bottom: 3px;
            line-height: 1.3;
        }
        .card .real-name {
            font-size: 0.75em;
            color: #666;
            margin-bottom: 5px;
        }
        .platform-badge {
            display: inline-block;
            font-size: 0.7em;
            padding: 3px 8px;
            border-radius: 10px;
            color: white;
        }
        .platform-instagram { background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888); }
        .platform-facebook { background: #1877f2; }
        .platform-youtube { background: #ff0000; }
        .platform-existing { background: #888; }
    </style>
    """
    
    cards_html = ""
    for kol in kol_data:
        platform = kol.get('platform', 'Unknown')
        platform_class = f"platform-{platform.lower()}"
        display_name = kol.get('display_name', kol.get('name', ''))
        clean_name = kol.get('clean_name', '')
        # 如果 display_name 和 clean_name 不同，顯示兩者
        if clean_name and clean_name != display_name:
            name_html = f"<h3>{display_name}</h3><p class='real-name'>({clean_name})</p>"
        else:
            name_html = f"<h3>{display_name}</h3>"
        cards_html += f"""
        <div class="card">
            <div class="img-wrapper">
                <img src="{kol['path']}" alt="{display_name}" loading="lazy">
            </div>
            <div class="card-body">
                {name_html}
                <span class="platform-badge {platform_class}">{platform}</span>
            </div>
        </div>
        """
        
    full_html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KOL 名單 - {datetime.now().strftime('%Y/%m/%d')}</title>
    {css_style}
</head>
<body>
    <h1>🎯 我的 KOL 追蹤名單</h1>
    <p class="stats">共 {len(kol_data)} 位 KOL</p>
    <div class="grid-container">
        {cards_html}
    </div>
</body>
</html>"""
    
    with open(HTML_FILENAME, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"\nHTML 已生成：{HTML_FILENAME}")

if __name__ == "__main__":
    try:
        data = main()
        if data:
            generate_html(data)
        else:
            print("未抓取到任何資料。")
    finally:
        close_selenium_driver()
