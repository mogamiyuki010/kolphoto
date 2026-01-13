"""
KOL 名單資料清洗腳本
從 Excel 讀取原始資料，清洗後輸出適合搜尋頭像的名單
"""

import pandas as pd
import re
import json

# 讀取 Excel
df = pd.read_excel(r'd:\google antigravity\kolphoto\kol_list_booklunch.xlsx', sheet_name='kol_list')

def extract_clean_name(raw_name, has_social_link=False):
    """
    清洗姓名欄位，提取主要 KOL 名稱
    規則：
    1. 移除括號內的資訊 (英文名、真名等)
    2. 移除「同行人」相關資訊（除非有自己的社群連結）
    3. 保留主要暱稱或藝名
    """
    if pd.isna(raw_name) or not str(raw_name).strip():
        return None
    
    name = str(raw_name).strip()
    
    # 跳過同行人，除非有自己的社群連結
    is_companion = '同行人' in name or '同行者' in name or '同仁人' in name or '同行' in name
    if is_companion and not has_social_link:
        return None
    
    # 移除特殊符號開頭 (如 🔖)
    name = re.sub(r'^[^\w\u4e00-\u9fff]+', '', name)
    
    # 提取括號前的名稱作為主要名稱
    # 例如: "朱麗禎 (超認真少年YT90.2萬)大咖" -> "朱麗禎" 或 "超認真少年"
    
    # 嘗試匹配模式: 真名 (暱稱)
    match = re.match(r'^(.+?)\s*[\(（](.+?)[\)）]', name)
    if match:
        real_name = match.group(1).strip()
        nickname = match.group(2).strip()
        # 移除暱稱中的額外資訊
        nickname = re.sub(r'(YT|yt|YouTube|FB|IG|粉絲|萬|大咖|,.*|，.*).*', '', nickname).strip()
        # 如果暱稱更有辨識度，優先使用暱稱
        if len(nickname) > 1 and not nickname.isdigit():
            return nickname
        return real_name
    
    # 移除後綴資訊
    name = re.sub(r'\s*[\(（].*', '', name)
    name = re.sub(r'\s*大咖.*', '', name)
    name = re.sub(r'\s*-.*', '', name)
    
    return name.strip() if name.strip() else None

def get_display_name(row):
    """
    取得用於顯示的名稱
    優先順序: 社群名稱 > 清洗後的姓名
    """
    social_name = row.get('社群名稱', '')
    if pd.notna(social_name) and str(social_name).strip():
        # 清理社群名稱
        social = str(social_name).strip()
        social = re.sub(r'\s*[\(（].*', '', social)  # 移除括號
        if social:
            return social
    
    return extract_clean_name(row.get('姓名', ''))

# 處理資料
kol_list = []
seen_names = set()

for idx, row in df.iterrows():
    raw_name = row.get('姓名', '')
    
    # 取得社群連結
    social_link = row.get('主要社群', '')
    has_social_link = pd.notna(social_link) and str(social_link).strip() and str(social_link).strip().startswith('http')
    
    # 同行人如果有自己的社群連結，也視為 KOL
    is_companion = pd.notna(raw_name) and ('同行人' in str(raw_name) or '同行者' in str(raw_name) or '同仁人' in str(raw_name) or '同行' in str(raw_name))
    if is_companion and not has_social_link:
        continue
    
    clean_name = extract_clean_name(raw_name, has_social_link)
    display_name = get_display_name(row)
    
    if clean_name and clean_name not in seen_names:
        seen_names.add(clean_name)
        
        # 取得社群連結
        social_link = row.get('主要社群', '')
        social_link = social_link if pd.notna(social_link) else ''
        
        # 取得 Email
        email = row.get('Email信箱/LINE', '')
        email = email if pd.notna(email) else ''
        
        kol_list.append({
            'name': clean_name,
            'display_name': display_name if display_name else clean_name,
            'social_link': str(social_link).strip(),
            'email': str(email).strip()
        })

print(f"總共清洗出 {len(kol_list)} 位 KOL")
print("\n前 20 位 KOL 名單:")
for i, kol in enumerate(kol_list[:20], 1):
    print(f"{i:3}. {kol['name']}")

# 輸出為 Python 可用的格式
print("\n\n" + "="*50)
print("Python 可用的 KOL 名稱列表:")
print("="*50)
kol_names = [kol['name'] for kol in kol_list]
print(f"\nKOL_NAMES = {json.dumps(kol_names, ensure_ascii=False, indent=4)}")

# 儲存清洗後的資料
output_df = pd.DataFrame(kol_list)
output_df.to_csv(r'd:\google antigravity\kolphoto\kol_list_cleaned.csv', index=False, encoding='utf-8-sig')
print(f"\n清洗後的資料已儲存至: kol_list_cleaned.csv")

# 另存為 JSON 格式
with open(r'd:\google antigravity\kolphoto\kol_list_cleaned.json', 'w', encoding='utf-8') as f:
    json.dump(kol_list, f, ensure_ascii=False, indent=2)
print(f"JSON 格式已儲存至: kol_list_cleaned.json")
