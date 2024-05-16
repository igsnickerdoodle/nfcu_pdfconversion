import pdfplumber
import re
import json
import pandas as pd
import os
from datetime import datetime
import shutil
from app import categories

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

def categorize_transaction(detail, categories):
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword.lower() in detail.lower():
                return category
    return "General"

def strip_unwanted_words(detail, unwanted_words):
    for word in unwanted_words:
        detail = detail.replace(word, "")
    detail = re.sub(r'\b\d{2}-\d{2}-\d{2}\b', '', detail)  
    detail = re.sub(r'\b\d{2}/\d{2}/\d{2}\b', '', detail) 
    detail = re.sub(r'\b\d{6}\b', '', detail)  
    detail = re.sub(r'\b\d{2}\.\d{2}\.\d{2}\b', '', detail) 
    return detail.strip()

def extract_transactions_from_pdf(pdf_path, categories):
    transactions = []
    transaction_pattern = re.compile(r'(\d{2}-\d{2})\s+(.+?)\s+([\d,]+\.\d{2}-?)\s+([\d,]+\.\d{2})$')

    # List of words/phrases to strip from the transaction detail
    unwanted_words = [
        "POS Debit - Debit Card 9825",
        "POS Debit - Debit Card 3834",
        "POS Debit-",
        "3834",
        "Paid To",
        "Debit Card",
        "POS Credit Adjustment 9825 Transaction",
        "Transaction",
        "-"
    ]

    with pdfplumber.open(pdf_path) as pdf:
        year = extract_year_from_statement_period(pdf)
        if not year:
            print(f"Year could not be extracted from the statement period in {pdf_path}.")
            return transactions

        for page_num, page in enumerate(pdf.pages):
            if page_num == 0:  # Skip the first page
                continue

            text = page.extract_text()
            if text:
                lines = text.split('\n')
                for line in lines:
                    if "Membership Savings" in line:
                        break  # Stop processing lines if "Membership Savings" is encountered
                    if "dividend" in line.lower():
                        continue  # Ignore lines that contain "dividend"

                    match = transaction_pattern.match(line)
                    if match:
                        date, detail, amount, balance = match.groups()
                        date = f"{date}-{year}"
                        amount = float(amount.replace(',', '').replace('-', ''))

                        detail = strip_unwanted_words(detail, unwanted_words)
                        category = categorize_transaction(detail.strip(), categories)

                        # Exclude "Transfer From Shares" and "Transfer To Shares"
                        if "Transfer From Shares" in detail:
                            continue

                        if detail.startswith(("Deposit", "Credit", "eDeposit", "Dividend")):
                            transactions.append({
                                "Date": date,
                                "Transaction Detail": detail.strip(),
                                "Catagory": category,
                                "Inflow": amount,
                                "Outflow": ""
                            })
                        else:
                            transactions.append({
                                "Date": date,
                                "Transaction Detail": detail.strip(),
                                "Catagory": category,
                                "Inflow": "",
                                "Outflow": -amount
                            })

    return transactions

def save_transactions_to_json(transactions, output_path):
    with open(output_path, 'w') as json_file:
        json.dump(transactions, json_file, indent=4)

def create_csv_from_json(json_path, csv_path):
    with open(json_path, 'r') as json_file:
        transactions = json.load(json_file)
    
    df = pd.DataFrame(transactions)
    
    df.to_csv(csv_path, index=False)

def merge_csv_files(csv_folder, merged_csv_path):
    all_dataframes = []
    for filename in os.listdir(csv_folder):
        if filename.endswith('.csv'):
            csv_path = os.path.join(csv_folder, filename)
            df = pd.read_csv(csv_path)
            all_dataframes.append(df)
    
    merged_df = pd.concat(all_dataframes, ignore_index=True)
    merged_df.to_csv(merged_csv_path, index=False)
def merge_json_files(json_folder, merged_json_path):
    all_transactions = []
    
    for filename in os.listdir(json_folder):
        if filename.endswith('.json'):
            json_path = os.path.join(json_folder, filename)
            with open(json_path, 'r') as json_file:
                transactions = json.load(json_file)
                all_transactions.extend(transactions)
    
    with open(merged_json_path, 'w') as merged_file:
        json.dump(all_transactions, merged_file, indent=4)
def process_pdfs(input_folder, json_output_folder, csv_output_folder, merged_json_path, merged_csv_path, categories):
    os.makedirs(json_output_folder, exist_ok=True)
    os.makedirs(csv_output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(input_folder, filename)
            json_output_path = os.path.join(json_output_folder, filename.replace('.pdf', '.json'))
            csv_output_path = os.path.join(csv_output_folder, filename.replace('.pdf', '.csv'))

            # print(f"Processing {pdf_path}...")

            transactions = extract_transactions_from_pdf(pdf_path, categories)

            save_transactions_to_json(transactions, json_output_path)

            create_csv_from_json(json_output_path, csv_output_path)

            # print(f"Transactions have been saved to {csv_output_path} and {json_output_path}")

    merge_json_files(json_output_folder, merged_json_path)
    print(f"All transactions have been merged into {merged_json_path}")

    merge_csv_files(csv_output_folder, merged_csv_path)
    print(f"All transactions have been merged into {merged_csv_path}")

categories = categories


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

# Configuration for input and output paths
input_folder = r'C:\Users\justc\Documents\Gitlab\pdfconvert\pdf'
json_output_folder = r'C:\Users\justc\Documents\Gitlab\pdfconvert\checking\merged_checking_json\checking_json'
csv_output_folder = r'C:\Users\justc\Documents\Gitlab\pdfconvert\checking\csv'
merged_json_path = r'C:\Users\justc\Documents\Gitlab\pdfconvert\checking\merged_checking_json\merged_checking.json'  # Ensure this is a valid file path ending in .json
merged_csv_path = r'C:\Users\justc\Documents\Gitlab\pdfconvert\checking\allchecking.csv'  # Ensure this is a valid file path ending in .csv

process_pdfs(input_folder, json_output_folder, csv_output_folder, merged_json_path, merged_csv_path, categories)

cleanup_folders(json_output_folder, os.path.dirname(merged_json_path), csv_output_folder)

