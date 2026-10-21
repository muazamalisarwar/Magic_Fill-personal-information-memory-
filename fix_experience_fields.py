"""Fix experience field names in MagicFillInteractive.astro"""
filepath = r'c:\Users\Muazam Ali\OneDrive\Desktop\Magic_Fill\automark-v1.0.0\src\layouts\components\MagicFillInteractive.astro'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix it.role -> it.job_title and it.company_name -> it.company
old1 = '${it.role || "Role"}'
new1 = '${it.job_title || "Role"}'
old2 = '${it.company_name || "Company"}'
new2 = '${it.company || "Company"}'

count1 = content.count(old1)
count2 = content.count(old2)
content = content.replace(old1, new1)
content = content.replace(old2, new2)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'Fixed {count1} occurrences of it.role -> it.job_title')
print(f'Fixed {count2} occurrences of it.company_name -> it.company')
print('Done!')
