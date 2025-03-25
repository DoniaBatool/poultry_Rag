import requests
import hashlib
import time
import smtplib
from bs4 import BeautifulSoup
from email.mime.text import MIMEText

URL = "https://eggrates.pk/"
PREVIOUS_HASH_FILE = "previous_hash.txt"

# Email Settings
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = "donia1510aptech@gmail.com"
EMAIL_PASSWORD = "vhsy iyxs wvbt pcpj"
EMAIL_RECEIVER = "ummejawwad313@gmail.com"

def send_email_alert():
    subject = "🚨 EggRates Website Structure Changed!"
    body = "The structure of the website has changed. You need to update your scraper."

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        server.quit()
        print("✅ Email alert sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send email alert: {e}")

def get_relevant_content():
    try:
        response = requests.get(URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # 🎯 Sirf relevant content extract karein
        egg_tables = soup.find_all("table", class_="kb-table")  # Target only egg price tables
        
        if not egg_tables:
            print("❌ No relevant content found.")
            return None

        relevant_html = "".join(str(table) for table in egg_tables)  # Convert tables to string
        return relevant_html.strip()

    except Exception as e:
        print(f"❌ Failed to fetch website: {e}")
        return None

def check_for_updates():
    relevant_html = get_relevant_content()
    if not relevant_html:
        return  # If fetching failed, don't continue

    new_hash = hashlib.md5(relevant_html.encode('utf-8')).hexdigest()

    try:
        with open(PREVIOUS_HASH_FILE, "r") as file:
            previous_hash = file.read().strip()
    except FileNotFoundError:
        previous_hash = ""

    if new_hash != previous_hash:
        print("🚨 Website structure changed! You need to update your scraper.")
        send_email_alert()  # Send email alert
        with open(PREVIOUS_HASH_FILE, "w") as file:
            file.write(new_hash)
    else:
        print("✅ No changes detected.")

# Run the check once every 24 hours
while True:
    check_for_updates()
    time.sleep(86400)  # 86400 seconds = 24 hours
