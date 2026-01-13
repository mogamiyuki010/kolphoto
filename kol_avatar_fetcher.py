"""
KOL 社群頭像抓取工具
從 Instagram, Facebook, YouTube 直接抓取頭像
"""

import os
import re
import json
import time
import requests
from urllib.parse import urlparse
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

def safe_filename(name):
    """產生安全的檔案名稱"""
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def download_image(name, url):
    """下載圖片並儲存到本地"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            # 判斷副檔名
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

def extract_instagram_username(url):
    """從 Instagram URL 提取用戶名"""
    patterns = [
        r'instagram\.com/([^/?]+)',
        r'instagram\.com/p/[^/]+.*?by=([^&]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            username = match.group(1).strip()
            if username not in ['p', 'reel', 'stories', 'explore', 'accounts']:
                return username
    return None

# Instagram loader 全域變數
_insta_loader = None

def get_instaloader():
    """取得或建立 instaloader 實例（帶登入）"""
    global _insta_loader
    if _insta_loader is None:
        try:
            import instaloader
            _insta_loader = instaloader.Instaloader()
            # 嘗試登入
            try:
                _insta_loader.login('kingway_publishing', 'Cmoney1234')
                print("    [IG] 登入成功")
            except Exception as e:
                print(f"    [IG] 登入失敗，使用匿名模式: {e}")
        except ImportError:
            print("    [IG] instaloader 未安裝")
            return None
    return _insta_loader

def fetch_instagram_avatar(url):
    """從 Instagram 抓取頭像"""
    username = extract_instagram_username(url)
    if not username:
        return None
    
    # 方法1: 使用 instaloader（更穩定）
    try:
        loader = get_instaloader()
        if loader:
            import instaloader
            profile = instaloader.Profile.from_username(loader.context, username)
            return profile.profile_pic_url
    except Exception as e:
        pass
    
    # 方法2: 從頁面 HTML 解析 og:image (fallback)
    try:
        profile_url = f"https://www.instagram.com/{username}/"
        response = requests.get(profile_url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            match = re.search(r'<meta property="og:image" content="([^"]+)"', response.text)
            if match:
                return match.group(1)
    except:
        pass
    
    return None

def extract_facebook_id(url):
    """從 Facebook URL 提取用戶 ID 或用戶名"""
    patterns = [
        r'facebook\.com/profile\.php\?id=(\d+)',
        r'facebook\.com/people/[^/]+/(\d+)',
        r'facebook\.com/([^/?]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            result = match.group(1).strip()
            if result not in ['p', 'share', 'sharer', 'dialog', 'watch', 'groups', 'events']:
                return result
    return None

def fetch_facebook_avatar(url):
    """從 Facebook 抓取頭像"""
    fb_id = extract_facebook_id(url)
    if not fb_id:
        return None
    
    try:
        # 使用 Graph API 風格 URL（適用數字 ID）
        if fb_id.isdigit():
            avatar_url = f"https://graph.facebook.com/{fb_id}/picture?type=large"
            response = requests.get(avatar_url, headers=HEADERS, timeout=10, allow_redirects=True)
            if response.status_code == 200 and len(response.content) > 1000:
                return response.url
    except:
        pass
    
    try:
        # 從頁面 HTML 解析 og:image
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            match = re.search(r'<meta property="og:image" content="([^"]+)"', response.text)
            if match:
                return match.group(1)
    except:
        pass
    
    return None

def extract_youtube_channel(url):
    """從 YouTube URL 提取頻道資訊"""
    patterns = [
        r'youtube\.com/@([^/?]+)',
        r'youtube\.com/channel/([^/?]+)',
        r'youtube\.com/c/([^/?]+)',
        r'youtube\.com/user/([^/?]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1).strip()
    return None

def fetch_youtube_avatar(url):
    """從 YouTube 抓取頭像"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            # 抓取頻道頭像 URL
            match = re.search(r'"avatar":\{"thumbnails":\[\{"url":"([^"]+)"', response.text)
            if match:
                return match.group(1).replace('\\u0026', '&')
            # 備用方法
            match = re.search(r'<link rel="image_src" href="([^"]+)"', response.text)
            if match:
                return match.group(1)
    except:
        pass
    return None

def fetch_avatar_by_platform(social_link):
    """根據平台類型選擇對應的抓取方法"""
    if not social_link or not social_link.startswith('http'):
        return None, None
    
    url_lower = social_link.lower()
    
    if 'instagram.com' in url_lower:
        return fetch_instagram_avatar(social_link), 'Instagram'
    elif 'facebook.com' in url_lower:
        return fetch_facebook_avatar(social_link), 'Facebook'
    elif 'youtube.com' in url_lower:
        return fetch_youtube_avatar(social_link), 'YouTube'
    elif 'x.com' in url_lower or 'twitter.com' in url_lower:
        # Twitter/X 需要登入，暫不支援
        return None, 'X/Twitter'
    
    return None, None

def search_fallback(name):
    """使用 DuckDuckGo 搜尋作為 fallback"""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            search_query = f"{name} 台灣 KOL 頭像"
            results = ddgs.images(search_query, max_results=1)
            if results:
                return results[0]['image']
    except Exception as e:
        print(f"    搜尋 fallback 失敗: {e}")
    return None

def main():
    # 讀取 KOL 資料
    with open(KOL_DATA_FILE, 'r', encoding='utf-8') as f:
        kol_list = json.load(f)
    
    print(f"載入 {len(kol_list)} 位 KOL 資料")
    print("="*60)
    
    results = []
    stats = {'instagram': 0, 'facebook': 0, 'youtube': 0, 'fallback': 0, 'failed': 0}
    
    for idx, kol in enumerate(kol_list, 1):
        name = kol['display_name']
        clean_name = kol['name']
        social_link = kol.get('social_link', '')
        
        print(f"[{idx}/{len(kol_list)}] {name}")
        
        avatar_url = None
        platform = None
        
        # 嘗試從社群連結抓取
        if social_link and social_link.startswith('http'):
            avatar_url, platform = fetch_avatar_by_platform(social_link)
            if avatar_url:
                print(f"    ✓ 從 {platform} 取得頭像")
        
        # 無社群連結的 KOL 暫時跳過（避免 DDG rate limit）
        if not avatar_url:
            if social_link and social_link.startswith('http'):
                print(f"    ✗ 無法從社群取得頭像")
            else:
                print(f"    - 無社群連結，跳過")
        
        # 下載圖片
        if avatar_url:
            local_path = download_image(clean_name, avatar_url)
            if local_path:
                results.append({
                    'name': name,
                    'path': local_path,
                    'platform': platform
                })
                if platform == 'Instagram':
                    stats['instagram'] += 1
                elif platform == 'Facebook':
                    stats['facebook'] += 1
                elif platform == 'YouTube':
                    stats['youtube'] += 1
                else:
                    stats['fallback'] += 1
            else:
                stats['failed'] += 1
                print(f"    ✗ 下載失敗")
        else:
            stats['failed'] += 1
            print(f"    ✗ 無法取得頭像")
        
        # 每 10 個休息一下
        if idx % 10 == 0:
            time.sleep(2)
    
    print("\n" + "="*60)
    print("抓取完成統計:")
    print(f"  Instagram: {stats['instagram']}")
    print(f"  Facebook:  {stats['facebook']}")
    print(f"  YouTube:   {stats['youtube']}")
    print(f"  搜尋補充:  {stats['fallback']}")
    print(f"  失敗:      {stats['failed']}")
    print(f"  總成功:    {len(results)}/{len(kol_list)}")
    
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
            font-size: 0.95em;
            color: #333; 
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
        .platform-search { background: #888; }
    </style>
    """
    
    cards_html = ""
    for kol in kol_data:
        platform = kol.get('platform', 'Search')
        platform_class = f"platform-{platform.lower()}"
        cards_html += f"""
        <div class="card">
            <img src="{kol['path']}" alt="{kol['name']}" loading="lazy">
            <div class="card-body">
                <h3>{kol['name']}</h3>
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
    data = main()
    if data:
        generate_html(data)
    else:
        print("未抓取到任何資料。")
