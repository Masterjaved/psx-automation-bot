import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import schedule
import time
import yfinance as yf

# 1. فائل سے ڈیٹا لوڈ کرنے کا فنکشن
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

# 2. واچ لسٹ میں شیئر شامل کرنے کا فنکشن
def add_stock(symbol):
    symbol = symbol.upper()
    if not symbol.endswith(".KA"):
        symbol += ".KA"
    data = load_data()
    if symbol not in data["watchlist"]:
        data["watchlist"].append(symbol)
        with open("watchlist.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"کامیابی سے شیئر '{symbol}' واچ لسٹ میں شامل کر دیا گیا ہے!")

# 3. لائیو ڈیٹا اور ٹریڈنگ لیولز نکالنے کا فنکشن
def generate_psx_report():
    data = load_data()
    stocks = data["watchlist"]
    to_email = data["email_recipient"]
    
    report_text = "السلام علیکم!\nیہ رہی آپ کی پاکستان اسٹاک ایکسچینج (PSX) کی خودکار مارکیٹ اور ٹریڈنگ رپورٹ:\n\n"
    report_text += "📈 **واچ لسٹ کے شیئرز کی لائیو صورتحال اور ٹریڈنگ سیٹ اپ:**\n\n"
    
    for stock in stocks:
        try:
            ticker_symbol = stock if "." in stock else stock + ".KA"
            ticker = yf.Ticker(ticker_symbol)
            todays_data = ticker.history(period="10d")
            
            if not todays_data.empty:
                current_price = todays_data['Close'].iloc[-1]
                open_price = todays_data['Open'].iloc[-1]
                price_change = current_price - open_price
                percent_change = (price_change / open_price) * 100 if open_price != 0 else 0
                
                # خودکار ٹریڈنگ لیولز کا حساب لگانا
                low_5days = todays_data['Low'].tail(5).min()
                stop_loss = round(low_5days * 0.98, 2)  
                target_1 = round(current_price * 1.025, 2) 
                target_2 = round(current_price * 1.05, 2)  
                
                sign = "+" if price_change >= 0 else ""
                
                report_text += f"🔹 **{stock.replace('.KA', '')}**\n"
                report_text += f"   • موجودہ قیمت: Rs. {current_price:.2f} ({sign}{percent_change:.2f}%)\n"
                report_text += f"   • پرچیزنگ / بائینگ زون: Rs. {current_price:.2f} کے آس پاس\n"
                report_text += f"   • اسٹاپ لاس (Stop Loss): Rs. {stop_loss}\n"
                report_text += f"   • پہلا ہدف (Target 1): Rs. {target_1}\n"
                report_text += f"   • دوسرا ہدف (Target 2): Rs. {target_2}\n\n"
            else:
                report_text += f"🔹 **{stock.replace('.KA', '')}**: ڈیٹا دستیاب نہیں۔\n\n"
        except Exception as e:
            report_text += f"🔹 **{stock.replace('.KA', '')}**: ڈیٹا فیچ کرنے میں عارضی مسئلہ۔\n\n"
            
    report_text += "⚠️ نوٹ: یہ تکنیکی اشارے تاریخی ڈیٹا کی بنیاد پر خودکار تیار کیے گئے ہیں، ٹریڈ کرنے سے پہلے مارکیٹ کا خود تجزیہ ضرور کریں۔"
    
    send_urdu_email("📊 PSX لائیو رپورٹ اور ٹریڈنگ سیٹ اپ", report_text, to_email)

# 4. اردو ای میل بھیجنے کا فنکشن (GitHub Secrets کے ذریعے)
def send_urdu_email(subject, body, to_email):
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")

    if not sender_email or not sender_password:
        print("ای میل یا پاس ورڈ کی سیٹنگ غائب ہے!")
        return

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject

    html_content = f"""
    <div dir="rtl" style="font-family: 'Jameel Noori Nastaleeq', Arial, sans-serif; font-size: 16px; line-height: 1.8;">
        <h2>📊 پاکستان اسٹاک ایکسچینج - ٹریڈنگ رپورٹ</h2>
        <pre style="font-family: inherit; white-space: pre-wrap;">{body}</pre>
    </div>
    """
    
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print("ای میل کامیابی سے بھیج دی گئی ہے!")
    except Exception as e:
        print(f"ای میل بھیجنے میں خرابی: {e}")

# 5. شیڈولنگ (صبح 7 اور شام 7 بجے)
schedule.every().day.at("07:00").do(generate_psx_report)
schedule.every().day.at("19:00").do(generate_psx_report)

print("PSX لائیو آٹومیشن بوٹ شروع ہو چکا ہے...")

while True:
    schedule.run_pending()
    time.sleep(1)
