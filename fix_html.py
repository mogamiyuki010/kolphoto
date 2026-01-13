import re

# 讀取 index.html
with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 替換 img 為 img-wrapper 包裹
content = re.sub(
    r'<img src="([^"]+)" alt="([^"]+)" loading="lazy">',
    r'<div class="img-wrapper"><img src="\1" alt="\2" loading="lazy"></div>',
    content
)

# 寫回
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('已更新 index.html 的圖片結構')
