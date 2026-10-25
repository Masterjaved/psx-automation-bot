import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
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
            "watchlist": ["SYS.KA", "OGDC.KA", "HUBC.KA", "FFC.KA"]
        }
        with open("watchlist.json", "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=4, ensure_ascii=False)
        return default_data

# 2. لائیو ڈیٹا اور ایچ ٹی ایم ایل ٹیبل بنانے کا فنکشن
def generate_psx_report():
    data = load_data()
    stocks = data["watchlist"]
    to_email = data["email_recipient"]
    
    # ٹیبل کی شروعات
    table_rows = ""
    
    for stock in stocks:
        try:
            ticker_symbol = stock if "." in stock else stock + ".KA"
            print(f"Fetching data for {ticker_symbol}...")
            
            ticker = yf.Ticker(ticker_symbol)
            todays_data = ticker.history(period="10d", timeout=10)
            
            clean_symbol = stock.replace('.KA', '')
            
            if not todays_data.empty:
                current_price = todays_data['Close'].iloc[-1]
                open_price = todays_data['Open'].iloc[-1]
                price_change = current_price - open_price
                percent_change = (price_change / open_price) * 100 if open_price != 0 else 0
                
                # تکنیکی لیولز کا حساب لگانا
                low_5days = todays_data['Low'].tail(5).min()
                stop_loss = round(low_5days * 0.98, 2)  
                target_1 = round(current_price * 1.025, 2) 
                target_2 = round(current_price * 1.05, 2)  
                
                sign = "+" if price_change >= 0 else ""
                color_class = "color: #2e7d32; font-weight: bold;" if price_change >= 0 else "color: #c62828; font-weight: bold;"
                bg_highlight = "#e8f5e9" if price_change >= 0 else "#ffebee"
                
                table_rows += f"""
                <tr style="background-color: {bg_highlight}; text-align: center;">
                    <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">{clean_symbol}</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">Rs. {current_price:.2f}</td>
                    <td style="padding: 10px; border: 1px solid #ddd; {color_class}">{sign}{percent_change:.2f}%</td>
                    <td style="padding: 10px; border: 1px solid #ddd; color: #d32f2f; font-weight: bold;">Rs. {stop_loss}</td>
                    <td style="padding: 10px; border: 1px solid #ddd; color: #388e3c;">Rs. {target_1}</td>
                    <td style="padding: 10px; border: 1px solid #ddd; color: #1976d2;">Rs. {target_2}</td>
                </tr>
                """
            else:
                table_rows += f"""
                <tr style="background-color: #fff3e0; text-align: center;">
                    <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">{clean_symbol}</td>
                    <td colspan="5" style="padding: 10px; border: 1px solid #ddd; color: #e65100;">فی الحال ڈیٹا دستیاب نہیں۔</td>
                </tr>
                """
        except Exception as e:
            print(f"Error fetching {stock}: {e}")
            table_rows += f"""
            <tr style="background-color: #ffebee; text-align: center;">
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">{stock.replace('.KA', '')}</td>
                <td colspan="5" style="padding: 10px; border: 1px solid #ddd; color: #c62828;">ڈیٹا حاصل کرنے میں تکنیکی مسئلہ۔</td>
            </tr>
            """

    # مکمل ای میل کا ایچ ٹی ایم ایل ڈھانچہ
    html_content = f"""
    <div dir="rtl" style="font-family: 'Jameel Noori Nastaleeq', Arial, sans-serif; background-color: #f4f6f8; padding: 20px; border-radius: 10px; color: #333333;">
        <div style="max-width: 700px; margin: auto; background: #ffffff; padding: 25px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            
            <h2 style="color: #004d40; text-align: center; border-bottom: 2px solid #004d40; padding-bottom: 10px;">📊 پاکستان اسٹاک ایکسچینج - خودکار لائیو رپورٹ</h2>
            
            <p style="font-size: 16px; line-height: 1.6;">السلام علیکم! یہ رہی آپ کی واچ لسٹ کے شیئرز کی تازہ ترین لائیو مارکیٹ اور ٹریڈنگ لیولز کی رپورٹ:</p>
            
            <h3 style="color: #37474f; margin-top: 20px;">📈 واچ لسٹ شیئرز اور تکنیکی سیٹ اپ</h3>
            
            <table style="width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px;">
                <thead>
                    <tr style="background-color: #004d40; color: #ffffff;">
                        <th style="padding: 12px; border: 1px solid #ddd;">اسٹاک</th>
                        <th style="padding: 12px; border: 1px solid #ddd;">موجودہ قیمت</th>
                        <th style="padding: 12px; border: 1px solid #ddd;">فیصد تبدیلی</th>
                        <th style="padding: 12px; border: 1px solid #ddd;">اسٹاپ لاس (Risk)</th>
                        <th style="padding: 12px; border: 1px solid #ddd;">پہلا ہدف (T1)</th>
                        <th style="padding: 12px; border: 1px solid #ddd;">دوسرا ہدف (T2)</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
            
            <div style="background-color: #fffde7; border-right: 5px solid #fbc02d; padding: 15px; margin-top: 20px; border-radius: 4px;">
                <h4 style="margin: 0 0 10px 0; color: #f57f17;">📰 مارکیٹ کا عمومی جائزہ اور اہم خبریں:</h4>
                <ul style="margin: 0; padding-right: 20px; font-size: 14px; line-height: 1.6; color: #4e342e;">
                    <li>انرجی سیکٹر اور بڑی کمپنیوں میں ادارہ جاتی بائینگ کا رجحان جاری ہے۔</li>
                    <li>موجودہ زون میں رسک مینجمنٹ کا خیال رکھیں اور اسٹاپ لاس کی سختی سے پابندی کریں۔</li>
                    <li>آنے والے کارپوریٹ اعلانات کے پیش نظر مارکیٹ میں اتار چڑھاؤ متوقع ہے۔</li>
                </ul>
            </div>
            
            <p style="font-size: 12px; color: #777777; text-align: center; margin-top: 30px; border-top: 1px solid #eeeeee; padding-top: 15px;">
                ⚠️ <strong>نوٹ:</strong> یہ تکنیکی اشارے خودکار تیار کیے گئے ہیں۔ ٹریڈ کرنے سے پہلے مارکیٹ کا خود تجزیہ ضرور کریں۔<br>
                آپ کے گٹ ہب کلاؤڈ بوٹ کے ذریعے خودکار ارسال کردہ۔
            </p>
            
        </div>
    </div>
    """
    
    send_email("📊 PSX رنگین اور فارمیٹڈ ٹریڈنگ رپورٹ", html_content, to_email)

# 3. ای میل بھیجنے کا فنکشن
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
