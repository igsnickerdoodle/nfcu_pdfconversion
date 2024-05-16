import pdfplumber
import re
import json
import pandas as pd
import os
from datetime import datetime
import shutil

def extract_year_from_statement_period(pdf):
    statement_period_pattern = re.compile(r'Statement Period\s+(\d{2}/\d{2}/\d{2})\s*-\s*(\d{2}/\d{2}/\d{2})')
    current_year = datetime.now().year
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            match = statement_period_pattern.search(text)
            if match:
                start_date_str, end_date_str = match.groups()
                start_date = datetime.strptime(start_date_str, '%m/%d/%y')
                end_date = datetime.strptime(end_date_str, '%m/%d/%y')

                if end_date.year > current_year:
                    end_date = datetime(end_date.year - 1, end_date.month, end_date.day)
                if start_date.year > current_year:
                    start_date = datetime(start_date.year - 1, start_date.month, start_date.day)
                if end_date.month < start_date.month:
                    start_date = datetime(start_date.year - 1, start_date.month, start_date.day)

                return str(end_date.year)
    return None

def extract_transactions_from_pdf(pdf_path):
    transactions = []
    transaction_pattern = re.compile(r'(\d{2}-\d{2})\s+(.+?)\s+([\d,]+.\d{2}-?)\s+([\d,]+.\d{2})$')
    unwanted_words = ["Transfer", "POS", "Transaction", "-"]
    start_processing = False

    with pdfplumber.open(pdf_path) as pdf:
        year = extract_year_from_statement_period(pdf)
        if not year:
            print(f"Year could not be extracted from {pdf_path}.")
            return transactions

        for page_num, page in enumerate(pdf.pages):
            if page_num == 0:
                continue

            text = page.extract_text()
            if text:
                lines = text.split('\n')
                for line in lines:
                    if "Membership Savings" in line:
                        start_processing = True
                        continue

                    if start_processing:
                        match = transaction_pattern.match(line)
                        if match:
                            date, detail, amount, balance = match.groups()
                            date = f"{date}-{year}"
                            if '-' in amount:
                                amount = -float(amount.replace('-', '').replace(',', ''))
                            else:
                                amount = float(amount.replace(',', ''))
                            detail = re.sub('|'.join(map(re.escape, unwanted_words)), '', detail).strip()
                            category = "Savings"
                            transactions.append({
                                "Date": date,
                                "Transaction Detail": detail,
                                "Category": category,
                                "Inflow": amount if amount > 0 else "",
                                "Outflow": -amount if amount < 0 else ""
                            })
                        else:
                            continue
    return transactions

def save_transactions_to_json(transactions, output_path):
    with open(output_path, 'w') as json_file:
        json.dump(transactions, json_file, indent=4)

def merge_json_files(json_folder, merged_json_path, merged_csv_path):
    all_transactions = []
    for filename in os.listdir(json_folder):
        if filename.endswith('.json'):
            json_path = os.path.join(json_folder, filename)
            with open(json_path, 'r') as json_file:
                transactions = json.load(json_file)
                all_transactions.extend(transactions)

    with open(merged_json_path, 'w') as merged_file:
        json.dump(all_transactions, merged_file, indent=4)
    print(f"All transactions have been merged into {merged_json_path}")
    
    convert_json_to_csv(merged_json_path, merged_csv_path)

def convert_json_to_csv(json_path, csv_path):
    with open(json_path, 'r') as json_file:
        data = json.load(json_file)
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    print(f"CSV file has been created at: {csv_path}")

def process_pdfs(input_folder, json_output_folder, merged_json_path, merged_csv_path):
    os.makedirs(json_output_folder, exist_ok=True)
    for filename in os.listdir(input_folder):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(input_folder, filename)
            json_output_path = os.path.join(json_output_folder, filename.replace('.pdf', '.json'))
            transactions = extract_transactions_from_pdf(pdf_path)
            save_transactions_to_json(transactions, json_output_path)
    merge_json_files(json_output_folder, merged_json_path, merged_csv_path)

# Configuration for input and output paths
input_folder = r'C:\Users\justc\Documents\Gitlab\pdfconvert\pdf'
json_output_folder = r'C:\Users\justc\Documents\Gitlab\pdfconvert\savings\merged_savings_json\savings_json'
merged_json_path = r'C:\Users\justc\Documents\Gitlab\pdfconvert\savings\merged_savings_json\merged_savings.json'
merged_csv_path = r'C:\Users\justc\Documents\Gitlab\pdfconvert\savings\allsavings.csv'

process_pdfs(input_folder, json_output_folder, merged_json_path, merged_csv_path)
def cleanup_folders(*folders):
    for folder in folders:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                # print(f"Deleted {file_path}")
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')
                
cleanup_folders(json_output_folder, os.path.dirname(merged_json_path))
