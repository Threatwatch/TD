import pandas as pd
import json

# Load the Excel file
excel_data = pd.read_excel(r'C:\Users\fsbks\OneDrive\Desktop\Company.xlsx')

# Convert the column of names to a list
names_list = excel_data.iloc[:, 0].tolist()  # Assumes names are in the first column

# Convert the list to JSON format and save it to a file
with open('Company.json', 'w') as json_file:
    json.dump(names_list, json_file, indent=4)

print("Conversion complete! JSON data saved as 'Company.json'")