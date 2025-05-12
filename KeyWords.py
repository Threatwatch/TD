import pandas as pd
import json

# Load the Excel files
comp_data = pd.read_excel(r'C:\Users\fsbks\OneDrive\Desktop\Company.xlsx')
key_data = pd.read_excel(r'C:\Users\fsbks\OneDrive\Desktop\KeyWords.xlsx')

# Save company names from first column
if comp_data.shape[1] >= 1:
    company_keywords = comp_data.iloc[:, 0].dropna().astype(str).str.strip().tolist()
    with open('Company.json', 'w', encoding='utf-8') as json_file:
        json.dump(company_keywords, json_file, ensure_ascii=False, indent=4)
    print("✅ Company.json saved.")

# Save Arabic keywords from first column
if key_data.shape[1] >= 1:
    arabic_keywords = key_data.iloc[:, 0].dropna().astype(str).str.strip().tolist()
    with open('KeyWords.json', 'w', encoding='utf-8') as json_file:
        json.dump(arabic_keywords, json_file, ensure_ascii=False, indent=4)
    print("✅ KeyWords.json saved.")
