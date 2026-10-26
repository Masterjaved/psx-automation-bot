import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import psxdata


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
            "watchlist": ["SYS", "OGDC", "HUBC", "FFC", "CHWC",
                          "CNERGY", "KEL", "MLCF", "SAZEW", "EFERT"],
        }
        with open("watchlist.json", "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=4, ensure_ascii=False)
        return default_data


def get_stock_data(symbol):
    """واپس: (قیمت, فیصد تبدیلی, ڈیویڈنڈ یلڈ) یا (None, None, None)"""
    try:
        q = psxdata.quote(symbol)
        if q.empty:
            print(f"{symbol}: خالی ڈیٹا")
            return None, None, None
        row = q.iloc[0]
        price = float(row["price"])
        change = float(row["change_pct"])
        dy = row.get("dividend_yield")
        dy = float(dy) if dy == dy else None  # NaN چیک
        print(f"{symbol}: price={price} change={change}%")
        return price, change, dy
    except Exception as e:
        print(f"{symbol} میں خرابی: {type(e).__name__}: {e}")
        return None, None, None


def generate_psx_report():
    data = load_data()
    stocks = data["watchlist"]
    to_email = data["email_recipient"]

    table_rows = ""
    total_pct = 0
    valid = 0

    for stock in stocks:
        sym = stock.replace(".KA", "").strip().upper()
        price, pct, dy = get_stock_data(sym)

        if price is None:
            table_rows += f"""
            <tr style="background-color:#fffde7;text-align:center;">
                <td style="padding:10px 6px;border:1px solid #ddd;font-weight:bold;font-size:13px;">{sym}</td>
                <td colspan="6" style="padding:10px 6px;border:1px solid #ddd;color:#f57f17;font-size:13px;">ڈیٹا دستیاب نہیں۔</td>
            </tr>"""
            continue

        total_pct += pct
        valid += 1
        stop_loss = round(price * 0.97, 2)
        t1 = round(price * 1.025, 2)
        t2 = round(price * 1.05, 2)

        sign = "+" if pct >= 0 else ""
        color = "color:#2e7d32;font-weight:bold;" if pct >= 0 else "color:#c62828;font-weight:bold;"
        danger = pct <= -2.5
        bg = "#ffcdd2" if danger else ("#e8f5e9" if pct >= 0 else "#ffebee")
        badge = (" <span style='background:#b71c1c;color:white;padding:2px 4px;"
                 "border-radius:3px;font-size:9px;'>الرٹ!</span>") if danger else ""
        dy_txt = f"{dy:.2f}%" if dy is not None else "-"

        table_rows += f"""
        <tr style="background-color:{bg};text-align:center;">
            <td style="padding:10px 6px;border:1px solid #ddd;font-weight:bold;font-size:13px;">{sym}{badge}</td>
            <td style="padding:10px 6px;border:1px solid #ddd;font-size:13px;">Rs. {price:.2f}</td>
            <td style="padding:10px 6px;border:1px solid #ddd;font-size:13px;{color}">{sign}{pct:.2f}%</td>
            <td style="padding:10px 6px;border:1px solid #ddd;font-size:13px;color:#d32f2f;font-weight:bold;">Rs. {stop_loss}</td>
            <td style="padding:10px 6px;border:1px solid #ddd;font-size:13px;color:#388e3c;font-weight:bold;">Rs. {t1}</td>
            <td style="padding:10px 6px;border:1px solid #ddd;font-size:13px;color:#1976d2;font-weight:bold;">Rs. {t2}</td>
            <td style="padding:10px 6px;border:1px solid #ddd;font-size:13px;">{dy_txt}</td>
        </tr>"""

    avg = (total_pct / valid) if valid else 0
    avg_sign = "+" if avg >= 0 else ""
    avg_color = "#2e7d32" if avg >= 0 else "#c62828"

    html = f"""
    <div dir="rtl" style="font-family:Arial,sans-serif;background-color:#f4f6f8;padding:10px;color:#333;">
      <div style="max-width:700px;margin:auto;background:#fff;padding:15px;border-radius:8px;box-shadow:0 4px 10px rgba(0,0,0,0.1);">
        <h2 style="color:#004d40;text-align:center;border-bottom:2px solid #004d40;padding-bottom:8px;font-size:16px;">
          📊 پاکستان اسٹاک ایکسچینج - واچ لسٹ رپورٹ</h2>
        <p style="font-size:13px;line-height:1.6;">السلام علیکم! یہ آپ کی واچ لسٹ کے شیئرز کی تازہ ترین رپورٹ ہے:</p>
        <div style="background-color:#e0f2f1;border:1px solid #b2dfdb;padding:10px;border-radius:6px;margin-bottom:15px;text-align:center;">
          <span style="font-size:14px;font-weight:bold;color:#00695c;">واچ لسٹ کی اوسط کارکردگی: </span>
          <span style="font-size:15px;font-weight:bold;color:{avg_color};">{avg_sign}{avg:.2f}%</span>
        </div>
        <div style="width:100%;overflow-x:auto;">
          <table style="width:100%;min-width:560px;border-collapse:collapse;font-size:12px;">
            <thead>
              <tr style="background-color:#004d40;color:#fff;">
                <th style="padding:8px 4px;border:1px solid #ddd;">اسٹاک</th>
                <th style="padding:8px 4px;border:1px solid #ddd;">موجودہ قیمت</th>
                <th style="padding:8px 4px;border:1px solid #ddd;">فیصد تبدیلی</th>
                <th style="padding:8px 4px;border:1px solid #ddd;">اسٹاپ لاس</th>
                <th style="padding:8px 4px;border:1px solid #ddd;">پہلا ہدف</th>
                <th style="padding:8px 4px;border:1px solid #ddd;">دوسرا ہدف</th>
                <th style="padding:8px 4px;border:1px solid #ddd;">ڈیویڈنڈ یلڈ</th>
              </tr>
            </thead>
            <tbody>{table_rows}</tbody>
          </table>
        </div>
        <p style="font-size:11px;color:#777;text-align:center;margin-top:15px;border-top:1px solid #eee;padding-top:10px;">
          ⚠️ <strong>نوٹ:</strong> اسٹاپ لاس اور اہداف قیمت کے مقررہ فیصد (-3%، +2.5%، +5%) سے نکلتے ہیں، کوئی تجزیاتی مشورہ نہیں۔ ٹریڈ سے پہلے تصدیق ضروری ہے۔
        </p>
      </div>
    </div>"""

    send_email("📊 PSX واچ لسٹ رپورٹ", html, to_email)


def send_email(subject, html_body, to_email):
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")

    if not sender_email or not sender_password:
        print("ای میل یا پاس ورڈ کی سیٹنگ موجود نہیں ہے!")
        return

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print("ای میل کامیابی سے بھیج دی گئی ہے!")
    except Exception as e:
        print(f"ای میل بھیجنے میں خرابی: {e}")


if __name__ == "__main__":
    generate_psx_report()
