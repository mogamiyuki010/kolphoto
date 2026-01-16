import json

with open('kol_list_cleaned.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

new_kols = [
    {'name': '李建復', 'display_name': '愛播聽書podcast', 'social_link': 'https://www.facebook.com/aibotingshupodcast/', 'email': ''},
]

existing_names = set(k['name'] for k in data)
existing_displays = set(k['display_name'] for k in data)

for new_kol in new_kols:
    if new_kol['name'] not in existing_names and new_kol['display_name'] not in existing_displays:
        data.append(new_kol)
        print(f"Added: {new_kol['display_name']}")
    else:
        print(f"Already exists: {new_kol['display_name']}")

with open('kol_list_cleaned.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print('Done')
