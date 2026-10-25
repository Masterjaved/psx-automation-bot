import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import schedule
import time
import yfinance as yf

# 1. File se data load karne ka function
def load_data():
    try:
        with open("watchlist.json", "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                raise ValueError("File is empty")
            return json.loads(content)
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        default_data = {
            "email_recipient": "apni_email_yahan_likhein@gmail.com",
            "watchlist": ["SYS.KA", "OGDC.KA", "FFC.KA"]
        }
        with open("watchlist.json", "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=4, ensure_ascii=False)
        return default_data

# 2. Live data aur trading levels nikalne ka function (Timeout aur Error Handling ke sath)
def generate_psx_report():
    data = load_data()
    stocks = data["watchlist"]
    to_email = data["email_recipient"]
    
    report_text = "Salam! Yeh rahi aapki Pakistan Stock Exchange (PSX) ki khudkar market aur trading report:\n\n"
    report_text += "📈 **Watchlist ke shares ki live surat-e-hal aur trading setup:**\n\n"
    
    for stock in stocks:
        try:
            ticker_symbol = stock if "." in stock else stock + ".KA"
            print(f"Fetching data for {ticker_symbol}...")
            
            # yfinance ko secure banane ke liye request
            ticker = yf.Ticker(ticker_symbol)
            todays_data = ticker.history(period="10d", timeout=10)
            
            if not todays_data.empty:
                current_price = todays_data['Close'].iloc[-1]
                open_price = todays_data['Open'].iloc[-1]
                price_change = current_price - open_price
                percent_change = (price_change / open_price) * 100 if open_price != 0 else 0
                
                # Khudkar trading levels ka hisaab lagana
                low_5days = todays_data['Low'].tail(5).min()
                stop_loss = round(low_5days * 0.98, 2)  
                target_1 = round(current_price * 1.025, 2) 
                target_2 = round(current_price * 1.05, 2)  
                
                sign = "+" if price_change >= 0 else ""
                
                report_text += f"🔹 **{stock.replace('.KA', '')}**\n"
                report_text += f"   • Mojooda qeemat: Rs. {current_price:.2f} ({sign}{percent_change:.2f}%)\n"
                report_text += f"   • Purchasing / Buying zone: Rs. {current_price:.2f} ke aas paas\n"
                report_text += f"   • Stop Loss: Rs. {stop_loss}\n"
                report_text += f"   • Pehla hadaf (Target 1): Rs. {target_1}\n"
                report_text += f"   • Dusra hadaf (Target 2): Rs. {target_2}\n\n"
            else:
                report_text += f"🔹 **{stock.replace('.KA', '')}**: Data dastiyab nahi.\n\n"
        except Exception as e:
            print(f"Error fetching {stock}: {e}")
            report_text += f"🔹 **{stock.replace('.KA', '')}**: Data fetch karne mein arzi masla.\n\n"
            
    report_text += "⚠️ Note: Yeh technical isharay tareekhi data ki buniyad par taiyar kiye gaye hain, trade karne se pehle market ka khud tajzia zaroor karein."
    
    send_urdu_email("📊 PSX Live Report aur Trading Setup", report_text, to_email)

# 3. Urdu email bhejne ka function (GitHub Secrets ke zariye)
def send_urdu_email(subject, body, to_email):
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")

    if not sender_email or not sender_password:
        print("Email ya password ki setting gayab hai!")
        return

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject

    html_content = f"""
    <div dir="ltr" style="font-family: Arial, sans-serif; font-size: 16px; line-height: 1.8;">
        <h2>📊 Pakistan Stock Exchange - Trading Report</h2>
        <pre style="font-family: inherit; white-space: pre-wrap;">{body}</pre>
    </div>
    """
    
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print("Email kamyabi se bhej di gayi hai!")
    except Exception as e:
        print(f"Email bhejne mein kharabi: {e}")

# Script run karne ke liye direct function call (Cloud / GitHub Actions ke liye best)
if __name__ == "__main__":
    generate_psx_report()
