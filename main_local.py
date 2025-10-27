from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import re

# ============== CONFIGURATION ==============
TICKET_URL = "https://www.viagogo.com/Concert-Tickets/Pop-Rock/Contemporary-Pop-Rock/Katy-Perry-Tickets/E-156452615?backUrl=%2FConcert-Tickets%2FPop-Rock%2FContemporary-Pop-Rock%2FKaty-Perry-Tickets&quantity=1&sections=&ticketClasses=&rows=&seats=&seatTypes=&listingQty="
PRICE_THRESHOLD = 24000  # HUF
CHECK_INTERVAL = 600 # 10 minutes in seconds

# Email configuration
SENDER_EMAIL = "pkans007x@gmail.com"
SENDER_PASSWORD = "oasf jovv owwe hxtl"
RECEIVER_EMAIL = "pkans007x@gmail.com"

# ============================================

def send_email_alert(tickets):
    """Send email alert when price condition is met"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = f"🎫 Katy Perry Ticket Alert - {len(tickets)} ticket(s) found!"
        
        ticket_list = "\n".join([
            f"• Section: {t['section']}, Price: {t['price']} HUF"
            for t in tickets
        ])
        
        body = f"""
        Good news! {len(tickets)} ticket(s) matching your criteria were found:
        
        {ticket_list}
        
        Price Threshold: Below {PRICE_THRESHOLD} HUF
        Time found: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Link: {TICKET_URL}
        
        Hurry! Tickets may sell out quickly.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to Gmail SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Alert email sent successfully at {datetime.now()}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

def extract_price(price_text):
    """Extract numeric price from text (handles various formats)"""
    # Remove everything except digits
    cleaned = re.sub(r'[^\d]', '', price_text)
    if cleaned:
        return int(cleaned)
    return None

def setup_driver():
    """Setup Chrome driver with options"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in background
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def check_tickets():
    """Check Viagogo for tickets matching criteria"""
    driver = None
    try:
        print(f"\n🔍 Checking tickets at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...")
        
        driver = setup_driver()
        driver.get(TICKET_URL)
        
        # Wait for listings to load (adjust timeout as needed)
        print("⏳ Waiting for page to load...")
        time.sleep(5)  # Give it time to load JavaScript
        
        # Try multiple possible selectors for ticket listings
        ticket_elements = []
        
        # Common selectors for Viagogo
        selectors = [
            "div[data-testid*='listing']",
            "div[class*='listing']",
            "div[class*='ticket']",
            "[class*='TicketCard']",
            "article",
            "li[class*='item']"
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    ticket_elements = elements
                    print(f"✅ Found {len(ticket_elements)} elements using selector: {selector}")
                    break
            except:
                continue
        
        if not ticket_elements:
            print("⚠️ Could not find ticket elements with known selectors")
            # Print page source for debugging (first 1000 chars)
            print("\n--- Page content sample ---")
            print(driver.page_source[:1000])
            print("--- End sample ---\n")
            return False
        
        matching_tickets = []
        
        for element in ticket_elements:
            try:
                text = element.text
                
                # Look for prices in the text
                # Viagogo typically shows prices like "Ft22,964" or "HUF 22,964"
                price_matches = re.findall(r'Ft\s*[\d,]+|HUF\s*[\d,]+|\d{2,3},\d{3}', text)
                
                for price_match in price_matches:
                    price = extract_price(price_match)
                    
                    if price and price < PRICE_THRESHOLD:
                        # Try to extract section info
                        section = "Unknown"
                        section_match = re.search(r'Section\s+([^\n]+)|Sektor\s+(\d+)', text)
                        if section_match:
                            section = section_match.group(0)
                        
                        ticket_info = {
                            'price': price,
                            'section': section
                        }
                        matching_tickets.append(ticket_info)
                        print(f"🎉 MATCH FOUND! Section: {section}, Price: {price} HUF")
            
            except Exception as e:
                continue
        
        if matching_tickets:
            send_email_alert(matching_tickets)
            return True
        else:
            print(f"No tickets found below {PRICE_THRESHOLD} HUF")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if driver:
            driver.quit()

def main():
    """Main monitoring loop"""
    print("=" * 50)
    print("🎫 Katy Perry Ticket Price Monitor Started")
    print("=" * 50)
    print(f"Monitoring URL: {TICKET_URL[:80]}...")
    print(f"Price threshold: {PRICE_THRESHOLD} HUF")
    print(f"Check interval: {CHECK_INTERVAL // 60} minutes")
    print(f"Email alerts to: {RECEIVER_EMAIL}")
    print("=" * 50)
    print("\nPress Ctrl+C to stop monitoring")
    print("First run may take longer while downloading ChromeDriver...\n")
    
    try:
        while True:
            check_tickets()
            
            print(f"⏰ Next check in {CHECK_INTERVAL // 60} minutes...")
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")

if __name__ == "__main__":
    main()