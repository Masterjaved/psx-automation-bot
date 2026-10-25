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

# 2. لائیو ڈیٹا، ٹریڈنگ لیولز، ڈیویڈنڈ اور ایچ ٹی ایم ایل ٹیبل بنانے کا فنکشن
def generate_psx_report():
    data = load_data()
    stocks = data["watchlist"]
    to_email = data["email_recipient"]
    
    table_rows = ""
    dividend_info = ""
    
    for stock in stocks:
        try:
            ticker_symbol = stock if "." in stock else stock + ".KA"
            print(f"Fetching data for {ticker_symbol}...")
            
            ticker = yf.Ticker(ticker_symbol)
            todays_data = ticker.history(period="10d", timeout=10)
            
            clean_symbol = stock.replace('.KA', '')
            
            # آنے والے ڈیویڈنڈ کا ڈیٹا چیک کرنا
            try:
                dividends = ticker.dividends
                if not dividends.empty:
                    last_div = dividends.tail(1)
                    div_date = last_div.index[0].strftime('%Y-%m-%d')
                    div_val = last_div.values[0]
                    if div_val > 0:
                        dividend_info += f"<li><b>{clean_symbol}</b>: آخری یا متوقع ڈیویڈنڈ روپیہ {div_val:.2f} (تاریخ: {div_date})</li>"
            except:
                pass

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
                    <td style="padding: 10px 6px; border: 1px solid #ddd; font-weight: bold; font-size: 13px;">{clean_symbol}</td>
                    <td style="padding: 10px 6px; border: 1px solid #ddd; font-size: 13px;">Rs. {current_price:.2f}</td>
                    <td style="padding: 10px 6px; border: 1px solid #ddd; font-size: 13px; {color_class}">{sign}{percent_change:.2f}%</td>
                    <td style="padding: 10px 6px; border: 1px solid #ddd; font-size: 13px; color: #d32f2f; font-weight: bold;">Rs. {stop_loss}</td>
                    <td style="padding: 10px 6px; border: 1px solid #ddd; font-size: 13px; color: #388e3c; font-weight: bold;">Rs. {target_1}</td>
                    <td style="padding: 10px 6px; border: 1px solid #ddd; font-size: 13px; color: #1976d2; font-weight: bold;">Rs. {target_2}</td>
                </tr>
                """
            else:
                table_rows += f"""
                <tr style="background-color: #fff3e0; text-align: center;">
                    <td style="padding: 10px 6px; border: 1px solid #ddd; font-weight: bold; font-size: 13px;">{clean_symbol}</td>
                    <td colspan="5" style="padding: 10px 6px; border: 1px solid #ddd; color: #e65100; font-size: 13px;">فی الحال ڈیٹا دستیاب نہیں۔</td>
                </tr>
                """
        except Exception as e:
            print(f"Error fetching {stock}: {e}")
            table_rows += f"""
            <tr style="background-color: #ffebee; text-align: center;">
                <td style="padding: 10px 6px; border: 1px solid #ddd; font-weight: bold; font-size: 13px;">{stock.replace('.KA', '')}</td>
                <td colspan="5" style="padding: 10px 6px; border: 1px solid #ddd; color: #c62828; font-size: 13px;">ڈیٹا حاصل کرنے میں عارضی مسئلہ۔</td>
            </tr>
            """

    if not dividend_info:
        dividend_info = "<li>موجودہ واچ لسٹ کے لیے قریبی ڈیویڈنڈ کا کوئی نیا باضابطہ اعلان تاحال موصول نہیں ہوا۔</li>"

    # مکمل ای میل کا بہتر اور موبائل فرینڈلی ڈیزائن
    html_content = f"""
    <div dir="rtl" style="font-family: Arial, sans-serif; background-color: #f4f6f8; padding: 10px; color: #333333;">
        <div style="max-width: 650px; margin: auto; background: #ffffff; padding: 15px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            
            <h2 style="color: #004d40; text-align: center; border-bottom: 2px solid #004d40; padding-bottom: 8px; font-size: 16px;">📊 پاکستان اسٹاک ایکسچینج - لائیو رپورٹ</h2>
            
            <p style="font-size: 13px; line-height: 1.6;">السلام علیکم! یہ رہی آپ کی واچ لسٹ کے شیئرز کی تازہ ترین لائیو مارکیٹ اور ٹریڈنگ لیولز کی رپورٹ:</p>
            
            <h3 style="color: #37474f; font-size: 14px; margin-top: 15px;">📈 واچ لسٹ شیئرز اور تکنیکی سیٹ اپ</h3>
            
            <!-- موبائل پر سکرول کرنے کے لیے بہترین فریم -->
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
                <h4 style="margin: 0 0 6px 0; color: #01579b; font-size: 13px;">💰 کمپنियों کے ڈیویڈنڈز کی تازہ ترین صورتحال:</h4>
                <ul style="margin: 0; padding-right: 15px; font-size: 12px; line-height: 1.5; color: #0d47a1;">
                    {dividend_info}
                </ul>
            </div>
            
            <div style="background-color: #fffde7; border-right: 4px solid #fbc02d; padding: 10px; margin-top: 10px; border-radius: 4px;">
                <h4 style="margin: 0 0 6px 0; color: #f57f17; font-size: 13px;">📰 مارکیٹ کا عمومی جائزہ اور اہم رجحان:</h4>
                <ul style="margin: 0; padding-right: 15px; font-size: 12px; line-height: 1.5; color: #4e342e;">
                    <li>انرجی سیکٹر اور بڑی کمپنیوں میں استحکام اور سلیکٹیو بائینگ جاری ہے۔</li>
                    <li>رسک مینجمنٹ کو مدنظر رکھتے ہوئے اپنے اسٹاپ لاس کی سختی سے پابندی کریں۔</li>
                </ul>
            </div>
            
            <p style="font-size: 11px; color: #777777; text-align: center; margin-top: 15px; border-top: 1px solid #eeeeee; padding-top: 10px;">
                ⚠️ <strong>نوٹ:</strong> یہ تکنیکی اشارے خودکار تیار کیے گئے ہیں۔ ٹریڈ کرنے سے پہلے مارکیٹ کا خود تجزیہ ضرور کریں۔
            </p>
            
        </div>
    </div>
    """
    
    send_email("📊 PSX درست اور مکمل ٹریڈنگ رپورٹ", html_content, to_email)

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
