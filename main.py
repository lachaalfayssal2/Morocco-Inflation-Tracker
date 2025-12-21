import time
import random
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. PRODUCT LIST ---
products_urls = [
    "https://www.marjane.ma/courses-en-ligne/8-epicerie/35-huiles-et-vinaigres/142-huiles-de-cuisson/1424-huile-de-friture-5l-lesieur",
    "https://www.marjane.ma/courses-en-ligne/8-epicerie/59-sucre-sucrettes/227-sucre-granule/2151-sucre-granule-2kg-enmer",
    "https://www.marjane.ma/courses-en-ligne/8-epicerie/34-farines-aide-a-la-patisserie/136-farine-fleur-patissiere-luxe/31760-farine-de-luxe-de-ble-tendre-10kg-al-itkane",
    "https://www.marjane.ma/courses-en-ligne/13-produits-laitiers-%C5%93ufs/64-laits-et-%C5%93ufs/248-lait-lben/25563-pack-lait-sterilise-uht-entier-6-x-1lsalim",
    "https://www.marjane.ma/courses-en-ligne/12-petit-dejeuner/60-thes-infusions-tisanes/231-the-vert-filaments/5352-the-vert-en-filaments-chaara-4011-200g-sultan",
    "https://www.marjane.ma/courses-en-ligne/8-epicerie/36-pates-riz-feculents/146-couscous/1581-couscous-al-belboula-1kg-dari",
    "https://www.marjane.ma/courses-en-ligne/8-epicerie/37-sauces-chaudes-concentres-tomates/151-concentre-coulis-de-tomate/2176-concentre-de-tomates-210g-aicha",
    "https://www.marjane.ma/courses-en-ligne/12-petit-dejeuner/53-cafe/213-soluble/495-cafe-soluble-classic-190g-nescafe",
    "https://www.marjane.ma/courses-en-ligne/7-entretien-nettoyage/29-lessive-soin-du-linge/115-lessive-liquide-dosettes-anticalcaire/660-lessive-liquide-matic-downy-3lariel",
    "https://www.marjane.ma/courses-en-ligne/13-produits-laitiers-%C5%93ufs/64-laits-et-%C5%93ufs/251-%C5%93ufs/27503-plateau-%C5%93ufs-frais-x30-unites-natur-%C5%93uf"
]

# --- 2. GOOGLE SHEETS CONNECTION ---
def upload_to_sheet(product_name, price, url):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # Check if credentials exist
        if not os.path.exists("credentials.json"):
            print("   ❌ Credentials File Missing! (Check GitHub Secrets)")
            return

        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open("Morocco_Inflation_DB").sheet1
        
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [current_date, product_name, price, url]
        sheet.append_row(row)
        print(f"   ✅ Saved: {product_name} -> {price} MAD")
        
    except Exception as e:
        print(f"   ❌ Sheets Error: {e}")

# --- 3. MAIN SCRAPER (STEALTH MODE) ---
def get_marjane_prices():
    print("🚀 Starting Stealth Scraper...")
    
    options = webdriver.ChromeOptions()
    
    # A. Use a real User-Agent (looks like a normal Windows PC)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # B. Disable Automation Flags (The "Anti-Detect" Magic)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # C. Standard Headless Options
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # D. JavaScript Injection to hide 'navigator.webdriver'
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    print(f"📦 Processing {len(products_urls)} products...")

    for i, url in enumerate(products_urls, 1):
        print(f"\n[{i}/{len(products_urls)}] Accessing URL...")
        try:
            driver.get(url)
            
            # E. Scroll down to trigger any lazy-loaded elements
            driver.execute_script("window.scrollTo(0, 500);")
            time.sleep(2) # Short pause after load
            
            # F. Wait up to 60 seconds (Robustness)
            wait = WebDriverWait(driver, 60)
            
            # 1. Get Price
            price_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.price")))
            raw_price = price_element.text 
            
            # Clean Price logic
            clean_price = raw_price.replace("DH", "").replace("dh", "").replace(" ", "").replace(",", ".").strip()
            if not clean_price:
                raise ValueError("Price text is empty")
                
            final_price = float(clean_price)

            # 2. Get Name
            try:
                name_element = driver.find_element(By.CSS_SELECTOR, "h1, h2.product-title")
                product_name = name_element.text
            except:
                product_name = "Unknown Product"

            # 3. Save
            upload_to_sheet(product_name, final_price, url)

        except Exception as e:
            # Skip error and continue to next product
            print(f"   ⚠️ SKIPPING Product (Error): {str(e)[:100]}...") 
            continue 
        
        # G. Random Sleep to mimic human behavior
        time.sleep(random.uniform(4, 8))

    driver.quit()
    print("\n🏁 Done.")

if __name__ == "__main__":
    get_marjane_prices()