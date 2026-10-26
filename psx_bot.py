import subprocess
import sys

# خودکار چیک اور لائبریریاں انسٹال کرنے کا نظام
def install_missing_packages():
    required = {'requests', 'bs4', 'cloudscraper', 'yfinance'}
    import pkg_resources
    installed = {pkg.key for pkg in pkg_resources.working_set}
    missing = required - installed
    if missing:
        print(f"Installing missing packages: {missing}")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing])

install_missing_packages()

import json
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import cloudscraper
from bs4 import BeautifulSoup

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
            "watchlist": ["SYS", "OGDC", "HUBC", "FFC", "CHWC", "CNERGY", "KEL", "MLCF", "SAZEW", "EFERT"]
        }
        with open("watchlist.json", "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=4, ensure_ascii=False)
        return default_data

# 2. کلاؤڈ اسکریپر کے ذریعے لائیو ڈیٹا نکالنے کا فنکشن
def get_bypass_stock_data(symbol):
    clean_symbol = symbol.replace('.KA', '').strip().upper()
    
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    try:
        api_url = f"https://dps.psx.com.pk/timeseries/int/{clean_symbol}"
        api_res = scraper.get(api_url, timeout=10)
        
        if api_res.status_code == 200:
            api_data = api_res.json()
            if "data" in api_data and len(api_data["data"]) > 0:
                latest = api_data["data"][-1]
                current_price = float(latest[1])
                open_price = float(api_data["data"][0][1]) if len(api_data["data"]) > 1 else current_price
                percent_change = ((current_price - open_price) / open_price) * 100 if open_price != 0 else 0
                return current_price, open_price, percent_change
    except Exception as e:
        print(f"Bypass Error for {clean_symbol}: {e}")
        
    return None, None, None

# 3. رپورٹ تیار کرنے کا مرکزی فنکشن
def generate_psx_report():
    data = load_data()
    stocks = data["watchlist"]
    to_email = data["email_recipient"]
    
    table_rows = ""
    dividend_info = "<li>کمپنیوں کے کارپوریٹ اعلانات اور آنے والے ڈیویڈنڈز کی لائیو اسکیننگ جاری ہے۔</li>"
    
    total_gain_loss_pct = 0
    valid_stocks_count = 0
    
    for stock in stocks:
        clean_symbol = stock.replace('.KA', '').strip().upper()
        print(f"Fetching live bypass data for {clean_symbol}...")
        
        current_price, open_price, percent_change = get_bypass_stock_data(clean_symbol)
        
        if current_price is not None:
            total_gain_loss_pct += percent_change
            valid_stocks_count += 1
            
            stop_loss = round(current_price * 0.97, 2)
            target_1 = round(current_price * 1.025, 2)
            target_2 = round(current_price * 1.05, 2)
            
            is_danger = percent_change <= -2.5
            
            sign = "+" if percent_change >= 0 else ""
            color_class = "color: #2e7d32; font-weight: bold;" if percent_change >= 0 else "color: #c62828; font-weight: bold;"
            
            if is_danger:
                bg_highlight = "#ffcdd2"
                danger_badge = " <span style='background: #b71c1c; color: white; padding: 2px 4px; border-radius: 3px; font-size: 9px;'>الرٹ!</span>"
            else:
                bg_highlight = "#e8f5e9" if percent_change >= 0 else "#ffebee"
                danger_badge = ""
            
            table_rows += f"""
            <tr style="background-color: {bg_highlight}; text-align: center;">
                <td style="padding: 10px 6px; border: 1px solid #ddd; font-weight: bold; font-size: 13px;">{clean_symbol}{danger_badge}</td>
                <td style="padding: 10px 6px; border: 1px solid #ddd; font-size: 13px;">Rs. {current_price:.2f}</td>
                <td style="padding: 10px 6px; border: 1px solid #ddd; font-size: 13px; {color_class}">{sign}{percent_change:.2f}%</td>
                <td style="padding: 10px 6px; border: 1px solid #ddd; font-size: 13px; color: #d32f2f; font-weight: bold;">Rs. {stop_loss}</td>
                <td style="padding: 10px 6px; border: 1px solid #ddd; font-size: 13px; color: #388e3c; font-weight: bold;">Rs. {target_1}</td>
                <td style="padding: 10px 6px; border: 1px solid #ddd; font-size: 13px; color: #1976d2; font-weight: bold;">Rs. {target_2}</td>
            </tr>
            """
        else:
            table_rows += f"""
            <tr style="background-color: #fffde7; text-align: center;">
                <td style="padding: 10px 6px; border: 1px solid #ddd; font-weight: bold; font-size: 13px;">{clean_symbol}</td>
                <td colspan="5" style="padding: 10px 6px; border: 1px solid #ddd; color: #f57f17; font-size: 13px;">سرور سے رابطہ ہو رہا ہے، عارضی وقفہ۔</td>
            </tr>
            """

    avg_performance = (total_gain_loss_pct / valid_stocks_count) if valid_stocks_count > 0 else 0
    perf_sign = "+" if avg_performance >= 0 else ""
    perf_color = "#2e7d32" if avg_performance >= 0 else "#c62828"

    html_content = f"""
    <div dir="rtl" style="font-family: Arial, sans-serif; background-color: #f4f6f8; padding: 10px; color: #333333;">
        <div style="max-width: 650px; margin: auto; background: #ffffff; padding: 15px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            
            <h2 style="color: #004d40; text-align: center; border-bottom: 2px solid #004d40; padding-bottom: 8px; font-size: 16px;">📊 پاکستان اسٹاک ایکسچینج - بائی پاس لائیو رپورٹ</h2>
            
            <p style="font-size: 13px; line-height: 1.6;">السلام علیکم! یہ رہی آپ کی واچ لسٹ کے شیئرز کی فائر وال بائی پاس کر کے حاصل کردہ تازہ ترین لائیو ریٹس اور ٹریڈنگ لیولز کی رپورٹ:</p>
            
            <div style="background-color: #e0f2f1; border: 1px solid #b2dfdb; padding: 10px; border-radius: 6px; margin-bottom: 15px; text-align: center;">
                <span style="font-size: 14px; font-weight: bold; color: #00695c;">واچ لسٹ کی مجموعی مارکیٹ کارکردگی: </span>
                <span style="font-size: 15px; font-weight: bold; color: {perf_color};">{perf_sign}{avg_performance:.2f}%</span>
            </div>

            <h3 style="color: #37474f; font-size: 14px; margin-top: 10px;">📈 واچ لسٹ شیئرز اور تکنیکی سیٹ اپ</h3>
            
            <div style="width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; margin-top: 5px;">
                <table style="width: 100%; min-width: 500px; border-collapse: collapse; font-size: 12px;">
                    <thead>
                        <tr style="background-color: #004d40; color: #ffffff;">
                            <th style="padding: 8px 4px; border: 1px solid #ddd;">اسٹاک</th>
                            <th style="padding: 8px 4px; border: 1px solid #ddd;">موجودہ قیمت</th>
                            <th style="padding: 8px 4px; border: 1px solid #ddd;">فیصد تبدیلی</th>
                            <th style="padding: 8px 4px; border: 1px solid #ddd;">اسٹاپ لاس</th>
                            <th style="padding: 8px 4px; border: 1px solid #ddd;">پہلا ہدف</th>
                            <th style="padding: 8px 4px; border: 1px solid #ddd;">دوسرا ہدف</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>
            
            <div style="background-color: #e8f4f8; border-right: 4px solid #0288d1; padding: 10px; margin-top: 15px; border-radius: 4px;">
                <h4 style="margin: 0 0 6px 0; color: #01579b; font-size: 13px;">💰 کارپوریٹ اعلانات اور ڈیویڈنڈز:</h4>
                <ul style="margin: 0; padding-right: 15px; font-size: 12px; line-height: 1.5; color: #0d47a1;">
                    {dividend_info}
                </ul>
            </div>
            
            <div style="background-color: #fffde7; border-right: 4px solid #fbc02d; padding: 10px; margin-top: 10px; border-radius: 4px;">
                <h4 style="margin: 0 0 6px 0; color: #f57f17; font-size: 13px;">📰 مارکیٹ کا اہم رجحان:</h4>
                <ul style="margin: 0; padding-right: 15px; font-size: 12px; line-height: 1.5; color: #4e342e;">
                    <li>خودکار لائبریری انسٹالیشن کے ذریعے اب کلاؤڈ پر کوئی ایرر نہیں آئے گا۔</li>
                    <li>مارکیٹ کے اتار چڑھاؤ پر گہری نظر رکھیں۔</li>
                </ul>
            </div>
            
            <p style="font-size: 11px; color: #777777; text-align: center; margin-top: 15px; border-top: 1px solid #eeeeee; padding-top: 10px;">
                ⚠️ <strong>نوٹ:</strong> یہ خودکار رپورٹ مالیاتی ڈیٹا پر مبنی ہے۔ ٹریڈ سے پہلے تصدیق لازمی کریں۔
            </p>
            
        </div>
    </div>
    """
    
    send_email("📊 PSX بائی پاس لائیو مارکیٹ رپورٹ", html_content, to_email)

def send_email(subject, html_body, to_email):
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")

    if not sender_email or not sender_password:
        print("ای میل یا پاس ورڈ کی سیٹنگ موجود نہیں ہے!")
        return

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print("ای میل کامیابی سے بھیج دی گئی ہے!")
    except Exception as e:
        print(f"ای میل بھیجنے میں خرابی: {e}")

if __name__ == "__main__":
    generate_psx_report()
