import requests
import json
from bs4 import BeautifulSoup
import time
import jdatetime
import pytz
from datetime import datetime
import sys
import io
import os

# تنظیم کدگذاری استاندارد به UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# تنظیم منطقه زمانی ایران
iran_tz = pytz.timezone('Asia/Tehran')

# 🔴 تنظیمات روبیکا
rubika_token = 'توکن ربات را اینجا قرار دهید' 
channel_id = '@art_codex' #آیدی کانال

# فایل ذخیره message_id
MESSAGE_ID_FILE = 'last_message_id.txt'

# URLها
sell_url = 'https://publicapi.ramzinex.com/exchange/api/v1.0/exchange/orderbooks/11/market_sell_price'
gold_url = 'https://publicapi.ramzinex.com/exchange/api/v1.0/exchange/orderbooks/678/market_buy_price'
bitcoin_url = 'https://publicapi.ramzinex.com/exchange/api/v1.0/exchange/orderbooks/12/market_buy_price'
xau_url = "https://www.usagold.com/live-gold-price-today/"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
}

def get_last_message_id():
    """خواندن message_id ذخیره شده"""
    try:
        if os.path.exists(MESSAGE_ID_FILE):
            with open(MESSAGE_ID_FILE, 'r') as f:
                data = json.load(f)
                return data.get('message_id')
    except:
        pass
    return None

def save_message_id(message_id):
    """ذخیره message_id"""
    try:
        with open(MESSAGE_ID_FILE, 'w') as f:
            json.dump({'message_id': message_id}, f)
    except Exception as e:
        print(f"⚠️ خطا در ذخیره message_id: {e}")

def send_or_edit_message(message, message_id=None):
    """ارسال پیام جدید یا ویرایش پیام قبلی"""
    rubika_base_url = f'https://botapi.rubika.ir/v3/{rubika_token}'
    
    if message_id:
        # ویرایش پیام قبلی
        url = f'{rubika_base_url}/editMessageText'
        payload = {
            'chat_id': channel_id,
            'message_id': message_id,
            'text': message
        }
        action = "ویرایش"
    else:
        # ارسال پیام جدید
        url = f'{rubika_base_url}/sendMessage'
        payload = {
            'chat_id': channel_id,
            'text': message
        }
        action = "ارسال"
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        res_json = response.json()
        
        if response.status_code == 200 and res_json.get('status') == 'OK':
            print(f"✅ پیام با موفقیت {action} شد.")
            
            # اگر پیام جدید ارسال شد، ID آن را ذخیره کن
            if not message_id and 'data' in res_json and 'message_id' in res_json['data']:
                new_message_id = res_json['data']['message_id']
                save_message_id(new_message_id)
                print(f"💾 message_id ذخیره شد: {new_message_id}")
            
            return True
        else:
            print(f"❌ خطا در {action} پیام:", res_json)
            
            # اگر ویرایش ناموفق بود، پیام جدید بفرست
            if message_id:
                print("🔄 تلاش برای ارسال پیام جدید...")
                return send_or_edit_message(message, message_id=None)
            
            return False
    except Exception as e:
        print(f"❌ خطا در درخواست به روبیکا: {e}")
        return False

while True:
    try:
        # تاریخ شمسی و ساعت
        now = jdatetime.datetime.now(iran_tz)
        persian_date = now.strftime("%Y/%m/%d")
        time_str = now.strftime("%H:%M")

        print(f"\n⏰ [{time_str}] شروع دریافت قیمت‌ها...")

        # دریافت قیمت انس جهانی
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
                f"💰 انس جهانی: {xau_price:,} $\n"
                f"💵 تتر: {tether_price_t} \n"
                f"🏆 طلا 18 عیار: {gold18_str} \n"
                f"🏆 طلا بدون حباب: {goldx18:,}\n"
                f"🥇 آبشده بدون حباب: {xau_price_without_bubble:,} \n"
                f"₿ بیت کوین: {bitcoin_price_str} \n\n"
                f"🗓 تاریخ: {persian_date}\n"
                f"⏱️ ساعت: {time_str}\n\n"
                f"💠 {channel_id}"
            )

            # خواندن message_id قبلی
            last_message_id = get_last_message_id()
            
            if last_message_id:
                print(f"📝 message_id قبلی: {last_message_id} - در حال ویرایش...")
            else:
                print("📝 message_id قبلی یافت نشد - ارسال پیام جدید...")

            # ارسال یا ویرایش پیام
            success = send_or_edit_message(message, last_message_id)
            
            if success:
                print(f"✅ انس: {xau_price:,.2f}$ | تتر: {tether_price_t} | آبشده: {xau_price_without_bubble:,}")
            else:
                print("❌ ارسال/ویرایش پیام ناموفق بود")
        else:
            print("❌ کلید 'data' در پاسخ تتر وجود ندارد.")

    except Exception as e:
        print(f"⛔ خطا در اجرای برنامه: {e}")

    # وقفه ۱۵ دقیقه‌ای (۹۰۰ ثانیه)
    print(f"\n⏳ انتظار برای 15 دقیقه...")
    time.sleep(900)
