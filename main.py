import time
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. PRODUCT LIST (Moroccan Basket) ---
products_urls = [
    # Oil (Lesieur 5L)
    "https://www.marjane.ma/courses-en-ligne/8-epicerie/35-huiles-et-vinaigres/142-huiles-de-cuisson/1424-huile-de-friture-5l-lesieur",
    
    # Sugar (Enmer 2kg)
    "https://www.marjane.ma/courses-en-ligne/8-epicerie/59-sucre-sucrettes/227-sucre-granule/2151-sucre-granule-2kg-enmer",
    
    # Flour (Al Itkane 10kg)
    "https://www.marjane.ma/courses-en-ligne/8-epicerie/34-farines-aide-a-la-patisserie/136-farine-fleur-patissiere-luxe/31760-farine-de-luxe-de-ble-tendre-10kg-al-itkane",
    
    # Milk (Salim Pack 6x1L)
    "https://www.marjane.ma/courses-en-ligne/13-produits-laitiers-%C5%93ufs/64-laits-et-%C5%93ufs/248-lait-lben/25563-pack-lait-sterilise-uht-entier-6-x-1lsalim",
    
    # Tea (Sultan Chaara 200g)
    "https://www.marjane.ma/courses-en-ligne/12-petit-dejeuner/60-thes-infusions-tisanes/231-the-vert-filaments/5352-the-vert-en-filaments-chaara-4011-200g-sultan",
    
    # Couscous (Dari 1kg)
    "https://www.marjane.ma/courses-en-ligne/8-epicerie/36-pates-riz-feculents/146-couscous/1581-couscous-al-belboula-1kg-dari",
    
    # Tomato Paste (Aicha 210g)
    "https://www.marjane.ma/courses-en-ligne/8-epicerie/37-sauces-chaudes-concentres-tomates/151-concentre-coulis-de-tomate/2176-concentre-de-tomates-210g-aicha",
    
    # Coffee (Nescafe Classic 190g)
    "https://www.marjane.ma/courses-en-ligne/12-petit-dejeuner/53-cafe/213-soluble/495-cafe-soluble-classic-190g-nescafe",
    
    # Laundry Detergent (Ariel Liquid 3L)
    "https://www.marjane.ma/courses-en-ligne/7-entretien-nettoyage/29-lessive-soin-du-linge/115-lessive-liquide-dosettes-anticalcaire/660-lessive-liquide-matic-downy-3lariel",
    
    # Eggs (Plate of 30)
    "https://www.marjane.ma/courses-en-ligne/13-produits-laitiers-%C5%93ufs/64-laits-et-%C5%93ufs/251-%C5%93ufs/27503-plateau-%C5%93ufs-frais-x30-unites-natur-%C5%93uf"
]

# --- 2. GOOGLE SHEETS CONNECTION ---
def upload_to_sheet(product_name, price, url):
    try:
        print("   > Connecting to Google Sheets...")
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        
        sheet = client.open("Morocco_Inflation_DB").sheet1
        
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [current_date, product_name, price, url]
        
        sheet.append_row(row)
        print(f"   ✅ Data Saved Successfully: {row}")
        
    except Exception as e:
        print(f"   ❌ Google Sheets Error: {e}")

# --- 3. MAIN SCRAPER ENGINE ---
def get_marjane_prices():
    options = webdriver.ChromeOptions()
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    options.add_argument("--start-maximized")
    options.add_argument("--headless") 

    print("🚀 Starting Marjane Scraper...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    count = 1
    total = len(products_urls)

    for url in products_urls:
        print(f"\n------------------------------------------------")
        print(f"[{count}/{total}] Processing URL...")
        
        try:
            driver.get(url)
            
            # Smart Wait (up to 20s) for price to appear
            wait = WebDriverWait(driver, 20)
            
            # 1. Get Price (Find span with class 'price')
            price_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.price")))
            raw_price = price_element.text  
            
            # Clean Price Data
            clean_price = raw_price.replace("DH", "").replace("dh", "").replace(" ", "").replace(",", ".").strip()
            final_price = float(clean_price)

            # 2. Get Product Name
            try:
                name_element = driver.find_element(By.CSS_SELECTOR, "h1, h2.product-title")
                product_name = name_element.text
            except:
                product_name = "Unknown Product"

            print(f"   📦 Product: {product_name}")
            print(f"   💰 Price: {final_price} MAD")
            
            # 3. Upload to Cloud
            upload_to_sheet(product_name, final_price, url)

            # Random sleep to mimic human behavior
            time.sleep(random.uniform(4, 8))

        except Exception as e:
            print(f"   ⚠️ Error processing link: {e}")
        
        finally:
            count += 1

    print("\n🏁 Scraping Finished. All data sent to Cloud.")
    driver.quit()

if __name__ == "__main__":
    get_marjane_prices()