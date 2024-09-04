import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import sqlite3

# List of words that indicate a domain might be premium
premium_words = ['business', 'finance', 'tech', 'health', 'travel', 'money', 'wealth']

# List of common first names (used to identify potentially valuable personal domains)
first_names = ['john', 'mary', 'patrick', 'siobhan']

def is_premium_domain(domain):
    """
    Determine if a domain is considered premium based on certain criteria.
    
    A domain is considered premium if it:
    1. Contains any word from the premium_words list
    2. Is 4 characters or less and all alphabetic
    3. Matches a first name longer than 3 characters
    4. Is 4 characters or less, all alphabetic, and doesn't contain triple letters
    """
    name = domain.split('.')[0].lower()
    return (
        any(word in name for word in premium_words) or
        (len(name) <= 4 and name.isalpha()) or
        (name in first_names and len(name) > 3) or
        (len(name) <= 4 and name.isalpha() and not any(char*3 in name for char in name))
    )

def scrape_domains():
    """
    Scrape domains from a specific website and filter for premium domains.
    
    Returns a list of premium domains found on the website.
    """
    url = 'https://www.weare.ie/deleted-domain-list/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    domains = []
    # Extract all text that ends with .ie, excluding email addresses
    for text in soup.stripped_strings:
        if text.lower().endswith('.ie') and not '@' in text:
            domain = text.strip()
            if is_premium_domain(domain):
                domains.append(domain)
    
    # Debug print statements
    print(f"Total potential domains found: {len([text for text in soup.stripped_strings if text.lower().endswith('.ie') and not '@' in text])}")
    print(f"Domains considered premium: {domains}")
    
    return domains

def init_db():
    """
    Initialize the SQLite database and create the sent_domains table if it doesn't exist.
    """
    conn = sqlite3.connect('domains.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sent_domains
                 (domain TEXT PRIMARY KEY, date_sent TEXT)''')
    conn.commit()
    conn.close()

def get_new_domains(domains):
    """
    Filter the list of domains to only include those not previously sent.
    
    Also adds newly found domains to the database.
    """
    conn = sqlite3.connect('domains.db')
    c = conn.cursor()
    new_domains = []
    for domain in domains:
        c.execute("SELECT * FROM sent_domains WHERE domain = ?", (domain,))
        if c.fetchone() is None:
            new_domains.append(domain)
            c.execute("INSERT INTO sent_domains VALUES (?, ?)", (domain, datetime.now().strftime('%Y-%m-%d')))
    conn.commit()
    conn.close()
    return new_domains

def send_email(domains):
    """
    Send an email with the list of new premium domains found.
    """
    sender_email = "scraperdomain@gmail.com"
    sender_password = "ffts mbrg aaog ecro"
    receiver_emails = ["jamiebehan@gmail.com"]

    subject = f"New Premium Irish Domains - {datetime.now().strftime('%Y-%m-%d')}"
    body = "Here are today's new premium Irish domains:\n\n" + "\n".join(domains)

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = ", ".join(receiver_emails)
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_emails, message.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email. Error: {str(e)}")

if __name__ == "__main__":
    # Main execution flow
    init_db()  # Initialize the database
    premium_domains = scrape_domains()  # Scrape and filter premium domains
    new_premium_domains = get_new_domains(premium_domains)  # Get only new premium domains
    
    if new_premium_domains:
        print(f"Found {len(new_premium_domains)} new premium domains.")
        send_email(new_premium_domains)  # Send email with new premium domains
    else:
        print("No new premium domains found today.")
        # Optionally, you can still send an email if no new domains are found
        # send_email(["No new premium domains found today."])
