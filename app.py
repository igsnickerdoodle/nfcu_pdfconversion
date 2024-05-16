import subprocess

categories = {
    "Credit Cards": ["Visa", "MasterCard", "AMEX", "Zelle", "Mercury Card", "Credit One", "Capital One"],
    "Bills": ["Audi Fincl", "Dept Education", "King George County", "Zip.Co", "Verizon", "TMobile", "T-Mobile",
              "T Mobile", "Tmobile"],
    "Food": ["Restaurant", "Grocery", "Cafe", "Sonic Drive", "Market River Falls", "Marine Mart", 
             "Mission Bbq", "Chick-Fil-A", "McDonald's", "Roma Pizza", "Starbucks", "DD/Br", "Pizza Bono", 
             "Benny Vitalis", "Jeresy Mikes", "Firehouse", "Wendys", "Wendy's", "Sonic"],
    "Fuel": ["Murphy Express", "Sheetz", "Wawa", "Shell"],
    "Utilities": ["Electric", "Water", "Internet", "Starlink", "All Point Broadband"],
    "General": ["Majest Martial Art", "Best Buy", "7-Eleven", "Tobaccohut", "Microsoft", "Wal-Mart", 
                "Ace Hardware", "Walmart", "Fas Mart", "Tobacco Hut", "Amzn Mktp Us", "Steam", "Tobacco", 
                "Gateway Tobacco", "Tobacco Land", "The Ups Store", "Ace Hardware"],
    "Maintenance/Parts": ["Fcp Euro", "Rock Auto", "Advance Auto Parts", "bimmergeek", "Kohl's",
                          "Lowe's", "Car Wash", "Rnr Tire Express", "Tire Rack"],
    "Medical": ["Roberta Price Support"],
    "Subscriptions": ["Plexincpass", "Prime Video", "Hidive", "Crunchyroll", "Netflix.Com"],
    "Income": ["Deposit", "Zachary Piper", "Cash App"],
    "Savings":["Transfered To Shares"]
}

def run_script(script_path):
    try:
        result = subprocess.run(['python', script_path], check=True, text=True, capture_output=True)
        print(f"Output from {script_path}:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_path}:\n{e.stderr}")

if __name__ == "__main__":
    # Run checking account processing
    run_script('checkingaccount.py')
    
    # Run savings account processing
    run_script('savingsaccount.py')
