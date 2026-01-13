"""
重命名圖片：統一命名為 社群名稱(姓名).jpg
"""
import os
import json
import re

DOWNLOAD_DIR = "kol_avatars"
KOL_DATA_FILE = r'd:\google antigravity\kolphoto\kol_list_cleaned.json'

def safe_filename(name):
    # 移除 Windows 不允許的字符
    return re.sub(r'[<>:"/\\|?*]', '_', name)

# 讀取 KOL 資料
with open(KOL_DATA_FILE, 'r', encoding='utf-8') as f:
    kol_list = json.load(f)

# 建立 name -> display_name 映射
name_to_display = {}
display_to_name = {}
for kol in kol_list:
    name = kol['name']
    display = kol['display_name']
    name_to_display[safe_filename(name)] = display
    display_to_name[safe_filename(display)] = name

# 取得所有圖片
images = os.listdir(DOWNLOAD_DIR)
print(f"找到 {len(images)} 張圖片\n")

rename_count = 0
for img in images:
    img_name, ext = os.path.splitext(img)
    old_path = os.path.join(DOWNLOAD_DIR, img)
    
    # 找出對應的 KOL
    display_name = None
    real_name = None
    
    # 嘗試用圖片名稱匹配 name
    if img_name in name_to_display:
        real_name = img_name
        display_name = name_to_display[img_name]
    # 嘗試用圖片名稱匹配 display_name
    elif img_name in display_to_name:
        display_name = img_name
        real_name = display_to_name[img_name]
    else:
        # 部分匹配
        for kol in kol_list:
            safe_name = safe_filename(kol['name'])
            safe_display = safe_filename(kol['display_name'])
            if (safe_name in img_name or img_name in safe_name or
                safe_display in img_name or img_name in safe_display):
                real_name = kol['name']
                display_name = kol['display_name']
                break
    
    if display_name and real_name:
        # 生成新檔名：社群名稱(姓名).ext
        if display_name != real_name:
            new_name = f"{safe_filename(display_name)}({safe_filename(real_name)}){ext}"
        else:
            new_name = f"{safe_filename(display_name)}{ext}"
        
        new_path = os.path.join(DOWNLOAD_DIR, new_name)
        
        if old_path != new_path and not os.path.exists(new_path):
            print(f"重命名: {img} -> {new_name}")
            os.rename(old_path, new_path)
            rename_count += 1
        elif old_path == new_path:
            print(f"保持: {img}")
        else:
            print(f"跳過(已存在): {img}")
    else:
        print(f"未匹配: {img}")

print(f"\n完成！重命名 {rename_count} 張圖片")
