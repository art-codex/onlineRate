import requests
import json
from bs4 import BeautifulSoup
import time
import jdatetime
import pytz
from datetime import datetime
import sys
import io

# تنظیم کدگذاری استاندارد به UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# تنظیم منطقه زمانی ایران
iran_tz = pytz.timezone('Asia/Tehran')

# 🔴 تنظیمات تلگرام
telegram_token = 'اینجا توکن ربات را قرار دهید'
channel_id = '@fxsignal313' #آیدی کانال

# URLها
sell_url = 'https://publicapi.ramzinex.com/exchange/api/v1.0/exchange/orderbooks/11/market_sell_price'
gold_url = 'https://publicapi.ramzinex.com/exchange/api/v1.0/exchange/orderbooks/678/market_buy_price'
bitcoin_url = 'https://publicapi.ramzinex.com/exchange/api/v1.0/exchange/orderbooks/12/market_buy_price'
xau_url = "https://www.usagold.com/live-gold-price-today/"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
}

# دکمه‌های شیشه‌ای
buttons = {
    "inline_keyboard": [
        [
            {"text": "📢 تبلیغات ویژه", "url": "https://t.me/art_codex"},
            {"text": "📣 عضویت در کانال", "url": "https://t.me/fxsignal313"}
        ]
    ]
}

while True:
    try:
        # تاریخ شمسی و ساعت
        now = jdatetime.datetime.now(iran_tz)
        persian_date = now.strftime("%Y/%m/%d")
        time_str = now.strftime("%H:%M")

        print(f"\n⏰ [{time_str}] شروع دریافت قیمت‌ها...")

        # دریافت قیمت انس جهانی
        try:
            response = requests.get(xau_url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                price_element = soup.find(class_="woocommerce-Price-amount amount")
                if price_element:
                    xau_price_str = price_element.text.strip().replace("$", "").replace(",", "")
                    xau_price = float(xau_price_str)
                else:
                    print("XAU: قیمت پیدا نشد.")
                    xau_price = 0
            else:
                print("XAU: خطا در اتصال به سایت.")
                xau_price = 0
        except Exception as e:
            print(f"XAU: خطا در دریافت قیمت انس: {e}")
            xau_price = 0

        if xau_price == 0:
            print("❌ قیمت انس دریافت نشد. تلاش مجدد...")
            time.sleep(60)
            continue

        # دریافت قیمت‌های رمزینهکس
        try:
            sell_response = requests.get(sell_url, timeout=10).json()
            gold_response = requests.get(gold_url, timeout=10).json()
            bitcoin_response = requests.get(bitcoin_url, timeout=10).json()
        except Exception as e:
            print(f"❌ خطا در دریافت قیمت‌های رمزینهکس: {e}")
            time.sleep(60)
            continue

        if 'data' in sell_response and 'data' in gold_response and 'data' in bitcoin_response:
            sell_price = sell_response['data']['price']
            t_price = sell_price // 10
            tether_price_t = f"{int(t_price):,}"
            tether_price = int(t_price)

            gold18 = int(gold_response['data']) * 100
            gold18_str = f"{gold18:,}"

            bitcoin_price = int(bitcoin_response['data'])
            bitcoin_price_str = f"{bitcoin_price:,}"

            goldx18 = int((xau_price * tether_price) / 41.45)

            # طلا آبشده بدون حباب
            xau_price_without_bubble = round(((xau_price * tether_price) / 0.97) / 10000) * 1000

            message = (
                f"💰 انس جهانی: {xau_price:,} \n"
                f"💵 تتر: {tether_price_t} \n"
                f"🏆 طلا 18 عیار: {gold18_str} \n"
                f"🏆 طلا بدون حباب: {goldx18:,}\n"
                f"🥇 آبشده بدون حباب: {xau_price_without_bubble:,} \n"
                f"₿ بیت کوین: {bitcoin_price_str} \n\n"
                f"🗓 تاریخ: {persian_date}\n"
                f"⏱️ ساعت: {time_str}\n\n"
                f"💠 {channel_id}"
            )

            # ارسال پیام جدید به کانال تلگرام
            telegram_url = f'https://api.telegram.org/bot{telegram_token}/sendMessage'
            
            telegram_payload = {
                'chat_id': channel_id,
                'text': message,
                'reply_markup': buttons
            }

            print("📤 در حال ارسال پیام جدید...")
            telegram_response = requests.post(telegram_url, json=telegram_payload, timeout=10)

            if telegram_response.status_code == 200:
                res_json = telegram_response.json()
                if res_json.get('ok'):
                    print("✅ پیام جدید با موفقیت ارسال شد.")
                    print(f"✅ انس: {xau_price:,.2f}$ | تتر: {tether_price_t} | آبشده: {xau_price_without_bubble:,}")
                else:
                    print("❌ خطا در ارسال پیام:", res_json)
            else:
                print("❌ خطا در ارسال پیام:", telegram_response.text)
        else:
            print("❌ کلید 'data' در پاسخ تتر وجود ندارد.")

    except Exception as e:
        print(f"⛔ خطا در اجرای برنامه: {e}")

    # وقفه ۱۵ دقیقه‌ای (۹۰۰ ثانیه)
    print(f"\n⏳ انتظار برای 15 دقیقه...")
    time.sleep(900)
