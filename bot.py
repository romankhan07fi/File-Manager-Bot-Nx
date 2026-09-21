import sys
import io
import unicodedata

# ==========================================
# Windows UTF-8 Fix (emoji & unicode support)
# ==========================================
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import requests
import time
import json
import os
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
import threading
import random
import re
import html
import pyotp
from collections import Counter, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from datetime import datetime 
from urllib.parse import urljoin

# ==========================================
# Configuration (Token & Owner ID)
# ==========================================
TOKEN = "8889132264:AAFGTB9ikI6xLEBTJJemc0hyCjrnZkySE1w"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
FILE_URL = f"https://api.telegram.org/file/bot{TOKEN}/"

OWNER_ID = 7603005230
BOT_USERNAME = "@Naruto_Number_Bot"
_BOT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(_BOT_DIR, "bot_data.json")
USERS_DATA_FILE = os.path.join(_BOT_DIR, "users_data.json")  # Local user storage (no Firestore needed)

# ==========================================
# Premium Emoji Database
# ==========================================
PEM = {
    "ok": '<tg-emoji emoji-id="5352694861990501856">✅</tg-emoji>',
    "no": '<tg-emoji emoji-id="5420130255174145507">❌</tg-emoji>',
    "warn": '<tg-emoji emoji-id="5336944168944047463">⚠️</tg-emoji>',
    "admin": '<tg-emoji emoji-id="5353032893096567467">📊</tg-emoji>',
    "user": '<tg-emoji emoji-id="5352861489541714456">👤</tg-emoji>',
    "file": '<tg-emoji emoji-id="5352721946054268944">📁</tg-emoji>',
    "rocket": '<tg-emoji emoji-id="5352597830089347330">🚀</tg-emoji>',
    "graph": '<tg-emoji emoji-id="5352877703043258544">📊</tg-emoji>',
    "money": '<tg-emoji emoji-id="5348469219761626211">💸</tg-emoji>',
    "gift": '<tg-emoji emoji-id="5420396762189831222">🎁</tg-emoji>',
    "msg": '<tg-emoji emoji-id="5337302974806922068">💬</tg-emoji>',
    "gear": '<tg-emoji emoji-id="5420155432272438703">⚙️</tg-emoji>',
    "link": '<tg-emoji emoji-id="5420517437885943844">🔗</tg-emoji>',
    "trash": '<tg-emoji emoji-id="5422557736330106570">🗑</tg-emoji>',
    "upload": '<tg-emoji emoji-id="5353001161878182134">📤</tg-emoji>',
    "world": '<tg-emoji emoji-id="5336972142066047577">🌐</tg-emoji>',
    "lock": '<tg-emoji emoji-id="5353022963132174959">🔐</tg-emoji>',
    "phone": '<tg-emoji emoji-id="5337132498965010628">📱</tg-emoji>',
    "num": '<tg-emoji emoji-id="5352862640592949843">🔢</tg-emoji>',
    "pin": '<tg-emoji emoji-id="5352922460897452503">📍</tg-emoji>',
    "star": '<tg-emoji emoji-id="5352552689983067014">✨</tg-emoji>',
    "hi": '<tg-emoji emoji-id="5353027129250453493">👋</tg-emoji>'
}

GLOBAL_BODY_EMOJIS = {
    "➖": "5870818207383686839", "🚫": "5334807341109908955", "😒": "5334763399299506604",
    "🖥": "5334880948259427772", "🌐": "5334590977837403844", "🌟": "5337102391244263212",
    "🕓": "5336983442125001376", "⌛": "5337172996211648018", "💬": "5337302974806922068",
    "🔐": "5337255927735163754", "🍏": "5337132498965010628", "❔": "5336850036145823599",
    "⚠️": "5336944168944047463", "🔥": "5337267511261960341", "💸": "5348469219761626211",
    "🥚": "5348390922507817684", "👨‍⚖": "5334763399299506604", "🐁": "5348494358205207761",
    "🧻": "5348486915026884464", "⚗": "5346311574221000149", "🛴": "5348075478634766440",
    "📊": "5353032893096567467", "🔢": "5352862640592949843", "👤": "5352861489541714456",
    "📁": "5352721946054268944", "🚀": "5352597830089347330", "💎": "5352838545826420397",
    "📍": "5352922460897452503", "👋": "5353027129250453493", "✅": "5352694861990501856",
    "1️⃣": "5352651766288652742", "2️⃣": "5355186458418257716", "3️⃣": "5352867219028091093",
    "4️⃣": "5352566657216714037", "5️⃣": "5353086880835474989", "6️⃣": "5354859211975071385",
    "7️⃣": "5352859127309707652", "8️⃣": "5352957533600389988", "9️⃣": "5353060913463204207",
    "🔤": "5352727417842606016", "📣": "5352980533150259581", "📤": "5353001161878182134",
    "✨": "5352552689983067014", "🔹": "5352638632278660622", "🎙": "5355102594886833928",
    "💴": "5352985330628730418", "📅": "5352585194295564660", "📴": "5352974971167611327",
    "✏️": "5395444784611480792", "📱": "5337132498965010628", "🔗": "5420517437885943844",
    "❌": "5420130255174145507", "⚙️": "5420155432272438703", "🫂": "5420145051336485498",
    "➕": "5420323438508155202", "🗑": "5422557736330106570", "🎁": "5420396762189831222",
    "➤": "5420618897898381296", "🏢": "5420156334215565595", "💳": "5190899075968441286",
    "📝": "5192739271886282680", "🛡": "5269634540992752336", "🤝": "5192805934073685937",
    "💰": "5190576863226933563", "👀": "5190645917711114179", "🕹": "5193100774988617665",
    "🟢": "5192812028632274956", "🧪": "5190781475468915802", "🎨": "5190751148704833975",
    "📂": "5257969839313526622", "🌍": "5780471598922337683", "📌": "5318986077455795572",
    "📢": "5789428375261023681", "🆔": "5352862640592949843", "📈": "5352877703043258544",
    "🔔": "5352980533150259581", "🏦": "5348469219761626211", "🧾": "5192739271886282680",
    "👨‍⚖️": "5334763399299506604", "🔍": "5463352748751753567",
    "🔑": "5197288647275071607"
    , "🎉": "5420396762189831222", "💙": "5348469219761626211"
}

DEFAULT_CUSTOM_MESSAGES = {
    "start": {"text": f"{PEM['hi']} <b>Welcome to Number Bot!</b>\n\n🎉 আপনাকে স্বাগতম!\n\nএই বটের মাধ্যমে আপনি সহজেই নম্বর-সংক্রান্ত সেবা ব্যবহার করতে পারবেন।\n\n{PEM['pin']} <b>শুরু করতে নিচের নির্দেশনা অনুসরণ করুন:</b>\n• আপনার প্রয়োজনীয় অপশন নির্বাচন করুন।\n• সঠিক তথ্য প্রদান করুন।\n• কোনো সমস্যায় পড়লে <b>Support</b> বাটনে যোগাযোগ করুন।\n\n💙 আমাদের বট ব্যবহার করার জন্য ধন্যবাদ।\nশুভকামনা রইল! {PEM['rocket']}", "buttons": []},
    "get_number": {"text": f"{PEM['pin']} Select a service:", "buttons": []},
    "select_country": {"text": f"📌 Select a country for {{service}}:", "buttons": []}, 
    "search_number": {"text": "╔═══════════╗\n     🔍 <b>SEARCH NUMBER</b>\n╚═══════════╝\n✅ Enter 3 to 9 digits  \nto search for a number.\n━━━━━━━━━━━━━\n📝 Example:\n➥ 880\n➥ 9227373\n━━━━━━━━━━━━━\n🔍 Fast Number Lookup System", "buttons": []},
    "traffic": {"text": f"{PEM['graph']} <b>Traffic Overview</b>\n\n{PEM['ok']} Available Numbers: {{avail}}\n{PEM['rocket']} Assigned Numbers: {{assigned}}", "buttons": []},
    "refer": {"text": f"➖➖➖➖➖➖➖\n« {PEM['gift']} REFER & EARN »\n➖➖➖➖➖➖➖\n{PEM['link']} YOUR LINK:\n<code>{{ref_link}}</code>\n➖➖➖➖➖➖➖\n{PEM['user']} TOTAL REFERS: <b>{{total_ref}}</b>\n➖➖➖➖➖➖➖\n{PEM['money']} PER REFER: <b>{{ref_reward}} TK</b>\n➖➖➖➖➖➖➖", "buttons": []},
    "withdrawal": {"text": "➖➖➖➖➖➖➖\n《 😒 WITHDRAWAL 》\n➖➖➖➖➖➖➖\n👋 Total Otp: {total_otp}\n➖➖➖➖➖➖➖\n🫂 Total Reffer :{total_ref}\n➖➖➖➖➖➖➖\n📅 BALANCE: {bal}৳\n➖➖➖➖➖➖➖\n🔐 MINIMUM: {min_w} ৳\n➖➖➖➖➖➖➖\nSELECT METHOD:", "buttons": []},
    "support": {"text": f"{PEM['msg']} Contact us for any help:", "buttons": []}
}

# ==========================================
# Firebase Setup
# ==========================================
firebase_config = {
  "type": "service_account",
  "project_id": "naruto-zone-bot",
  "private_key_id": "af70acb1ecdb9089023b1fdf37205b4e2eff9a95",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCgsthuc6/0F3OT\nFo+W3LcLPybW+3mQvOxjkGiNh7Cp1AVXqqD9jiOX/mzPlW8MqnVEnzJ0uCyOlHVa\nWvT/JkRfXx0L1mTJ6dMlrMXLHYnXOdMXt2XuZ8I0R+Pc9rsirnYISy9NgSeah3z2\naCOkOCI+id7vuqb2ZrNhu3nUUkRLjX5bLdB2bPb4FK+0tMWXrD8fr6cBz2Kr1HU3\n7QGuK5f91255FJ92GhG6r3/11ofn/6Q66AOUcNZLBWUsvJan30HU6piGJNNts6c7\nhg3eJT4y81DJOveGp/Ju9XtXT2XDXR0M7nOCmdMqaH5ZnwOchjkKJSULKgCnabSy\nG5yspertAgMBAAECggEAFYqDyqKFVpICMxhWHSHvA3nuqejBze4VPe9wpHAo9Urv\ngGXl+Lch/FDloxnj7e23lIBGkjDSADbUWE1TBBTMG4Czcw/FKO/IFwfG58hI3uno\nawhxiHiuJrXwTIFiam66cbgqWhhTB7rbvGgPRwcjSADROo9prCPuLc6ksRpp/zp8\n64cOpgTbTvkHr1sfzmpemWMCuLdnRvX+ekb+6CJfh95D4kkzzhfzoeS47deL6huX\nyq5Janvu+9TFdypygmz9XcoesJH4yWGU0FTJEwLKB+zPb6WLHc9Swkbt1pVglaZj\nXSadL4JMXwguBWEzXtKXMjjIoM9ruKZSZd115fTf4QKBgQDRHBkYzXoGJdoE35pD\nJhpKoK1Y4vrdpZkM55bvyuOeLN90R7SBnS62YIgKgbIJhTlAJ24tEs25MOF8BEwF\n67D+BUwblrroP3HJimFSGi5tNe6Sgja7aApWespLCsDdHlQWNUlNSI+0//fhQMHj\nql6IVDqivrgljg+6APGZo47FWQKBgQDEu7dCKbTcmkT2wvRcG6iYzD4vlsxcRnMy\n65zRXeWFA4iUgV0kP+jFdSDC+vZQHuRKxinnCSjp4TxhVebMVM32GXnuiMLnUufJ\naaTpOxDO/GlEizw4hmbO7quUJh0zfr7OJfJNxFOdJps+qlO79sKoyjLPpkiitb9q\njqpw+IQbtQKBgEsAOvgsasHdva7VzGydM/zkWIhzEOuCw7xfLEHhkXZgPd1lApci\nm2iKgwDRt9u2Tux1uAyum976a0Wh/Op6uMbDe6LBk1RNvTA+U92wykodd+5QifT5\nwgt2iywTNU2Z3SsB/cKcbf7LeErwgRp5NuLK4yUQJthBdd6PDBjBEyoxAoGBAIwU\nPQBXQfhxv/kUB3ouF3X0t7Ka5Rgu8YeoTBiniu2S/oT/N5rABrXSGGm81/VkiZjU\nULG4y/D790o3KAcFu0EoErHNnzmmxnObTVjkPauj/jBYE6EL0dg2COWL3e70qFeQ\nnV7SE9cpzhBopwaHRUN59YP1GnMAhjMRMjsOOMKhAoGBALgCDopCQDQjQ+HQe7Zm\n8Yd/bmO+GIGwq4xwDX2BFFKZN+PcMIUVv4fpzkdMwFblRWYTfmtCZu2kyWYEfh0N\ntAQrHmZ2eQGmlnIAVIzlCsv5XBYuhRthaHNsv06VoSBByXIkCJ7gJz5nubKM1+SR\neO0vyUfS3g/mChrqS0WeR0Mj\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-fbsvc@naruto-zone-bot.iam.gserviceaccount.com",
  "client_id": "103615271888355731058",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40naruto-zone-bot.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}


try:
    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✅ Firebase Connected! (Full Sync Enabled)")
except Exception as e:
    print(f"❌ Firebase Error: {e}")
    db = None

bot_settings = {
    "admins": [6922039299],
    "panels": [], 
    "fw_groups": [], 
    "otp_link": "https://t.me/me",
    "main_channel": "https://t.me",
    "withdraw_on": True,
    "min_withdraw": 30.0,
    "otp_reward": 0.1,
    "service_otp_rates": {},
    "service_reward_enabled": {},
    "refer_reward": 0.2,
    "cooldown": 10,
    "num_req": 3,
    "num_share": 1, 
    "support_link": "",
    "w_methods": ["bKash", "Nagad"],
    "w_group": "", 
    
    "fj_on": False,
    "fj_channels": [],
    "bulk_auto_approve": False,
    "stex_keys": [],
    "voltx_keys": [],
    "zenex_keys": [],
    "shark_tokens": [],
    "shark_panel_on": False,
    "cr_tokens": [],
    "cr_panel_on": False,
    "flex_api_url": "",
    "flex_tokens": [],
    "flex_panel_on": False,
    "nexus_keys": [],
    "nexus_panel_on": False,
    "nexus_services": {},
    "panel_alert_on": True,
    "user_otp_notify": True,
    "no_match_alert_on": True,
    "user_otp_rates": {},
    "stex_services": {},
    "voltx_services": {},
    "zenex_services": {},
    "stex_search_countries": [],
    "premium_flags": {
        "1": {"char": "🇺🇸", "iso": "US", "name": "United States", "id": "5913463998522592692"},
        "880": {"char": "🇧🇩", "iso": "BD", "name": "Bangladesh", "id": "5911365056594973179"},
        "91": {"char": "🇮🇳", "iso": "IN", "name": "India", "id": "5913754823643107921"},
        "92": {"char": "🇵🇰", "iso": "PK", "name": "Pakistan", "id": "5913705895375672082"},
        "44": {"char": "🇬🇧", "iso": "GB", "name": "United Kingdom", "id": "5913443365499703513"}
    },
    "premium_apps": {
        "FACEBOOK": {"char": "🚫", "id": "5334807341109908955", "name": "Facebook"},
        "WHATSAPP": {"char": "🚫", "id": "5334759662677957452", "name": "WhatsApp"}
    },
    "custom_messages": DEFAULT_CUSTOM_MESSAGES.copy(),
    "rand_name_pass": ""
}

FS_KEYS = [
    "admins", "panels", "fw_groups", "otp_link", "main_channel", "withdraw_on", 
    "min_withdraw", "otp_reward", "service_otp_rates", "service_reward_enabled", "refer_reward", "cooldown", 
    "num_req", "num_share", "support_link", "w_methods", "w_group",
    "stex_keys", "voltx_keys", "zenex_keys", "shark_tokens", "shark_panel_on", "cr_tokens", "cr_panel_on", "flex_api_url", "flex_tokens", "flex_panel_on", "nexus_keys", "nexus_panel_on", "user_otp_rates",
    "stex_services", "voltx_services", "zenex_services", "nexus_services", "stex_search_countries",
    "fj_on", "fj_channels", "bulk_auto_approve",
    "panel_alert_on", "user_otp_notify", "no_match_alert_on", "rand_name_pass"
]

def get_service_reward(app_full_name, user_id=None):
    """Returns (reward_amount, is_enabled).
    Priority: per-user rate → per-service rate → global rate."""
    # 1. Per-user rate সবচেয়ে আগে চেক করো
    if user_id is not None:
        user_rates = bot_settings.get("user_otp_rates", {})
        uid_str = str(user_id)
        if uid_str in user_rates:
            return float(user_rates[uid_str]), True

    # 2. Per-service rate
    service_key = str(app_full_name).upper().strip()
    rates = bot_settings.get("service_otp_rates", {})
    enabled = bot_settings.get("service_reward_enabled", {})
    matched_key = None
    for k in rates:
        if k in service_key or service_key in k:
            matched_key = k
            break
    if matched_key:
        amount = float(rates.get(matched_key, bot_settings.get("otp_reward", 0.0)))
        is_on = enabled.get(matched_key, True)
        # BUG FIX: service rate 0.0 হলে global otp_reward-এ fallback করো
        if amount <= 0 and is_on:
            amount = float(bot_settings.get("otp_reward", 0.0))
        return amount, is_on

    # 3. Global fallback
    return float(bot_settings.get("otp_reward", 0.0)), True

def service_rates_keyboard():
    rates = bot_settings.get("service_otp_rates", {})
    enabled = bot_settings.get("service_reward_enabled", {})
    kb = []
    for srv, rate in rates.items():
        is_on = enabled.get(srv, True)
        tog_icon = "5192812028632274956" if is_on else "5318840353510408444"
        tog_style = "success" if is_on else "danger"
        tog_label = "ON" if is_on else "OFF"
        kb.append([
            {"text": f"{srv}: {rate} tk", "icon_custom_emoji_id": "5190576863226933563", "callback_data": f"dxa_srv_rate_{srv}", "style": "primary"},
            {"text": tog_label, "icon_custom_emoji_id": tog_icon, "callback_data": f"dxa_srv_tog_{srv}", "style": tog_style},
            {"text": "Del", "icon_custom_emoji_id": "5422557736330106570", "callback_data": f"dxa_del_srv_{srv}", "style": "danger"}
        ])
    kb.append([{"text": "Add New Service", "icon_custom_emoji_id": "5420323438508155202", "callback_data": "dxa_add_srv", "style": "success"}])
    kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "dxa_control", "style": "danger"}])
    return {"inline_keyboard": kb}

_panel_alert_sent = {}  # panel idx -> last alert time (avoid spam)

def _send_panel_alert(idx, p, msg):
    """Admin-কে panel alert পাঠায়, কিন্তু ৫ মিনিটে একবারের বেশি না।"""
    if not bot_settings.get("panel_alert_on", True):
        return
    now = time.time()
    if now - _panel_alert_sent.get(idx, 0) < 300:
        return
    _panel_alert_sent[idx] = now
    try:
        alert_text = f"⚠️ <b>Panel Alert</b>\n\n🔢 Panel #{idx+1}: <b>{p.get('name','?')}</b>\n\n{msg}\n\n🔄 Bot auto retry করছে..."
        send_message(OWNER_ID, alert_text)
        for admin_id in bot_settings.get("admins", []):
            if admin_id != OWNER_ID:
                try: send_message(admin_id, alert_text)
                except: pass
    except: pass

def _fetch_one_panel(idx, p):
    """Fetch OTP data from one panel. Returns list of parsed items, or empty list on error."""
    try:
        if p.get("type") == "Auto Captcha Panel":
            # FIX: consecutive empty response counter — session silently dead হলে force re-login
            empty_count = p.get("_empty_fetch_count", 0)
            if empty_count >= 30:  # ৩০ বার (≈৩০ সেকেন্ড) empty এলে session মরে গেছে ধরো
                print(f"🔄 [Panel #{idx} - {p.get('name','?')}] {empty_count} consecutive empty responses → force re-login")
                if idx in panel_sessions:
                    del panel_sessions[idx]
                p["_empty_fetch_count"] = 0
                p["last_login_attempt"] = 0  # cooldown bypass
                _send_panel_alert(idx, p, f"🔄 Panel #{idx} '{p.get('name','?')}' — {empty_count} বার empty response, force re-login করা হচ্ছে।")
            sess = panel_sessions.get(idx)
            if not sess:
                now = time.time()
                # FIX: cooldown 30s → 10s, faster retry
                if now - p.get("last_login_attempt", 0) < 10:
                    return []
                p["last_login_attempt"] = now
                success = attempt_auto_login(p, idx)
                save_db()
                if not success:
                    fail_count = p.get("_login_fail_count", 0) + 1
                    p["_login_fail_count"] = fail_count
                    print(f"⚠️ [Panel #{idx} - {p.get('name','?')}] Login failed (attempt #{fail_count})")
                    # ৩ বার fail হলে admin-কে alert পাঠাও
                    if fail_count >= 3:
                        _send_panel_alert(idx, p, f"❌ Login <b>{fail_count} বার fail</b> হয়েছে!\nOTP আসা বন্ধ আছে।\n\nLogin: <code>{p.get('login_url','?')}</code>")
                    return []
                else:
                    p["_login_fail_count"] = 0  # success হলে reset
                    p["_empty_fetch_count"] = 0
                sess = panel_sessions.get(idx)
            try:
                _cpt_login_url = p.get("login_url", "").strip()
                if not _cpt_login_url.startswith("http"): _cpt_login_url = "http://" + _cpt_login_url
                _cpt_msg_link = p.get("msg_link", "").strip()
                if not _cpt_msg_link.startswith("http") and _cpt_msg_link != "": _cpt_msg_link = "http://" + _cpt_msg_link
                _cpt_check_url = _cpt_msg_link if _cpt_msg_link else f"{_cpt_login_url.split('/login')[0]}/client/SMSCDRStats"
                parsed_data, res_text = fetch_cpt_panel_cdrs(p, sess, _cpt_check_url)
                p["login_status"] = "✅ Active & Fetching"
                p["_login_fail_count"] = 0  # success হলে fail count reset
                # FIX: data এলে empty counter reset, না এলে বাড়াও
                if parsed_data:
                    p["_empty_fetch_count"] = 0
                else:
                    p["_empty_fetch_count"] = p.get("_empty_fetch_count", 0) + 1
                return parsed_data
            except Exception as e:
                print(f"⚠️ [Panel #{idx} - {p.get('name','?')}] Fetch failed: {e}")
                p["login_status"] = f"❌ Session Expired (Retrying...) [{e}]"
                if idx in panel_sessions: del panel_sessions[idx]
                # FIX: session expire হলে সাথে সাথে admin alert
                _send_panel_alert(idx, p, f"🔐 Session expire হয়েছে!\n10 সেকেন্ডে auto re-login করবে।\n\nError: <code>{str(e)[:80]}</code>")
                save_db()
                return []
        elif p.get("api_url") or p.get("full_api_url"):
            full_url = p.get("full_api_url", "").strip()
            url = p.get("api_url", "").strip()
            token = p.get("token", "").strip()
            if not full_url and not url: return []
            urls_to_try = []
            if full_url:
                urls_to_try.append(full_url)
            else:
                if "{token}" in url or "{key}" in url:
                    urls_to_try.append(url.replace("{token}", token).replace("{key}", token))
                elif "token=" in url or "key=" in url:
                    urls_to_try.append(url)
                else:
                    sep = '&' if '?' in url else '?'
                    urls_to_try.append(f"{url}{sep}token={token}")
                    urls_to_try.append(f"{url}{sep}key={token}&start=0")
                    urls_to_try.append(f"{url}{sep}key={token}")
            parsed_data = []
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
            for try_url in urls_to_try:
                try:
                    res = requests.get(try_url, headers=headers, timeout=8)
                    parsed_data = parse_panel_response(res.text, p)
                    if parsed_data:
                        if not full_url and try_url != url and token:
                            p["api_url"] = try_url.replace(token, "{token}")
                            save_db()
                        break
                except: continue
            return parsed_data
        return []
    except Exception as e:
        print(f"⚠️ [Panel #{idx} - {p.get('name','?')}] _fetch_one_panel crashed: {e}")
        return []

number_batches = {}
used_numbers_list = []
stex_assigned_numbers = {}
voltx_assigned_numbers = {}
zenex_assigned_numbers = {}
nexus_assigned_numbers = {}
batch_assigned_numbers = {}          # local batch (Shark Panel upload) number → chat_id, restart-safe
_assigned_lock = threading.RLock()   # guards all assigned dicts
STEX_BASE_URL = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api"
VOLTX_BASE_URL = "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api"
ZENEX_BASE_URL = "https://api.zenexnetwork.com"
SHARK_API_URL = "http://139.99.62.188/crapi/sha/viewstats"
CR_API_URL = "http://147.135.212.197/crapi/had/viewstats"

def _try_stex_key(api_key, query):
    """Single Stex key try — returns (num_str, api_key) or (None, None)."""
    try:
        headers = {"mauthapi": api_key}
        res = requests.post(f"{STEX_BASE_URL}/getnum", json={"rid": query}, headers=headers, timeout=8)
        resp_data = res.json()
        if resp_data.get("meta", {}).get("code") == 200 and resp_data.get("data"):
            num_str = str(resp_data["data"].get("no_plus_number", "")).replace("+", "")
            if not num_str:
                num_str = str(resp_data["data"].get("national_number", ""))
            if num_str:
                return (num_str, api_key)
    except:
        pass
    return (None, None)

def _fetch_stex_parallel(query, keys):
    """সব Stex key একসাথে parallel এ try করে, যে আগে success দেয় সেটা নেয়।"""
    if not keys:
        return (None, None)
    with ThreadPoolExecutor(max_workers=len(keys)) as ex:
        futures = {ex.submit(_try_stex_key, k, query): k for k in keys}
        for f in as_completed(futures, timeout=9):
            try:
                result = f.result()
                if result[0]:
                    return result
            except:
                pass
    return (None, None)

def _try_voltx_key(api_key, query):
    """Single Voltx key try — returns (num_str, api_key) or (None, None)."""
    try:
        headers = {"mauthapi": api_key}
        res = requests.post(f"{VOLTX_BASE_URL}/getnum", json={"rid": query}, headers=headers, timeout=8)
        resp_data = res.json()
        if resp_data.get("meta", {}).get("code") == 200 and resp_data.get("data"):
            num_str = str(resp_data["data"].get("no_plus_number", "")).replace("+", "")
            if not num_str:
                num_str = str(resp_data["data"].get("national_number", ""))
            if num_str:
                return (num_str, api_key)
    except:
        pass
    return (None, None)

def _fetch_voltx_parallel(query, keys):
    """সব Voltx key একসাথে parallel এ try করে, যে আগে success দেয় সেটা নেয়।"""
    if not keys:
        return (None, None)
    with ThreadPoolExecutor(max_workers=len(keys)) as ex:
        futures = {ex.submit(_try_voltx_key, k, query): k for k in keys}
        for f in as_completed(futures, timeout=9):
            try:
                result = f.result()
                if result[0]:
                    return result
            except:
                pass
    return (None, None)

def _try_zenex_key(api_key, range_):
    """Single Zenex key try — returns (num_str, number_id, api_key) or (None, None, None)."""
    try:
        headers = {"mapikey": api_key, "Content-Type": "application/json"}
        res = requests.post(f"{ZENEX_BASE_URL}/v1/getnum", json={"range": range_, "is_national": False, "remove_plus": False}, headers=headers, timeout=8)
        resp_data = res.json()
        num_str, number_id = _parse_zenex_getnum(resp_data)
        if num_str:
            return (num_str, number_id, api_key)
    except:
        pass
    return (None, None, None)


def _fetch_zenex_parallel(range_, keys):
    """সব Zenex key একসাথে parallel এ try করে, যে আগে success দেয় সেটা নেয়।
    Returns (num_str, number_id, api_key) or (None, None, None)."""
    if not keys:
        return (None, None, None)
    with ThreadPoolExecutor(max_workers=len(keys)) as ex:
        futures = {ex.submit(_try_zenex_key, k, range_): k for k in keys}
        for f in as_completed(futures, timeout=9):
            try:
                result = f.result()
                if result[0]:
                    return result
            except:
                pass
    return (None, None, None)


def _try_nexus_key(api_key, range_, service_sid="any"):
    """Single Nexus-X key try — POST /api/v1/numbers থেকে number allocate করে।
    Returns (num_str, number_id, api_key) or (None, None, None)."""
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "range": range_,
            "sid": service_sid if service_sid else "any",
            "no_plus": False,
            "national": False
        }
        res = requests.post("https://v2.nexus-x.site/api/v1/numbers", json=payload, headers=headers, timeout=12)
        if res.status_code in (200, 201):
            data = res.json()
            if data.get("ok") or data.get("number"):
                num_raw = data.get("number", "")
                num_str = str(num_raw).replace("+", "").replace(" ", "").replace("-", "").strip()
                number_id = data.get("id", "")
                if num_str and number_id:
                    return (num_str, number_id, api_key)
    except:
        pass
    return (None, None, None)


def _fetch_nexus_parallel(range_, service_sid, keys):
    """সব Nexus-X key একসাথে parallel এ try করে, যে আগে success দেয় সেটা নেয়।
    Returns (num_str, number_id, api_key) or (None, None, None)."""
    if not keys:
        return (None, None, None)
    with ThreadPoolExecutor(max_workers=max(1, len(keys))) as ex:
        futures = {ex.submit(_try_nexus_key, k, range_, service_sid): k for k in keys}
        for f in as_completed(futures, timeout=15):
            try:
                result = f.result()
                if result[0]:
                    return result
            except:
                pass
    return (None, None, None)


def _smart_fetch_one(query_prefix, zenex_range, owner_id):
    """
    Switching system: Local Stock skip (caller handles it).
    Tries: Stex → VoltexSMS → Zenex in order.
    Returns (num_str, source, number_id, used_key)
      source = "stex" | "voltx" | "zenex"
      number_id / used_key only meaningful for zenex.
    """
    # ── Step A: Stex ──────────────────────────────────────────
    stex_keys = bot_settings.get("stex_keys", [])
    if stex_keys:
        num_str, used_key = _fetch_stex_parallel(query_prefix, stex_keys)
        if num_str:
            stex_assigned_numbers[num_str] = owner_id
            return (num_str, "stex", None, used_key)

    # ── Step B: VoltexSMS ─────────────────────────────────────
    voltx_keys = bot_settings.get("voltx_keys", [])
    if voltx_keys:
        num_str, used_key = _fetch_voltx_parallel(query_prefix, voltx_keys)
        if num_str:
            voltx_assigned_numbers[num_str] = owner_id
            return (num_str, "voltx", None, used_key)

    # ── Step C: Zenex ─────────────────────────────────────────
    zenex_keys = bot_settings.get("zenex_keys", [])
    if zenex_keys:
        num_str, number_id, used_key = _fetch_zenex_parallel(zenex_range, zenex_keys)
        if num_str:
            zenex_assigned_numbers[num_str] = owner_id
            return (num_str, "zenex", number_id, used_key)

    return (None, None, None, None)

total_uploaded_stats = 0
total_assigned_stats = 0
processed_otps = set()  # Fixed: was deque, but .add() is a set method
_PROCESSED_OTPS_MAX = 10000  # memory cap
_otp_lock = threading.Lock()  # guards processed_otps for thread-safe check+add

def _safe_add_otp(uid):
    """Thread-safe add to processed_otps with size cap."""
    with _otp_lock:
        if uid in processed_otps:
            return False   # already seen
        if len(processed_otps) >= _PROCESSED_OTPS_MAX:
            # Evict oldest half under the lock (snapshot to avoid RuntimeError)
            to_remove = list(processed_otps)[:_PROCESSED_OTPS_MAX // 2]
            for item in to_remove:
                processed_otps.discard(item)
        processed_otps.add(uid)
        return True
recent_traffic = []
user_banned_cache = {}

# Active HTTP sessions for Auto Captcha Panels
panel_sessions = {}

# 🌟 sAjaxSource (AJAX/DataTable) এবং Fallback HTML Parser Helper Function
def _is_session_dead(html_text):
    """
    Panel response দেখে session expire হয়েছে কিনা বোঝে।
    Reference bot-এর মতো "login"/"signin" check + extra patterns।
    """
    lower = html_text.lower()
    # Reference bot-এর exact check (সবচেয়ে reliable)
    has_login_url = "login" in lower or "signin" in lower
    # Extra patterns for common login pages
    has_password_field = bool(re.search(r'type=["\'\'?password["\'\'?]', lower))
    login_keywords = [
        "sign in to your account", "please sign in", "welcome back!",
        "forgot password", "forgot your password",
        "login to your account", "log in to your account",
        "remember me", "keep me logged in",
        "আপনার অ্যাকাউন্টে লগইন", "লগইন করুন",
        "enter your password", "enter password",
    ]
    has_login_text = any(kw in lower for kw in login_keywords)
    # session alive indicators
    alive_keywords = ["logout", "log out", "sign out", "dashboard", "sms report", "cdrs", "aadata",
                       "nav-bar", "navbar", "topbar", "side-menu", "sidemenu",
                       "welcome,", "logged in as", "profile", "admin panel", "control panel"]
    is_alive = any(kw in lower for kw in alive_keywords)
    return (has_login_url or has_password_field or has_login_text) and not is_alive

def fetch_cpt_panel_cdrs(p, session, check_url):
    res = session.get(check_url, timeout=15)
    html_text = res.text
    
    # সেশন শেষ হয়েছে বা লগইন পেজে রিডাইরেক্ট করেছে কি না তা চেক করা
    _lower_html = html_text.lower()
    if _is_session_dead(html_text):
        raise Exception("Session expired")
        
    soup = BeautifulSoup(html_text, 'html.parser')
    s_ajax_source = ""
    for script in soup.find_all("script"):
        script_text = script.string or ""
        match = re.search(r'"?(?:sAjaxSource|ajax|url)"?\s*:\s*"([^"]+)"', script_text)
        if match:
            s_ajax_source = match.group(1)
            break
            
    results = []
    
    n_col_name = p.get("num_col_name", "number").lower()
    m_col_name = p.get("msg_col_name", "message").lower()
    n_idx = int(p.get("num_col_idx", 1)) - 1 if p.get("num_col_idx") else 1
    m_idx = int(p.get("msg_col_idx", 2)) - 1 if p.get("msg_col_idx") else 2

    # FIX: AJAX/DataTables path আগে num/msg column index সরাসরি user-এর দেওয়া settings
    # থেকে নিতো, HTML table-এর header (thead) এর সাথে মিলিয়ে ঠিক করতো না -- অথচ নিচের
    # non-AJAX backup logic-এ এই header-matching ছিল। ফলে যেসব panel-এর table-এ extra
    # column থাকে (test/setup row-এ না থাকা কিন্তু আসল running number-এর row-এ থাকা
    # Action/Client column ইত্যাদি), সেখানে ভুল column থেকে number/message পড়ার কারণে
    # running number-এর OTP miss হয়ে যেত, যদিও test connect ঠিকই কাজ করতো (কারণ test
    # row-টা কাকতালীয়ভাবে সঠিক column-এ পড়ে যেত)। এখন AJAX path-এও HTML table header
    # text মিলিয়ে সঠিক column index বের করা হচ্ছে।
    for _table in soup.find_all('table'):
        _header_rows = _table.find_all('tr')
        if not _header_rows:
            continue
        _header_cells = _header_rows[0].find_all(['th', 'td'])
        for _i, _cell in enumerate(_header_cells):
            _c_text = _cell.get_text(strip=True).lower()
            if n_col_name in _c_text: n_idx = _i
            if m_col_name in _c_text: m_idx = _i
        break

    # ৫.১ যদি sAjaxSource AJAX লিংক পাওয়া যায়
    if s_ajax_source:
        baseUrl = p.get("login_url", "").split("/client")[0].split("/login")[0].strip()
        if not baseUrl.startswith("http"):
            baseUrl = "http://" + baseUrl
            
        full_ajax_url = ""
        if s_ajax_source.startswith("http"):
            full_ajax_url = s_ajax_source
        elif s_ajax_source.startswith("/"):
            full_ajax_url = f"{baseUrl}{s_ajax_source}"
        else:
            last_slash_idx = check_url.rfind("/")
            current_dir = check_url[:last_slash_idx]
            full_ajax_url = f"{current_dir}/{s_ajax_source}"

        if "iDisplayLength" not in full_ajax_url:
            query_params = "sEcho=1&iColumns=7&iDisplayStart=0&iDisplayLength=250&sSearch=&iSortingCols=1&iSortCol_0=0&sSortDir_0=desc"
            divider = "&" if "?" in full_ajax_url else "?"
            full_ajax_url += f"{divider}{query_params}"

        ajax_headers = {
            "Referer": check_url,
            "X-Requested-With": "XMLHttpRequest"
        }
        
        ajax_res = session.get(full_ajax_url, headers=ajax_headers, timeout=15)
        data_dict = ajax_res.json()
        # 🌟 FIX: পুরনো DataTables "aaData" key ব্যবহার করে, কিন্তু নতুন ভার্সনের প্যানেল
        # "data" key দেয় — শুধু "aaData" চেক করলে rows সবসময় খালি আসতো এবং OTP কখনো
        # forward হতো না। এখন দুটোই চেক করা হচ্ছে।
        rows = data_dict.get("aaData") or data_dict.get("data") or []
        for row_val in rows:
            if isinstance(row_val, dict):
                row_val = list(row_val.values())
            if not isinstance(row_val, list):
                continue
                
            if len(row_val) < max(n_idx, m_idx) + 1:
                continue
                
            num_val = row_val[n_idx] if (0 <= n_idx < len(row_val)) else row_val[2]
            msg_val = row_val[m_idx] if (0 <= m_idx < len(row_val)) else row_val[4]
            # 🌟 FIX: msg_val/num_val সবসময় str না ও হতে পারে (int/None) — সরাসরি len()/regex
            # চালালে TypeError হয়ে পুরো fetch silently ব্যর্থ হয়ে যেত (except: pass এ চাপা পড়তো)।
            num_val = "" if num_val is None else str(num_val)
            msg_val = "" if msg_val is None else BeautifulSoup(str(msg_val), 'html.parser').get_text(separator=" ", strip=True)
            
            clean_num = re.sub(r'\D', '', num_val)
            if clean_num and 5 <= len(clean_num) <= 18:
                otp = extract_otp_code(msg_val)
                if otp and len(msg_val) > 4:
                    results.append({"number": clean_num, "message": msg_val, "otp": otp})
                    
    else:
        # ৫.২ ডাইরেক্ট HTML টেবিল থেকে রিড করার ব্যাকআপ লজিক
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if not rows: continue
            
            final_n_idx = n_idx
            final_m_idx = m_idx
            
            header_cells = rows[0].find_all(['th', 'td'])
            for i, cell in enumerate(header_cells):
                c_text = cell.get_text(strip=True).lower()
                if n_col_name in c_text: final_n_idx = i
                if m_col_name in c_text: final_m_idx = i

            for row in rows:
                cols = row.find_all(['td', 'th'])
                if all(c.name == 'th' for c in cols): continue
                
                if len(cols) > max(final_n_idx, final_m_idx):
                    num_text = cols[final_n_idx].get_text(separator=" ", strip=True)
                    msg_text = cols[final_m_idx].get_text(separator=" ", strip=True)
                    
                    clean_num = re.sub(r'\D', '', num_text)
                    if clean_num and 5 <= len(clean_num) <= 18:
                        otp = extract_otp_code(msg_text)
                        if otp and len(msg_text) > 4:
                            results.append({"number": clean_num, "message": msg_text, "otp": otp})
                            
    return results, html_text

# Track active number sessions to expire them automatically
user_active_sessions = {}

# Number-button status icons: waiting until an OTP arrives, then received.
WAITING_NUMBER_EMOJI_ID = "5386367538735104399"
OTP_RECEIVED_NUMBER_EMOJI_ID = "5936067938955039275"

FS_CACHE_FILE = os.path.join(_BOT_DIR, "fs_cache.json")

def _save_fs_cache():
    """FS_KEYS গুলো local file এ cache করে রাখে — Firestore down থাকলে fallback হিসেবে কাজ করে।"""
    try:
        cache = {k: bot_settings[k] for k in FS_KEYS if k in bot_settings}
        with open(FS_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"⚠️ FS cache save error: {e}")

def _load_fs_cache():
    """Firestore load না হলে local cache থেকে FS_KEYS load করে।"""
    if not os.path.exists(FS_CACHE_FILE):
        return False
    try:
        with open(FS_CACHE_FILE, "r", encoding="utf-8") as f:
            cache = json.load(f)
        for k in FS_KEYS:
            if k in cache:
                bot_settings[k] = cache[k]
        print("⚠️ Firestore unavailable — local cache থেকে settings load হয়েছে!")
        return True
    except Exception as e:
        print(f"⚠️ FS cache load error: {e}")
        return False

def load_db():
    global bot_settings, number_batches, used_numbers_list, total_uploaded_stats, total_assigned_stats, recent_traffic, stex_assigned_numbers, voltx_assigned_numbers, zenex_assigned_numbers, nexus_assigned_numbers, batch_assigned_numbers
    # 🌟 Quota বাঁচাতে: settings/panels/tokens ইত্যাদি (FS_KEYS) আর Firestore-এ যায় না —
    # শুধু local file (fs_cache.json)-এ save/load হয়। Firestore শুধু 'users' এবং
    # 'withdrawals' collection-এর জন্যই ব্যবহার হয় (আসল user data), তাই quota এখন
    # অনেক কম খরচ হবে।
    _load_fs_cache()

    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                data = json.load(f)
                saved_settings = data.get("bot_settings", {})
                for key, val in saved_settings.items():
                    if key not in FS_KEYS:
                        if key == "custom_messages":
                            for m_key, m_val in val.items():
                                bot_settings["custom_messages"][m_key] = m_val
                        else:
                            bot_settings[key] = val
                        
                for m_key, m_val in DEFAULT_CUSTOM_MESSAGES.items():
                    if m_key not in bot_settings["custom_messages"]:
                        bot_settings["custom_messages"][m_key] = m_val
                        
                number_batches = data.get("number_batches", {})
                used_numbers_list = data.get("used_numbers_list", [])
                total_uploaded_stats = data.get("total_uploaded_stats", 0)
                total_assigned_stats = data.get("total_assigned_stats", 0)
                recent_traffic = data.get("recent_traffic", [])
                stex_assigned_numbers = data.get("stex_assigned_numbers", {})
                voltx_assigned_numbers = data.get("voltx_assigned_numbers", {})
                zenex_assigned_numbers = data.get("zenex_assigned_numbers", {})
                nexus_assigned_numbers = data.get("nexus_assigned_numbers", {})
                batch_assigned_numbers = data.get("batch_assigned_numbers", {})
            print("✅ Local Stock/UI DB Loaded Successfully!")
        except Exception as e:
            print(f"❌ Error loading local DB: {e}")

def save_local_db():
    local_data = {
        "bot_settings": {k: v for k, v in bot_settings.items() if k not in FS_KEYS},
        "number_batches": number_batches,
        "used_numbers_list": used_numbers_list,
        "total_uploaded_stats": total_uploaded_stats,
        "total_assigned_stats": total_assigned_stats,
        "recent_traffic": recent_traffic,
        "stex_assigned_numbers": stex_assigned_numbers,
        "voltx_assigned_numbers": voltx_assigned_numbers,
        "zenex_assigned_numbers": zenex_assigned_numbers,
        "nexus_assigned_numbers": nexus_assigned_numbers,
        "batch_assigned_numbers": batch_assigned_numbers
    }
    try:
        with open(DB_FILE, "w", encoding='utf-8') as f:
            json.dump(local_data, f, indent=4)
    except Exception as e:
        pass

def _sync_fs():
    # 🌟 Quota বাঁচাতে: settings আর Firestore-এ sync হয় না, শুধু local file-এ থাকে।
    _save_fs_cache()

def save_db():
    save_local_db()
    # settings (FS_KEYS) এখন শুধু local file-এ synchronously save হয় —
    # Firestore-এ আর কোনো write যায় না, শুধু 'users'/'withdrawals' collection-এর
    # জন্যই Firestore ব্যবহার হয়।
    _save_fs_cache()

load_db()

user_states = {}
temp_data = {}
user_cooldowns = {}
pending_withdrawals = {}
pending_bulk_requests = {}  # req_id -> {user_id, service, country, full_name, ranges, status}
bulk_sessions = {}           # user_id -> {nums: [...], num_to_ids: {num: (nid, key)}, service, country}
support_msg_map = {}         # (admin_id, admin_msg_id) -> user_id  [Live Support chat mapping]

# ==========================================
# Telegram API & Helpers
# ==========================================
tg_session = requests.Session() # 🌟 Keep-Alive Connection (Makes bot 10x faster)

def api_call(method, payload=None):
    url = f"{BASE_URL}/{method}"
    try:
        # 🌟 Added timeout to prevent hanging!
        res = tg_session.post(url, json=payload, timeout=15)
        return res.json()
    except Exception as e:
        return {}

_BOLD_ASCII = str.maketrans(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789"
)

_PLAIN_BOLD_UNICODE = str.maketrans(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789",
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789"
)

def _bold_button_text(value):
    """Render ASCII menu labels in Telegram-compatible bold Unicode."""
    return str(value).translate(_BOLD_ASCII)

def _plain_button_text(value):
    """Normalize bold Unicode keyboard labels back to plain text for routing."""
    # NFKC handles both mathematical bold (𝐆) and sans-serif bold (𝗚).
    return unicodedata.normalize("NFKC", str(value)).translate(_PLAIN_BOLD_UNICODE)

def _bold_keyboard_markup(reply_markup):
    """Bold every Telegram keyboard button label without changing its actions."""
    if not isinstance(reply_markup, dict):
        return reply_markup
    markup = dict(reply_markup)
    for key in ("keyboard", "inline_keyboard"):
        rows = markup.get(key)
        if isinstance(rows, list):
            new_rows = []
            for row in rows:
                if isinstance(row, list):
                    new_row = []
                    for button in row:
                        if isinstance(button, dict):
                            button_copy = dict(button)
                            if "text" in button_copy:
                                button_copy["text"] = _bold_button_text(button_copy["text"])
                            new_row.append(button_copy)
                        else:
                            new_row.append(button)
                    new_rows.append(new_row)
                else:
                    new_rows.append(row)
            markup[key] = new_rows
    return markup

def send_message(chat_id, text, reply_markup=None, parse_mode="HTML"):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode, "disable_web_page_preview": True}
    if reply_markup: payload["reply_markup"] = _bold_keyboard_markup(reply_markup)
    return api_call("sendMessage", payload)

def send_photo(chat_id, photo_url_or_file_id, caption="", reply_markup=None, parse_mode="HTML"):
    payload = {"chat_id": chat_id, "photo": photo_url_or_file_id, "caption": caption, "parse_mode": parse_mode}
    if reply_markup: payload["reply_markup"] = _bold_keyboard_markup(reply_markup)
    return api_call("sendPhoto", payload)

def edit_message(chat_id, message_id, text, reply_markup=None, parse_mode="HTML"):
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": parse_mode, "disable_web_page_preview": True}
    if reply_markup: payload["reply_markup"] = _bold_keyboard_markup(reply_markup)
    return api_call("editMessageText", payload)

def edit_message_reply_markup(chat_id, message_id, reply_markup):
    """Update only the inline keyboard, preserving the assignment caption."""
    return api_call("editMessageReplyMarkup", {
        "chat_id": chat_id,
        "message_id": message_id,
        "reply_markup": _bold_keyboard_markup(reply_markup),
    })

def delete_message(chat_id, message_id):
    return api_call("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

def answer_callback(callback_id, text="", show_alert=False):
    api_call("answerCallbackQuery", {"callback_query_id": callback_id, "text": text, "show_alert": show_alert})

def send_document(chat_id, filename, text_content):
    url = f"{BASE_URL}/sendDocument"
    files = {'document': (filename, text_content)}
    data = {'chat_id': chat_id}
    try: requests.post(url, data=data, files=files)
    except: pass

# 🌟 Local User List to completely remove Firebase Read Costs!
all_known_users = set()

USERS_LIST_FILE = os.path.join(_BOT_DIR, "users_list.json")

def sync_users_list():
    global all_known_users
    try:
        if os.path.exists(USERS_LIST_FILE):
            with open(USERS_LIST_FILE, "r") as f:
                all_known_users = set(json.load(f))
        if not all_known_users and db:
            for doc in db.collection('users').select([]).stream():
                all_known_users.add(doc.id)
            with open(USERS_LIST_FILE, "w") as f:
                json.dump(list(all_known_users), f)
    except: pass

threading.Thread(target=sync_users_list, daemon=True).start()

def _save_users_list():
    try:
        with open(USERS_LIST_FILE, "w") as f:
            json.dump(list(all_known_users), f)
    except: pass

def register_user_local(uid):
    uid_str = str(uid)
    if uid_str not in all_known_users:
        all_known_users.add(uid_str)
        # 🌟 Non-blocking background save (Prevents lag)
        threading.Thread(target=_save_users_list, daemon=True).start()

def broadcast_copymessage(from_chat_id, msg_id):
    success = 0
    failed = 0
    users = list(all_known_users)
    
    # 🌟 Dedicated Connection Pool for Broadcast (Fixes Port Exhaustion & Network Lag)
    b_session = requests.Session()
    url = f"{BASE_URL}/copyMessage"
    
    for user_id in users:
        payload = {"chat_id": user_id, "from_chat_id": from_chat_id, "message_id": msg_id}
        try:
            res = b_session.post(url, json=payload, timeout=5).json()
            if res.get("ok"): success += 1
            else: failed += 1
        except:
            failed += 1
        time.sleep(0.035) # Safe speed (28 msgs/sec) to prevent Telegram Ban
        
    send_message(from_chat_id, render_body_text(f"📢 <b>Broadcast Completed!</b>\n✅ Success: {success}\n❌ Failed: {failed}\n👥 Total Sent: {len(users)}"))

def render_body_text(text):
    if not text: return str(text)
    parts = re.split(r'(<tg-emoji.*?</tg-emoji>)', str(text))
    for i in range(len(parts)):
        if not parts[i].startswith('<tg-emoji'):
            for normal_emj, prem_id in GLOBAL_BODY_EMOJIS.items():
                if normal_emj in parts[i]:
                    parts[i] = parts[i].replace(normal_emj, f'<tg-emoji emoji-id="{prem_id}">{normal_emj}</tg-emoji>')
    return "".join(parts)

def extract_premium_html(msg):
    text = msg.get("text", msg.get("caption", ""))
    entities = msg.get("entities", msg.get("caption_entities", []))
    if not entities: return text
    try:
        b_text = text.encode('utf-16-le')
        c_entities = [e for e in entities if e.get("type") == "custom_emoji"]
        c_entities.sort(key=lambda x: x["offset"], reverse=True)
        for ent in c_entities:
            offset = ent["offset"] * 2
            length = ent["length"] * 2
            eid = ent["custom_emoji_id"]
            emoji_char = b_text[offset:offset+length].decode('utf-16-le')
            html_tag = f'<tg-emoji emoji-id="{eid}">{emoji_char}</tg-emoji>'
            replacement = html_tag.encode('utf-16-le')
            b_text = b_text[:offset] + replacement + b_text[offset+length:]
        return b_text.decode('utf-16-le')
    except Exception as e:
        return text 

# Phone prefix → ISO fallback table (all world codes)
PHONE_CODE_TO_ISO = {
    "1":"US","7":"RU","20":"EG","27":"ZA","30":"GR","31":"NL","32":"BE","33":"FR",
    "34":"ES","36":"HU","39":"IT","40":"RO","41":"CH","43":"AT","44":"GB","45":"DK",
    "46":"SE","47":"NO","48":"PL","49":"DE","51":"PE","52":"MX","53":"CU","54":"AR",
    "55":"BR","56":"CL","57":"CO","58":"VE","60":"MY","61":"AU","62":"ID","63":"PH",
    "64":"NZ","65":"SG","66":"TH","81":"JP","82":"KR","84":"VN","86":"CN","90":"TR",
    "91":"IN","92":"PK","93":"AF","94":"LK","95":"MM","98":"IR","212":"MA","213":"DZ",
    "216":"TN","218":"LY","220":"GM","221":"SN","222":"MR","223":"ML","224":"GN",
    "225":"CI","226":"BF","227":"NE","228":"TG","229":"BJ","230":"MU","231":"LR",
    "232":"SL","233":"GH","234":"NG","235":"TD","236":"CF","237":"CM","238":"CV",
    "239":"ST","240":"GQ","241":"GA","242":"CG","243":"CD","244":"AO","245":"GW",
    "248":"SC","249":"SD","250":"RW","251":"ET","252":"SO","253":"DJ","254":"KE",
    "255":"TZ","256":"UG","257":"BI","258":"MZ","260":"ZM","261":"MG","263":"ZW",
    "264":"NA","265":"MW","266":"LS","267":"BW","268":"SZ","269":"KM","291":"ER",
    "297":"AW","298":"FO","299":"GL","350":"GI","351":"PT","352":"LU","353":"IE",
    "354":"IS","355":"AL","356":"MT","357":"CY","358":"FI","359":"BG","370":"LT",
    "371":"LV","372":"EE","373":"MD","374":"AM","375":"BY","376":"AD","377":"MC",
    "380":"UA","381":"RS","385":"HR","386":"SI","387":"BA","389":"MK","420":"CZ",
    "421":"SK","500":"FK","501":"BZ","502":"GT","503":"SV","504":"HN","505":"NI",
    "506":"CR","507":"PA","509":"HT","590":"GP","591":"BO","592":"GY","593":"EC",
    "595":"PY","597":"SR","598":"UY","670":"TL","673":"BN","674":"NR","675":"PG",
    "676":"TO","677":"SB","678":"VU","679":"FJ","680":"PW","685":"WS","686":"KI",
    "687":"NC","688":"TV","689":"PF","691":"FM","692":"MH","850":"KP","852":"HK",
    "853":"MO","855":"KH","856":"LA","880":"BD","886":"TW","960":"MV","961":"LB",
    "962":"JO","963":"SY","964":"IQ","965":"KW","966":"SA","967":"YE","968":"OM",
    "970":"PS","971":"AE","972":"IL","973":"BH","974":"QA","975":"BT","976":"MN",
    "977":"NP","992":"TJ","993":"TM","994":"AZ","995":"GE","996":"KG","998":"UZ"
}

def mask_num_for_group(num):
    """OTP group-এ masked number: +2250❖ROMAN❖2223"""
    clean = num.replace(" ", "")
    prefix = "+" if clean.startswith("+") else ""
    digits = clean[1:] if prefix else clean
    if len(digits) > 9:
        return f"{prefix}{digits[:4]}❖ROMAN❖{digits[-4:]}"
    elif len(digits) > 5:
        return f"{prefix}{digits[:4]}❖ROMAN❖{digits[-4:]}"
    return clean

def get_flag_info_from_num(num):
    clean = num.replace("+", "").replace(" ", "")
    sorted_codes = sorted(bot_settings.get("premium_flags", {}).keys(), key=len, reverse=True)
    for code in sorted_codes:
        if clean.startswith(code):
            data = bot_settings["premium_flags"][code]
            return data["char"], data.get("iso", "XX"), data.get("id")
    # Fallback: global phone prefix lookup (3-digit → 2-digit → 1-digit)
    for plen in [3, 2, 1]:
        iso = PHONE_CODE_TO_ISO.get(clean[:plen])
        if iso:
            return "🌍", iso, None
    return "🌍", "XX", None

def get_flag_and_code(num):
    char, iso, _ = get_flag_info_from_num(num)
    return char, iso

def get_flag_info_html(num_or_iso):
    if len(num_or_iso) == 2:
        for code, data in bot_settings.get("premium_flags", {}).items():
            if data.get("iso") == num_or_iso:
                eid = data.get("id")
                char = data.get("char")
                if eid: return f'<tg-emoji emoji-id="{eid}">{char}</tg-emoji>'
                return char
        return "🌍"
        
    char, _, eid = get_flag_info_from_num(num_or_iso)
    if eid:
        return f'<tg-emoji emoji-id="{eid}">{char}</tg-emoji>'
    return char

def get_country_name(iso):
    """ISO code থেকে দেশের পূর্ণ নাম বের করে (premium_flags-এর name field)।"""
    if not iso:
        return "??"
    for code, data in bot_settings.get("premium_flags", {}).items():
        if data.get("iso", "").upper() == iso.upper():
            return data.get("name", iso.upper())
    return iso.upper()


def mask_number(num):
    clean = num.replace("+", "").replace(" ", "")
    if len(clean) > 6: return f"{clean[:3]}XXX{clean[-3:]}"
    elif len(clean) > 2: return f"{clean[:1]}XXX{clean[-1:]}"
    return clean

_LANG_NAMES = {
    "#EN": "English", "#AR": "Arabic", "#BN": "Bengali", "#HI": "Hindi",
    "#RU": "Russian", "#ZH": "Chinese", "#TR": "Turkish", "#ES": "Spanish",
    "#FR": "French", "#DE": "German", "#PT": "Portuguese", "#PA": "Punjabi",
    "#GU": "Gujarati", "#OR": "Odia", "#TA": "Tamil", "#TE": "Telugu",
    "#KN": "Kannada", "#ML": "Malayalam", "#MR": "Marathi", "#UR": "Urdu",
    "#FA": "Persian", "#TH": "Thai", "#JA": "Japanese", "#KO": "Korean",
    "#IT": "Italian", "#NL": "Dutch", "#PL": "Polish", "#VI": "Vietnamese",
    "#ID": "Indonesian", "#MS": "Malay", "#SI": "Sinhala", "#MY": "Burmese",
    "#KM": "Khmer", "#LO": "Lao", "#KA": "Georgian", "#AM": "Amharic",
    "#HE": "Hebrew", "#UK": "Ukrainian",
}

def build_otp_inbox(app_full_name, prem_app_html, char, iso, display_num, lang, otp, reward=0, reward_on=False):
    """Build OTP inbox message + keyboard in new design:
       {premium_flag} {ISO_short} {service_logo} {number}
       [Number Bot]  [Main Channel]
    """
    flag_html = get_flag_info_html(iso) if iso else char
    iso_short = iso.upper() if iso and iso != "XX" else (PHONE_CODE_TO_ISO.get(display_num.replace("+","")[:3]) or PHONE_CODE_TO_ISO.get(display_num.replace("+","")[:2]) or iso or "??")
    masked_num = mask_num_for_group(display_num)
    msg = render_body_text(f"{flag_html} {iso_short} {prem_app_html} {masked_num}")
    kb = [
        [{"text": f"{otp}", "icon_custom_emoji_id": "5251227707026470504",
          "copy_text": {"text": otp}, "style": "success"}],
        [
            {"text": "Number Bot", "icon_custom_emoji_id": "5231012545799666522",
             "url": f"https://t.me/{BOT_USERNAME}", "style": "primary"},
            {"text": "Main Channel", "icon_custom_emoji_id": "5217822164362739968",
             "url": bot_settings.get("main_channel", "https://t.me"), "style": "danger"}
        ]
    ]
    if reward > 0 and reward_on:
        kb.append([{"text": f"Added {reward} tk", "icon_custom_emoji_id": "5420396762189831222",
                    "callback_data": "ignore", "style": "primary"}])
    return msg, kb


def _fw_send_otp(fw_list, app_full_name, prem_app_html, char, iso, display_num, lang, otp):
    """Group-এ fancy (inbox) design পাঠায় — আগে bot user পেত, এখন group পাবে।"""
    grp_msg, grp_kb = build_otp_inbox(app_full_name, prem_app_html, char, iso, display_num, lang, otp, 0, False)
    for fw in fw_list:
        fw_kb = [row[:] for row in grp_kb]
        for btn in fw.get("buttons", []):
            b_obj = {"text": btn["text"], "url": btn["url"], "style": "primary"}
            if "icon_custom_emoji_id" in btn:
                b_obj["icon_custom_emoji_id"] = btn["icon_custom_emoji_id"]
            fw_kb.append([b_obj])
        send_message(fw["chat_id"], grp_msg, reply_markup={"inline_keyboard": fw_kb})

def _user_send_otp(owner_id, char, iso, prem_app_html, display_num, otp, reward=0, reward_on=False):
    """Bot user-কে simple design পাঠায় — আগে group পেত, এখন bot user পাবে।"""
    if not bot_settings.get("user_otp_notify", True):
        return
    # Change the assigned number's icon from waiting to OTP-received.
    session = user_active_sessions.get(owner_id)
    if session and session.get("reply_markup"):
        clean_display = str(display_num).replace("+", "").replace(" ", "").replace("-", "")
        updated_markup = {
            "inline_keyboard": [
                [dict(button) for button in row]
                for row in session["reply_markup"].get("inline_keyboard", [])
            ]
        }
        changed = False
        for row in updated_markup["inline_keyboard"]:
            for button in row:
                button_num = str(button.get("text", "")).replace("+", "").replace(" ", "").replace("-", "")
                if button_num == clean_display:
                    button["icon_custom_emoji_id"] = OTP_RECEIVED_NUMBER_EMOJI_ID
                    changed = True
        if changed:
            edit_message_reply_markup(owner_id, session["msg_id"], updated_markup)
            session["reply_markup"] = updated_markup

    flag_html = get_flag_info_html(iso) if iso else char
    simple_msg = render_body_text(f"{flag_html} {get_country_name(iso)} {prem_app_html} {display_num}")
    user_kb = [[{"text": f"{otp}", "icon_custom_emoji_id": "5353022963132174959",
                 "copy_text": {"text": otp}, "style": "success"}]]
    if reward > 0 and reward_on:
        user_kb.append([{"text": f"Added {reward} tk", "icon_custom_emoji_id": "5420396762189831222",
                         "callback_data": "ignore", "style": "primary"}])
    send_message(owner_id, simple_msg, reply_markup={"inline_keyboard": user_kb})

# ==========================================
# 🌟 ADVANCED SERVICE & LANGUAGE DETECTION
# ==========================================

SERVICE_SMS_KEYWORDS = {
    # 🟢 Social Media & Chat (Added Arabic Keywords)
    "whatsapp": ["whatsapp", "wa", "wap", "w/a", "whatsapp business", "wa.me", "wa code", "wh", "واتساب", "واتساپ", "واٹس ایپ", "व्हाट्सएप", "वाट्सएप", "वॉट्सऐप", "व्हाट्सप्प", "হোয়াটসঅ্যাপ", "হোটসঅ্যাপ", "ватсап", "уотсап", "вотсап", "ватс апп", "వాట్సాప్", "വാട്‌സ്ആപ്പ്", "வாட்ஸ்அப்", "ವಾಟ್ಸಾಪ್", "વોટ્સએપ", "ਵਟਸਐਪ", "ହ୍ଵାଟସ୍ ଆପ୍", "වට්ස්ඇප්", "วอตส์แอปป์", "วอทส์แอพ", "ဝက်စ်အက်ပ်", "វ៉តសាប់", "ວອດແອັບ", "ワッツアップ", "왓츠앱", "whatsapp的", "whatsapp验证码", "וואטסאפ", "γουάτσαπ", "ዋትስአፕ", "ვოთსאფი", "վոթսափ"],
    "facebook": ["facebook", "fb", "meta", "fbook", "fb code", "facebook code", "فيسبوك", "فيس بوك"],
    "instagram": ["instagram", "insta", "ig", "ig code", "instagram code", "انستغرام", "انستقرام"],
    "telegram": ["telegram", "tg", "tele", "telegram code", "tg code", "t.me", "تيليجرام", "تليجرام"],
    "tiktok": ["tiktok", "tik tok", "tikvideo", "tiktok code", "tik code", "تيك توك"],
    "snapchat": ["snapchat", "snap", "snap code", "سناب شات"],
    "twitter": ["twitter", "x.com", "x code", "twitter code", "تويتر"],
    "discord": ["discord", "discord code", "ديسكورد"],
    "viber": ["viber", "viber code", "فايبر"],
    "line": ["line", "line code", "line verification", "لاين"],
    "wechat": ["wechat", "we chat", "wechat code", "وي تشات"],
    "signal": ["signal", "signal code", "سيجنال"],
    "linkedin": ["linkedin", "linked in", "لينكد إن"],
    "imo": ["imo", "imo code", "imo verification", "ايمو"],
    "kakaotalk": ["kakao", "kakaotalk", "كاكاو"],
    "qq": ["qq", "tencent qq"],
    "vk": ["vk", "vkontakte"],

    # 🔵 Tech & Mail
    "google": ["google", "gmail", "youtube", "g-", "google voice", "جوجل", "غوغل"],
    "microsoft": ["microsoft", "ms", "outlook", "live.com", "hotmail"],
    "apple": ["apple", "icloud", "itunes", "apple id"],
    "yahoo": ["yahoo", "yahoo code", "ymail"],
    "protonmail": ["proton", "protonmail"],
    
    # 💰 Crypto & Trading
    "binance": ["binance", "bnb", "binances"],
    "coinbase": ["coinbase"],
    "okx": ["okx", "okex"],
    "kucoin": ["kucoin"],
    "bybit": ["bybit"],
    "huobi": ["huobi", "htx"],
    "mexc": ["mexc"],
    "trustwallet": ["trust wallet", "trustwallet"],

    # 💳 Finance & Wallets
    "bkash": ["bkash", "b-kash", "bkash code"],
    "nagad": ["nagad", "nagad code"],
    "rocket": ["rocket", "dutch bangla"],
    "upay": ["upay", "upay code"],
    "paypal": ["paypal", "pay pal"],
    "paytm": ["paytm"],
    "cashapp": ["cash app", "cashapp"],
    "wise": ["wise", "transferwise"],

    # 🛒 E-commerce & Delivery
    "amazon": ["amazon", "amzn", "amazon code"],
    "ebay": ["ebay"],
    "aliexpress": ["aliexpress", "ali express"],
    "alibaba": ["alibaba"],
    "daraz": ["daraz", "daraz code"],
    "foodpanda": ["foodpanda", "food panda"],
    "uber": ["uber", "uber code", "uber verification", "uber eats"],
    "pathao": ["pathao", "pathao ride"],

    # 🎮 Gaming & Entertainment
    "netflix": ["netflix", "netflix code"],
    "spotify": ["spotify", "spotify code"],
    "steam": ["steam", "steam guard"],
    "epicgames": ["epic games", "epicgames"],
    "roblox": ["roblox", "roblox code"],
    "riotgames": ["riot", "riot games", "valorant", "league of legends"],
    "garena": ["garena", "free fire", "freefire"],
    "playstation": ["playstation", "psn"],

    # 🎲 Betting & Casino
    "1xbet": ["1xbet", "1x bet"],
    "melbet": ["melbet", "melbet code"],
    "linebet": ["linebet"],
    "bet365": ["bet365"],
    "megapari": ["megapari"],

    # ❤️ Dating
    "tinder": ["tinder", "tinder code"],
    "bumble": ["bumble"],
    "badoo": ["badoo"]
}

def detect_service(text):
    """
    🌟 FIX: আগে যেকোনো keyword substring match করলেই সার্ভিস বদলে যেত।
    এখন short keyword (≤3 char) word-boundary দিয়ে চেক, আর সব match এর মধ্যে
    সবচেয়ে দীর্ঘ keyword টাকে (সবচেয়ে specific) বেছে নেওয়া হয়।
    """
    text_lower = str(text).lower()
    best_match = None  # (keyword_length, service_key)
    for service_key, keywords in SERVICE_SMS_KEYWORDS.items():
        for kw in keywords:
            kw_l = kw.lower()
            if len(kw_l) <= 3:
                # ছোট keyword → সম্পূর্ণ শব্দ হিসেবে মিলাতে হবে
                if re.search(r'\b' + re.escape(kw_l) + r'\b', text_lower):
                    if best_match is None or len(kw_l) > best_match[0]:
                        best_match = (len(kw_l), service_key.upper())
            else:
                if kw_l in text_lower:
                    if best_match is None or len(kw_l) > best_match[0]:
                        best_match = (len(kw_l), service_key.upper())
    return best_match[1] if best_match else None


def get_service_info_html(service_text, msg_text=""):
    """
    🌟 FIX: আগে service_text ignore করে msg_text থেকে detect করত, তাই ভুল
    service দেখাত। এখন priority:
      1) service_text যদি premium_apps এ থাকে → সেটাই দেখাও
      2) service_text যদি SERVICE_SMS_KEYWORDS এ থাকে → সেটাই দেখাও
      3) তারপরই msg_text থেকে detect করার চেষ্টা
      4) কিছু না মিললে → service_text নিজেই
    """
    s = str(service_text).upper().strip()
    m = str(msg_text).lower().strip()
    apps = bot_settings.get("premium_apps", {})

    def _lookup_app(key):
        key_up = key.upper().strip()
        if not key_up:
            return None
        # Exact match সবচেয়ে আগে চেক করো
        if key_up in apps:
            data = apps[key_up]
            full_name = data.get("name", key_up.title())
            char = data.get("char", "📱")
            eid = data.get("id")
            if eid: return full_name, f'<tg-emoji emoji-id="{eid}">{char}</tg-emoji>'
            return full_name, char
        # তারপর word-level match (substring হলেও কমপক্ষে 4 char হতে হবে)
        for app_name, data in apps.items():
            if len(key_up) >= 4 and len(app_name) >= 4:
                if key_up == app_name or (len(key_up) >= 5 and key_up in app_name) or (len(app_name) >= 5 and app_name in key_up):
                    full_name = data.get("name", app_name.title())
                    char = data.get("char", "📱")
                    eid = data.get("id")
                    if eid: return full_name, f'<tg-emoji emoji-id="{eid}">{char}</tg-emoji>'
                    return full_name, char
        return None

    # 1. service_text → premium_apps 직접 검색
    result = _lookup_app(s)
    if result:
        return result

    # 2. service_text → SERVICE_SMS_KEYWORDS 에 있으면 그대로 사용
    clean_s = re.sub(r'[^\w]', '', s).strip()
    for svc_key in SERVICE_SMS_KEYWORDS:
        if clean_s and (clean_s == svc_key.upper() or clean_s in svc_key.upper() or svc_key.upper() in clean_s):
            result = _lookup_app(svc_key)
            if result:
                return result
            # app এ না থাকলেও সার্ভিস নাম দেখাও
            if len(svc_key) <= 20:
                return svc_key.title(), "📱"

    # 3. msg_text থেকে detect (only if service_text is generic / panel name)
    if m:
        detected = detect_service(m)
        if detected:
            result = _lookup_app(detected)
            if result:
                return result
            if len(detected) <= 20:
                return detected.title(), "📱"

    # 4. fallback → service_text
    if len(s) > 25:
        return "Message", "💬"
    if s:
        return s.title(), "📱"
    return "Message", "💬"

def detect_language(text):
    if not text: return "#EN"
    text_str = str(text)

    # ১. Unicode Block দিয়ে নিখুঁত বর্ণমালা শনাক্তকরণ (100% Accurate for scripts)
    if any('\u0600' <= c <= '\u06ff' for c in text_str): return "#AR" # Arabic / Persian / Urdu
    if any('\u0980' <= c <= '\u09ff' for c in text_str): return "#BN" # Bengali
    if any('\u0900' <= c <= '\u097f' for c in text_str): return "#HI" # Hindi / Marathi / Nepali
    if any('\u0a00' <= c <= '\u0a7f' for c in text_str): return "#PA" # Punjabi (Gurmukhi)
    if any('\u0a80' <= c <= '\u0aff' for c in text_str): return "#GU" # Gujarati
    if any('\u0b00' <= c <= '\u0b7f' for c in text_str): return "#OR" # Odia
    if any('\u0b80' <= c <= '\u0bff' for c in text_str): return "#TA" # Tamil
    if any('\u0c00' <= c <= '\u0c7f' for c in text_str): return "#TE" # Telugu
    if any('\u0c80' <= c <= '\u0cff' for c in text_str): return "#KN" # Kannada
    if any('\u0d00' <= c <= '\u0d7f' for c in text_str): return "#ML" # Malayalam
    if any('\u0d80' <= c <= '\u0dff' for c in text_str): return "#SI" # Sinhala
    if any('\u0e00' <= c <= '\u0e7f' for c in text_str): return "#TH" # Thai
    if any('\u0e80' <= c <= '\u0eff' for c in text_str): return "#LO" # Lao
    if any('\u0f00' <= c <= '\u0fff' for c in text_str): return "#BO" # Tibetan
    if any('\u1000' <= c <= '\u109f' for c in text_str): return "#MY" # Burmese (Myanmar)
    if any('\u1200' <= c <= '\u137f' for c in text_str): return "#AM" # Amharic (Ethiopic)
    if any('\u1780' <= c <= '\u17ff' for c in text_str): return "#KM" # Khmer
    if any('\u10a0' <= c <= '\u10ff' for c in text_str): return "#KA" # Georgian
    if any('\u0530' <= c <= '\u058f' for c in text_str): return "#HY" # Armenian
    if any('\u0590' <= c <= '\u05ff' for c in text_str): return "#HE" # Hebrew
    if any('\u0370' <= c <= '\u03ff' for c in text_str): return "#EL" # Greek
    if any('\u0400' <= c <= '\u04ff' for c in text_str): return "#RU" # Russian / Ukrainian (Cyrillic)
    if any('\u4e00' <= c <= '\u9fff' for c in text_str): return "#ZH" # Chinese
    if any('\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff' for c in text_str): return "#JA" # Japanese
    if any('\uac00' <= c <= '\ud7af' for c in text_str): return "#KO" # Korean

    # ২. OTP Keyword দিয়ে ভাষা শনাক্তকরণ (Latin script languages)
    text_lower = text_str.lower()
    
    # Asian / Pacific
    if any(w in text_lower for w in ["kode verifikasi", "jangan bagikan", "rahasia"]): return "#ID" # Indonesian
    if any(w in text_lower for w in ["kod pengesahan", "jangan kongsi"]): return "#MS" # Malay
    if any(w in text_lower for w in ["mã của bạn", "không chia sẻ", "mã xác minh"]): return "#VN" # Vietnamese
    if any(w in text_lower for w in ["ang iyong code", "huwag ibahagi"]): return "#TL" # Tagalog / Filipino
    
    # European / Americas
    if any(w in text_lower for w in ["código", "tu código", "verificación", "no compartas"]): return "#ES" # Spanish
    if any(w in text_lower for w in ["seu código", "código de verificação", "não compartilhe"]): return "#PT" # Portuguese
    if any(w in text_lower for w in ["code secret", "ne partagez pas", "votre code"]): return "#FR" # French
    if any(w in text_lower for w in ["dein code", "bestätigungscode", "nicht teilen"]): return "#DE" # German
    if any(w in text_lower for w in ["il tuo codice", "codice di verifica", "non condividere"]): return "#IT" # Italian
    if any(w in text_lower for w in ["twój kod", "nie udostępniaj", "kod weryfikacyjny"]): return "#PL" # Polish
    if any(w in text_lower for w in ["doğrulama kodu", "paylaşmayın", "onay kodu"]): return "#TR" # Turkish
    if any(w in text_lower for w in ["jouw code", "verificatiecode", "niet delen"]): return "#NL" # Dutch
    if any(w in text_lower for w in ["din kod", "verifieringskod", "dela inte"]): return "#SV" # Swedish
    if any(w in text_lower for w in ["bekræftelseskode", "del ikke"]): return "#DA" # Danish
    if any(w in text_lower for w in ["bekreftelseskode", "ikke del"]): return "#NO" # Norwegian
    if any(w in text_lower for w in ["vahvistuskoodi", "älä jaa"]): return "#FI" # Finnish
    if any(w in text_lower for w in ["váš kód", "ověřovací kód", "nesdílejte"]): return "#CS" # Czech
    if any(w in text_lower for w in ["overovací kód", "nezdieľajte"]): return "#SK" # Slovak
    if any(w in text_lower for w in ["ellenőrző kód", "ne oszd meg"]): return "#HU" # Hungarian
    if any(w in text_lower for w in ["codul tău", "codul de verificare", "nu partaja"]): return "#RO" # Romanian
    if any(w in text_lower for w in ["kontrolni kod", "kod za potvrdu", "ne delite"]): return "#HR" # Croatian/Serbian
    if any(w in text_lower for w in ["код за потвърждение", "не споделяйте"]): return "#BG" # Bulgarian
    if any(w in text_lower for w in ["ваш код", "код підтвердження"]): return "#UK" # Ukrainian
    
    # African
    if any(w in text_lower for w in ["msimbo wako", "usishiriki"]): return "#SW" # Swahili
    if any(w in text_lower for w in ["verifikasiekode", "moenie deel nie"]): return "#AF" # Afrikaans
    
    # ৩. উপরের কোনোটি না মিললে ডিফল্ট
    return "#EN"

def parse_chat_id(text):
    text = text.strip()
    if text.startswith("-100") or (text.startswith("-") and text[1:].isdigit()):
        return text
    if "t.me/" in text:
        parts = text.split("/")
        username = parts[-1]
        if username: return "@" + username if not username.startswith("@") else username
    if text.startswith("@"):
        return text
    return "@" + text

def is_admin(user_id):
    return user_id in bot_settings["admins"] or user_id == OWNER_ID

def check_force_join(user_id):
    if not bot_settings["fj_on"] or not bot_settings["fj_channels"]: return True
    if is_admin(user_id): return True
    for ch in bot_settings["fj_channels"]:
        res = api_call("getChatMember", {"chat_id": ch, "user_id": user_id})
        if res.get("ok") and res["result"]["status"] not in ["left", "kicked"]: continue
        else: return False
    return True

def send_force_join_msg(chat_id):
    kb = []
    for ch in bot_settings["fj_channels"]:
        url = f"https://t.me/{ch.replace('@', '')}" if ch.startswith("@") else ch
        kb.append([{"text": f"Join Channel", "icon_custom_emoji_id": "5789428375261023681", "url": url, "style": "primary"}])
    kb.append([{"text": "Check Joined", "icon_custom_emoji_id": "5352694861990501856", "callback_data": "check_fj", "style": "success"}])
    send_message(chat_id, render_body_text(f"{PEM['warn']} <b>Please join our channels to use the bot!</b>"), reply_markup={"inline_keyboard": kb})

def is_user_banned(user_id):
    if is_admin(user_id): return False
    if user_id in user_banned_cache and time.time() - user_banned_cache[user_id]['time'] < 60:
        return user_banned_cache[user_id]['banned']
    banned = False
    if db:
        try:
            doc = db.collection('users').document(str(user_id)).get()
            banned = doc.exists and doc.to_dict().get("banned", False)
        except: pass
    user_banned_cache[user_id] = {'banned': banned, 'time': time.time()}
    return banned

# ==========================================
# Captcha Auto Login & Parsing Core
# ==========================================
def extract_otp_code(text):
    clean_text = re.sub(r'[\u200B-\u200D\uFEFF]', '', str(text))

    # 1. Multi-part OTPs (e.g. 123-456 or 809-761)
    multi_part = re.search(r'(\d{3}[-\s]+\d{3})|(\d{2}[-\s]+\d{2}[-\s]+\d{2})', clean_text)
    if multi_part:
        # হাইফেন (-) থাকলে সেটা রেখে দিবে, কিন্তু স্পেস থাকলে মুছে একসাথে করে দিবে
        return multi_part.group(0).replace(" ", "")

    # 2. Keyword-based extraction
    otp_keywords = ['code', 'is', 'otp', 'pin', 'verification', 'auth', 'কোড', 'رمز', 'your code']
    keywords_pattern = '|'.join(otp_keywords)
    keyword_match = re.search(rf'(?:{keywords_pattern})\s*(?:is|:|-|=)?\s*([a-z0-9]{{4,10}})', clean_text, re.I)
    if keyword_match and keyword_match.group(1).isdigit():
        return keyword_match.group(1)
        
    keyword_match_rev = re.search(rf'([a-z0-9]{{4,10}})\s*(?:is your|is the|কোড)', clean_text, re.I)
    if keyword_match_rev and keyword_match_rev.group(1).isdigit():
        return keyword_match_rev.group(1)

    # 3. Google OTP
    g_match = re.search(r'G-(\d{6})', clean_text, re.IGNORECASE)
    if g_match: return g_match.group(1)

    # 4. Digit sequences fallback
    digit_matches = re.findall(r'(?<!\d)\d{4,8}(?!\d)', clean_text)
    if digit_matches: return digit_matches[0]

    return None

def parse_panel_response(response_text, p_config=None):
    results = []
    p_type = p_config.get("type", "API Panel") if p_config else "API Panel"
    
    n_col_name = p_config.get("num_col_name", "number").lower() if p_config else "number"
    m_col_name = p_config.get("msg_col_name", "message").lower() if p_config else "message"
    n_idx = int(p_config.get("num_col_idx", 1)) - 1 if p_config and p_config.get("num_col_idx") else 1
    m_idx = int(p_config.get("msg_col_idx", 2)) - 1 if p_config and p_config.get("msg_col_idx") else 2

    if p_type == "Auto Captcha Panel":
        try:
            soup = BeautifulSoup(response_text, 'html.parser')
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                if not rows: continue
                
                # 🌟 Option 1 + Smart HTML Detection: কলামের নাম ও ব্যবহারকারীর দেওয়া সিরিয়াল দিয়ে সঠিক পজিশন বের করা
                final_n_idx = n_idx
                final_m_idx = m_idx
                
                # প্রথম রো (Header) চেক করে কলামের আসল সিরিয়াল মিলিয়ে নেওয়া
                header_cells = rows[0].find_all(['th', 'td'])
                for i, cell in enumerate(header_cells):
                    c_text = cell.get_text(strip=True).lower()
                    if n_col_name in c_text: final_n_idx = i
                    if m_col_name in c_text: final_m_idx = i

                for row in rows:
                    cols = row.find_all(['td', 'th'])
                    
                    # হেডার রো (যেখানে সব th থাকে) সেগুলো থেকে ডাটা নিবে না
                    if all(c.name == 'th' for c in cols): continue
                    
                    if len(cols) > max(final_n_idx, final_m_idx):
                        # HTML টেবিল থেকে টেক্সট বের করা
                        num_text = cols[final_n_idx].get_text(separator=" ", strip=True)
                        msg_text = cols[final_m_idx].get_text(separator=" ", strip=True)
                        
                        clean_num = re.sub(r'\D', '', num_text)
                        
                        # নাম্বারটা আসলেই ৫-১৮ ডিজিটের কিনা তা নিশ্চিত করা (যাতে উল্টাপাল্টা টেক্সট না আসে)
                        if clean_num and 5 <= len(clean_num) <= 18:
                            otp = extract_otp_code(msg_text)
                            if otp and len(msg_text) > 4:
                                results.append({"number": clean_num, "message": msg_text, "otp": otp})
        except Exception as e:
            pass
    else:
        try:
            data = json.loads(response_text)
            temp_results = []
            
            def process_item(item):
                pot_nums_list = []
                pot_msg = None
                values = []
                
                if isinstance(item, dict):
                    # ১. প্রথমে পরিচিত JSON Key (যেমন: num, phone, sms) দিয়ে খোঁজার চেষ্টা
                    lower_keys = {str(k).lower(): v for k, v in item.items()}
                    for k in ["number", "num", "phone", "msisdn", "sender"]:
                        if k in lower_keys:
                            clean_val = re.sub(r'\D', '', str(lower_keys[k]))
                            if 5 <= len(clean_val) <= 18:
                                if clean_val not in pot_nums_list: pot_nums_list.append(clean_val)
                    for k in ["message", "msg", "sms", "content", "text"]:
                        if k in lower_keys:
                            val = str(lower_keys[k])
                            if len(val) > 4:
                                pot_msg = val
                                break
                    values = list(item.values())
                elif isinstance(item, list):
                    values = item

                # ২. যদি Key দিয়ে না পাওয়া যায়, তবে Smart Blind Scan (সব ভ্যালু চেক করবে)
                for v in values:
                    if isinstance(v, (dict, list)) or v is None: continue
                    v_str = str(v).strip()
                    
                    # Number Detection: 7 থেকে 18 ডিজিট
                    clean_v = re.sub(r'\D', '', v_str)
                    if 7 <= len(clean_v) <= 18 and not re.search(r'[a-zA-Z]', v_str):
                        # Date/Time/IP এড়ানোর লজিক
                        if not re.search(r'\d{4}[-/]\d{2}[-/]\d{2}', v_str) and not re.search(r'\d{2}:\d{2}:\d{2}', v_str) and "." not in v_str:
                            if clean_v not in pot_nums_list:
                                pot_nums_list.append(clean_v)
                    
                    # Message Detection: 5 অক্ষরের বেশি এবং শুধু সংখ্যা নয়
                    if len(v_str) > 4 and not v_str.isdigit():
                        if extract_otp_code(v_str):
                            if pot_msg is None or len(v_str) > len(pot_msg):
                                pot_msg = v_str
                                
                # 🌟 ৩. Multiple Numbers Logic (User Priority > Second Number > First Number)
                pot_num = None
                if pot_nums_list:
                    matched_user_num = None
                    for n in pot_nums_list:
                        # চেক করবে ইউজারের অ্যাসাইন করা নাম্বারের তালিকায় এই নাম্বারটি আছে কি না
                        if n in zenex_assigned_numbers or any(n in str(key) for key in zenex_assigned_numbers.keys()):
                            matched_user_num = n
                            break
                    
                    if matched_user_num:
                        pot_num = matched_user_num
                    elif len(pot_nums_list) >= 2:
                        pot_num = pot_nums_list[1] # ইউজারের কাছে না থাকলে সরাসরি দ্বিতীয় নাম্বারটি নেবে
                    else:
                        pot_num = pot_nums_list[0]
                            
                if pot_num and pot_msg:
                    otp = extract_otp_code(pot_msg)
                    if otp:
                        temp_results.append({"number": pot_num, "message": pot_msg, "otp": otp})
                        
            def traverse_json(node):
                if isinstance(node, list):
                    if len(node) > 0 and not isinstance(node[0], (dict, list)):
                        # It's a flat list representing one record
                        process_item(node)
                    for child in node:
                        if isinstance(child, (dict, list)):
                            traverse_json(child)
                elif isinstance(node, dict):
                    process_item(node)
                    for val in node.values():
                        if isinstance(val, (dict, list)):
                            traverse_json(val)

            traverse_json(data)
            
            # Remove duplicates
            seen = set()
            for r in temp_results:
                uid = f"{r['number']}_{r['otp']}"
                if uid not in seen:
                    seen.add(uid)
                    results.append(r)
        except: pass
        
    return results

# 🌟 Advanced Automated Background Captcha Solver 🌟
def attempt_auto_login(p, idx):
    login_url = p.get("login_url", "").strip()
    if not login_url.startswith("http"):
        login_url = "http://" + login_url
        
    if not login_url.lower().endswith('/login') and not login_url.lower().endswith('.php'):
        login_url = f"{login_url.rstrip('/')}/login"
        
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    })
    
    try:
        res = session.get(login_url, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        all_text = res.text
        
        # 1. SOLVE CAPTCHA (Exact bot 3.py logic)
        captcha_match = re.search(r'(\d+\s*[\+\-\*]\s*\d+)\s*[=\?:]', all_text)
        if not captcha_match:
            captcha_match = re.search(r'what is\s*(\d+\s*[\+\-\*]\s*\d+)', all_text, re.I)
        if not captcha_match:
            elements = soup.find_all(["label", "div", "span", "p", "strong"])
            for el in elements:
                txt = el.get_text(separator=" ", strip=True)
                if any(op in txt for op in ["+", "-", "*"]):
                    m = re.search(r'(\d+\s*[\+\-\*]\s*\d+)', txt)
                    if m:
                        captcha_match = m
                        break
                        
        captcha_text = captcha_match.group(1) if captcha_match else "0 + 0"
        answer = "0"
        m2 = re.search(r'(\d+)\s*([\+\-\*])\s*(\d+)', captcha_text)
        if m2:
            a, op, b = int(m2.group(1)), m2.group(2), int(m2.group(3))
            if op == '+': answer = str(a + b)
            elif op == '-': answer = str(a - b)
            elif op == '*': answer = str(a * b)

        # 2. FIND FORM
        form = soup.find("form")
        if not form:
            p["login_status"] = "❌ No login form found"
            return False
            
        action = form.get("action")
        from urllib.parse import urljoin
        post_url = urljoin(login_url, action) if action else login_url

        form_data = {}
        for hidden in form.find_all("input", type="hidden"):
            name = hidden.get("name")
            if name: form_data[name] = hidden.get("value") or ""
        
        user_input = form.find("input", {"name": re.compile(r"user|email|id", re.I)}) or \
                     form.find("input", {"type": "text", "placeholder": re.compile(r"user|email", re.I)}) or \
                     form.find("input", {"type": "text"})
                     
        pass_input = form.find("input", {"name": re.compile(r"pass", re.I)}) or \
                     form.find("input", {"type": "password"})
                     
        captcha_input = form.find("input", {"placeholder": re.compile(r"answer|ans|code|verification|value|captcha", re.I)}) or \
                        form.find("input", {"name": re.compile(r"ans|captcha|ver|code", re.I)})
        
        user_field = user_input.get("name") if user_input else "username"
        pass_field = pass_input.get("name") if pass_input else "password"
        captcha_field = captcha_input.get("name") if captcha_input else "answer"

        form_data[user_field] = p.get("username", "")
        form_data[pass_field] = p.get("password", "")
        if captcha_field:
            form_data[captcha_field] = answer

        # 3. SUBMIT
        login_req = session.post(post_url, data=form_data, allow_redirects=True, timeout=15)
        
        # 4. VERIFY (Exact bot 3.py check logic)
        msg_link = p.get("msg_link", "").strip()
        if not msg_link.startswith("http") and msg_link != "":
            msg_link = "http://" + msg_link
            
        check_url = msg_link if msg_link else f"{login_url.split('/login')[0]}/client/SMSCDRStats"
        
        check_res = session.get(check_url, timeout=10)
        
        if 'logout' in login_req.text.lower() or 'logout' in check_res.text.lower() or 'sms reports' in check_res.text.lower() or 'dashboard' in check_res.text.lower() or 'cdrs' in check_res.text.lower():
            panel_sessions[idx] = session
            p["login_status"] = "✅ Active & Fetching"
            return True
        else:
            # এখানে ফেইল হলে অংক কী পেয়েছিল তা দেখা যাবে
            p["login_status"] = f"❌ Login Failed (Math: {captcha_text} = {answer})"
            return False
            
    except Exception as e:
        p["login_status"] = f"❌ Error: {str(e)[:20]}"
        
    return False

def panel_keepalive_thread():
    """
    প্রতি ২ মিনিটে সব Auto Captcha Panel-এ ping পাঠায় যাতে session জীবিত থাকে।
    Session expire হওয়ার আগেই এটা active রাখে — OTP কখনো miss হবে না।
    """
    KEEPALIVE_INTERVAL = 120  # 2 মিনিট পর পর ping
    while True:
        try:
            time.sleep(KEEPALIVE_INTERVAL)
            panels = bot_settings.get("panels", [])
            for idx, p in enumerate(panels):
                if p.get("status") != "ON" or p.get("type") != "Auto Captcha Panel":
                    continue
                sess = panel_sessions.get(idx)
                if not sess:
                    continue
                try:
                    login_url = p.get("login_url", "").strip()
                    if not login_url.startswith("http"):
                        login_url = "http://" + login_url
                    msg_link = p.get("msg_link", "").strip()
                    if msg_link and not msg_link.startswith("http"):
                        msg_link = "http://" + msg_link
                    ping_url = msg_link if msg_link else f"{login_url.split('/login')[0]}/client/SMSCDRStats"

                    res = sess.get(ping_url, timeout=12)
                    resp_lower = res.text.lower()

                    # Session শেষ হয়েছে কিনা check করা (improved — covers more panel types)
                    session_dead = _is_session_dead(res.text)

                    if session_dead:
                        print(f"🔄 [KeepAlive] Panel #{idx} '{p.get('name','?')}' session dead — re-logging in now")
                        if idx in panel_sessions:
                            del panel_sessions[idx]
                        # সাথে সাথে re-login
                        p["last_login_attempt"] = 0  # cooldown bypass করো
                        success = attempt_auto_login(p, idx)
                        if success:
                            print(f"✅ [KeepAlive] Panel #{idx} '{p.get('name','?')}' re-login successful")
                            p["_login_fail_count"] = 0
                        else:
                            print(f"❌ [KeepAlive] Panel #{idx} '{p.get('name','?')}' re-login failed")
                            _send_panel_alert(idx, p, "❌ Keep-Alive re-login <b>fail</b> হয়েছে!\nOTP আসা বন্ধ হতে পারে। Panel check করুন।")
                    else:
                        print(f"💚 [KeepAlive] Panel #{idx} '{p.get('name','?')}' session alive")
                except Exception as e:
                    print(f"⚠️ [KeepAlive] Panel #{idx} '{p.get('name','?')}' ping error: {e}")
                    # Ping fail হলে session মুছে দাও, monitor thread আবার login করবে
                    if idx in panel_sessions:
                        del panel_sessions[idx]
                    p["last_login_attempt"] = 0
        except Exception as e:
            print(f"⚠️ panel_keepalive_thread crashed: {e}")


def panel_monitor_thread():
    global processed_otps, recent_traffic, panel_sessions
    _pexecutor = ThreadPoolExecutor(max_workers=20)
    while True:
        try:
            active_panels = [(idx, p) for idx, p in enumerate(bot_settings.get("panels", [])) if p.get("status") == "ON"]
            futures = {_pexecutor.submit(_fetch_one_panel, idx, p): (idx, p) for idx, p in active_panels}
            for future, (idx, p) in futures.items():
                try:
                    parsed_data = future.result(timeout=15)
                    if not parsed_data: continue
                    if p.get("type") != "Auto Captcha Panel":
                        limit = p.get("records", 0)
                        if limit > 0: parsed_data = parsed_data[:limit]
                    for item in parsed_data:
                        num = item["number"]
                        otp = item["otp"]
                        msg_text = item["message"]
                        unique_id = f"{num}_{otp}"
                        
                        if _safe_add_otp(unique_id):  # thread-safe check+add atomically

                                 
                            char, iso = get_flag_and_code(num)
                            app_full_name, prem_app_html = get_service_info_html(p.get("name", "Panel"), msg_text)
                            current_time = time.time()
                            
                            recent_traffic = [t for t in recent_traffic if current_time - t.get("time", 0) <= 3600]
                            recent_traffic.append({
                                "service": app_full_name,
                                "iso": iso,
                                "flag": char,
                                "number": num,
                                "time": current_time
                            })
                            # 🌟 শুধু লোকাল ফাইলে সেভ করবে, Firestore এ অহেতুক Write করবে না!
                            save_local_db()
                                 
                            display_num = f"+{num}" if not str(num).startswith("+") else str(num)
                            masked = mask_number(display_num)
                            lang = detect_language(msg_text)
                            
                            display_msg = render_body_text(f"{get_flag_info_html(iso) if iso else char} {get_country_name(iso)} {prem_app_html} {display_num}")
                            
                            # 🌟 FIX: এখানে যদি group-এ পাঠাতে গিয়ে exception হতো (যেমন bot গ্রুপ থেকে
                            # kick হয়ে গেছে, বা fw_groups এ ভুল chat_id), তাহলে নিচের user forward
                            # কোড পর্যন্ত কখনো পৌঁছাতো না — bot ও group দুটোই OTP পেত না। এখন আলাদা
                            # try/except দিয়ে ঘিরে দেওয়া হয়েছে যাতে একটা ব্যর্থ হলেও অন্যটা চলে, এবং
                            # এরর কনসোলে দেখা যায়।
                            try:
                                _fw_send_otp(bot_settings.get("fw_groups", []), app_full_name, prem_app_html, char, iso, display_num, lang, otp)
                            except Exception as e:
                                print(f"⚠️ [Panel #{idx}] _fw_send_otp (group forward) failed: {e}")
                            
                            owners = []
                            clean_api_num = str(num).replace("+", "").replace(" ", "").replace("-", "").strip()

                            # Shark/CR/Flex-এর মতোই: Active Sessions + সব provider (batch/stex/voltx/zenex)
                            # merge করে চেক করা হয় — কোনো একটাতে পেলেই বাকিগুলো skip করা হয় না,
                            # যাতে একই নাম্বার একাধিক জায়গায় assign থাকলে সবাই OTP পায়।
                            for uid, session_data in list(user_active_sessions.items()):
                                for act_num in session_data.get("nums", []):
                                    act_clean = str(act_num).replace("+", "").replace(" ", "").replace("-", "").strip()
                                    if act_clean == clean_api_num or (len(act_clean) >= 8 and act_clean.endswith(clean_api_num[-8:])) or (len(clean_api_num) >= 8 and clean_api_num.endswith(act_clean[-8:])):
                                        if uid not in owners:
                                            owners.append(uid)

                            for assigned_dict in [batch_assigned_numbers, stex_assigned_numbers, voltx_assigned_numbers, zenex_assigned_numbers, nexus_assigned_numbers]:
                                for a_num, n_owner in list(assigned_dict.items()):
                                    clean_a = str(a_num).replace("+", "").replace(" ", "").replace("-", "").strip()
                                    if clean_a == clean_api_num or (len(clean_a) >= 8 and clean_a.endswith(clean_api_num[-8:])) or (len(clean_api_num) >= 8 and clean_api_num.endswith(clean_a[-8:])):
                                        if n_owner not in owners:
                                            owners.append(n_owner)

                            owners = list(set(owners))
                            if not owners:
                                print(f"⚠️ [Panel #{idx}] No owner matched for number {clean_api_num} (OTP still sent to group).")
                                if bot_settings.get("no_match_alert_on", True):
                                    try:
                                        _all_admins = list(bot_settings.get("admins", []))
                                        if OWNER_ID not in _all_admins:
                                            _all_admins.append(OWNER_ID)
                                        _dbg_msg = render_body_text(
                                            f"🔌 <b>Panel #{idx} '{p.get('name','?')}' — OTP পেয়েছি কিন্তু কোনো user match নেই!</b>\n\n"
                                            f"📱 <b>Number:</b> <code>+{clean_api_num}</code>\n"
                                            f"🔑 <b>OTP:</b> <code>{otp}</code>\n"
                                            f"📊 batch_assigned: {len(batch_assigned_numbers)} | sessions: {len(user_active_sessions)}\n\n"
                                            f"⚠️ এই number bot-এ কোনো user-কে দেওয়া হয়নি।"
                                        )
                                        for _adm in _all_admins:
                                            try: send_message(_adm, _dbg_msg)
                                            except: pass
                                    except: pass
                            for owner_id in owners:
                                try:
                                    reward, reward_on = get_service_reward(app_full_name, owner_id)
                                    if reward > 0 and reward_on:
                                        update_balance(owner_id, reward)
                                    _user_send_otp(owner_id, char, iso, prem_app_html, display_num, otp, reward if reward_on else 0, reward_on)
                                    increment_total_otps(owner_id)
                                except Exception as e:
                                    print(f"⚠️ [Panel #{idx}] _user_send_otp failed for owner {owner_id}: {e}")
                except Exception as e:
                    print(f"⚠️ [Panel #{idx}] panel_monitor_thread item loop crashed: {e}")
        except Exception as e:
            print(f"⚠️ panel_monitor_thread outer loop crashed: {e}")
        time.sleep(1) 

# ==========================================
# User Management — Local JSON + Firestore (optional)
# ==========================================
# Firestore না থাকলে সব user data local users_data.json-এ save হয়।
# RAM cache: 5 মিনিটের TTL, সর্বোচ্চ 200 user।

_user_cache = {}      # {user_id: (data_dict, timestamp)}
_USER_TTL = 300       # 5 মিনিট (seconds)
_USER_CACHE_MAX = 200

# Local (no-Firestore) user store — key: str(user_id)
_local_users: dict = {}

def _load_users_local():
    """Bot start-এ users_data.json থেকে user data লোড করে।"""
    global _local_users
    if os.path.exists(USERS_DATA_FILE):
        try:
            with open(USERS_DATA_FILE, "r", encoding="utf-8") as f:
                _local_users = json.load(f)
            print(f"✅ Local users DB loaded ({len(_local_users)} users)")
        except Exception as e:
            print(f"❌ Error loading users_data.json: {e}")
            _local_users = {}
    else:
        _local_users = {}

_load_users_local()

def _save_users_local():
    """users_data.json-এ user data সেভ করে।"""
    try:
        with open(USERS_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(_local_users, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Error saving users_data.json: {e}")

def _get_local_user(user_id):
    """Local store থেকে user dict return করে। না থাকলে নতুন বানায়।"""
    key = str(user_id)
    if key not in _local_users:
        _local_users[key] = {
            "user_id": user_id, "balance": 0.0,
            "total_refers": 0, "total_otps": 0,
            "banned": False, "verified": False,
            "referred_by": None, "ref_paid": False
        }
    return _local_users[key]

def _cache_get(user_id):
    entry = _user_cache.get(user_id)
    if entry and (time.time() - entry[1]) < _USER_TTL:
        return entry[0]
    if user_id in _user_cache:
        del _user_cache[user_id]
    return None

def _cache_set(user_id, data):
    if len(_user_cache) >= _USER_CACHE_MAX:
        oldest = min(_user_cache, key=lambda k: _user_cache[k][1])
        del _user_cache[oldest]
    _user_cache[user_id] = (data, time.time())

def get_user(user_id):
    """User data ফেরত দেয়। Firestore থাকলে Firestore, না থাকলে local file।"""
    cached = _cache_get(user_id)
    if cached:
        return cached
    if not db:
        # ── LOCAL MODE ──
        data = _get_local_user(user_id)
        _cache_set(user_id, data)
        return data
    # ── FIRESTORE MODE ──
    try:
        doc_ref = db.collection('users').document(str(user_id))
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            if "total_otps" not in data: data["total_otps"] = 0
            if "banned" not in data: data["banned"] = False
            if "verified" not in data: data["verified"] = False
            _cache_set(user_id, data)
            return data
        else:
            new_user = {"user_id": user_id, "balance": 0.0, "total_refers": 0,
                        "total_otps": 0, "banned": False, "verified": False}
            doc_ref.set(new_user)
            _cache_set(user_id, new_user)
            return new_user
    except:
        return {"user_id": user_id, "balance": 0.0, "total_refers": 0, "total_otps": 0}

def update_balance(user_id, amount):
    """Balance update করে। Firestore না থাকলে local file-এ save করে।"""
    amt = float(amount)
    if not db:
        # ── LOCAL MODE: local file-এ save ──
        data = _get_local_user(user_id)
        data["balance"] = round(data.get("balance", 0.0) + amt, 6)
        _cache_set(user_id, data)
        _save_users_local()
        return
    # ── FIRESTORE MODE ──
    try:
        doc_ref = db.collection('users').document(str(user_id))
        doc_ref.set({"user_id": user_id, "balance": firestore.Increment(amt)}, merge=True)
        # Firestore সফল — cache sync করো
        cached = _cache_get(user_id)
        if cached:
            cached["balance"] = round(cached.get("balance", 0.0) + amt, 6)
            _cache_set(user_id, cached)
        else:
            _user_cache.pop(user_id, None)
    except Exception as e:
        print(f"⚠️ update_balance FAILED for user {user_id}: {e}")

def increment_total_otps(user_id):
    """total_otps বাড়ায়। Firestore না থাকলে local file-এ save করে।"""
    if not db:
        # ── LOCAL MODE ──
        data = _get_local_user(user_id)
        data["total_otps"] = data.get("total_otps", 0) + 1
        _cache_set(user_id, data)
        _save_users_local()
        return
    # ── FIRESTORE MODE ──
    try:
        db.collection('users').document(str(user_id)).update({"total_otps": firestore.Increment(1)})
        cached = _cache_get(user_id)
        if cached:
            cached["total_otps"] = cached.get("total_otps", 0) + 1
            _cache_set(user_id, cached)
    except Exception as e:
        print(f"⚠️ increment_total_otps FAILED for user {user_id}: {e}")

def add_referral(inviter_id, new_user_id):
    """Refer reward দেয়। Firestore বা local file — যেটা available।"""
    get_user(new_user_id)
    reward = bot_settings.get("refer_reward", 0.2)
    update_balance(inviter_id, reward)
    if not db:
        # ── LOCAL MODE ──
        data = _get_local_user(inviter_id)
        data["total_refers"] = data.get("total_refers", 0) + 1
        _cache_set(inviter_id, data)
        _save_users_local()
    else:
        try:
            db.collection('users').document(str(inviter_id)).update({"total_refers": firestore.Increment(1)})
            cached = _cache_get(inviter_id)
            if cached:
                cached["total_refers"] = cached.get("total_refers", 0) + 1
                _cache_set(inviter_id, cached)
        except Exception as e:
            print(f"⚠️ add_referral total_refers FAILED: {e}")
    ref_msg = (
        f"{PEM['gift']} <b>New Referral !</b>\n"
        f"------------------\n"
        f"🔥 <b>You Received {reward} TK</b>\n"
        f"------------------\n"
        f"{PEM['user']} <b>From User ID:</b> <code>{new_user_id}</code>"
    )
    send_message(inviter_id, render_body_text(ref_msg))

def _process_pending_referral(user_id):
    """User এর pending referral reward process করে। Firestore বা local — যেটা available।"""
    if not db:
        # ── LOCAL MODE ──
        data = _get_local_user(user_id)
        inviter = data.get("referred_by")
        if inviter and not data.get("ref_paid"):
            data["ref_paid"] = True
            _cache_set(user_id, data)
            _save_users_local()
            reward = bot_settings.get("refer_reward", 0.2)
            update_balance(inviter, reward)
            inviter_data = _get_local_user(inviter)
            inviter_data["total_refers"] = inviter_data.get("total_refers", 0) + 1
            cached = _cache_get(inviter)
            if cached:
                cached["total_refers"] = inviter_data["total_refers"]
                _cache_set(inviter, cached)
            _save_users_local()
            ref_msg = (
                f"{PEM['gift']} <b>New Referral !</b>\n"
                f"------------------\n"
                f"🔥 <b>You Received {reward} TK</b>\n"
                f"------------------\n"
                f"{PEM['user']} <b>From User ID:</b> <code>{user_id}</code>"
            )
            try: send_message(inviter, render_body_text(ref_msg))
            except: pass
        return
    # ── FIRESTORE MODE ──
    try:
        doc = db.collection('users').document(str(user_id)).get()
        if doc.exists:
            u_data = doc.to_dict()
            if u_data.get("referred_by") and not u_data.get("ref_paid"):
                inviter = u_data["referred_by"]
                db.collection('users').document(str(user_id)).update({"ref_paid": True})
                reward = bot_settings.get("refer_reward", 0.2)
                update_balance(inviter, reward)
                db.collection('users').document(str(inviter)).update({"total_refers": firestore.Increment(1)})
                ref_msg = (
                    f"{PEM['gift']} <b>New Referral !</b>\n"
                    f"------------------\n"
                    f"🔥 <b>You Received {reward} TK</b>\n"
                    f"------------------\n"
                    f"{PEM['user']} <b>From User ID:</b> <code>{user_id}</code>"
                )
                try: send_message(inviter, render_body_text(ref_msg))
                except: pass
    except Exception as e:
        print(f"⚠️ _process_pending_referral failed: {e}")

# ==========================================
# UI Keyboards & Menu Builders
# ==========================================
def get_cancel_kb():
    return {"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "cancel_state", "style": "danger"}]]}

def main_menu(user_id):
    kb = [
        [
            {"text": "Get Number", "icon_custom_emoji_id": "5226772700113935347", "style": "primary"},
            {"text": "100 Buy Number", "icon_custom_emoji_id": "5337080053119336309", "style": "primary"}
        ],
        [
            {"text": "Referral", "icon_custom_emoji_id": "6289791863381563934", "style": "primary"},
            {"text": "Withdrawal", "icon_custom_emoji_id": "5440539497383087970", "style": "primary"}
        ],
        [
            {"text": "TRAFFIC", "icon_custom_emoji_id": "5353032893096567467", "style": "primary"},
            {"text": "2F CODE", "icon_custom_emoji_id": "5353022963132174959", "style": "primary"}
        ],
        [
            {"text": "LEADERBOARD", "icon_custom_emoji_id": "5353032893096567467", "style": "primary"},
            {"text": "Live Support Admin", "icon_custom_emoji_id": "5337302974806922068", "style": "primary"}
        ],
    ]
    if is_admin(user_id): 
        kb.append([{"text": "Admin Panel", "icon_custom_emoji_id": "5420155432272438703", "style": "primary"}])
    return {"keyboard": kb, "resize_keyboard": True}

def get_admin_text():
    users_count = len(all_known_users) # 🌟 Zero Cost User Count!
    total_files = len(number_batches)
    available_nums = sum(len(b["numbers"]) for b in number_batches.values())

    txt = f"""
{PEM['admin']} <b>ADMIN CONTROL PANEL</b> {PEM['admin']}
━━━━━━━━━━━━━━━━━━

{PEM['graph']} <b>DATABASE OVERVIEW</b>
— — — — — — — — — —
{PEM['user']} Users      » {users_count}
{PEM['file']} Files      » {total_files}
{PEM['num']} Numbers    » {total_uploaded_stats}
{PEM['ok']} Assigned   » {total_assigned_stats}
{PEM['rocket']} Available  » {available_nums}

{PEM['graph']} <b>STOCK LEVEL</b>
— — — — — — — — — —
[██████░░░░░░░░░] {available_nums} free
"""
    return render_body_text(txt)

def admin_panel_keyboard():
    return {"inline_keyboard": [
        [{"text": "LEADER BOARD SYSTEM", "icon_custom_emoji_id": "5353032893096567467", "callback_data": "lb_main", "style": "success"}],
        [{"text": "Upload Number", "icon_custom_emoji_id": "5353001161878182134", "callback_data": "upload_num", "style": "primary"},
         {"text": "Delete files", "icon_custom_emoji_id": "5422557736330106570", "callback_data": "delete_files", "style": "danger"}],
        [{"text": "Broadcast", "icon_custom_emoji_id": "5789428375261023681", "callback_data": "broadcast_msg", "style": "success"},
         {"text": "System", "icon_custom_emoji_id": "5420155432272438703", "callback_data": "system_settings", "style": "primary"}],
        [{"text": "Used number", "icon_custom_emoji_id": "5352694861990501856", "callback_data": "show_used", "style": "success"},
         {"text": "Unused number", "icon_custom_emoji_id": "5352597830089347330", "callback_data": "show_unused", "style": "success"}],
        [{"text": f"💰 Pending Withdrawals ({len(pending_withdrawals)})", "icon_custom_emoji_id": "5190576863226933563", "callback_data": "adm_pending_w", "style": "danger"}],
        [{"text": "Close", "icon_custom_emoji_id": "5420130255174145507", "callback_data": "close_msg", "style": "danger"}]
    ]}

def shark_control_keyboard():
    status = "🟢 ON" if bot_settings.get("shark_panel_on", False) else "🔴 OFF"
    token_count = len(bot_settings.get("shark_tokens", []))
    return {"inline_keyboard": [
        [{"text": f"🦈 Shark Panel: {status}", "icon_custom_emoji_id": "5336972142066047577", "callback_data": "shark_toggle", "style": "success" if bot_settings.get("shark_panel_on") else "danger"}],
        [{"text": f"➕ Add Token ({token_count})", "icon_custom_emoji_id": "5420323438508155202", "callback_data": "shark_add_token", "style": "primary"}],
        [{"text": "🗑 View / Delete Tokens", "icon_custom_emoji_id": "5422557736330106570", "callback_data": "shark_view_tokens", "style": "danger"}],
        [{"text": "🔍 Live API Test", "icon_custom_emoji_id": "5310119944219927745", "callback_data": "shark_live_test", "style": "success"}],
        [{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "system_settings", "style": "primary"}]
    ]}

def cr_control_keyboard():
    status = "🟢 ON" if bot_settings.get("cr_panel_on", False) else "🔴 OFF"
    token_count = len(bot_settings.get("cr_tokens", []))
    return {"inline_keyboard": [
        [{"text": f"🌐 CR Panel: {status}", "icon_custom_emoji_id": "5336972142066047577", "callback_data": "cr_toggle", "style": "success" if bot_settings.get("cr_panel_on") else "danger"}],
        [{"text": f"➕ Add Token ({token_count})", "icon_custom_emoji_id": "5420323438508155202", "callback_data": "cr_add_token", "style": "primary"}],
        [{"text": "🗑 View / Delete Tokens", "icon_custom_emoji_id": "5422557736330106570", "callback_data": "cr_view_tokens", "style": "danger"}],
        [{"text": "🔍 Live API Test", "icon_custom_emoji_id": "5310119944219927745", "callback_data": "cr_live_test", "style": "success"}],
        [{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "system_settings", "style": "primary"}]
    ]}

def flex_control_keyboard():
    status = "🟢 ON" if bot_settings.get("flex_panel_on", False) else "🔴 OFF"
    token_count = len(bot_settings.get("flex_tokens", []))
    current_url = bot_settings.get("flex_api_url", "") or "❌ Not Set"
    return {"inline_keyboard": [
        [{"text": f"⚡ Flex Panel: {status}", "icon_custom_emoji_id": "5336972142066047577", "callback_data": "flex_toggle", "style": "success" if bot_settings.get("flex_panel_on") else "danger"}],
        [{"text": "🔗 Set API URL", "icon_custom_emoji_id": "5420323438508155202", "callback_data": "flex_set_url", "style": "primary"}],
        [{"text": f"➕ Add Token ({token_count})", "icon_custom_emoji_id": "5420323438508155202", "callback_data": "flex_add_token", "style": "primary"}],
        [{"text": "🗑 View / Delete Tokens", "icon_custom_emoji_id": "5422557736330106570", "callback_data": "flex_view_tokens", "style": "danger"}],
        [{"text": "🔍 Live API Test", "icon_custom_emoji_id": "5310119944219927745", "callback_data": "flex_live_test", "style": "success"}],
        [{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "system_settings", "style": "primary"}]
    ]}

def nexus_control_keyboard():
    status = "🟢 ON" if bot_settings.get("nexus_panel_on", False) else "🔴 OFF"
    key_count = len(bot_settings.get("nexus_keys", []))
    srv_count = len(bot_settings.get("nexus_services", {}))
    return {"inline_keyboard": [
        [{"text": f"🔷 Nexus-X Panel: {status}", "icon_custom_emoji_id": "5336972142066047577", "callback_data": "nexus_toggle", "style": "success" if bot_settings.get("nexus_panel_on") else "danger"}],
        [{"text": f"➕ Add API Key ({key_count})", "icon_custom_emoji_id": "5420323438508155202", "callback_data": "nexus_add_key", "style": "primary"}],
        [{"text": "🗑 View / Delete Keys", "icon_custom_emoji_id": "5422557736330106570", "callback_data": "nexus_view_keys", "style": "danger"}],
        [{"text": f"📦 Manage Services ({srv_count})", "icon_custom_emoji_id": "5257969839313526622", "callback_data": "manage_nexus_srv", "style": "primary"}],
        [{"text": "🔍 Live API Test", "icon_custom_emoji_id": "5310119944219927745", "callback_data": "nexus_live_test", "style": "success"}],
        [{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "system_settings", "style": "primary"}]
    ]}

def system_settings_keyboard():
    return {"inline_keyboard": [
        [{"text": "Stex Control", "icon_custom_emoji_id": "5336972142066047577", "callback_data": "stex_control", "style": "success"},
         {"text": "Voltx Control", "icon_custom_emoji_id": "5336972142066047577", "callback_data": "voltx_control", "style": "primary"}],
        [{"text": "Zenex Control", "icon_custom_emoji_id": "5336972142066047577", "callback_data": "zenex_control", "style": "success"},
         {"text": "🦈 Shark Panel", "icon_custom_emoji_id": "5336972142066047577", "callback_data": "shark_control", "style": "primary"}],
        [{"text": "🌐 CR Panel", "icon_custom_emoji_id": "5336972142066047577", "callback_data": "cr_control", "style": "success"},
         {"text": "⚡ Flex Panel", "icon_custom_emoji_id": "5336972142066047577", "callback_data": "flex_control", "style": "primary"}],
        [{"text": "🔷 Nexus-X Panel", "icon_custom_emoji_id": "5336972142066047577", "callback_data": "nexus_control", "style": "success"}],
        [{"text": "Force Join System", "icon_custom_emoji_id": "5420517437885943844", "callback_data": "manage_fj", "style": "primary"},
         {"text": "OTP Group", "icon_custom_emoji_id": "6235727781427155894", "callback_data": "manage_otp_groups", "style": "danger"}],
        [{"text": "Admin Management", "icon_custom_emoji_id": "5420145051336485498", "callback_data": "manage_admins", "style": "danger"},
         {"text": "User Management", "icon_custom_emoji_id": "5193063022226086560", "callback_data": "user_management", "style": "primary"}],
        [{"text": "Panel MANAGEMENT", "icon_custom_emoji_id": "5336879280578138635", "callback_data": "manage_panels", "style": "danger"},
         {"text": "Subscription", "icon_custom_emoji_id": "5190899075968441286", "callback_data": "dummy_alert", "style": "success"}],
        [{"text": "Premium Emoji", "icon_custom_emoji_id": "5352552689983067014", "callback_data": "manage_emojis", "style": "success"},
         {"text": "RAHIN CONTROL", "icon_custom_emoji_id": "5193100774988617665", "callback_data": "dxa_control", "style": "primary"}],
        [{"text": "Menu Design", "icon_custom_emoji_id": "5190751148704833975", "callback_data": "menu_design_list", "style": "primary"},
         {"text": "Test", "icon_custom_emoji_id": "5190781475468915802", "callback_data": "test_message_flow", "style": "primary"}],
        [{"text": f"🔔 Panel Alert: {'🟢 ON' if bot_settings.get('panel_alert_on', True) else '🔴 OFF'}", "icon_custom_emoji_id": "5352980533150259581", "callback_data": "tog_panel_alert", "style": "success" if bot_settings.get("panel_alert_on", True) else "danger"},
         {"text": f"📩 User OTP Notify: {'🟢 ON' if bot_settings.get('user_otp_notify', True) else '🔴 OFF'}", "icon_custom_emoji_id": "5352694861990501856", "callback_data": "tog_user_otp_notify", "style": "success" if bot_settings.get("user_otp_notify", True) else "danger"}],
        [{"text": f"⚠️ No-Match Alert: {'🟢 ON' if bot_settings.get('no_match_alert_on', True) else '🔴 OFF'}", "icon_custom_emoji_id": "5336944168944047463", "callback_data": "tog_no_match_alert", "style": "success" if bot_settings.get("no_match_alert_on", True) else "danger"}],
        [{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "back_to_admin", "style": "danger"}]
    ]}

def get_user_management_text():
    # 🌟 Fast & Free User Management Stats!
    total = len(all_known_users)
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    txt = f"""➖➖➖➖➖➖➖➖
《 👋 USER VIEW 》
➖➖➖➖➖➖➖➖
📊 LIVE STATISTICS:
➖➖➖➖➖➖➖➖
🫂 TOTAL USERS: {total}
✅ VERIFIED USERS: (Hidden to save DB Cost)
🚫 BANNED USERS: (Hidden to save DB Cost)
➖➖➖➖➖➖➖➖
⌛ UPDATED: {now_str}"""
    return render_body_text(txt)

def user_management_keyboard():
    return {"inline_keyboard": [
        [{"text": "Manage Balance", "icon_custom_emoji_id": "5190576863226933563", "callback_data": "um_manage_balance", "style": "primary"},
         {"text": "Ban/Unban User", "icon_custom_emoji_id": "5334807341109908955", "callback_data": "um_ban_unban", "style": "danger"}],
        [{"text": "User Profile", "icon_custom_emoji_id": "5352861489541714456", "callback_data": "um_user_profile", "style": "success"},
         {"text": "💰 User OTP Rate", "icon_custom_emoji_id": "5190576863226933563", "callback_data": "um_user_otp_rate", "style": "primary"}],
        [{"text": "📋 View All User Rates", "icon_custom_emoji_id": "5352877703043258544", "callback_data": "um_view_user_rates", "style": "success"}],
        [{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "system_settings", "style": "primary"}]
    ]}

def menu_design_list_keyboard():
    return {"inline_keyboard": [
        [{"text": "Edit /start Menu", "icon_custom_emoji_id": "5395444784611480792", "callback_data": "md_edit_start", "style": "primary"}],
        [{"text": "Edit GET NUMBER", "icon_custom_emoji_id": "5337132498965010628", "callback_data": "md_edit_get_number", "style": "success"},
         {"text": "Edit Search Number", "icon_custom_emoji_id": "5190645917711114179", "callback_data": "md_edit_search_number", "style": "success"}],
        [{"text": "Edit Select Country", "icon_custom_emoji_id": "5336972142066047577", "callback_data": "md_edit_select_country", "style": "primary"}],
        [{"text": "Edit TRAFFIC", "icon_custom_emoji_id": "5353032893096567467", "callback_data": "md_edit_traffic", "style": "primary"},
         {"text": "Edit Refer", "icon_custom_emoji_id": "5420396762189831222", "callback_data": "md_edit_refer", "style": "primary"}],
        [{"text": "Edit WITHDRAWAL", "icon_custom_emoji_id": "5352585194295564660", "callback_data": "md_edit_withdrawal", "style": "danger"},
         {"text": "Edit SUPPORT", "icon_custom_emoji_id": "5420145051336485498", "callback_data": "md_edit_support", "style": "danger"}],
        [{"text": "Reset Defaults", "icon_custom_emoji_id": "5192812028632274956", "callback_data": "md_reset_defaults", "style": "success"}],
        [{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "system_settings", "style": "primary"}]
    ]}

def menu_edit_options_keyboard(menu_key):
    return {"inline_keyboard": [
        [{"text": "Edit Body (Text)", "icon_custom_emoji_id": "5395444784611480792", "callback_data": f"md_text_{menu_key}", "style": "primary"}],
        [{"text": "Edit Inline Buttons", "icon_custom_emoji_id": "5420155432272438703", "callback_data": f"md_btns_{menu_key}", "style": "success"}],
        [{"text": "Back to Menus", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "menu_design_list", "style": "danger"}]
    ]}

def menu_buttons_list_keyboard(menu_key):
    kb = []
    btns = bot_settings["custom_messages"].get(menu_key, {}).get("buttons", [])
    for idx, btn in enumerate(btns):
        kb.append([{"text": f"Del: {btn['text']}", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"md_delbtn_{menu_key}_{idx}", "style": "danger"}])
    kb.append([{"text": "Add Inline Button", "icon_custom_emoji_id": "5420323438508155202", "callback_data": f"md_addbtn_{menu_key}", "style": "success"}])
    kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"md_edit_{menu_key}", "style": "primary"}])
    return {"inline_keyboard": kb}

def generate_emoji_txt(mode):
    """
    Generate downloadable TXT content for premium emojis.
    mode='flags'  -> generates flag emoji list
    mode='apps'   -> generates service/app emoji list
    Returns bytes or None if empty.
    """
    lines = []
    if mode == "flags":
        flags_db = bot_settings.get("premium_flags", {})
        for code, data in flags_db.items():
            char = data.get("char", "")
            iso = data.get("iso", "")
            name = data.get("name", "")
            eid = data.get("id", "")
            if char and eid:
                json_part = json.dumps({"emoji": char, "id": eid}, ensure_ascii=False)
                lines.append(f"{char} ({code}) ({iso}) {name} {json_part}")
    elif mode == "apps":
        apps_db = bot_settings.get("premium_apps", {})
        for key, data in apps_db.items():
            char = data.get("char", "")
            name = data.get("name", key.title())
            eid = data.get("id", "")
            if char and eid:
                json_part = json.dumps({"emoji": char, "id": eid}, ensure_ascii=False)
                lines.append(f"{char} {name} {json_part}")
    if not lines:
        return None
    return "\n".join(lines).encode("utf-8")

def emoji_settings_keyboard():
    return {"inline_keyboard": [
        [{"text": "Upload Flags (TXT)", "icon_custom_emoji_id": "5353001161878182134", "callback_data": "up_flags_txt", "style": "primary"},
         {"text": "Download Flags", "icon_custom_emoji_id": "5257969839313526622", "callback_data": "dl_flags_txt", "style": "success"}],
        [{"text": "Upload Services (TXT)", "icon_custom_emoji_id": "5353001161878182134", "callback_data": "up_apps_txt", "style": "primary"},
         {"text": "Download Services", "icon_custom_emoji_id": "5257969839313526622", "callback_data": "dl_apps_txt", "style": "success"}],
        [{"text": "Delete All Flags", "icon_custom_emoji_id": "5422557736330106570", "callback_data": "del_all_flags", "style": "danger"},
         {"text": "Add Single Emoji", "icon_custom_emoji_id": "5420323438508155202", "callback_data": "add_single_emoji", "style": "success"}],
        [{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "system_settings", "style": "danger"}]
    ]}

def fj_settings_keyboard():
    status_text = 'ON' if bot_settings['fj_on'] else 'OFF'
    status_icon = "5352694861990501856" if bot_settings['fj_on'] else "5318840353510408444"
    kb = [[{"text": f"STATUS: {status_text}", "icon_custom_emoji_id": status_icon, "callback_data": "toggle_fj", "style": "primary"}]]
    for idx, ch in enumerate(bot_settings["fj_channels"]):
        kb.append([{"text": f"Delete: {ch}", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"del_fj_{idx}", "style": "danger"}])
    kb.append([{"text": "Add Channel", "icon_custom_emoji_id": "5420323438508155202", "callback_data": "add_fj", "style": "success"}])
    kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "system_settings", "style": "primary"}])
    return {"inline_keyboard": kb}

def admin_settings_keyboard():
    kb = []
    for idx, adm in enumerate(bot_settings["admins"]):
        text_btn = f"Owner: {adm}" if adm == OWNER_ID else f"Delete: {adm}"
        icon_id = "5353032893096567467" if adm == OWNER_ID else "5420130255174145507"
        cb_data = "ignore" if adm == OWNER_ID else f"del_adm_{idx}"
        kb.append([{"text": text_btn, "icon_custom_emoji_id": icon_id, "callback_data": cb_data, "style": "danger" if adm != OWNER_ID else "primary"}])
    kb.append([{"text": "Add Admin", "icon_custom_emoji_id": "5420323438508155202", "callback_data": "add_adm", "style": "success"}])
    kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "system_settings", "style": "primary"}])
    return {"inline_keyboard": kb}

def otp_groups_list_keyboard():
    kb = [[{"text": "Edit OTP Button Link", "icon_custom_emoji_id": "5420517437885943844", "callback_data": "edit_otp_link", "style": "primary"}],
          [{"text": "Edit Main Channel Link", "icon_custom_emoji_id": "5217822164362739968", "callback_data": "edit_main_channel", "style": "primary"}]]
    for idx, fg in enumerate(bot_settings["fw_groups"]):
        kb.append([{"text": f"Group: {fg['chat_id']}", "icon_custom_emoji_id": "5193063022226086560", "callback_data": f"manage_fw_{idx}", "style": "primary"}])
    kb.append([{"text": "Add Forward Group", "icon_custom_emoji_id": "5420323438508155202", "callback_data": "add_fw", "style": "success"}])
    kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "system_settings", "style": "danger"}])
    return {"inline_keyboard": kb}


def stex_control_keyboard():
    return {"inline_keyboard": [
        [{"text": "Add Stex Key", "icon_custom_emoji_id": "5420323438508155202", "callback_data": "add_stex_key", "style": "success"},
         {"text": "View/Del Keys", "icon_custom_emoji_id": "5422557736330106570", "callback_data": "view_stex_keys", "style": "danger"}],
        [{"text": "Manage Stex Services", "icon_custom_emoji_id": "5192739271886282680", "callback_data": "manage_stex_srv", "style": "success"}],
        [{"text": "Search Country", "icon_custom_emoji_id": "5336972142066047577", "callback_data": "stex_search_country", "style": "primary"}],
        [{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "system_settings", "style": "primary"}]
    ]}

def voltx_control_keyboard():
    return {"inline_keyboard": [
        [{"text": "Add Voltx Key", "icon_custom_emoji_id": "5420323438508155202", "callback_data": "add_voltx_key", "style": "success"},
         {"text": "View/Del Keys", "icon_custom_emoji_id": "5422557736330106570", "callback_data": "view_voltx_keys", "style": "danger"}],
        [{"text": "Manage Voltx Services", "icon_custom_emoji_id": "5192739271886282680", "callback_data": "manage_voltx_srv", "style": "success"}],
        [{"text": "Search Country", "icon_custom_emoji_id": "5336972142066047577", "callback_data": "voltx_search_country", "style": "primary"}],
        [{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "system_settings", "style": "primary"}]
    ]}

def zenex_control_keyboard():
    return {"inline_keyboard": [
        [{"text": "Add Zenex Key", "icon_custom_emoji_id": "5420323438508155202", "callback_data": "add_zenex_key", "style": "success"},
         {"text": "View/Del Keys", "icon_custom_emoji_id": "5422557736330106570", "callback_data": "view_zenex_keys", "style": "danger"}],
        [{"text": "Manage Zenex Services", "icon_custom_emoji_id": "5192739271886282680", "callback_data": "manage_zenex_srv", "style": "success"}],
            [{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "system_settings", "style": "primary"}]
    ]}

def specific_fw_group_keyboard(idx):
    group = bot_settings["fw_groups"][idx]
    kb = []
    for b_idx, btn in enumerate(group.get("buttons", [])):
        kb.append([{"text": f"Del: {btn['text']}", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"del_fwbtn_{idx}_{b_idx}", "style": "danger"}])
    
    kb.append([{"text": "Add Inline Button", "icon_custom_emoji_id": "5420323438508155202", "callback_data": f"add_fwbtn_{idx}", "style": "success"}])
    kb.append([{"text": "Delete Entire Group", "icon_custom_emoji_id": "5422557736330106570", "callback_data": f"del_fw_{idx}", "style": "danger"}])
    kb.append([{"text": "Back to Groups", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "manage_otp_groups", "style": "primary"}])
    return {"inline_keyboard": kb}

def dxa_control_keyboard():
    w_status = "ON" if bot_settings["withdraw_on"] else "OFF"
    sup_status = "ON" if bot_settings.get("support_link") else "OFF"
    grp_status = "ON" if bot_settings.get("w_group") else "OFF"
    bulk_auto = "ON ✅" if bot_settings.get("bulk_auto_approve") else "OFF ❌"
    return {"inline_keyboard": [
        [{"text": f"WITHDRAW: {w_status}", "icon_custom_emoji_id": "5348469219761626211", "callback_data": "dxa_toggle_w", "style": "primary"}],
        [{"text": f"MIN WITHDRAW: {bot_settings['min_withdraw']}", "icon_custom_emoji_id": "5352877703043258544", "callback_data": "dxa_min_w", "style": "success"},
         {"text": f"OTP REWARD: {bot_settings['otp_reward']}", "icon_custom_emoji_id": "5190576863226933563", "callback_data": "dxa_otp_r", "style": "primary"}],
        [{"text": f"REFER REWARD: {bot_settings['refer_reward']}", "icon_custom_emoji_id": "5420396762189831222", "callback_data": "dxa_ref_r", "style": "success"},
         {"text": f"COOLDOWN: {bot_settings['cooldown']}s", "icon_custom_emoji_id": "5337172996211648018", "callback_data": "dxa_cool", "style": "primary"}],
        [{"text": f"NUM/REQ: {bot_settings['num_req']}", "icon_custom_emoji_id": "5337132498965010628", "callback_data": "dxa_num_req", "style": "success"},
         {"text": f"NUM/SHARE: {bot_settings['num_share']}", "icon_custom_emoji_id": "5352862640592949843", "callback_data": "dxa_num_share", "style": "primary"}],
        [{"text": f"SUPPORT LINK: {sup_status}", "icon_custom_emoji_id": "5420145051336485498", "callback_data": "dxa_sup_link", "style": "success"},
         {"text": "W. METHODS", "icon_custom_emoji_id": "5190899075968441286", "callback_data": "manage_w_methods", "style": "primary"}],
        [{"text": "SERVICE RATES", "icon_custom_emoji_id": "5190576863226933563", "callback_data": "dxa_service_rates", "style": "success"},
         {"text": f"W. GROUP: {grp_status}", "icon_custom_emoji_id": "5420517437885943844", "callback_data": "dxa_w_group", "style": "primary"}],
        [{"text": f"📦 BULK AUTO APPROVE: {bulk_auto}", "icon_custom_emoji_id": "5352694861990501856", "callback_data": "dxa_toggle_bulk_auto", "style": "success" if bot_settings.get("bulk_auto_approve") else "danger"}],
        [{"text": f"RAND NAME PASS: {'SET ✅' if bot_settings.get('rand_name_pass') else 'NOT SET ❌'}", "icon_custom_emoji_id": "5352552689983067014", "callback_data": "dxa_set_rand_pass", "style": "primary"}],
        [{"text": "BACK", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "system_settings", "style": "danger"}]
    ]}

def w_methods_keyboard():
    kb = []
    for idx, m in enumerate(bot_settings["w_methods"]):
        kb.append([{"text": f"Delete: {m}", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"del_wm_{idx}", "style": "danger"}])
    kb.append([{"text": "Add Method", "icon_custom_emoji_id": "5420323438508155202", "callback_data": "add_wm", "style": "success"}])
    kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "dxa_control", "style": "primary"}])
    return {"inline_keyboard": kb}

def typed_panels_list_keyboard(p_type):
    kb = []
    for idx, p in enumerate(bot_settings["panels"]):
        if p.get("type", "API Panel") != p_type: continue
        action_text = f"Turn OFF {p['name']}" if p['status'] == 'ON' else f"Turn ON {p['name']}"
        action_icon = "5318840353510408444" if p['status'] == 'ON' else "5192812028632274956"
        icon_id = "5420155432272438703" 
        kb.append([
            {"text": action_text, "icon_custom_emoji_id": action_icon, "callback_data": f"tog_pnl_{idx}", "style": "danger" if p['status'] == 'ON' else "success"},
            {"text": f"{p['name']}", "icon_custom_emoji_id": icon_id, "callback_data": f"conf_pnl_{idx}", "style": "primary"}
        ])
    add_cb = "add_api_panel" if p_type == "API Panel" else "add_cpt_panel"
    kb.append([{"text": "Add New Provider", "icon_custom_emoji_id": "5420323438508155202", "callback_data": add_cb, "style": "success"}])
    kb.append([{"text": "Delete Provider", "icon_custom_emoji_id": "5336944168944047463", "callback_data": f"list_del_{'api' if p_type=='API Panel' else 'cpt'}", "style": "danger"}])
    kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "manage_panels", "style": "primary"}])
    return {"inline_keyboard": kb}

def panel_config_keyboard(idx):
    p = bot_settings["panels"][idx]
    
    kb = []
    action_text = "Turn OFF" if p['status'] == 'ON' else "Turn ON"
    action_icon = "5318840353510408444" if p['status'] == 'ON' else "5192812028632274956"
    kb.append([{"text": action_text, "icon_custom_emoji_id": action_icon, "callback_data": f"tog_pnl_{idx}", "style": "danger" if p['status'] == 'ON' else "success"}])
    
    if p["type"] != "Auto Captcha Panel":
        rec_count_text = "All (Unlimited)" if p.get('records', 0) == 0 else str(p.get('records'))
        kb.append([{"text": "Set API URL", "icon_custom_emoji_id": "5420517437885943844", "callback_data": f"set_p_api_{idx}", "style": "primary"}])
        kb.append([{"text": "Set Token", "icon_custom_emoji_id": "5353022963132174959", "callback_data": f"set_p_tok_{idx}", "style": "primary"}])
        kb.append([{"text": "🌐 Full API (URL+Token)", "icon_custom_emoji_id": "5420517437885943844", "callback_data": f"set_p_fapi_{idx}", "style": "primary"}])
        kb.append([{"text": f"Set Records Count: {rec_count_text}", "icon_custom_emoji_id": "5192739271886282680", "callback_data": f"set_p_rec_{idx}", "style": "primary"}])
        
    kb.append([{"text": "Test Connection", "icon_custom_emoji_id": "5352694861990501856", "callback_data": f"test_p_conn_{idx}", "style": "success"}])
        
    back_data = "manage_api_panels" if p.get("type", "API Panel") == "API Panel" else "manage_cpt_panels"
    kb.append([{"text": "Back to Providers", "icon_custom_emoji_id": "5267490665117275176", "callback_data": back_data, "style": "danger"}])
    return {"inline_keyboard": kb}

def build_traffic_ui():
    global recent_traffic
    current_time = time.time()
    recent_traffic = [t for t in recent_traffic if current_time - t.get("time", 0) <= 3600]
    
    stats = {}
    for t in recent_traffic:
        srv = t.get("service", "Unknown")
        iso = t.get("iso", "XX")
        flag = t.get("flag", "🌍")
        
        if srv not in stats:
            stats[srv] = {}
        if iso not in stats[srv]:
            stats[srv][iso] = {"count": 0, "flag": flag}
        stats[srv][iso]["count"] += 1
        
    txt = "╔═════════════════╗\n║  📈 <b>NETWORK TRAFFIC</b>\n╚═════════════════╝\n\n"
    
    kb = []
    if not stats:
        txt += "<i>No recent traffic found in the last hour...</i>\n"
    else:
        srv_totals = []
        for srv, countries in stats.items():
            total = sum(c["count"] for c in countries.values())
            srv_totals.append((srv, total, countries))
        
        srv_totals.sort(key=lambda x: x[1], reverse=True)
        
        for srv, total, countries in srv_totals:
            app_full_name, prem_app_html = get_service_info_html(srv)
            txt += f"[ {prem_app_html} <b>{app_full_name}</b> ]\n│\n"
            
            c_list = sorted(countries.items(), key=lambda x: x[1]["count"], reverse=True)
            c_list = c_list[:7] 
            
            for i, (iso, c_data) in enumerate(c_list):
                prem_flag_html = get_flag_info_html(iso)
                count = c_data["count"]
                
                c_name = iso
                for code, fdata in bot_settings.get("premium_flags", {}).items():
                    if fdata.get("iso") == iso:
                        c_name = fdata.get("name", iso)
                        break
                        
                txt += f"├ {prem_flag_html} <b>{c_name} ({iso})</b>\n"
                txt += f"│ ╰ Success: {count}\n"
                if i < len(c_list) - 1:
                    txt += "│\n"
            txt += "\n"
        
        # 🌟 FIX: [:3] লিমিট তুলে দেওয়া হলো, এখন যতো সার্ভিস থাকবে সবগুলোর বাটন নিচে শো করবে!
        for srv, _, _ in srv_totals: 
            safe_srv = srv[:20] 
            # বাটনে সুন্দরভাবে ফুল নাম দেখানোর জন্য
            app_full_name, _ = get_service_info_html(safe_srv, safe_srv)
            kb.append([{"text": f"Explore {app_full_name} Range", "icon_custom_emoji_id": "5190645917711114179", "callback_data": f"exp_rng_{safe_srv}", "style": "success"}])
            
    txt = render_body_text(txt)
    kb.append([{"text": "Refresh", "icon_custom_emoji_id": "5465368548702446780", "callback_data": "refresh_traffic", "style": "primary"}])
    kb.append([{"text": "Close", "icon_custom_emoji_id": "5420130255174145507", "callback_data": "close_msg", "style": "danger"}])
    
    return txt, {"inline_keyboard": kb}

# ==========================================
# Message Handler
# ==========================================
def handle_message(msg):
    global total_uploaded_stats, total_assigned_stats
    try:
        chat_id = msg["chat"]["id"]
    except Exception:
        return
    try:
        _handle_message_inner(msg)
    except Exception as e:
        print(f"❌ handle_message crash (user {chat_id}): {e}")

def _handle_message_inner(msg):
    global total_uploaded_stats, total_assigned_stats
    chat_id = msg["chat"]["id"]
    chat_type = msg["chat"].get("type", "private")
    
    if chat_type != "private":
        return
        
    # Telegram sends back the exact bold Unicode label displayed on the
    # reply keyboard. Normalize it so all existing menu handlers continue
    # routing by their stable plain-text command names.
    text = _plain_button_text(msg.get("text", ""))
    register_user_local(chat_id) # 🌟 Save User locally for Free Broadcasts!

    if is_user_banned(chat_id):
        send_message(chat_id, render_body_text("🚫 <b>You are banned from using this bot!</b>\nIf you think this is a mistake, please contact support."))
        return
    
    # --- REFERRAL FIX: Save inviter BEFORE Force Join ---
    if text.startswith("/start"):
        parts = text.split()
        if len(parts) > 1 and parts[1].isdigit():
            inviter = int(parts[1])
            if inviter != chat_id:
                # Save referred_by (works with or without Firestore)
                u_data = get_user(chat_id)
                if not u_data.get("referred_by"):
                    if not db:
                        _get_local_user(chat_id)["referred_by"] = inviter
                        _get_local_user(chat_id)["ref_paid"] = False
                        _save_users_local()
                    else:
                        try:
                            db.collection('users').document(str(chat_id)).update({"referred_by": inviter, "ref_paid": False})
                        except Exception:
                            pass
                    # cache update
                    cached = _cache_get(chat_id)
                    if cached:
                        cached["referred_by"] = inviter
                        cached["ref_paid"] = False
                        _cache_set(chat_id, cached)
                        
    if not check_force_join(chat_id):
        send_force_join_msg(chat_id)
        return

    # ─── Admin Reply → Forward to User (Live Support) ────────────────────────
    if is_admin(chat_id) and msg.get("reply_to_message") and text:
        replied_msg_id = msg["reply_to_message"]["message_id"]
        target_user = support_msg_map.get((chat_id, replied_msg_id))
        if target_user:
            send_message(target_user, render_body_text(
                f"💬 <b>Admin Reply:</b>\n\n{text}"
            ))
            send_message(chat_id, render_body_text("✅ Reply sent to user."))
            return
    # ─────────────────────────────────────────────────────────────────────────

    MAIN_MENU_CMDS = ["100 Bulk Number", "100 Buy Number", "Referral", "Balance & Withdrawal", "Withdrawal", "Admin Panel", "Get Number", "Search Number", "TRAFFIC", "Refer", "WITHDRAWAL", "SUPPORT", "2FA ONLINE", "Live Support Admin", "2F CODE", "LEADERBOARD"]
    
    is_main_cmd = False
    if text in MAIN_MENU_CMDS or text.startswith("/start"):
        if chat_id in user_states: del user_states[chat_id]
        if chat_id in temp_data: del temp_data[chat_id]
        is_main_cmd = True
    
    if chat_id in user_states and not is_main_cmd:
        state = user_states[chat_id]
        
        # 🌟 Auto Captcha Panel Setup Flow 
        if state == "wait_for_cpanel_url" and text:
            temp_data[chat_id]["p_data"]["login_url"] = text.strip()
            user_states[chat_id] = "wait_for_cpanel_user"
            send_message(chat_id, render_body_text("2️⃣ <b>Username</b>\n➡️ Panel এর Username দিন:"), reply_markup=get_cancel_kb())
            return
            
        elif state == "wait_for_cpanel_user" and text:
            temp_data[chat_id]["p_data"]["username"] = text.strip()
            user_states[chat_id] = "wait_for_cpanel_pass"
            send_message(chat_id, render_body_text("3️⃣ <b>Password</b>\n➡️ Panel এর Password দিন:"), reply_markup=get_cancel_kb())
            return
            
        elif state == "wait_for_cpanel_pass" and text:
            temp_data[chat_id]["p_data"]["password"] = text.strip()
            user_states[chat_id] = "wait_for_cpanel_msg_link"
            send_message(chat_id, render_body_text("4️⃣ <b>Message Link</b>\n➡️ যেখান থেকে SMS/OTP ডাটা (JSON) আসবে সেই Link দিন:"), reply_markup=get_cancel_kb())
            return
            
        elif state == "wait_for_cpanel_msg_link" and text:
            temp_data[chat_id]["p_data"]["msg_link"] = text.strip()
            user_states[chat_id] = "wait_for_cpanel_num_col_name"
            send_message(chat_id, render_body_text("5️⃣ <b>Number Column Name</b>\n➡️ Data তে Number column এর নাম কী? (যেমন: number, phone):"), reply_markup=get_cancel_kb())
            return
            
        elif state == "wait_for_cpanel_num_col_name" and text:
            temp_data[chat_id]["p_data"]["num_col_name"] = text.strip()
            user_states[chat_id] = "wait_for_cpanel_num_col_idx"
            send_message(chat_id, render_body_text("6️⃣ <b>Number Column Serial</b>\n➡️ Number Column এর Serial Number কত? (যেমন: 3, 5):"), reply_markup=get_cancel_kb())
            return
            
        elif state == "wait_for_cpanel_num_col_idx" and text:
            if text.isdigit():
                temp_data[chat_id]["p_data"]["num_col_idx"] = int(text)
                user_states[chat_id] = "wait_for_cpanel_msg_col_name"
                send_message(chat_id, render_body_text("7️⃣ <b>Message Column Name</b>\n➡️ Message/OTP column এর নাম কী? (যেমন: message, sms):"), reply_markup=get_cancel_kb())
            else:
                 send_message(chat_id, render_body_text("❌ Please enter a valid number serial!"), reply_markup=get_cancel_kb())
            return
            
        elif state == "wait_for_cpanel_msg_col_name" and text:
            temp_data[chat_id]["p_data"]["msg_col_name"] = text.strip()
            user_states[chat_id] = "wait_for_cpanel_msg_col_idx"
            send_message(chat_id, render_body_text("8️⃣ <b>Message Column Serial</b>\n➡️ Message Column এর Serial Number কত? (যেমন: 5, 7):"), reply_markup=get_cancel_kb())
            return
            
        elif state == "wait_for_cpanel_msg_col_idx" and text:
            if text.isdigit():
                temp_data[chat_id]["p_data"]["msg_col_idx"] = int(text)
                temp_data[chat_id]["p_data"]["login_status"] = "⏳ Pending Auto-Login..."
                
                # Save the panel configuration
                bot_settings["panels"].append(temp_data[chat_id]["p_data"])
                save_db()
                
                send_message(chat_id, render_body_text(f"{PEM['ok']} <b>Auto Captcha Panel Added Successfully!</b>\nবট এখন থেকে নিজেই ব্যাকগ্রাউন্ডে ক্যাপচা সলভ করে লগিন করে নিবে।"), reply_markup=main_menu(chat_id))
                
                msg_id = temp_data[chat_id]["msg_id"]
                handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "manage_cpt_panels", "id": "internal"})
                
                del user_states[chat_id]
                del temp_data[chat_id]
            else:
                 send_message(chat_id, render_body_text("❌ Please enter a valid number serial!"), reply_markup=get_cancel_kb())
            return

        # --- User Management Flows ---
        elif state == "wait_for_um_bal_uid" and text:
            target_uid_str = text.strip()
            if not target_uid_str.isdigit():
                send_message(chat_id, render_body_text("❌ Invalid ID! Please send a numeric User ID."), reply_markup=get_cancel_kb())
                return
            target_uid = int(target_uid_str)
            u_data = get_user(target_uid)
            current_bal = u_data.get('balance', 0.0)
            temp_data[chat_id]["target_uid"] = target_uid
            user_states[chat_id] = "wait_for_um_bal_amt"
            send_message(chat_id, render_body_text(f"✅ User found!\n💰 Current Balance: {current_bal} ৳\n\n📝 Send the amount to ADD (e.g. 50) or REMOVE (e.g. -50):"), reply_markup=get_cancel_kb())
            return

        elif state == "wait_for_um_bal_amt" and text:
            try:
                amt = float(text.strip())
                target_uid = temp_data[chat_id]["target_uid"]
                update_balance(target_uid, amt)
                send_message(chat_id, render_body_text(f"{PEM['ok']} Balance updated successfully for {target_uid}!"), reply_markup=main_menu(chat_id))
                send_message(target_uid, render_body_text(f"🔔 Your balance has been adjusted by <b>{amt} ৳</b> by an Admin."))
                del user_states[chat_id]
                del temp_data[chat_id]
            except ValueError:
                send_message(chat_id, render_body_text("❌ Invalid amount! Please send a number."), reply_markup=get_cancel_kb())
            return

        elif state == "wait_for_um_ban_uid" and text:
            target_uid_str = text.strip()
            if not target_uid_str.isdigit():
                send_message(chat_id, render_body_text("❌ Invalid ID!"), reply_markup=get_cancel_kb())
                return
            target_uid = int(target_uid_str)
            u_data = get_user(target_uid)
            current_status = u_data.get("banned", False)
            new_status = not current_status
            if db:
                try:
                    db.collection('users').document(str(target_uid)).update({"banned": new_status})
                except Exception as e:
                    print(f"⚠️ ban update Firestore failed: {e}")
            else:
                _get_local_user(target_uid)["banned"] = new_status
                _save_users_local()
            # cache ও update করো
            cached = _cache_get(target_uid)
            if cached:
                cached["banned"] = new_status
                _cache_set(target_uid, cached)
            user_banned_cache[target_uid] = {'banned': new_status, 'time': time.time()}
            status_text = "BANNED 🚫" if new_status else "UNBANNED ✅"
            send_message(chat_id, render_body_text(f"✅ User {target_uid} has been {status_text}!"), reply_markup=main_menu(chat_id))
            del user_states[chat_id]
            del temp_data[chat_id]
            return

        elif state == "wait_for_um_prof_uid" and text:
            target_uid_str = text.strip()
            if not target_uid_str.isdigit():
                send_message(chat_id, render_body_text("❌ Invalid ID!"), reply_markup=get_cancel_kb())
                return
            target_uid = int(target_uid_str)
            data = get_user(target_uid)
            is_verified = True if data.get('total_otps', 0) > 0 else data.get('verified', False)
            prof_text = f"""➖➖➖➖➖➖➖➖
👤 <b>USER PROFILE</b>
➖➖➖➖➖➖➖➖
🆔 ID: <code>{target_uid}</code>
💰 Balance: {data.get('balance', 0.0)} ৳
🤝 Total Refers: {data.get('total_refers', 0)}
🔐 Total OTPs: {data.get('total_otps', 0)}
✅ Verified: {is_verified}
🚫 Banned: {data.get('banned', False)}
➖➖➖➖➖➖➖➖"""
            kb = {"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "user_management", "style": "primary"}]]}
            send_message(chat_id, render_body_text(prof_text), reply_markup=kb)
            del user_states[chat_id]
            del temp_data[chat_id]
            return

        # --- Menu Design Flow ---
        elif state == "wait_for_menu_text" and text:
            try:
                menu_key = temp_data[chat_id]["menu_key"]
                formatted_html_text = extract_premium_html(msg)
                
                bot_settings["custom_messages"][menu_key]["text"] = formatted_html_text
                save_db()
                
                delete_message(chat_id, msg["message_id"])
                
                preview_text = render_body_text(formatted_html_text)
                success_text = f"{PEM['ok']} <b>Message Body Updated successfully!</b>\n\n🎨 <b>Editing: {menu_key.upper()}</b>\n\nPreview of current Text:\n{preview_text}"
                edit_message(chat_id, temp_data[chat_id]["msg_id"], render_body_text(success_text), reply_markup=menu_edit_options_keyboard(menu_key))
            except Exception as e:
                send_message(chat_id, f"❌ Error saving text: {e}")
            finally:
                if chat_id in user_states: del user_states[chat_id]
                if chat_id in temp_data: del temp_data[chat_id]
            return
            
        elif state == "wait_for_menu_btn" and text:
            try:
                menu_key = temp_data[chat_id]["menu_key"]
                if "-" in text:
                    parts = text.split("-", 1)
                    btn_text = parts[0].strip()
                    btn_url = parts[1].strip()
                    
                    emoji_id = None
                    emoji_char = ""
                    for ent in msg.get("entities", []):
                        if ent.get("type") == "custom_emoji":
                            emoji_id = ent.get("custom_emoji_id")
                            offset = ent.get("offset", 0)
                            length = ent.get("length", 0)
                            b_text = text.encode('utf-16-le')
                            emoji_char = b_text[offset*2:(offset+length)*2].decode('utf-16-le')
                            break
                            
                    if emoji_char:
                        btn_text = btn_text.replace(emoji_char, "").strip()
                        
                    btn_data = {"text": btn_text, "url": btn_url, "style": "primary"}
                    if emoji_id:
                        btn_data["icon_custom_emoji_id"] = emoji_id
                        
                    bot_settings["custom_messages"][menu_key]["buttons"].append(btn_data)
                    save_db()
                    delete_message(chat_id, msg["message_id"])
                    edit_message(chat_id, temp_data[chat_id]["msg_id"], render_body_text(f"{PEM['gear']} <b>Edit Inline Buttons: {menu_key.upper()}</b>"), reply_markup=menu_buttons_list_keyboard(menu_key))
                else:
                    send_message(chat_id, render_body_text(f"{PEM['no']} Invalid format. Use <code>Button Text - https://link.com</code>"))
            except Exception as e:
                 pass
            finally:
                if chat_id in user_states: del user_states[chat_id]
                if chat_id in temp_data: del temp_data[chat_id]
            return

        elif state == "wait_for_test_service" and text:
            temp_data[chat_id]["service"] = text.strip()
            user_states[chat_id] = "wait_for_test_number"
            send_message(chat_id, render_body_text("📝 Send the Number (e.g. +8801712345678):"), reply_markup=get_cancel_kb())
            return
            
        elif state == "wait_for_test_number" and text:
            temp_data[chat_id]["number"] = text.strip()
            user_states[chat_id] = "wait_for_test_otp"
            send_message(chat_id, render_body_text("📝 Send the OTP (e.g. 556677):"), reply_markup=get_cancel_kb())
            return
            
        elif state == "wait_for_test_otp" and text:
            temp_data[chat_id]["otp"] = text.strip()
            user_states[chat_id] = "wait_for_test_lang"
            send_message(chat_id, render_body_text("📝 Send the Language (e.g. EN, AR):"), reply_markup=get_cancel_kb())
            return
            
        elif state == "wait_for_test_lang" and text:
            lang = text.strip().upper()
            if not lang.startswith("#"):
                lang = "#" + lang
                
            srv = temp_data[chat_id]["service"]
            num = temp_data[chat_id]["number"]
            otp = temp_data[chat_id]["otp"]
            
            masked = mask_number(num)
            prem_flag_html = get_flag_info_html(num)
            char, iso = get_flag_and_code(num)
            app_full_name, prem_app_html = get_service_info_html(srv)
            
            display_num_test = f"+{num}" if not str(num).startswith("+") else str(num)
            fw_msg = render_body_text(f"{get_flag_info_html(display_num_test)} {get_country_name(iso)} {prem_app_html} {display_num_test}")
            
            _fw_send_otp(bot_settings.get("fw_groups", []), app_full_name, prem_app_html, char, iso, display_num_test, lang, otp)
            _user_send_otp(chat_id, char, iso, prem_app_html, display_num_test, otp, 0, False)
            del user_states[chat_id]
            del temp_data[chat_id]
            return

        elif state == "wait_for_emoji_extract":
            entities = msg.get("entities", [])
            custom_emoji_id = None
            emoji_text = ""
            for ent in entities:
                if ent.get("type") == "custom_emoji":
                    custom_emoji_id = ent.get("custom_emoji_id")
                    offset = ent.get("offset", 0)
                    length = ent.get("length", 0)
                    b_text = msg.get("text", "").encode('utf-16-le')
                    emoji_text = b_text[offset*2:(offset+length)*2].decode('utf-16-le')
                    break
            
            if custom_emoji_id:
                temp_data[chat_id] = {"id": custom_emoji_id, "char": emoji_text}
                user_states[chat_id] = "wait_for_emoji_details"
                send_message(chat_id, render_body_text(f"{PEM['ok']} Emoji ID পাওয়া গেছে: <code>{custom_emoji_id}</code>\n\n📌 এখন এটি সেভ করার জন্য টাইপ এবং নাম লিখুন।\n\n<b>ফরমেট:</b>\n`FLAG | 880 | BD | Bangladesh`\nঅথবা\n`APP | WhatsApp`"), reply_markup=get_cancel_kb())
            else:
                send_message(chat_id, render_body_text(f"{PEM['no']} কোনো Premium Emoji পাওয়া যায়নি! দয়া করে Custom Emoji সেন্ড করুন।"), reply_markup=get_cancel_kb())
            return
            
        elif state == "wait_for_emoji_details" and text:
            parts = [p.strip() for p in text.split("|")]
            mode = parts[0].upper()
            eid = temp_data[chat_id]["id"]
            char = temp_data[chat_id]["char"]
            
            if mode == "FLAG" and len(parts) == 4:
                code, iso, name = parts[1], parts[2], parts[3]
                bot_settings["premium_flags"][code] = {"char": char, "iso": iso.upper(), "name": name, "id": eid}
                save_db()
                send_message(chat_id, render_body_text(f"{PEM['ok']} Flag Emoji সেভ হয়েছে!\nCode: {code} | Name: {name}"), reply_markup=emoji_settings_keyboard())
            elif mode == "APP" and len(parts) == 2:
                name = parts[1]
                bot_settings["premium_apps"][name.upper()] = {"char": char, "id": eid, "name": name.title()}
                save_db()
                send_message(chat_id, render_body_text(f"{PEM['ok']} App Emoji সেভ হয়েছে!\nName: {name}"), reply_markup=emoji_settings_keyboard())
            else:
                send_message(chat_id, render_body_text(f"{PEM['no']} ফরম্যাট ভুল!\n\nসঠিক ফরম্যাট:\n`FLAG | 880 | BD | Bangladesh`\n`APP | WhatsApp`"))
            del user_states[chat_id]
            del temp_data[chat_id]
            return

        elif state in ["wait_for_flag_txt", "wait_for_app_txt"] and "document" in msg:
            doc = msg["document"]
            if not doc["file_name"].endswith(".txt"):
                send_message(chat_id, render_body_text(f"{PEM['no']} Please upload a .txt file only."))
                return
            file_id = doc["file_id"]
            file_info = requests.get(f"{BASE_URL}/getFile?file_id={file_id}").json()
            file_path = file_info["result"]["file_path"]
            content = requests.get(f"{FILE_URL}{file_path}").text
            
            mode = "flags" if state == "wait_for_flag_txt" else "apps"
            count = 0
            
            if mode == "flags":
                for line in content.splitlines():
                    json_match = re.search(r'(\{.*\})', line)
                    if json_match:
                        try:
                            data = json.loads(json_match.group(1))
                            char = data.get("emoji")
                            eid = data.get("id")
                            
                            prefix_str = line[:json_match.start()].strip()
                            code_match = re.search(r'\((\d+)\)', prefix_str)
                            iso_match = re.search(r'\(([A-Za-z]+)\)', prefix_str)
                            
                            if code_match and iso_match and char and eid:
                                code = code_match.group(1)
                                iso = iso_match.group(1).upper()
                                name = prefix_str.replace(f"({code})", "").replace(f"({iso_match.group(1)})", "").replace(char, "").strip()
                                bot_settings["premium_flags"][code] = {"char": char, "iso": iso, "name": name, "id": eid}
                                count += 1
                        except: pass
            else:
                for line in content.splitlines():
                    json_match = re.search(r'(\{.*\})', line)
                    if json_match:
                        try:
                            data = json.loads(json_match.group(1))
                            char = data.get("emoji")
                            eid = data.get("id")
                            
                            name_part = line[:json_match.start()].strip()
                            name = name_part.replace(char, '').strip() if char else name_part
                            
                            if char and eid and name:
                                bot_settings["premium_apps"][name.upper()] = {"char": char, "id": eid, "name": name}
                                count += 1
                        except: pass
            
            save_db()
            send_message(chat_id, render_body_text(f"{PEM['ok']} Successfully loaded {count} Emojis!"), reply_markup=emoji_settings_keyboard())
            del user_states[chat_id]
            return

        elif state == "wait_for_broadcast":
            msg_id = msg["message_id"]
            send_message(chat_id, render_body_text(f"{PEM['ok']} Broadcast started..."))
            threading.Thread(target=broadcast_copymessage, args=(chat_id, msg_id)).start()
            del user_states[chat_id]
            return

        elif state == "wait_for_txt" and "document" in msg:
            doc = msg["document"]
            if not doc["file_name"].endswith(".txt"):
                send_message(chat_id, render_body_text(f"{PEM['no']} Please upload a .txt file only."))
                return
            file_id = doc["file_id"]
            file_info = requests.get(f"{BASE_URL}/getFile?file_id={file_id}").json()
            file_path = file_info["result"]["file_path"]
            file_content = requests.get(f"{FILE_URL}{file_path}").text
            
            temp_data[chat_id] = {"numbers": file_content.splitlines(), "filename": doc["file_name"]}
            user_states[chat_id] = "wait_for_service"
            send_message(chat_id, render_body_text(f"{PEM['ok']} File received.\n\n📌 Enter the service name (e.g., WHATSAPP):"), reply_markup=get_cancel_kb())
            return

        elif state == "wait_for_service" and text:
            temp_data[chat_id]["service"] = text.upper()
            user_states[chat_id] = "wait_for_country"
            send_message(chat_id, render_body_text(f"{PEM['ok']} Service set.\n\n🌍 Enter the country name (e.g., YEMEN):"), reply_markup=get_cancel_kb())
            return

        elif state == "wait_for_country" and text:
            country = text.upper()
            service = temp_data[chat_id]["service"]
            raw_numbers = temp_data[chat_id]["numbers"]
            
            clean_nums = []
            for num in raw_numbers:
                num = num.strip()
                if num:
                    if not num.startswith('+'): num = '+' + num
                    clean_nums.append(num)
            
            batch_id = str(uuid.uuid4())[:8]
            number_batches[batch_id] = {"filename": temp_data[chat_id]["filename"], "service": service, "country": country, "numbers": [{"num": n, "shares": 0, "used_by": []} for n in clean_nums]}
            total_uploaded_stats += len(clean_nums)
            save_db()
            
            app_full_name, prem_app_html = get_service_info_html(service)
            prem_flag_html = get_flag_info_html(clean_nums[0]) if clean_nums else f"{PEM['world']} "
            
            broadcast_txt = f"➖➖➖➖➖➖➖➖\n《 NEW NUMBERS 》\n➖➖➖➖➖➖➖➖\n{prem_flag_html} {country} {prem_app_html} {service}\n➖➖➖➖➖➖➖➖\n📤 Total Added: <b>{len(clean_nums)}</b>\n➖➖➖➖➖➖➖➖\nUse /start to get your numbers!"
            broadcast_txt = render_body_text(broadcast_txt)
            
            send_message(chat_id, render_body_text(f"{PEM['ok']} Numbers added to local stock! Starting broadcast..."))
            
            def simple_broadcast(txt):
                b_session = requests.Session()
                url = f"{BASE_URL}/sendMessage"
                for u_id in list(all_known_users):
                    try:
                        b_session.post(url, json={"chat_id": u_id, "text": txt, "parse_mode": "HTML", "disable_web_page_preview": True}, timeout=5)
                    except: pass
                    time.sleep(0.035)
            threading.Thread(target=simple_broadcast, args=(broadcast_txt,)).start()
            
            del user_states[chat_id]
            del temp_data[chat_id]
            return

        elif state == "wait_for_add_stex_key" and text:
            bot_settings["stex_keys"].append(text.strip())
            save_db()
            delete_message(chat_id, msg["message_id"])
            edit_message(chat_id, temp_data[chat_id]["msg_id"], render_body_text(f"✅ Stex API Key Added! Total Keys: {len(bot_settings.get('stex_keys', []))}"), reply_markup=stex_control_keyboard())
            del user_states[chat_id]
            del temp_data[chat_id]
            return

        elif state == "wait_for_add_voltx_key" and text:
            bot_settings["voltx_keys"].append(text.strip())
            save_db()
            delete_message(chat_id, msg["message_id"])
            edit_message(chat_id, temp_data[chat_id]["msg_id"], render_body_text(f"✅ Voltx API Key Added! Total Keys: {len(bot_settings.get('voltx_keys', []))}"), reply_markup=voltx_control_keyboard())
            del user_states[chat_id]
            del temp_data[chat_id]
            return

        elif state == "wait_for_add_sc" and text:
            code = text.strip().replace("+", "")
            if "stex_search_countries" not in bot_settings: bot_settings["stex_search_countries"] = []
            bot_settings["stex_search_countries"].append(code)
            save_db()
            delete_message(chat_id, msg["message_id"])
            kb = []
            for idx, c in enumerate(bot_settings.get("stex_search_countries", [])):
                kb.append([{"text": f"Delete {c}", "callback_data": f"del_sc_{idx}", "style": "danger"}])
            kb.append([{"text": "Add Country Code", "callback_data": "add_search_country", "style": "success"}])
            kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "stex_control", "style": "primary"}])
            edit_message(chat_id, temp_data[chat_id]["msg_id"], render_body_text("🌍 <b>Allowed Search Countries:</b>\nOnly these country codes will be allowed in Search Number."), reply_markup={"inline_keyboard": kb})
            del user_states[chat_id]
            del temp_data[chat_id]
            return

        elif state == "wait_for_add_vsc" and text:
            code = text.strip().replace("+", "")
            if "voltx_stex_search_countries" not in bot_settings: bot_settings["voltx_stex_search_countries"] = []
            bot_settings["voltx_stex_search_countries"].append(code)
            save_db()
            delete_message(chat_id, msg["message_id"])
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": temp_data[chat_id]["msg_id"]}, "data": "voltx_search_country", "id": "internal"})
            del user_states[chat_id]
            del temp_data[chat_id]
            return

        elif state == "wait_nx_srv_name" and text:
            srv = text.strip().upper()
            if "stex_services" not in bot_settings: bot_settings["stex_services"] = {}
            if srv not in bot_settings["stex_services"]: bot_settings["stex_services"][srv] = {}
            save_db()
            delete_message(chat_id, msg["message_id"])
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": temp_data[chat_id]["msg_id"]}, "data": "manage_stex_srv", "id": "internal"})
            del user_states[chat_id]
            return

        elif state == "wait_nx_cnt_name" and text:
            cnt = text.strip()
            srv = temp_data[chat_id]["srv"]
            if cnt not in bot_settings["stex_services"][srv]: bot_settings["stex_services"][srv][cnt] = []
            save_db()
            delete_message(chat_id, msg["message_id"])
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": temp_data[chat_id]["msg_id"]}, "data": f"nx_srv_{srv}", "id": "internal"})
            del user_states[chat_id]
            return

        elif state == "wait_nx_addr" and text:
            srv, cnt = temp_data[chat_id]["srv"], temp_data[chat_id]["cnt"]
            new_range = text.strip().replace("+", "")
            if new_range not in bot_settings["stex_services"][srv][cnt]:
                bot_settings["stex_services"][srv][cnt].append(new_range)
                if "stex_search_countries" not in bot_settings: bot_settings["stex_search_countries"] = []
                if new_range not in bot_settings["stex_search_countries"]:
                    bot_settings["stex_search_countries"].append(new_range)
                save_db()
            delete_message(chat_id, msg["message_id"])
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": temp_data[chat_id]["msg_id"]}, "data": f"nx_cnt_{srv}_{cnt}", "id": "internal"})
            del user_states[chat_id]
            return

        elif state == "wait_vx_srv_name" and text:
            srv = text.strip().upper()
            if "voltx_services" not in bot_settings: bot_settings["voltx_services"] = {}
            if srv not in bot_settings["voltx_services"]: bot_settings["voltx_services"][srv] = {}
            save_db()
            delete_message(chat_id, msg["message_id"])
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": temp_data[chat_id]["msg_id"]}, "data": "manage_voltx_srv", "id": "internal"})
            del user_states[chat_id]
            return

        elif state == "wait_vx_cnt_name" and text:
            cnt = text.strip()
            srv = temp_data[chat_id]["srv"]
            if cnt not in bot_settings["voltx_services"][srv]: bot_settings["voltx_services"][srv][cnt] = []
            save_db()
            delete_message(chat_id, msg["message_id"])
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": temp_data[chat_id]["msg_id"]}, "data": f"vx_srv_{srv}", "id": "internal"})
            del user_states[chat_id]
            return

        elif state == "wait_vx_addr" and text:
            srv, cnt = temp_data[chat_id]["srv"], temp_data[chat_id]["cnt"]
            new_range = text.strip().replace("+", "")
            if new_range not in bot_settings["voltx_services"][srv][cnt]:
                bot_settings["voltx_services"][srv][cnt].append(new_range)
                if "voltx_stex_search_countries" not in bot_settings: bot_settings["voltx_stex_search_countries"] = []
                if new_range not in bot_settings["voltx_stex_search_countries"]:
                    bot_settings["voltx_stex_search_countries"].append(new_range)
                save_db()
            delete_message(chat_id, msg["message_id"])
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": temp_data[chat_id]["msg_id"]}, "data": f"vx_cnt_{srv}_{cnt}", "id": "internal"})
            del user_states[chat_id]
            return

        elif state == "wait_for_add_zenex_key" and text:
            bot_settings["zenex_keys"].append(text.strip())
            save_db()
            delete_message(chat_id, msg["message_id"])
            edit_message(chat_id, temp_data[chat_id]["msg_id"], render_body_text(f"✅ Zenex API Key Added! Total Keys: {len(bot_settings.get('zenex_keys', []))}"), reply_markup=zenex_control_keyboard())
            del user_states[chat_id]
            del temp_data[chat_id]
            return

        elif state == "wait_for_add_shark_token" and text:
            new_token = text.strip()
            if "shark_tokens" not in bot_settings:
                bot_settings["shark_tokens"] = []
            bot_settings["shark_tokens"].append(new_token)
            save_db()
            delete_message(chat_id, msg["message_id"])
            edit_message(chat_id, temp_data[chat_id]["msg_id"],
                render_body_text(f"✅ Shark Panel Token Added!\nTotal Tokens: {len(bot_settings['shark_tokens'])}"),
                reply_markup=shark_control_keyboard())
            del user_states[chat_id]
            del temp_data[chat_id]
            return

        elif state == "wait_for_add_cr_token" and text:
            new_token = text.strip()
            if "cr_tokens" not in bot_settings:
                bot_settings["cr_tokens"] = []
            bot_settings["cr_tokens"].append(new_token)
            save_db()
            delete_message(chat_id, msg["message_id"])
            edit_message(chat_id, temp_data[chat_id]["msg_id"],
                render_body_text(f"✅ CR Panel Token Added!\nTotal Tokens: {len(bot_settings['cr_tokens'])}"),
                reply_markup=cr_control_keyboard())
            del user_states[chat_id]
            del temp_data[chat_id]
            return

        elif state == "wait_for_set_flex_url" and text:
            new_url = text.strip()
            if not new_url.startswith("http"):
                edit_message(chat_id, temp_data[chat_id]["msg_id"],
                    render_body_text("❌ Invalid URL! http:// দিয়ে শুরু করতে হবে।\nExample: http://168.119.13.175/crapi/xxx/viewstats"),
                    reply_markup={"inline_keyboard": [[{"text": "Cancel", "callback_data": "flex_control", "style": "danger"}]]})
                delete_message(chat_id, msg["message_id"])
                return
            bot_settings["flex_api_url"] = new_url
            save_db()
            delete_message(chat_id, msg["message_id"])
            edit_message(chat_id, temp_data[chat_id]["msg_id"],
                render_body_text(f"✅ Flex Panel API URL Set!\n\n🔗 <code>{new_url}</code>"),
                reply_markup=flex_control_keyboard())
            del user_states[chat_id]
            del temp_data[chat_id]
            return

        elif state == "wait_for_add_flex_token" and text:
            new_token = text.strip()
            if "flex_tokens" not in bot_settings:
                bot_settings["flex_tokens"] = []
            bot_settings["flex_tokens"].append(new_token)
            save_db()
            delete_message(chat_id, msg["message_id"])
            edit_message(chat_id, temp_data[chat_id]["msg_id"],
                render_body_text(f"✅ Flex Panel Token Added!\nTotal Tokens: {len(bot_settings['flex_tokens'])}"),
                reply_markup=flex_control_keyboard())
            del user_states[chat_id]
            del temp_data[chat_id]
            return

        elif state == "wait_for_add_nexus_key" and text:
            new_key = text.strip()
            if "nexus_keys" not in bot_settings:
                bot_settings["nexus_keys"] = []
            bot_settings["nexus_keys"].append(new_key)
            save_db()
            delete_message(chat_id, msg["message_id"])
            edit_message(chat_id, temp_data[chat_id]["msg_id"],
                render_body_text(f"✅ Nexus-X API Key Added!\nTotal Keys: {len(bot_settings['nexus_keys'])}"),
                reply_markup=nexus_control_keyboard())
            del user_states[chat_id]
            del temp_data[chat_id]
            return

        elif state == "wait_for_user_rate_uid" and text:
            # UID নিলাম, এখন amount চাইব
            uid_input = text.strip().replace("@", "")
            if not uid_input.lstrip("-").isdigit():
                edit_message(chat_id, temp_data[chat_id]["msg_id"],
                    render_body_text("❌ ভুল User ID! শুধু সংখ্যা (যেমন: 123456789) পাঠান।"),
                    reply_markup={"inline_keyboard": [[{"text": "Cancel", "callback_data": "user_management", "style": "danger"}]]})
                delete_message(chat_id, msg["message_id"])
                return
            delete_message(chat_id, msg["message_id"])
            temp_data[chat_id]["target_uid"] = uid_input
            user_states[chat_id] = "wait_for_user_rate_amount"
            edit_message(chat_id, temp_data[chat_id]["msg_id"],
                render_body_text(
                    f"💰 User <code>{uid_input}</code> এর OTP Rate\n\n"
                    f"📝 কত TK দিতে চান প্রতি OTP তে?\n"
                    f"Example: <code>0.5</code> অথবা <code>2</code>\n\n"
                    f"<i>0 লিখলে custom rate সরে যাবে (global rate চলবে)</i>"
                ),
                reply_markup={"inline_keyboard": [[{"text": "Cancel", "callback_data": "user_management", "style": "danger"}]]})
            return

        elif state == "wait_for_user_rate_amount" and text:
            try:
                rate_val = float(text.strip())
            except ValueError:
                delete_message(chat_id, msg["message_id"])
                edit_message(chat_id, temp_data[chat_id]["msg_id"],
                    render_body_text("❌ ভুল সংখ্যা! দশমিক দিয়ে লিখুন (যেমন: 0.5 বা 2)।"),
                    reply_markup={"inline_keyboard": [[{"text": "Cancel", "callback_data": "user_management", "style": "danger"}]]})
                return
            uid_key = str(temp_data[chat_id].get("target_uid", ""))
            if "user_otp_rates" not in bot_settings:
                bot_settings["user_otp_rates"] = {}
            if rate_val <= 0:
                bot_settings["user_otp_rates"].pop(uid_key, None)
                result_txt = f"✅ User <code>{uid_key}</code> এর Custom Rate সরানো হয়েছে। Global Rate চলবে।"
            else:
                bot_settings["user_otp_rates"][uid_key] = rate_val
                result_txt = f"✅ User <code>{uid_key}</code> এর OTP Rate: <b>{rate_val} TK</b> সেট হয়েছে!"
            save_db()
            delete_message(chat_id, msg["message_id"])
            edit_message(chat_id, temp_data[chat_id]["msg_id"],
                render_body_text(result_txt),
                reply_markup=user_management_keyboard())
            del user_states[chat_id]
            del temp_data[chat_id]
            return

        elif state == "wait_for_add_znx_sc" and text:
            code = text.strip().replace("+", "")
            if "zenex_stex_search_countries" not in bot_settings: bot_settings["zenex_stex_search_countries"] = []
            bot_settings["zenex_stex_search_countries"].append(code)
            save_db()
            delete_message(chat_id, msg["message_id"])
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": temp_data[chat_id]["msg_id"]}, "data": "zenex_search_country", "id": "internal"})
            del user_states[chat_id]
            del temp_data[chat_id]
            return

        elif state == "wait_znx_srv_name" and text:
            srv = text.strip().upper()
            if "zenex_services" not in bot_settings: bot_settings["zenex_services"] = {}
            if srv not in bot_settings["zenex_services"]: bot_settings["zenex_services"][srv] = {}
            save_db()
            delete_message(chat_id, msg["message_id"])
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": temp_data[chat_id]["msg_id"]}, "data": "manage_zenex_srv", "id": "internal"})
            del user_states[chat_id]
            return

        elif state == "wait_znx_cnt_name" and text:
            cnt = text.strip()
            srv = temp_data[chat_id]["srv"]
            if "zenex_services" not in bot_settings: bot_settings["zenex_services"] = {}
            if srv not in bot_settings["zenex_services"]: bot_settings["zenex_services"][srv] = {}
            if cnt not in bot_settings["zenex_services"][srv]: bot_settings["zenex_services"][srv][cnt] = []
            save_db()
            delete_message(chat_id, msg["message_id"])
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": temp_data[chat_id]["msg_id"]}, "data": f"znx_srv_{srv}", "id": "internal"})
            del user_states[chat_id]
            return

        elif state == "wait_znx_addr" and text:
            srv, cnt = temp_data[chat_id]["srv"], temp_data[chat_id]["cnt"]
            new_range = text.strip().replace("+", "")

            if "zenex_services" not in bot_settings: bot_settings["zenex_services"] = {}
            if srv not in bot_settings["zenex_services"]: bot_settings["zenex_services"][srv] = {}
            if cnt not in bot_settings["zenex_services"][srv]: bot_settings["zenex_services"][srv][cnt] = []

            if new_range not in bot_settings["zenex_services"][srv][cnt]:
                bot_settings["zenex_services"][srv][cnt].append(new_range)

                if "zenex_stex_search_countries" not in bot_settings:
                    bot_settings["zenex_stex_search_countries"] = []
                if new_range not in bot_settings["zenex_stex_search_countries"]:
                    bot_settings["zenex_stex_search_countries"].append(new_range)

                save_db()

            delete_message(chat_id, msg["message_id"])
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": temp_data[chat_id]["msg_id"]}, "data": f"znx_cnt_{srv}_{cnt}", "id": "internal"})
            del user_states[chat_id]
            return

        # ── Nexus Services State Handlers ──────────────────────────────────
        elif state == "wait_nxs_srv_name" and text:
            srv = text.strip().upper()
            if "nexus_services" not in bot_settings: bot_settings["nexus_services"] = {}
            if srv not in bot_settings["nexus_services"]: bot_settings["nexus_services"][srv] = {}
            save_db()
            delete_message(chat_id, msg["message_id"])
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": temp_data[chat_id]["msg_id"]}, "data": "manage_nexus_srv", "id": "internal"})
            del user_states[chat_id]
            return

        elif state == "wait_nxs_cnt_name" and text:
            cnt = text.strip()
            srv = temp_data[chat_id]["srv"]
            if "nexus_services" not in bot_settings: bot_settings["nexus_services"] = {}
            if srv not in bot_settings["nexus_services"]: bot_settings["nexus_services"][srv] = {}
            if cnt not in bot_settings["nexus_services"][srv]: bot_settings["nexus_services"][srv][cnt] = []
            save_db()
            delete_message(chat_id, msg["message_id"])
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": temp_data[chat_id]["msg_id"]}, "data": f"nxs_srv_{srv}", "id": "internal"})
            del user_states[chat_id]
            return

        elif state == "wait_nxs_addr" and text:
            srv, cnt = temp_data[chat_id]["srv"], temp_data[chat_id]["cnt"]
            new_range = text.strip().replace("+", "")

            if "nexus_services" not in bot_settings: bot_settings["nexus_services"] = {}
            if srv not in bot_settings["nexus_services"]: bot_settings["nexus_services"][srv] = {}
            if cnt not in bot_settings["nexus_services"][srv]: bot_settings["nexus_services"][srv][cnt] = []

            if new_range not in bot_settings["nexus_services"][srv][cnt]:
                bot_settings["nexus_services"][srv][cnt].append(new_range)
                save_db()

            delete_message(chat_id, msg["message_id"])
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": temp_data[chat_id]["msg_id"]}, "data": f"nxs_cnt_{srv}_{cnt}", "id": "internal"})
            del user_states[chat_id]
            return

        elif state == "wait_for_add_wm" and text:
            bot_settings["w_methods"].append(text.strip())
            save_db()
            delete_message(chat_id, msg["message_id"])
            edit_message(chat_id, temp_data[chat_id]["msg_id"], render_body_text("💳 <b>WITHDRAWAL METHODS</b>\n\nManage your withdrawal methods below:"), reply_markup=w_methods_keyboard())
            del user_states[chat_id]
            del temp_data[chat_id]
            return

        elif state == "wait_for_add_fj" and text:
            bot_settings["fj_channels"].append(parse_chat_id(text))
            save_db()
            delete_message(chat_id, msg["message_id"])
            edit_message(chat_id, temp_data[chat_id]["msg_id"], render_body_text("🔗 <b>FORCE JOIN SYSTEM</b>\nManage channels below:\n<i>(Note: For private links, use numeric IDs like -100...)</i>"), reply_markup=fj_settings_keyboard())
            del user_states[chat_id]
            del temp_data[chat_id]
            return
            
        elif state == "wait_for_add_adm" and text:
            if text.isdigit():
                bot_settings["admins"].append(int(text))
                save_db()
            delete_message(chat_id, msg["message_id"])
            edit_message(chat_id, temp_data[chat_id]["msg_id"], render_body_text("👥 <b>ADMIN MANAGEMENT</b>\nManage your bot admins below:"), reply_markup=admin_settings_keyboard())
            del user_states[chat_id]
            del temp_data[chat_id]
            return

        elif state == "wait_for_add_fw_id" and text:
            bot_settings["fw_groups"].append({"chat_id": text.strip(), "buttons": []})
            save_db()
            delete_message(chat_id, msg["message_id"])
            edit_message(chat_id, temp_data[chat_id]["msg_id"], render_body_text("🛡 <b>OTP GROUP MANAGEMENT</b>\nManage settings below:"), reply_markup=otp_groups_list_keyboard())
            del user_states[chat_id]
            del temp_data[chat_id]
            return
            
        elif state == "wait_for_add_fw_btn" and text:
            fw_idx = temp_data[chat_id]["fw_idx"]
            if "-" in text:
                parts = text.split("-", 1)
                btn_text = parts[0].strip()
                btn_url = parts[1].strip()
                
                emoji_id = None
                emoji_char = ""
                for ent in msg.get("entities", []):
                    if ent.get("type") == "custom_emoji":
                        emoji_id = ent.get("custom_emoji_id")
                        offset = ent.get("offset", 0)
                        length = ent.get("length", 0)
                        b_text = text.encode('utf-16-le')
                        emoji_char = b_text[offset*2:(offset+length)*2].decode('utf-16-le')
                        break
                
                if emoji_char:
                    btn_text = btn_text.replace(emoji_char, "").strip()
                    
                btn_data = {"text": btn_text, "url": btn_url}
                if emoji_id:
                    btn_data["icon_custom_emoji_id"] = emoji_id
                    
                bot_settings["fw_groups"][fw_idx]["buttons"].append(btn_data)
                save_db()
            delete_message(chat_id, msg["message_id"])
            edit_message(chat_id, temp_data[chat_id]["msg_id"], render_body_text(f"🛡 <b>Manage Group:</b> {bot_settings['fw_groups'][fw_idx]['chat_id']}"), reply_markup=specific_fw_group_keyboard(fw_idx))
            del user_states[chat_id]
            del temp_data[chat_id]
            return
            
        elif state == "wait_for_otp_link" and text:
            bot_settings["otp_link"] = text.strip()
            save_db()
            delete_message(chat_id, msg["message_id"])
            edit_message(chat_id, temp_data[chat_id]["msg_id"], render_body_text("🛡 <b>OTP GROUP MANAGEMENT</b>\nManage settings below:"), reply_markup=otp_groups_list_keyboard())
            del user_states[chat_id]
            del temp_data[chat_id]
            return

        elif state == "wait_for_main_channel" and text:
            bot_settings["main_channel"] = text.strip()
            save_db()
            delete_message(chat_id, msg["message_id"])
            edit_message(chat_id, temp_data[chat_id]["msg_id"], render_body_text("🛡 <b>OTP GROUP MANAGEMENT</b>\nManage settings below:"), reply_markup=otp_groups_list_keyboard())
            del user_states[chat_id]
            del temp_data[chat_id]
            return

        elif state == "wait_for_panel_name" and text:
            p_name = text.strip()
            t_key = temp_data[chat_id].get("add_type", "api")
            msg_id = temp_data[chat_id]["msg_id"]
            delete_message(chat_id, msg["message_id"])
            
            if t_key == "logc":
                user_states[chat_id] = "wait_for_cpanel_url"
                temp_data[chat_id] = {"msg_id": msg_id, "p_data": {
                    "name": p_name, "type": "Auto Captcha Panel", "status": "ON", "records": 0, "login_status": "⏳ Pending First Login"
                }}
                edit_message(chat_id, msg_id, render_body_text("1️⃣ <b>Login URL</b>\n➡️ Panel এর Login Link দিন:"), reply_markup=get_cancel_kb())
                return
            else:
                bot_settings["panels"].append({
                    "name": p_name, "type": "API Panel", "status": "OFF", "api_url": "", "token": "", "records": 0
                })
                save_db()
                handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "manage_api_panels", "id": "internal"})
                if chat_id in user_states: del user_states[chat_id]
                if chat_id in temp_data: del temp_data[chat_id]
                return

        elif state == "wait_for_p_api" and text:
            idx = temp_data[chat_id]["p_idx"]
            bot_settings["panels"][idx]["api_url"] = text.strip()
            save_db()
            delete_message(chat_id, msg["message_id"])
            p = bot_settings["panels"][idx]
            ui_text = f"⚙️ <b>Configure {p['name']}</b>\n\n<b>Type:</b> {p['type']}\n<b>Status:</b> {'🟢 Monitoring' if p['status'] == 'ON' else '🔴 Stopped'}\n<b>API URL:</b> <code>{p.get('api_url', 'None')}</code>\n<b>Token:</b> <code>{p.get('token', 'None')}</code>"
            edit_message(chat_id, temp_data[chat_id]["msg_id"], render_body_text(ui_text), reply_markup=panel_config_keyboard(idx))
            del user_states[chat_id]
            del temp_data[chat_id]
            return

        elif state == "wait_for_p_tok" and text:
            idx = temp_data[chat_id]["p_idx"]
            bot_settings["panels"][idx]["token"] = text.strip()
            save_db()
            delete_message(chat_id, msg["message_id"])
            p = bot_settings["panels"][idx]
            ui_text = f"⚙️ <b>Configure {p['name']}</b>\n\n<b>Type:</b> {p['type']}\n<b>Status:</b> {'🟢 Monitoring' if p['status'] == 'ON' else '🔴 Stopped'}\n<b>API URL:</b> <code>{p.get('api_url', 'None')}</code>\n<b>Token:</b> <code>{p.get('token', 'None')}</code>"
            edit_message(chat_id, temp_data[chat_id]["msg_id"], render_body_text(ui_text), reply_markup=panel_config_keyboard(idx))
            del user_states[chat_id]
            del temp_data[chat_id]
            return

        elif state == "wait_for_p_fapi" and text:
            idx = temp_data[chat_id]["p_idx"]
            bot_settings["panels"][idx]["full_api_url"] = text.strip()
            save_db()
            delete_message(chat_id, msg["message_id"])
            p = bot_settings["panels"][idx]
            ui_text = f"⚙️ <b>Configure {p['name']}</b>\n\n<b>Type:</b> {p['type']}\n<b>Status:</b> {'🟢 Monitoring' if p['status'] == 'ON' else '🔴 Stopped'}\n<b>API URL:</b> <code>{p.get('api_url', 'None')}</code>\n<b>Full API URL:</b> <code>{p.get('full_api_url', 'None')}</code>"
            edit_message(chat_id, temp_data[chat_id]["msg_id"], render_body_text(ui_text), reply_markup=panel_config_keyboard(idx))
            del user_states[chat_id]
            del temp_data[chat_id]
            return

        elif state == "wait_for_p_rec" and text:
            if text.isdigit():
                idx = temp_data[chat_id]["p_idx"]
                bot_settings["panels"][idx]["records"] = int(text)
                save_db()
                delete_message(chat_id, msg["message_id"])
                p = bot_settings["panels"][idx]
                
                ui_text = f"⚙️ <b>Configure {p['name']}</b>\n\n<b>Type:</b> {p['type']}\n<b>Status:</b> {'🟢 Monitoring' if p['status'] == 'ON' else '🔴 Stopped'}\n<b>API URL:</b> <code>{p.get('api_url', 'None')}</code>\n<b>Token:</b> <code>{p.get('token', 'None')}</code>"
                edit_message(chat_id, temp_data[chat_id]["msg_id"], render_body_text(ui_text), reply_markup=panel_config_keyboard(idx))
            else:
                send_message(chat_id, render_body_text("❌ Please enter a valid number! Try again."), reply_markup=get_cancel_kb())
            del user_states[chat_id]
            del temp_data[chat_id]
            return

        elif state == "wait_for_rand_pass" and text:
            msg_id = temp_data[chat_id].get("msg_id")
            bot_settings["rand_name_pass"] = text.strip()
            save_db()
            delete_message(chat_id, msg["message_id"])
            if msg_id:
                edit_message(chat_id, msg_id, render_body_text(
                    f"🕹 <b>RAHIN CONTROL PANEL</b>\n\n✅ Random Name Pass set করা হয়েছে:\n<code>{text.strip()}</code>"
                ), reply_markup=dxa_control_keyboard())
            del user_states[chat_id]
            del temp_data[chat_id]
            return

        elif state == "set_dxa":
            msg_id = temp_data[chat_id]["msg_id"]
            key = temp_data[chat_id]["key"]
            try:
                if key in ["min_withdraw", "otp_reward", "refer_reward"]: bot_settings[key] = float(text)
                elif key in ["cooldown", "num_req", "num_share"]: bot_settings[key] = int(text)
                else: bot_settings[key] = text
                save_db()
                delete_message(chat_id, msg["message_id"])
                edit_message(chat_id, msg_id, render_body_text("🕹 <b>RAHIN CONTROL PANEL</b>"), reply_markup=dxa_control_keyboard())
            except:
                delete_message(chat_id, msg["message_id"])
                edit_message(chat_id, msg_id, render_body_text("🕹 <b>RAHIN CONTROL PANEL</b>\n\n❌ Invalid value!"), reply_markup=dxa_control_keyboard())
            del user_states[chat_id]
            del temp_data[chat_id]
            return

        elif state == "set_srv_rate":
            msg_id = temp_data[chat_id]["msg_id"]
            srv = temp_data[chat_id]["srv"]
            try:
                rate = float(text.strip())
                bot_settings.setdefault("service_otp_rates", {})[srv] = rate
                save_db()
                delete_message(chat_id, msg["message_id"])
                edit_message(chat_id, msg_id, render_body_text("⚙️ <b>SERVICE OTP RATES</b>"), reply_markup=service_rates_keyboard())
            except:
                delete_message(chat_id, msg["message_id"])
                edit_message(chat_id, msg_id, render_body_text("⚙️ <b>SERVICE OTP RATES</b>\n\n❌ Invalid value!"), reply_markup=service_rates_keyboard())
            del user_states[chat_id]
            del temp_data[chat_id]
            return

        elif state == "set_srv_name":
            msg_id = temp_data[chat_id]["msg_id"]
            srv = text.strip().upper()
            if srv:
                bot_settings.setdefault("service_otp_rates", {}).setdefault(srv, 0.0)
                bot_settings.setdefault("service_reward_enabled", {})[srv] = True
                save_db()
                delete_message(chat_id, msg["message_id"])
                user_states[chat_id] = "set_srv_rate"
                temp_data[chat_id] = {"msg_id": msg_id, "srv": srv}
                cancel_kb = {"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "dxa_service_rates", "style": "danger"}]]}
                edit_message(chat_id, msg_id, render_body_text(f"📝 Send reward amount (tk) for <b>{srv}</b>:"), reply_markup=cancel_kb)
            else:
                del user_states[chat_id]
                del temp_data[chat_id]
            return

  
        elif False and state == "wait_for_custom_number_prefix" and text:
            raw = text.strip()
            # Accept +236X or 236X or 236 format
            range_text = raw.lstrip("+").strip().upper()
            # Accept: pure digits OR digits followed by one or more X's (e.g. 236X, 22507XXX)
            # digit prefix = everything before the first X
            if "X" in range_text:
                range_clean = range_text.split("X")[0]   # digits before first X
                suffix = range_text[len(range_clean):]   # all X's
                valid = range_clean.isdigit() and all(c == "X" for c in suffix)
            else:
                range_clean = range_text
                valid = range_clean.isdigit()

            if not valid or len(range_clean) < 3 or len(range_text) > 20:
                send_message(chat_id, render_body_text(
                    "❌ <b>ভুল format!</b>\n"
                    "━━━━━━━━━━━━━\n"
                    "✅ সঠিক উদাহরণ:\n"
                    "➥ <code>+236X</code>\n"
                    "➥ <code>22507XXX</code>\n"
                    "➥ <code>880</code>\n"
                    "━━━━━━━━━━━━━\n"
                    "⚠️ সংখ্যার পরে X দেওয়া যাবে"
                ))
                return
            del user_states[chat_id]
            query = range_clean  # digit-only prefix for local search & number filter

            wait_msg = send_message(chat_id, render_body_text("⌛ <i>VIP নম্বর দেওয়া হচ্ছে...</i>"))
            wait_msg_id = wait_msg.get("result", {}).get("message_id")

            def _do_custom_fetch(chat_id, query, range_text, wait_msg_id):
                global total_assigned_stats
                # ── Step 1: Local stock search ──
                found_indices = []
                for b_id, b_data in number_batches.items():
                    for idx, n_obj in enumerate(b_data["numbers"]):
                        if n_obj["num"].replace("+", "").startswith(query) and chat_id not in n_obj.get("used_by", []):
                            found_indices.append((b_id, idx))

                req_count = bot_settings.get("num_req", 1)
                assigned_nums = []

                if found_indices:
                    expire_previous_number(chat_id)
                    for b_id, idx in found_indices[:req_count]:
                        n_obj = number_batches[b_id]["numbers"][idx]
                        assigned_nums.append(n_obj["num"])
                        if chat_id not in n_obj.get("used_by", []): n_obj.setdefault("used_by", []).append(chat_id)
                        batch_assigned_numbers[str(n_obj["num"]).replace("+","").strip()] = chat_id
                    save_db()

                else:
                    # ── Step 2–4: Stex → Voltx → Zenex switching ──────────────────
                    if wait_msg_id:
                        try: edit_message(chat_id, wait_msg_id, render_body_text("⌛ <i>নম্বর খোঁজা হচ্ছে...</i>"))
                        except: pass
                    has_any_api = (bot_settings.get("stex_keys") or
                                   bot_settings.get("voltx_keys") or
                                   bot_settings.get("zenex_keys"))
                    if not has_any_api:
                        if wait_msg_id:
                            try: delete_message(chat_id, wait_msg_id)
                            except: pass
                        send_message(chat_id, render_body_text("❌ No numbers available for this range! Please contact admin."), reply_markup=main_menu(chat_id))
                        return

                    expire_previous_number(chat_id)
                    fetched_count = 0
                    while fetched_count < req_count:
                        num_str, source, number_id, used_key = _smart_fetch_one(query, range_text, chat_id)
                        if not num_str:
                            break
                        # Filter: number must start with digit prefix of range
                        clean_fetched = str(num_str).replace("+", "").replace(" ", "").replace("-", "")
                        if not clean_fetched.startswith(query):
                            continue
                        assigned_nums.append(num_str)
                        total_assigned_stats += 1
                        if source == "zenex" and number_id and used_key:
                            threading.Thread(target=poll_zenex_otp, args=(number_id, num_str, chat_id, used_key), daemon=True).start()
                        fetched_count += 1
                    save_db()

                if not assigned_nums:
                    if wait_msg_id:
                        try: delete_message(chat_id, wait_msg_id)
                        except: pass
                    send_message(chat_id, render_body_text(f"❌ No number found for range <b>{range_text}</b>!\n\nPlease try a different range or contact admin."), reply_markup=main_menu(chat_id))
                    return

                # Build display like Get Number — flag emoji buttons with copy_text
                flags_db = bot_settings.get("premium_flags", {})
                kb = []
                for num in assigned_nums:
                    _, iso = get_flag_and_code(num)
                    display_num = f"+{num}" if not str(num).startswith("+") else str(num)
                    emoji_id = "5780471598922337783"
                    for flag_code, flag_data in flags_db.items():
                        if iso == flag_data.get("iso"):
                            if "id" in flag_data: emoji_id = flag_data["id"]; break
                    kb.append([{"text": display_num, "icon_custom_emoji_id": WAITING_NUMBER_EMOJI_ID, "copy_text": {"text": display_num}, "style": "primary"}])

                kb.append([{"text": "Change Number", "icon_custom_emoji_id": "5377774889723798543", "callback_data": f"c_custom_{range_text}", "style": "danger"},
                           {"text": "OTP Group", "icon_custom_emoji_id": "6235727781427155894", "url": bot_settings.get("otp_link", "https://t.me"), "style": "primary"}])
                kb.append([{"text": "Expire Number", "icon_custom_emoji_id": "5420130255174145507", "callback_data": "expire_num", "style": "danger"}])

                txt = render_body_text(
                    f"{PEM['ok']} <b>নাম্বার নিছেন ভালো কথা অটিপি আনা লাগবে</b>\n\n"
                    f"🎯 <b>Range:</b> {range_text}"
                )
                try:
                    edit_message(chat_id, wait_msg_id, txt, reply_markup={"inline_keyboard": kb})
                    user_active_sessions[chat_id] = {"msg_id": wait_msg_id, "nums": assigned_nums, "service": "Custom", "country": range_text, "reply_markup": {"inline_keyboard": kb}}
                except:
                    if wait_msg_id:
                        try: delete_message(chat_id, wait_msg_id)
                        except: pass
                    res = send_message(chat_id, txt, reply_markup={"inline_keyboard": kb})
                    new_msg_id = res.get("result", {}).get("message_id")
                    if new_msg_id:
                        user_active_sessions[chat_id] = {"msg_id": new_msg_id, "nums": assigned_nums, "service": "Custom", "country": range_text, "reply_markup": {"inline_keyboard": kb}}

            threading.Thread(target=_do_custom_fetch, args=(chat_id, query, range_text, wait_msg_id), daemon=True).start()
            return

        elif state == "wait_for_search" and text:
            query = text.strip().replace("+", "")
            if not query.isdigit() or len(query) < 3 or len(query) > 9:
                send_message(chat_id, render_body_text("❌ Please enter a valid 3 to 9 digit number!"))
                return
                
            wait_msg = send_message(chat_id, render_body_text("⌛ <i>Processing... Finding Number...</i>"))
            wait_msg_id = wait_msg.get("result", {}).get("message_id")
            
            # 🌟 ১. প্রথমে Local থেকে নাম্বার খুঁজবে (যে কোনো দেশের জন্য)
            found_indices = []
            for b_id, b_data in number_batches.items():
                for idx, n_obj in enumerate(b_data["numbers"]):
                    if n_obj["num"].replace("+", "").startswith(query) and chat_id not in n_obj.get("used_by", []):
                        found_indices.append((b_id, idx))
            
            fetched_nums = []
            if not found_indices:
                # 🌟 ২. যদি Local এ না পায়, তখন API থেকে আনার চেষ্টা করবে
                stex_allowed = bot_settings.get("stex_search_countries", [])
                voltx_allowed = bot_settings.get("voltx_stex_search_countries", [])
                zenex_allowed = bot_settings.get("zenex_stex_search_countries", [])
                is_stex_allowed = any(query.startswith(c) for c in stex_allowed) if stex_allowed else False
                is_voltx_allowed = any(query.startswith(c) for c in voltx_allowed) if voltx_allowed else False
                is_zenex_allowed = any(query.startswith(c) for c in zenex_allowed) if zenex_allowed else False

                if not is_stex_allowed and not is_voltx_allowed and not is_zenex_allowed:
                    if wait_msg_id: delete_message(chat_id, wait_msg_id)
                    send_message(chat_id, render_body_text("❌ This country code is not allowed!"), reply_markup=main_menu(chat_id))
                    del user_states[chat_id]
                    return

                if wait_msg_id: edit_message(chat_id, wait_msg_id, render_body_text("⌛ <i>Processing... Finding Number via API...</i>"))

                req_count = bot_settings.get("num_req", 1)

                # Check Voltx first — সব key parallel এ try করা হয়
                if is_voltx_allowed:
                    voltx_keys = bot_settings.get("voltx_keys", [])
                    while len(fetched_nums) < req_count:
                        num_str, _ = _fetch_voltx_parallel(query, voltx_keys)
                        if not num_str: break
                        fetched_nums.append(num_str)
                        voltx_assigned_numbers[num_str] = chat_id
                        total_assigned_stats += 1

                # Check Zenex if still need numbers
                if len(fetched_nums) < req_count and is_zenex_allowed:
                    zenex_keys = bot_settings.get("zenex_keys", [])
                    while len(fetched_nums) < req_count:
                        num_str, number_id, used_key = _fetch_zenex_parallel(query, zenex_keys)
                        if not num_str: break
                        fetched_nums.append(num_str)
                        zenex_assigned_numbers[num_str] = chat_id
                        total_assigned_stats += 1
                        if number_id and used_key:
                            threading.Thread(target=poll_zenex_otp, args=(number_id, num_str, chat_id, used_key), daemon=True).start()

                # Check Stex if still need numbers
                if len(fetched_nums) < req_count and is_stex_allowed:
                    stex_keys = bot_settings.get("stex_keys", [])
                    while len(fetched_nums) < req_count:
                        num_str, _ = _fetch_stex_parallel(query, stex_keys)
                        if not num_str: break
                        fetched_nums.append(num_str)
                        stex_assigned_numbers[num_str] = chat_id
                        total_assigned_stats += 1

                if not fetched_nums:
                    if wait_msg_id: delete_message(chat_id, wait_msg_id)
                    send_message(chat_id, render_body_text("❌ Number out of stock!"), reply_markup=main_menu(chat_id))
                    del user_states[chat_id]
                    return
                save_db()
            else:
                random.shuffle(found_indices)
                for b_id, idx in found_indices:
                    if len(fetched_nums) >= bot_settings.get("num_req", 1): break
                    n_obj = number_batches[b_id]["numbers"][idx]
                    num_str = n_obj["num"]
                    
                    fetched_nums.append(num_str)
                    batch_assigned_numbers[str(num_str).replace("+","").strip()] = chat_id
                    
                    n_obj["shares"] += 1
                    n_obj["used_by"].append(chat_id)
                    total_assigned_stats += 1
                    
                    if n_obj["shares"] >= bot_settings.get("num_share", 1):
                        n_obj["to_remove"] = True
                        used_numbers_list.append(num_str)
                
                for b_id in number_batches:
                    number_batches[b_id]["numbers"] = [n for n in number_batches[b_id]["numbers"] if not n.get("to_remove")]
                save_db()
                
            if wait_msg_id: edit_message(chat_id, wait_msg_id, render_body_text("✅ Number Found!"))
            kb = []
            flags_db = bot_settings.get("premium_flags", {})
            for num in fetched_nums:
                _, iso = get_flag_and_code(num)
                display_num = f"+{num}" if not num.startswith("+") else num
                
                emoji_id = "5780471598922337683" # Default Flag
                for flag_code, flag_data in flags_db.items():
                    if iso == flag_data.get("iso"):
                        if "id" in flag_data: emoji_id = flag_data["id"]
                        break
                kb.append([{"text": f"{display_num}", "icon_custom_emoji_id": WAITING_NUMBER_EMOJI_ID, "copy_text": {"text": display_num}, "style": "primary"}])
                
            kb.append([{"text": "Change Number", "icon_custom_emoji_id": "5377774889723798543", "callback_data": f"c_n_s_{query}", "style": "danger"},
                       {"text": "OTP Group", "icon_custom_emoji_id": "6235727781427155894", "url": bot_settings["otp_link"], "style": "primary"}])
            
            c_btns = bot_settings["custom_messages"].get("search_number", {}).get("buttons", [])
            for c_b in c_btns: 
                b_copy = c_b.copy()
                if "style" not in b_copy: b_copy["style"] = "primary"
                kb.append([b_copy])
            
            kb.append([{"text": "Back to Menu", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "close_msg", "style": "danger"}])
            
            search_header = render_body_text(
                f"{PEM['ok']} <b>নাম্বার নিছেন ভালো কথা অটিপি আনা লাগবে</b>\n\n"
                f"🔍 <b>Search:</b> +{query}"
            )
            if wait_msg_id:
                edit_message(chat_id, wait_msg_id, search_header, reply_markup={"inline_keyboard": kb})
                user_active_sessions[chat_id] = {"msg_id": wait_msg_id, "nums": fetched_nums, "reply_markup": {"inline_keyboard": kb}}
            else:
                msg_res = send_message(chat_id, search_header, reply_markup={"inline_keyboard": kb})
                if msg_res and "result" in msg_res:
                    user_active_sessions[chat_id] = {"msg_id": msg_res["result"]["message_id"], "nums": fetched_nums, "reply_markup": {"inline_keyboard": kb}}
            return
            
        elif state == "wait_for_support_msg" and text:
            support_name = temp_data.get(chat_id, {}).get("support_name", "User")
            safe_name = support_name.replace("_", " ")
            admin_txt = render_body_text(
                f"💬 <b>LIVE SUPPORT REQUEST</b>\n"
                f"➖➖➖➖➖➖➖\n"
                f"👤 <b>User:</b> <a href='tg://user?id={chat_id}'>{safe_name}</a>\n"
                f"🆔 <b>ID:</b> <code>{chat_id}</code>\n"
                f"➖➖➖➖➖➖➖\n"
                f"📝 <b>Message:</b>\n{text}\n"
                f"➖➖➖➖➖➖➖"
            )
            reply_btn = {"inline_keyboard": [[
                {"text": "💬 Reply to User", "callback_data": f"sup_reply_{chat_id}", "style": "primary"}
            ]]}
            all_admins = list(bot_settings.get("admins", []))
            if OWNER_ID not in all_admins:
                all_admins.append(OWNER_ID)
            for _adm in all_admins:
                try:
                    res = send_message(_adm, admin_txt, reply_markup=reply_btn)
                    if res and res.get("ok"):
                        adm_msg_id = res["result"]["message_id"]
                        support_msg_map[(_adm, adm_msg_id)] = chat_id
                except: pass
            send_message(chat_id, render_body_text(
                f"✅ <b>Message Sent!</b>\n\n"
                f"📩 আপনার message admin এর কাছে পৌঁছেছে।\n"
                f"Admin reply দিলে আপনি সাথে সাথে পাবেন। 💬"
            ), reply_markup=main_menu(chat_id))
            if chat_id in user_states: del user_states[chat_id]
            if chat_id in temp_data: del temp_data[chat_id]
            return

        elif state == "wait_for_admin_support_reply" and text:
            target_uid = temp_data.get(chat_id, {}).get("support_target_user")
            if target_uid:
                send_message(target_uid, render_body_text(
                    f"💬 <b>Admin Reply:</b>\n\n{text}"
                ))
                send_message(chat_id, render_body_text("✅ Reply sent to user!"), reply_markup=main_menu(chat_id))
            if chat_id in user_states: del user_states[chat_id]
            if chat_id in temp_data: del temp_data[chat_id]
            return

        elif state == "wait_for_withdraw_amount" and text:
            msg_id_to_edit = temp_data[chat_id].get("msg_id")
            try:
                amount = float(text.strip())
                bal = temp_data[chat_id]["balance"]
                min_w = bot_settings['min_withdraw']
                
                if amount < min_w:
                    if msg_id_to_edit: edit_message(chat_id, msg_id_to_edit, render_body_text(f"❌ Minimum withdrawal is {min_w} ৳!\n💰 Balance: {bal} ৳\n\n📝 Enter again:"), reply_markup=get_cancel_kb())
                    return
                if amount > bal:
                    if msg_id_to_edit: edit_message(chat_id, msg_id_to_edit, render_body_text(f"❌ You don't have enough balance!\n💰 Balance: {bal} ৳\n\n📝 Enter again:"), reply_markup=get_cancel_kb())
                    return
                    
                temp_data[chat_id]["amount"] = amount
                user_states[chat_id] = "wait_for_withdraw_number"
                if msg_id_to_edit:
                    edit_message(chat_id, msg_id_to_edit, render_body_text(f"✅ Amount: {amount} ৳\n\n📱 Now send your <b>{temp_data[chat_id]['method']}</b> account number:"), reply_markup=get_cancel_kb())
            except ValueError:
                if msg_id_to_edit: edit_message(chat_id, msg_id_to_edit, render_body_text("❌ Invalid amount!\n\n📝 Please send a valid number:"), reply_markup=get_cancel_kb())
            return
            
        elif state == "wait_for_2fa_key" and text:
            msg_id_to_edit = temp_data.get(chat_id, {}).get("msg_id")
            delete_message(chat_id, msg.get("message_id")) # ইউজারের মেসেজ ডিলিট

            if not msg_id_to_edit:
                send_message(chat_id, render_body_text("❌ Error: Message not found. Try again."))
                del user_states[chat_id]
                return

            try:
                secret = text.strip().replace(" ", "")
                totp = pyotp.TOTP(secret)
                code = totp.now()
                remaining_time = 30 - (int(time.time()) % 30)
                
                success_txt = (
                    f"━━━━━━━━━━━━━━━\n"
                    f"《 🔐 <b>2FA CODE</b> 》\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🔐 <b>CODE:</b> <code>{code}</code>\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🕓 <b>EXPIRES IN:</b> {remaining_time}s\n"
                    f"━━━━━━━━━━━━━━━"
                )
                kb = [[{"text": f"Click to copy {code}", "icon_custom_emoji_id": "5353022963132174959", "copy_text": {"text": code}, "style": "success"}],
                      [{"text": "Refresh", "icon_custom_emoji_id": "5420155432272438703", "callback_data": f"ref_2fa_{secret}", "style": "primary"},
                       {"text": "New Code", "icon_custom_emoji_id": "5352552689983067014", "callback_data": "gen_2fa", "style": "danger"}],
                      [{"text": "Close", "icon_custom_emoji_id": "5420130255174145507", "callback_data": "close_msg", "style": "danger"}]]
                
                edit_message(chat_id, msg_id_to_edit, render_body_text(success_txt), reply_markup={"inline_keyboard": kb})
                del user_states[chat_id]
                if chat_id in temp_data: del temp_data[chat_id]
            except Exception:
                error_txt = "━━━━━━━━━━━━━━━\n《 🔑 <b>ENTER 2FA KEY</b> 》\n━━━━━━━━━━━━━━━\n📝 <b>SEND YOUR 2FA SECRET KEY</b>\n━━━━━━━━━━━━━━━\n❌ <b>Invalid Secret Key! Try again.</b>\n━━━━━━━━━━━━━━━"
                cancel_kb = {"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "cancel_2fa", "style": "danger"}]]}
                edit_message(chat_id, msg_id_to_edit, render_body_text(error_txt), reply_markup=cancel_kb)
            return

        elif state == "wait_for_withdraw_number":
            msg_id_to_edit = temp_data[chat_id].get("msg_id")
            
            method = temp_data[chat_id]["method"]
            amount = temp_data[chat_id]["amount"]
            number = text
            req_id = f"W_{str(uuid.uuid4())[:6].upper()}"
            
            first_name = msg.get("from", {}).get("first_name", "User")
            last_name = msg.get("from", {}).get("last_name", "")
            full_name = f"{first_name} {last_name}".strip()
            
            update_balance(chat_id, -amount)
            pending_withdrawals[req_id] = {"user_id": chat_id, "amount": amount, "method": method, "number": number, "full_name": full_name}
            
            # Save to Firestore for History
            if db:
                try:
                    db.collection('withdrawals').document(req_id).set({
                        "user_id": str(chat_id),
                        "amount": amount,
                        "method": method,
                        "status": "pending",
                        "timestamp": firestore.SERVER_TIMESTAMP
                    })
                except: pass
                
            w_admin_msg = f"🎙 <b>NEW WITHDRAWAL REQUEST</b>\n\n👤 <b>USER:</b> <a href='tg://user?id={chat_id}'>{full_name}</a>\n💳 <b>WITHDRAWAL:</b> {amount} TK\n🍏 <b>NUMBER:</b> <code>{number}</code>\n🏦 <b>METHOD:</b> {method}\n\n🧾 <b>REQ ID:</b> {req_id}\n👨‍⚖️ <b>PROCESSED BY ADMIN</b>"
            w_approve_kb = {"inline_keyboard": [[{"text": "APPROVE", "icon_custom_emoji_id": "5352694861990501856", "callback_data": f"wapp_{req_id}", "style": "success"}, {"text": "REJECT", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"wrej_{req_id}", "style": "danger"}]]}
            if bot_settings["w_group"]:
                send_message(bot_settings["w_group"], render_body_text(w_admin_msg), reply_markup=w_approve_kb)
            notified = set()
            for _adm in bot_settings.get("admins", []):
                try:
                    send_message(_adm, render_body_text(w_admin_msg), reply_markup=w_approve_kb)
                    notified.add(_adm)
                except: pass
            if OWNER_ID not in notified:
                try: send_message(OWNER_ID, render_body_text(w_admin_msg), reply_markup=w_approve_kb)
                except: pass
            
            kb = {"inline_keyboard": [[{"text": "Close", "icon_custom_emoji_id": "5420130255174145507", "callback_data": "close_msg", "style": "danger"}]]}
            success_text = f"{PEM['ok']} Your withdrawal request has been submitted!\n\n🧾 <b>Req ID:</b> {req_id}\n💰 <b>Amount:</b> {amount} ৳\n🏦 <b>Method:</b> {method}\n📱 <b>Number:</b> <code>{number}</code>"
            
            if msg_id_to_edit:
                edit_message(chat_id, msg_id_to_edit, render_body_text(success_text), reply_markup=kb)
            else:
                send_message(chat_id, render_body_text(success_text), reply_markup=kb)
                
            del user_states[chat_id]
            del temp_data[chat_id]
            return

    # --- Regular Commands ---
    if text.startswith("/start"):
        get_user(chat_id)
        
        # --- PROCESS PENDING REFERRAL ---
        # --- PROCESS PENDING REFERRAL (works with or without Firestore) ---
        _process_pending_referral(chat_id)
        c_msg = bot_settings["custom_messages"].get("start", {})
        txt = render_body_text(c_msg.get("text", f"{PEM['hi']} Welcome!"))
        kb = []
        for b in c_msg.get("buttons", []):
            b_copy = b.copy()
            if "style" not in b_copy: b_copy["style"] = "primary"
            kb.append([b_copy])
        
        if kb:
            send_message(chat_id, txt, reply_markup={"inline_keyboard": kb})
            send_message(chat_id, render_body_text(f"{PEM['gear']} Navigation Menu:"), reply_markup=main_menu(chat_id))
        else:
            send_message(chat_id, txt, reply_markup=main_menu(chat_id))
            
    elif text == "TRAFFIC":
        txt, markup = build_traffic_ui()
        send_message(chat_id, txt, reply_markup=markup)
        
    elif text == "Refer" or text == "Referral":
        u_data = get_user(chat_id)
        ref_link = f"https://t.me/{BOT_USERNAME}?start={chat_id}"
        c_msg = bot_settings["custom_messages"].get("refer", {})
        
        raw_txt = c_msg.get("text", f"{PEM['gift']} Refer").replace("{ref_link}", ref_link).replace("{total_ref}", str(u_data.get('total_refers', 0))).replace("{ref_reward}", str(bot_settings['refer_reward']))
        txt = render_body_text(raw_txt)
        
        kb = [[{"text": "COPY LINK", "icon_custom_emoji_id": "5192739271886282680", "copy_text": {"text": ref_link}, "style": "success"}]]
        for b in c_msg.get("buttons", []): 
            b_copy = b.copy()
            if "style" not in b_copy: b_copy["style"] = "primary"
            kb.append([b_copy])
        kb.append([{"text": "CLOSE", "icon_custom_emoji_id": "5420130255174145507", "callback_data": "close_msg", "style": "danger"}])
        
        send_message(chat_id, txt, reply_markup={"inline_keyboard": kb})

    elif text in ("WITHDRAWAL", "Balance & Withdrawal", "Withdrawal"):
        u_data = get_user(chat_id)
        bal = u_data.get('balance', 0.0)
        
        # Balance info show করা
        bal_txt = render_body_text(f"""➖➖➖➖➖➖➖
《 💰 WITHDRAWAL 》
➖➖➖➖➖➖➖
📅 BALANCE: <b>{bal} ৳</b>
📊 Total OTP: <b>{u_data.get('total_otps', 0)}</b>
🫂 Total Refer: <b>{u_data.get('total_refers', 0)}</b>
➖➖➖➖➖➖➖
🔐 MIN WITHDRAW: <b>{bot_settings['min_withdraw']} ৳</b>
➖➖➖➖➖➖➖""")
        
        bal_kb = []
        if bot_settings["withdraw_on"]:
            for m in bot_settings["w_methods"]:
                bal_kb.append([{"text": f"Withdraw via {m.strip()}", "icon_custom_emoji_id": "5190899075968441286", "callback_data": f"sel_wm_{m.strip()}", "style": "primary"}])
        else:
            bal_kb.append([{"text": "⚠️ Withdrawal Disabled", "icon_custom_emoji_id": "5336944168944047463", "callback_data": "ignore", "style": "danger"}])
        bal_kb.append([{"text": "Close", "icon_custom_emoji_id": "5420130255174145507", "callback_data": "close_msg", "style": "danger"}])
        send_message(chat_id, bal_txt, reply_markup={"inline_keyboard": bal_kb})

    elif text == "Admin Panel" and is_admin(chat_id):
        send_message(chat_id, get_admin_text(), reply_markup=admin_panel_keyboard())

    elif text == "Number" or text == "Get Number":
        local_srvs = set([b["service"] for b in number_batches.values() if b["numbers"]])
        zenex_srvs = set(bot_settings.get("zenex_services", {}).keys())
        stex_srvs  = set(bot_settings.get("stex_services", {}).keys())
        voltx_srvs = set(bot_settings.get("voltx_services", {}).keys())
        nexus_srvs = set(bot_settings.get("nexus_services", {}).keys())
        all_services = local_srvs.union(zenex_srvs).union(stex_srvs).union(voltx_srvs).union(nexus_srvs)
        
        if not all_services:
            send_message(chat_id, render_body_text(f"{PEM['no']} No numbers or services available!"))
        else:
            c_msg = bot_settings["custom_messages"].get("get_number", {})
            txt = render_body_text(c_msg.get("text", f"{PEM['pin']} Select Service"))
            
            apps_db = bot_settings.get("premium_apps", {})
            kb = []
            _srv_btns = []
            for s in all_services:
                emoji_id = "5352694861990501856" # Default icon
                for app_key, app_data in apps_db.items():
                    if s.upper() == app_key or s.upper() in app_key or app_key in s.upper():
                        if "id" in app_data:
                            emoji_id = app_data["id"]
                            break
                _srv_btns.append({"text": f"{s}", "icon_custom_emoji_id": emoji_id, "callback_data": f"g_s_{s}", "style": "primary"})
            for i in range(0, len(_srv_btns), 2):
                kb.append(_srv_btns[i:i+2])
            
            for b in c_msg.get("buttons", []): 
                b_copy = b.copy()
                if "style" not in b_copy: b_copy["style"] = "primary"
                kb.append([b_copy])
            kb.append([{"text": "Close", "icon_custom_emoji_id": "5420130255174145507", "callback_data": "close_msg", "style": "danger"}])
            
            send_message(chat_id, txt, reply_markup={"inline_keyboard": kb})

    elif text == "Search Number":
        user_states[chat_id] = "wait_for_search"
        c_msg = bot_settings["custom_messages"].get("search_number", {})
        txt = render_body_text(c_msg.get("text", f"{PEM['num']} Search Number"))
        kb = [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "cancel_state", "style": "danger"}]]
        for b in c_msg.get("buttons", []): 
            b_copy = b.copy()
            if "style" not in b_copy: b_copy["style"] = "primary"
            kb.append([b_copy])
        send_message(chat_id, txt, reply_markup={"inline_keyboard": kb})

    elif text == "100 Bulk Number" or text == "100 Buy Number":
        local_srvs = set([b["service"] for b in number_batches.values() if b["numbers"]])
        zenex_srvs = set(bot_settings.get("zenex_services", {}).keys())
        stex_srvs  = set(bot_settings.get("stex_services", {}).keys())
        voltx_srvs = set(bot_settings.get("voltx_services", {}).keys())
        nexus_srvs = set(bot_settings.get("nexus_services", {}).keys())
        all_services = local_srvs.union(zenex_srvs).union(stex_srvs).union(voltx_srvs).union(nexus_srvs)

        if not all_services:
            send_message(chat_id, render_body_text(f"{PEM['no']} No numbers or services available! Admin must configure Zenex services or upload stock."))
        else:
            txt = render_body_text(f"╔═══════════╗\n     📦 <b>100 BULK NUMBER</b>\n╚═══════════╝\n✅ একটি service বাছুন\n━━━━━━━━━━━━━\n📝 আপনাকে 100টি নম্বর পাঠানো হবে\n━━━━━━━━━━━━━")
            apps_db = bot_settings.get("premium_apps", {})
            kb = []
            for s in all_services:
                emoji_id = "5352694861990501856"
                for app_key, app_data in apps_db.items():
                    if s.upper() == app_key or s.upper() in app_key or app_key in s.upper():
                        if "id" in app_data:
                            emoji_id = app_data["id"]
                            break
                kb.append([{"text": f"{s}", "icon_custom_emoji_id": emoji_id, "callback_data": f"bulk100_s_{s}", "style": "primary"}])
            kb.append([{"text": "Close", "icon_custom_emoji_id": "5420130255174145507", "callback_data": "close_msg", "style": "danger"}])
            send_message(chat_id, txt, reply_markup={"inline_keyboard": kb})

    elif text == "2F CODE" or text == "2FA ONLINE" or text == "🔐 2FA ONLINE":
        txt = f"━━━━━━━━━━━━━━━\n《 🔐 <b>2F CODE</b> 》\n━━━━━━━━━━━━━━━\n<i>নিচের যেকোনো একটি সেবা বেছে নিন।</i>\n━━━━━━━━━━━━━━━"
        kb = [
            [{"text": "2FA CODE", "icon_custom_emoji_id": "5353022963132174959", "callback_data": "gen_2fa", "style": "success"}],
            [{"text": "RANDOM NAME", "icon_custom_emoji_id": "5352552689983067014", "callback_data": "rand_name", "style": "primary"}],
            [{"text": "Close", "icon_custom_emoji_id": "5420130255174145507", "callback_data": "close_msg", "style": "danger"}]
        ]
        send_message(chat_id, render_body_text(txt), reply_markup={"inline_keyboard": kb})

    elif text == "LEADERBOARD":
        # ── Public Top-10 OTP Leaderboard ──────────────────────────────────
        num_map = {"1": "1️⃣", "2": "2️⃣", "3": "3️⃣", "4": "4️⃣", "5": "5️⃣",
                   "6": "6️⃣", "7": "7️⃣", "8": "8️⃣", "9": "9️⃣", "0": "0️⃣"}
        def _pnum(n): return "".join(num_map.get(c, c) for c in str(n))

        rows = ""
        count = 1
        limit = 10
        try:
            # ── Firestore path ──────────────────────────────────────────────
            if db:
                users = db.collection('users').order_by("total_otps", direction="DESCENDING").limit(limit).stream()
                for u in users:
                    d = u.to_dict()
                    otps = d.get("total_otps", 0)
                    if otps <= 0: continue
                    name = d.get("first_name") or d.get("name") or f"User"
                    uid  = u.id
                    p = "└" if count == limit else "├"
                    rows += f"{p} {_pnum(count)} <a href='tg://user?id={uid}'><b>{name}</b></a> ➔ {otps} OTP\n"
                    count += 1
            # ── Local fallback ──────────────────────────────────────────────
            if not rows:
                sorted_users = sorted(
                    _local_users.items(),
                    key=lambda x: x[1].get("total_otps", 0),
                    reverse=True
                )[:limit]
                for uid_str, d in sorted_users:
                    otps = d.get("total_otps", 0)
                    if otps <= 0: continue
                    name = d.get("first_name") or d.get("name") or f"User"
                    p = "└" if count == limit else "├"
                    rows += f"{p} {_pnum(count)} <a href='tg://user?id={uid_str}'><b>{name}</b></a> ➔ {otps} OTP\n"
                    count += 1
        except Exception as _e:
            rows = f"└ <i>Error: {_e}</i>\n"

        if not rows:
            rows = "└ <i>এখনো কোনো OTP receive হয়নি।</i>\n"

        txt = (
            f"━━━━━━━━━━━━━━━\n"
            f"《 {PEM['graph']} <b>TOP 10 LEADERBOARD</b> 》\n"
            f"━━━━━━━━━━━━━━━\n"
            f"{PEM['msg']} <b>OTP RECEIVERS</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"{rows}"
            f"━━━━━━━━━━━━━━━"
        )
        kb = {"inline_keyboard": [[
            {"text": "Refresh", "icon_custom_emoji_id": "5420155432272438703", "callback_data": "pub_lb_refresh", "style": "success"},
            {"text": "Close", "icon_custom_emoji_id": "5420130255174145507", "callback_data": "close_msg", "style": "danger"}
        ]]}
        send_message(chat_id, render_body_text(txt), reply_markup=kb)

    elif text == "Live Support Admin":
        first_name = msg.get("from", {}).get("first_name", "User")
        last_name = msg.get("from", {}).get("last_name", "")
        full_name = f"{first_name} {last_name}".strip()
        user_states[chat_id] = "wait_for_support_msg"
        temp_data[chat_id] = {"support_name": full_name}
        kb = [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "cancel_state", "style": "danger"}]]
        send_message(chat_id, render_body_text(
            "💬 <b>Live Support Admin</b>\n\n"
            "➖➖➖➖➖➖➖\n"
            "📝 আপনার সমস্যা বা প্রশ্ন টাইপ করুন।\n"
            "Admin reply দিলে আপনি সাথে সাথে পাবেন।\n"
            "➖➖➖➖➖➖➖"
        ), reply_markup={"inline_keyboard": kb})
        return

    elif text == "SUPPORT":
        c_msg = bot_settings["custom_messages"].get("support", {})
        txt = render_body_text(c_msg.get("text", f"{PEM['msg']} Support"))
        if not txt.strip(): txt = render_body_text(f"{PEM['msg']} Support")
        kb = []
        for b in c_msg.get("buttons", []):
            b_copy = b.copy()
            if "style" not in b_copy: b_copy["style"] = "primary"
            kb.append([b_copy])
            
        sup_link = bot_settings.get("support_link", "")
        if sup_link:
            kb.insert(0, [{"text": "Contact Support", "icon_custom_emoji_id": "5337302974806922068", "url": sup_link, "style": "success"}])
            
        kb.append([{"text": "Close", "icon_custom_emoji_id": "5420130255174145507", "callback_data": "close_msg", "style": "danger"}])
        send_message(chat_id, txt, reply_markup={"inline_keyboard": kb} if kb else None)

def expire_previous_number(chat_id):
    if chat_id in user_active_sessions:
        prev_data = user_active_sessions[chat_id]
        prev_msg_id = prev_data["msg_id"]
        nums = prev_data["nums"]
        
        # Nexa সিস্টেম থেকে রিমুভ করা যাতে ইনবক্সে আর মেসেজ না যায়
        for num in nums:
            # Format normalize — stored key may be with or without + prefix
            num_clean = str(num).replace('+', '').replace(' ', '').replace('-', '').strip()
            num_plus  = '+' + num_clean
            for d in (stex_assigned_numbers, voltx_assigned_numbers, zenex_assigned_numbers):
                d.pop(num, None)
                d.pop(num_clean, None)
                d.pop(num_plus, None)
        save_db()
        
        # আগের মেসেজ ইডিট করে Expired বাটন বসানো
        kb = [[{"text": "Number Expired", "icon_custom_emoji_id": "5336997731481193790", "callback_data": "ignore", "style": "danger"}]]
        try:
            edit_message(chat_id, prev_msg_id, "ㅤ\n", reply_markup={"inline_keyboard": kb})
        except:
            pass
        del user_active_sessions[chat_id]

# ==========================================
# Callback Query Handler
# ==========================================
def handle_callback(call):
    global total_assigned_stats
    chat_id = call["message"]["chat"]["id"]
    chat_type = call["message"]["chat"].get("type", "private")
    data = call.get("data", "")

    # 🌟 Button Loading Fix: বাটন চাপার সাথে সাথেই টেলিগ্রামকে Response দিয়ে দেওয়া, যাতে বাটন আটকে না থাকে!
    if not data.startswith("test_p_conn_") and not data.startswith("c_n_") and not data.startswith("g_c_"):
        try: threading.Thread(target=answer_callback, args=(call["id"],)).start()
        except: pass

    if chat_type != "private" and not (data.startswith("wapp_") or data.startswith("wrej_") or data.startswith("bapp_") or data.startswith("brej_")):
        return

    msg_id = call["message"]["message_id"]

    if chat_type == "private":
        if is_user_banned(chat_id):
            answer_callback(call["id"], "🚫 You are banned from using this bot!", show_alert=True)
            return

    if not check_force_join(chat_id) and data != "check_fj":
        send_force_join_msg(chat_id)
        return

    if data == "check_fj":
        if check_force_join(chat_id):
            delete_message(chat_id, msg_id)
            send_message(chat_id, render_body_text(f"{PEM['ok']} Thanks for joining! You can now use the bot."), reply_markup=main_menu(chat_id))
            
            # --- PROCESS PENDING REFERRAL (works with or without Firestore) ---
            _process_pending_referral(chat_id)
        else:
            answer_callback(call["id"], "❌ You haven't joined all channels yet!", show_alert=True)
        return

    if data == "close_msg":
        delete_message(chat_id, msg_id)

    elif data == "otp_done":
        # ব্যবহারকারী OTP পেয়েছে — session expire করে মেসেজ বন্ধ করো
        expire_previous_number(chat_id)
        answer_callback(call["id"], "✅ Done! Number session closed.", show_alert=False)

    elif data == "expire_num":
        # ব্যবহারকারী নম্বর expire করতে চায়
        expire_previous_number(chat_id)
        answer_callback(call["id"], "❌ Number expired.", show_alert=False)

    elif data == "cancel_state":
        if chat_id in user_states: del user_states[chat_id]
        if chat_id in temp_data: del temp_data[chat_id]
        delete_message(chat_id, msg_id)

    elif data.startswith("sup_reply_"):
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True)
            return
        target_uid = int(data.replace("sup_reply_", ""))
        user_states[chat_id] = "wait_for_admin_support_reply"
        temp_data[chat_id] = {"support_target_user": target_uid}
        edit_message(chat_id, msg_id, render_body_text(
            f"💬 <b>Reply to User</b>\n"
            f"➖➖➖➖➖➖➖\n"
            f"🆔 User ID: <code>{target_uid}</code>\n"
            f"➖➖➖➖➖➖➖\n"
            f"📝 আপনার reply টাইপ করুন:"
        ), reply_markup={"inline_keyboard": [[{"text": "Cancel", "callback_data": "cancel_state", "style": "danger"}]]})
        answer_callback(call["id"])

    elif data == "rand_name":
        # ── Random Name Generator ───────────────────────────────────────────
        first_names = [
            "Arif", "Sakib", "Raihan", "Imran", "Rahim", "Karim", "Hasan", "Nabil",
            "Farhan", "Tanvir", "Mahdi", "Shihab", "Jubair", "Rashed", "Zahid",
            "Mehedi", "Shuvo", "Rakib", "Tuhin", "Asif", "Rifat", "Sadat", "Naeem",
            "Sumon", "Limon", "Milon", "Nahid", "Yusuf", "Bashir", "Anwar",
            "Adnan", "Shahin", "Sayem", "Fahim", "Ripon", "Mamun", "Babu", "Robin",
            "Siam", "Fuad", "Ridoy", "Shohan", "Alif", "Anik", "Rony", "Tanjim",
            "Sohel", "Jewel", "Dulal", "Riaz", "Sabbir", "Maruf", "Emon", "Tahmid"
        ]
        last_names = [
            "Ahmed", "Islam", "Hossain", "Rahman", "Khan", "Ali", "Mia", "Sarkar",
            "Chowdhury", "Alam", "Uddin", "Sheikh", "Bhuiyan", "Mondal", "Dey",
            "Paul", "Roy", "Das", "Biswas", "Saha", "Nath", "Ghosh", "Barua",
            "Talukdar", "Hawlader", "Majumder", "Sikder", "Mollah", "Bepari", "Gazi",
            "Shikder", "Fakir", "Barik", "Patowary", "Chandra", "Kumar", "Gain",
            "Halder", "Mandal", "Karmaker", "Nandi", "Sutradhar", "Chakraborty"
        ]
        rand_first = random.choice(first_names)
        rand_last  = random.choice(last_names)
        full_rand_name = f"{rand_first} {rand_last}"
        admin_pass = bot_settings.get("rand_name_pass", "")
        pass_line = f"\n🔑 <b>PASS:</b> <code>{admin_pass}</code>" if admin_pass else ""
        txt = (
            f"━━━━━━━━━━━━━━━\n"
            f"《 {PEM['star']} <b>RANDOM NAME</b> 》\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👤 <b>NAME:</b> <code>{full_rand_name}</code>"
            f"{pass_line}\n"
            f"━━━━━━━━━━━━━━━"
        )
        kb = [
            [{"text": full_rand_name, "icon_custom_emoji_id": "5352861489541714456", "copy_text": {"text": full_rand_name}, "style": "success"}],
            [{"text": "New Name", "icon_custom_emoji_id": "5377774889723798543", "callback_data": "rand_name", "style": "primary"}],
            [{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "back_to_2fmenu", "style": "danger"}]
        ]
        if admin_pass:
            kb.insert(1, [{"text": admin_pass, "icon_custom_emoji_id": "5353022963132174959", "copy_text": {"text": admin_pass}, "style": "primary"}])
        edit_message(chat_id, msg_id, render_body_text(txt), reply_markup={"inline_keyboard": kb})
        answer_callback(call["id"])

    elif data == "back_to_2fmenu":
        txt = f"━━━━━━━━━━━━━━━\n《 🔐 <b>2F CODE</b> 》\n━━━━━━━━━━━━━━━\n<i>নিচের যেকোনো একটি সেবা বেছে নিন।</i>\n━━━━━━━━━━━━━━━"
        kb = [
            [{"text": "2FA CODE", "icon_custom_emoji_id": "5353022963132174959", "callback_data": "gen_2fa", "style": "success"}],
            [{"text": "RANDOM NAME", "icon_custom_emoji_id": "5352552689983067014", "callback_data": "rand_name", "style": "primary"}],
            [{"text": "Close", "icon_custom_emoji_id": "5420130255174145507", "callback_data": "close_msg", "style": "danger"}]
        ]
        edit_message(chat_id, msg_id, render_body_text(txt), reply_markup={"inline_keyboard": kb})
        answer_callback(call["id"])

    elif data == "cancel_2fa":
        if chat_id in user_states: del user_states[chat_id]
        if chat_id in temp_data: del temp_data[chat_id]
        txt = f"━━━━━━━━━━━━━━━\n《 🔐 <b>2F CODE</b> 》\n━━━━━━━━━━━━━━━\n<i>নিচের যেকোনো একটি সেবা বেছে নিন।</i>\n━━━━━━━━━━━━━━━"
        kb = [
            [{"text": "2FA CODE", "icon_custom_emoji_id": "5353022963132174959", "callback_data": "gen_2fa", "style": "success"}],
            [{"text": "RANDOM NAME", "icon_custom_emoji_id": "5352552689983067014", "callback_data": "rand_name", "style": "primary"}],
            [{"text": "Close", "icon_custom_emoji_id": "5420130255174145507", "callback_data": "close_msg", "style": "danger"}]
        ]
        edit_message(chat_id, msg_id, render_body_text(txt), reply_markup={"inline_keyboard": kb})
        answer_callback(call["id"])

    elif data == "gen_2fa":
        user_states[chat_id] = "wait_for_2fa_key"
        temp_data[chat_id] = {"msg_id": msg_id}
        txt = "━━━━━━━━━━━━━━━\n《 🔑 <b>ENTER 2FA KEY</b> 》\n━━━━━━━━━━━━━━━\n📝 <b>SEND YOUR 2FA SECRET KEY</b>\n━━━━━━━━━━━━━━━"
        kb = {"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "cancel_2fa", "style": "danger"}]]}
        edit_message(chat_id, msg_id, render_body_text(txt), reply_markup=kb)
        answer_callback(call["id"])

    elif data.startswith("ref_2fa_"):
        secret = data.replace("ref_2fa_", "")
        try:
            totp = pyotp.TOTP(secret)
            code = totp.now()
            remaining_time = 30 - (int(time.time()) % 30)
            
            success_txt = (
                f"━━━━━━━━━━━━━━━\n"
                f"《 🔐 <b>2FA CODE</b> 》\n"
                f"━━━━━━━━━━━━━━━\n"
                f"🔐 <b>CODE:</b> <code>{code}</code>\n"
                f"━━━━━━━━━━━━━━━\n"
                f"🕓 <b>EXPIRES IN:</b> {remaining_time}s\n"
                f"━━━━━━━━━━━━━━━"
            )
            kb = [[{"text": f"Click to copy {code}", "icon_custom_emoji_id": "5353022963132174959", "copy_text": {"text": code}, "style": "success"}],
                  [{"text": "Refresh", "icon_custom_emoji_id": "5420155432272438703", "callback_data": f"ref_2fa_{secret}", "style": "primary"},
                   {"text": "New Code", "icon_custom_emoji_id": "5352552689983067014", "callback_data": "gen_2fa", "style": "danger"}],
                  [{"text": "Close", "icon_custom_emoji_id": "5420130255174145507", "callback_data": "close_msg", "style": "danger"}]]
            
            edit_message(chat_id, msg_id, render_body_text(success_txt), reply_markup={"inline_keyboard": kb})
        except:
            answer_callback(call["id"], "❌ Error refreshing code!", show_alert=True)

    elif data == "cancel_dxa_edit":
        if chat_id in user_states: del user_states[chat_id]
        if chat_id in temp_data: del temp_data[chat_id]
        edit_message(chat_id, msg_id, render_body_text("🕹 <b>RAHIN CONTROL PANEL</b>"), reply_markup=dxa_control_keyboard())
        
    elif data == "dummy_alert":
        answer_callback(call["id"], "This feature will be added later!", show_alert=True)
        
    elif data == "pub_lb_refresh":
        # ── Public Leaderboard Refresh ──────────────────────────────────────
        num_map = {"1": "1️⃣", "2": "2️⃣", "3": "3️⃣", "4": "4️⃣", "5": "5️⃣",
                   "6": "6️⃣", "7": "7️⃣", "8": "8️⃣", "9": "9️⃣", "0": "0️⃣"}
        def _pnum2(n): return "".join(num_map.get(c, c) for c in str(n))
        rows = ""
        count = 1
        limit = 10
        try:
            if db:
                users = db.collection('users').order_by("total_otps", direction="DESCENDING").limit(limit).stream()
                for u in users:
                    d = u.to_dict()
                    otps = d.get("total_otps", 0)
                    if otps <= 0: continue
                    name = d.get("first_name") or d.get("name") or "User"
                    p = "└" if count == limit else "├"
                    rows += f"{p} {_pnum2(count)} <a href='tg://user?id={u.id}'><b>{name}</b></a> ➔ {otps} OTP\n"
                    count += 1
            if not rows:
                for uid_str, d in sorted(_local_users.items(), key=lambda x: x[1].get("total_otps", 0), reverse=True)[:limit]:
                    otps = d.get("total_otps", 0)
                    if otps <= 0: continue
                    name = d.get("first_name") or d.get("name") or "User"
                    p = "└" if count == limit else "├"
                    rows += f"{p} {_pnum2(count)} <a href='tg://user?id={uid_str}'><b>{name}</b></a> ➔ {otps} OTP\n"
                    count += 1
        except Exception as _e:
            rows = f"└ <i>Error: {_e}</i>\n"
        if not rows: rows = "└ <i>এখনো কোনো OTP receive হয়নি।</i>\n"
        txt = (
            f"━━━━━━━━━━━━━━━\n"
            f"《 {PEM['graph']} <b>TOP 10 LEADERBOARD</b> 》\n"
            f"━━━━━━━━━━━━━━━\n"
            f"{PEM['msg']} <b>OTP RECEIVERS</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"{rows}"
            f"━━━━━━━━━━━━━━━"
        )
        kb = {"inline_keyboard": [[
            {"text": "Refresh", "icon_custom_emoji_id": "5420155432272438703", "callback_data": "pub_lb_refresh", "style": "success"},
            {"text": "Close", "icon_custom_emoji_id": "5420130255174145507", "callback_data": "close_msg", "style": "danger"}
        ]]}
        edit_message(chat_id, msg_id, render_body_text(txt), reply_markup=kb)
        answer_callback(call["id"], "✅ Refreshed!", show_alert=False)

    elif data == "refresh_traffic":
        txt, markup = build_traffic_ui()
        edit_message(chat_id, msg_id, txt, reply_markup=markup)
        answer_callback(call["id"], "✅ Traffic Refreshed!", show_alert=False)

    elif data.startswith("exp_rng_"):
        srv_query = data.replace("exp_rng_", "")
        
        country_stats = {}
        current_time = time.time()
        for t in recent_traffic:
            if current_time - t.get("time", 0) <= 3600:
                if t.get("service", "").startswith(srv_query):
                    iso = t.get("iso", "XX")
                    flag = t.get("flag", "🌍")
                    if iso not in country_stats:
                        country_stats[iso] = {"count": 0, "flag": flag}
                    country_stats[iso]["count"] += 1
        
        if not country_stats:
            answer_callback(call["id"], "❌ No recent traffic found for this service!", show_alert=True)
            return
            
        kb = []
        for iso, c_data in sorted(country_stats.items(), key=lambda x: x[1]["count"], reverse=True):
            count = c_data["count"]
            c_name = iso
            emoji_id = "5780471598922337683"
            for code, fdata in bot_settings.get("premium_flags", {}).items():
                if fdata.get("iso") == iso:
                    c_name = fdata.get("name", iso)
                    if "id" in fdata: emoji_id = fdata["id"]
                    break
            
            btn_text = f"{c_name} ({iso}) - {count} OTP"
            kb.append([{"text": btn_text, "icon_custom_emoji_id": emoji_id, "callback_data": f"exp_c_{srv_query}_{iso}", "style": "primary"}])
            
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "refresh_traffic", "style": "danger"}])
        
        app_full_name, prem_app_html = get_service_info_html(srv_query)
        edit_message(chat_id, msg_id, render_body_text(f"📊 <b>Explore Service: {prem_app_html} {app_full_name}</b>\n\nSelect a country to view available ranges:"), reply_markup={"inline_keyboard": kb})
        answer_callback(call["id"])

    elif data.startswith("exp_c_"):
        parts = data.split("_")
        srv_query = parts[2]
        iso_query = parts[3]
        
        nums = []
        current_time = time.time()
        for t in recent_traffic:
            if current_time - t.get("time", 0) <= 3600:
                if t.get("service", "").startswith(srv_query) and t.get("iso") == iso_query:
                    num = t.get("number", "").replace("+", "").strip()
                    if num: nums.append(num)
        
        if not nums:
            answer_callback(call["id"], "❌ No recent numbers found for this country!", show_alert=True)
            return
            
        # Zenex Services থেকে রেঞ্জ নিবো (Search Countries নিবো না)
        known_ranges = set()
        for s_name, c_dict in bot_settings.get("zenex_services", {}).items():
            for c_name, r_list in c_dict.items():
                for r in r_list:
                    known_ranges.add(r)
                    
        sorted_known = sorted(list(known_ranges), key=len, reverse=True)
        
        r_counts = Counter()
        for num in nums:
            matched = False
            for r in sorted_known:
                if num.startswith(r):
                    r_counts[r] += 1
                    matched = True
                    break
            if not matched:
                if len(num) >= 7:
                    r_counts[num[:7]] += 1
                else:
                    r_counts[num] += 1
                    
        r_list = r_counts.most_common(12)
        
        kb = []
        for r, count in r_list:
            # এক লাইনে একটা করে বাটন
            kb.append([{"text": f"{r} ({count})", "icon_custom_emoji_id": "5352862640592949843", "copy_text": {"text": r}, "style": "primary"}])
            
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"exp_rng_{srv_query}", "style": "danger"}])
        
        app_full_name, prem_app_html = get_service_info_html(srv_query)
        prem_flag_html = get_flag_info_html(iso_query)
        
        edit_message(chat_id, msg_id, render_body_text(f"📊 <b>Ranges for {prem_app_html} {app_full_name} - {prem_flag_html} {iso_query}</b>\n\nClick on any range to copy it."), reply_markup={"inline_keyboard": kb})
        answer_callback(call["id"])

    # --- User Management Flows Integration ---
    elif data == "user_management":
        edit_message(chat_id, msg_id, get_user_management_text(), reply_markup=user_management_keyboard())

    elif data == "um_manage_balance":
        user_states[chat_id] = "wait_for_um_bal_uid"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the User ID to Manage Balance:"), reply_markup=get_cancel_kb())
        
    elif data == "um_ban_unban":
        user_states[chat_id] = "wait_for_um_ban_uid"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the User ID to Ban or Unban:"), reply_markup=get_cancel_kb())

    elif data == "um_user_profile":
        user_states[chat_id] = "wait_for_um_prof_uid"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the User ID to View Profile:"), reply_markup=get_cancel_kb())

    elif data == "um_user_otp_rate":
        user_states[chat_id] = "wait_for_user_rate_uid"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text(
            "💰 <b>User OTP Rate Set করুন</b>\n\n"
            "📝 যে User এর rate আলাদা করতে চান তার User ID পাঠান:\n\n"
            "<i>Example: 123456789</i>"
        ), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "user_management", "style": "danger"}]]})

    elif data == "um_view_user_rates":
        rates = bot_settings.get("user_otp_rates", {})
        if not rates:
            answer_callback(call["id"], "কোনো Custom Rate নেই।", show_alert=True)
        else:
            kb = []
            lines = []
            for uid, rate in rates.items():
                lines.append(f"👤 <code>{uid}</code> → <b>{rate} TK</b>")
                kb.append([{"text": f"🗑 Remove {uid}", "callback_data": f"rm_user_rate_{uid}", "style": "danger"}])
            kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "user_management", "style": "primary"}])
            edit_message(chat_id, msg_id, render_body_text(
                f"💰 <b>Custom User OTP Rates ({len(rates)}):</b>\n\n" + "\n".join(lines)
            ), reply_markup={"inline_keyboard": kb})

    elif data.startswith("rm_user_rate_"):
        uid_to_rm = data.replace("rm_user_rate_", "")
        if uid_to_rm in bot_settings.get("user_otp_rates", {}):
            del bot_settings["user_otp_rates"][uid_to_rm]
            save_db()
            answer_callback(call["id"], f"✅ {uid_to_rm} এর Custom Rate সরানো হয়েছে!", show_alert=True)
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "um_view_user_rates", "id": "internal"})

    # --- Menu Design Integration ---
    elif data == "menu_design_list":
        edit_message(chat_id, msg_id, render_body_text(f"🎨 <b>Menu Design Editor</b>\n\nSelect a menu block to edit its Body Text and Inline Buttons. You can use Premium Emojis too!"), reply_markup=menu_design_list_keyboard())

    elif data == "md_reset_defaults":
        bot_settings["custom_messages"] = DEFAULT_CUSTOM_MESSAGES.copy()
        save_db()
        answer_callback(call["id"], "✅ Resetted to Premium Defaults!", show_alert=True)

    elif data.startswith("md_edit_"):
        answer_callback(call["id"])
        if chat_id in user_states: del user_states[chat_id]
        if chat_id in temp_data: del temp_data[chat_id]
        key = data.replace("md_edit_", "")
        cm_text = render_body_text(bot_settings["custom_messages"].get(key, {}).get("text", "..."))
        try:
            edit_message(chat_id, msg_id, render_body_text(f"🎨 <b>Editing: {key.upper()}</b>\n\nPreview of current Text:\n{cm_text}"), reply_markup=menu_edit_options_keyboard(key))
        except: pass

    elif data.startswith("md_text_"):
        key = data.replace("md_text_", "")
        user_states[chat_id] = "wait_for_menu_text"
        temp_data[chat_id] = {"msg_id": msg_id, "menu_key": key}
        edit_message(chat_id, msg_id, render_body_text(f"📝 <b>Edit Body: {key.upper()}</b>\n\nSend the new text. You can use Premium Emojis directly here.\n(Use standard HTML like <b>bold</b>, <i>italic</i> for formatting)"), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"md_edit_{key}", "style": "danger"}]]})

    elif data.startswith("md_btns_"):
        answer_callback(call["id"]) 
        if chat_id in user_states: del user_states[chat_id] 
        if chat_id in temp_data: del temp_data[chat_id]
        key = data.replace("md_btns_", "")
        try:
            edit_message(chat_id, msg_id, render_body_text(f"⚙️ <b>Edit Inline Buttons: {key.upper()}</b>"), reply_markup=menu_buttons_list_keyboard(key))
        except: pass

    elif data.startswith("md_addbtn_"):
        key = data.replace("md_addbtn_", "")
        user_states[chat_id] = "wait_for_menu_btn"
        temp_data[chat_id] = {"msg_id": msg_id, "menu_key": key}
        edit_message(chat_id, msg_id, render_body_text(f"➕ <b>Add Button: {key.upper()}</b>\n\nSend custom button in this format:\n<code>Button Text - https://link.com</code>\n\n<i>(Only normal Emojis supported here!)</i>"), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"md_btns_{key}", "style": "danger"}]]})

    elif data.startswith("md_delbtn_"):
        parts = data.split("_")
        key = parts[2]
        b_idx = int(parts[3])
        if b_idx < len(bot_settings["custom_messages"][key]["buttons"]):
            del bot_settings["custom_messages"][key]["buttons"][b_idx]
            save_db()
            answer_callback(call["id"], "✅ Button Deleted!", show_alert=True)
            edit_message(chat_id, msg_id, render_body_text(f"⚙️ <b>Edit Inline Buttons: {key.upper()}</b>"), reply_markup=menu_buttons_list_keyboard(key))

    elif data.startswith("sel_wm_"):
        method = data.replace("sel_wm_", "")
        bal = get_user(chat_id).get('balance', 0.0)
        min_w = bot_settings['min_withdraw']
        
        if bal < min_w:
            answer_callback(call["id"], f"❌ আপনার ব্যালেন্স অপর্যাপ্ত! মিনিমাম {min_w} ৳ প্রয়োজন।", show_alert=True)
            return
            
        temp_data[chat_id] = {"method": method, "balance": bal, "msg_id": msg_id}
        user_states[chat_id] = "wait_for_withdraw_amount"
        edit_message(chat_id, msg_id, render_body_text(f"{PEM['ok']} Method: {method}\n💰 Available Balance: {bal} ৳\n\n📝 Enter the amount you want to withdraw (Min: {min_w} ৳):"), reply_markup=get_cancel_kb())
        answer_callback(call["id"])

    elif data == "test_message_flow":
        user_states[chat_id] = "wait_for_test_service"
        temp_data[chat_id] = {}
        edit_message(chat_id, msg_id, render_body_text("🧪 <b>Test Mode</b>\n\n📝 Send the Service Name (e.g., IG):"), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "system_settings", "style": "danger"}]]})

    elif data == "manage_emojis":
        edit_message(chat_id, msg_id, render_body_text(f"{PEM['star']} <b>Premium Emoji Management</b>\n\nUpload your TXT files or manually add them below:"), reply_markup=emoji_settings_keyboard())

    elif data == "up_flags_txt":
        user_states[chat_id] = "wait_for_flag_txt"
        edit_message(chat_id, msg_id, render_body_text("📂 Please upload the <b>Flag Emojis</b> <code>.txt</code> file."), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "manage_emojis", "style": "danger"}]]})

    elif data == "up_apps_txt":
        user_states[chat_id] = "wait_for_app_txt"
        edit_message(chat_id, msg_id, render_body_text("📂 Please upload the <b>Service Apps</b> <code>.txt</code> file."), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "manage_emojis", "style": "danger"}]]})

    elif data == "add_single_emoji":
        user_states[chat_id] = "wait_for_emoji_extract"
        edit_message(chat_id, msg_id, render_body_text("📝 যেকোনো একটি Premium Emoji সেন্ড করুন (যেমন: 🇧🇩 বা 🚫):"), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "manage_emojis", "style": "danger"}]]})

    elif data == "dl_flags_txt":
        content = generate_emoji_txt("flags")
        if content:
            send_document(chat_id, "Flag_Emojis.txt", content)
            answer_callback(call["id"], "✅ Downloaded!")
        else:
            answer_callback(call["id"], "❌ No Flag Emojis found!", show_alert=True)

    elif data == "dl_apps_txt":
        content = generate_emoji_txt("apps")
        if content:
            send_document(chat_id, "Service_Apps.txt", content)
            answer_callback(call["id"], "✅ Downloaded!")
        else:
            answer_callback(call["id"], "❌ No App Emojis found!", show_alert=True)

    elif data == "del_all_flags":
        bot_settings["premium_flags"] = {}
        save_db()
        answer_callback(call["id"], "✅ All Premium Flags Deleted Successfully!", show_alert=True)

    elif data == "broadcast_msg":
        user_states[chat_id] = "wait_for_broadcast"
        edit_message(chat_id, msg_id, render_body_text("📢 <b>Broadcast Mode</b>\n\nSend the message you want to broadcast (Text, Photo, Video, File etc)."), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "back_to_admin", "style": "danger"}]]})

    elif data == "upload_num":
        user_states[chat_id] = "wait_for_txt"
        edit_message(chat_id, msg_id, render_body_text("📂 Please upload the numbers in a <b>.txt</b> file."), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "back_to_admin", "style": "danger"}]]})

    elif data == "delete_files":
        kb = []
        for b_id, b_data in number_batches.items():
            kb.append([{"text": f"{b_data['filename']} ({len(b_data['numbers'])})", "icon_custom_emoji_id": "5422557736330106570", "callback_data": f"del_b_{b_id}", "style": "danger"}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "back_to_admin", "style": "primary"}])
        txt = "🗑 Select a file to delete:" if len(kb) > 1 else f"{PEM['no']} No files found."
        edit_message(chat_id, msg_id, render_body_text(txt), reply_markup={"inline_keyboard": kb})

    elif data.startswith("del_b_"):
        b_id = data.split("del_b_")[1]
        if b_id in number_batches:
            del number_batches[b_id]
            save_db()
            answer_callback(call["id"], "✅ File deleted!", show_alert=True)
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "delete_files", "id": call["id"]})

    elif data == "show_used":
        kb = {"inline_keyboard": [[{"text": "Download TXT", "icon_custom_emoji_id": "5257969839313526622", "callback_data": "dl_used", "style": "primary"}], [{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "back_to_admin", "style": "danger"}]]}
        edit_message(chat_id, msg_id, render_body_text(f"{PEM['ok']} <b>Total Used Numbers:</b> {len(used_numbers_list)}"), reply_markup=kb)

    elif data == "show_unused":
        unused_count = sum(len(b["numbers"]) for b in number_batches.values())
        kb = {"inline_keyboard": [[{"text": "Download TXT", "icon_custom_emoji_id": "5257969839313526622", "callback_data": "dl_unused", "style": "primary"}], [{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "back_to_admin", "style": "danger"}]]}
        edit_message(chat_id, msg_id, render_body_text(f"{PEM['rocket']} <b>Total Unused Numbers:</b> {unused_count}"), reply_markup=kb)

    elif data == "dl_used":
        if not used_numbers_list:
            answer_callback(call["id"], "❌ No used numbers found!", show_alert=True)
            return
        content = "\n".join(used_numbers_list).encode('utf-8')
        send_document(chat_id, "used_numbers.txt", content)
        answer_callback(call["id"])

    elif data == "dl_unused":
        unused_list = [n["num"] for b in number_batches.values() for n in b["numbers"]]
        if not unused_list:
            answer_callback(call["id"], "❌ No unused numbers found!", show_alert=True)
            return
        content = "\n".join(unused_list).encode('utf-8')
        send_document(chat_id, "unused_numbers.txt", content)
        answer_callback(call["id"])

    elif data == "lb_main":
        txt = f"━━━━━━━━━━━━━━━\n《 {PEM['admin']} <b>LEADER BOARD MENU</b> 》\n━━━━━━━━━━━━━━━\n<i>Select a category to view the top performers or history.</i>\n━━━━━━━━━━━━━━━"
        kb = [
            [{"text": "Top Referrers", "icon_custom_emoji_id": "5420145051336485498", "callback_data": "lb_top_refs", "style": "primary"}],
            [{"text": "Top OTP Receivers", "icon_custom_emoji_id": "5353001161878182134", "callback_data": "lb_top_otps", "style": "primary"}],
            [{"text": "Withdrawal History", "icon_custom_emoji_id": "5348469219761626211", "callback_data": "lb_w_history", "style": "success"}],
            [{"text": "Back to Admin", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "back_to_admin", "style": "danger"}]
        ]
        edit_message(chat_id, msg_id, render_body_text(txt), reply_markup={"inline_keyboard": kb})

    elif data.startswith("lb_"):
        sub = data.replace("lb_", "")
        edit_message(chat_id, msg_id, render_body_text("⌛ <i>Fetching Data...</i>"))
        
        num_map = {"1": "1️⃣", "2": "2️⃣", "3": "3️⃣", "4": "4️⃣", "5": "5️⃣", "6": "6️⃣", "7": "7️⃣", "8": "8️⃣", "9": "9️⃣", "0": "0️⃣"}
        def get_p_num(n): return "".join([num_map.get(c, c) for c in str(n)])
        
        try:
            if sub == "top_refs":
                title, field, limit, icon = "TOP 5 REFERRERS", "total_refers", 5, PEM.get('user', '👥')
                users = db.collection('users').order_by(field, direction="DESCENDING").limit(limit).stream()
                res_txt = ""
                count = 1
                for u in users:
                    d = u.to_dict()
                    if d.get(field, 0) > 0:
                        p = "└" if count == limit else "├"
                        res_txt += f"{p} {get_p_num(count)} <a href='tg://user?id={u.id}'>{u.id}</a> ➔ <b>{d.get(field,0)}</b>\n"
                        count += 1
                if not res_txt: res_txt = "└ <i>No data found.</i>\n"

            elif sub == "top_otps":
                title, field, limit, icon = "TOP 5 OTP RECEIVERS", "total_otps", 5, PEM.get('msg', '📩')
                users = db.collection('users').order_by(field, direction="DESCENDING").limit(limit).stream()
                res_txt = ""
                count = 1
                for u in users:
                    d = u.to_dict()
                    if d.get(field, 0) > 0:
                        p = "└" if count == limit else "├"
                        res_txt += f"{p} {get_p_num(count)} <a href='tg://user?id={u.id}'>{u.id}</a> ➔ <b>{d.get(field,0)}</b>\n"
                        count += 1
                if not res_txt: res_txt = "└ <i>No data found.</i>\n"

            elif sub == "w_history":
                title, limit, icon = "LAST 10 WITHDRAWALS", 10, PEM.get('money', '💸')
                ws = db.collection('withdrawals').order_by('timestamp', direction="DESCENDING").limit(limit).stream()
                res_txt = ""
                count = 1
                for w in ws:
                    d = w.to_dict()
                    s = str(d.get('status','Pending')).lower()
                    stat_icon = PEM.get('ok','✅') if s in ["approved","success"] else PEM.get('no','❌') if s=="rejected" else "⏳"
                    uid = d.get('user_id','User')
                    p = "└" if count == limit else "├"
                    res_txt += f"{p} {get_p_num(count)} <a href='tg://user?id={uid}'>{uid}</a> ➔ <b>{d.get('amount',0)}৳</b> {stat_icon}\n"
                    count += 1
                if not res_txt: res_txt = "└ <i>No history found.</i>\n"

            final_msg = f"━━━━━━━━━━━━━━━\n{icon} <b>{title}</b>\n━━━━━━━━━━━━━━━\n{res_txt}━━━━━━━━━━━━━━━"
            kb = [[{"text": "Refresh", "icon_custom_emoji_id": "5420155432272438703", "callback_data": data, "style": "success"}, {"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "lb_main", "style": "danger"}]]
            edit_message(chat_id, msg_id, render_body_text(final_msg), reply_markup={"inline_keyboard": kb})

        except Exception as e:
            edit_message(chat_id, msg_id, render_body_text(f"❌ Error: {e}"), reply_markup={"inline_keyboard": [[{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "lb_main", "style": "danger"}]]})

    elif data == "back_to_admin":
        if chat_id in user_states: del user_states[chat_id]
        edit_message(chat_id, msg_id, get_admin_text(), reply_markup=admin_panel_keyboard())

    elif data == "adm_pending_w":
        if not is_admin(chat_id):
            answer_callback(call["id"], "🚫 Only Admins!", show_alert=True)
            return
        if not pending_withdrawals:
            edit_message(chat_id, msg_id,
                render_body_text("💰 <b>Pending Withdrawals</b>\n\n✅ No pending withdrawal requests!"),
                reply_markup={"inline_keyboard": [[{"text": "🔙 Back", "icon_custom_emoji_id": "5267490665117275166", "callback_data": "back_to_admin", "style": "primary"}]]})
            return
        kb = []
        txt = "💰 <b>PENDING WITHDRAWALS</b>\n━━━━━━━━━━━━━━━\n\n"
        for i, (req_id, req) in enumerate(list(pending_withdrawals.items()), 1):
            u_id   = req.get("user_id", "?")
            amt    = req.get("amount", 0)
            method = req.get("method", "?")
            number = req.get("number", "?")
            name   = req.get("full_name", str(u_id))
            txt += (f"{i}. 👤 <a href='tg://user?id={u_id}'>{name}</a>\n"
                    f"   💳 {amt} ৳ | 🏦 {method}\n"
                    f"   📱 <code>{number}</code>\n"
                    f"   🧾 <code>{req_id}</code>\n\n")
            kb.append([
                {"text": f"✅ APPROVE #{i}", "icon_custom_emoji_id": "5352694861990501856", "callback_data": f"wapp_{req_id}", "style": "success"},
                {"text": f"❌ REJECT #{i}", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"wrej_{req_id}", "style": "danger"}
            ])
        kb.append([{"text": "🔄 Refresh", "icon_custom_emoji_id": "5420155432272438703", "callback_data": "adm_pending_w", "style": "primary"},
                   {"text": "🔙 Back", "icon_custom_emoji_id": "5267490665117275166", "callback_data": "back_to_admin", "style": "danger"}])
        edit_message(chat_id, msg_id, render_body_text(txt), reply_markup={"inline_keyboard": kb})

    elif data == "system_settings":
        edit_message(chat_id, msg_id, render_body_text(f"{PEM['gear']} <b>System Settings</b>\nManage advanced bot configurations below:"), reply_markup=system_settings_keyboard())

    # ==========================================
    # Stex Control Callbacks
    # ==========================================
    elif data == "stex_control":
        edit_message(chat_id, msg_id, render_body_text(f"🌐 <b>Stex Control Panel</b>\n\nTotal API Keys: {len(bot_settings.get('stex_keys', []))}\nManage your Stex API Keys below:"), reply_markup=stex_control_keyboard())

    elif data == "add_stex_key":
        user_states[chat_id] = "wait_for_add_stex_key"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the new Stex API Key (e.g. nxa_...):"), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "stex_control", "style": "danger"}]]})

    elif data == "view_stex_keys":
        kb = []
        for idx, key in enumerate(bot_settings.get("stex_keys", [])):
            safe_name = key[:10] + "..." if len(key) > 10 else key
            kb.append([{"text": f"Delete {safe_name}", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"del_nxa_{idx}", "style": "danger"}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "stex_control", "style": "primary"}])
        edit_message(chat_id, msg_id, render_body_text("🗑 <b>Select Stex Key to Delete:</b>"), reply_markup={"inline_keyboard": kb})

    elif data.startswith("del_nxa_"):
        idx = int(data.split("_")[2])
        if 0 <= idx < len(bot_settings.get("stex_keys", [])):
            del bot_settings["stex_keys"][idx]
            save_db()
            answer_callback(call["id"], "✅ Stex Key Deleted!", show_alert=True)
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "view_stex_keys", "id": call["id"]})

    elif data == "stex_search_country":
        kb = []
        for idx, c in enumerate(bot_settings.get("stex_search_countries", [])):
            kb.append([{"text": f"Delete {c}", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"del_sc_{idx}", "style": "danger"}])
        kb.append([{"text": "Add Country Code", "icon_custom_emoji_id": "5420323438508155202", "callback_data": "add_search_country", "style": "success"}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "stex_control", "style": "primary"}])
        edit_message(chat_id, msg_id, render_body_text("🌍 <b>Allowed Search Countries:</b>\nOnly these country codes will be allowed in Search Number."), reply_markup={"inline_keyboard": kb})

    elif data == "add_search_country":
        user_states[chat_id] = "wait_for_add_sc"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the Country Code (e.g. 880 or 92):"), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "stex_search_country", "style": "danger"}]]})

    elif data.startswith("del_sc_"):
        idx = int(data.split("_")[2])
        if 0 <= idx < len(bot_settings.get("stex_search_countries", [])):
            del bot_settings["stex_search_countries"][idx]
            save_db()
            answer_callback(call["id"], "✅ Country Deleted!", show_alert=True)
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "stex_search_country", "id": call["id"]})

    elif data == "manage_stex_srv":
        kb = []
        srvs = bot_settings.get("stex_services", {})
        apps_db = bot_settings.get("premium_apps", {})
        for srv in srvs:
            emoji_id = "5257969839313526622"
            for app_key, app_data in apps_db.items():
                if srv.upper() == app_key or srv.upper() in app_key or app_key in srv.upper():
                    if "id" in app_data: emoji_id = app_data["id"]; break
            kb.append([{"text": f"{srv}", "icon_custom_emoji_id": emoji_id, "callback_data": f"nx_srv_{srv}", "style": "primary"}])
        kb.append([{"text": "Add New Service", "icon_custom_emoji_id": "5420323438508155202", "callback_data": "nx_add_srv", "style": "success"}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "stex_control", "style": "danger"}])
        edit_message(chat_id, msg_id, render_body_text("📦 <b>Stex Services Manager</b>\nManage your API-based dynamic services below:"), reply_markup={"inline_keyboard": kb})

    elif data == "nx_add_srv":
        user_states[chat_id] = "wait_nx_srv_name"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Enter Service Name (e.g. TELEGRAM):"), reply_markup=get_cancel_kb())

    elif data.startswith("nx_srv_"):
        srv = data.replace("nx_srv_", "")
        kb = []
        countries = bot_settings["stex_services"].get(srv, {})
        flags_db = bot_settings.get("premium_flags", {})
        for c in countries:
            emoji_id = "5780471598922337683"
            for flag_code, flag_data in flags_db.items():
                iso = flag_data.get("iso", "").upper()
                name = flag_data.get("name", "").upper()
                if c.upper() == iso or c.upper() == name or c.upper() in name or name in c.upper():
                    if "id" in flag_data: emoji_id = flag_data["id"]; break
            kb.append([{"text": f"{c} ({len(countries[c])} Ranges)", "icon_custom_emoji_id": emoji_id, "callback_data": f"nx_cnt_{srv}_{c}", "style": "primary"}])
        kb.append([{"text": "Add Country", "icon_custom_emoji_id": "5420323438508155202", "callback_data": f"nx_add_cnt_{srv}", "style": "success"}])
        kb.append([{"text": "Delete Service", "icon_custom_emoji_id": "5422557736330106570", "callback_data": f"nx_del_srv_{srv}", "style": "danger"}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "manage_stex_srv", "style": "primary"}])
        edit_message(chat_id, msg_id, render_body_text(f"📂 <b>Service: {srv}</b>\nManage countries for this service:"), reply_markup={"inline_keyboard": kb})

    elif data.startswith("nx_add_cnt_"):
        srv = data.replace("nx_add_cnt_", "")
        user_states[chat_id] = "wait_nx_cnt_name"
        temp_data[chat_id] = {"msg_id": msg_id, "srv": srv}
        edit_message(chat_id, msg_id, render_body_text(f"🌍 Enter Country Name for <b>{srv}</b> (e.g. BD, INDIA):"), reply_markup=get_cancel_kb())

    elif data.startswith("nx_cnt_"):
        parts = data.split("_")
        srv, cnt = parts[2], parts[3]
        ranges = bot_settings["stex_services"][srv].get(cnt, [])
        kb = []
        row = []
        for r in ranges:
            row.append({"text": f"Delete {r}", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"nx_dr_{srv}_{cnt}_{r}", "style": "danger"})
            if len(row) == 2: kb.append(row); row = []
        if row: kb.append(row)
        kb.append([{"text": "Add Range", "icon_custom_emoji_id": "5420323438508155202", "callback_data": f"nx_addr_{srv}_{cnt}", "style": "success"}])
        kb.append([{"text": "Delete Entire Country", "icon_custom_emoji_id": "5422557736330106570", "callback_data": f"nx_del_cnt_{srv}_{cnt}", "style": "danger"}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"nx_srv_{srv}", "style": "primary"}])
        txt = f"📍 <b>Service: {srv} | Country: {cnt}</b>\n\n<b>Total Ranges:</b> {len(ranges)}"
        edit_message(chat_id, msg_id, render_body_text(txt), reply_markup={"inline_keyboard": kb})

    elif data.startswith("nx_addr_"):
        parts = data.split("_")
        srv, cnt = parts[2], parts[3]
        user_states[chat_id] = "wait_nx_addr"
        temp_data[chat_id] = {"msg_id": msg_id, "srv": srv, "cnt": cnt}
        edit_message(chat_id, msg_id, render_body_text(f"📝 Send the new Range for <b>{cnt}</b> (e.g. 88017):"), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"nx_cnt_{srv}_{cnt}", "style": "danger"}]]})

    elif data.startswith("nx_dr_"):
        parts = data.split("_")
        srv, cnt, rng = parts[2], parts[3], parts[4]
        if rng in bot_settings["stex_services"].get(srv, {}).get(cnt, []):
            bot_settings["stex_services"][srv][cnt].remove(rng)
            save_db()
            answer_callback(call["id"], f"✅ Range {rng} deleted!", show_alert=True)
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": f"nx_cnt_{srv}_{cnt}", "id": call["id"]})

    elif data.startswith("nx_del_srv_"):
        srv = data.replace("nx_del_srv_", "")
        if srv in bot_settings["stex_services"]: del bot_settings["stex_services"][srv]
        save_db()
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "manage_stex_srv", "id": call["id"]})

    elif data.startswith("nx_del_cnt_"):
        parts = data.split("_")
        srv, cnt = parts[3], parts[4]
        if cnt in bot_settings["stex_services"].get(srv, {}): del bot_settings["stex_services"][srv][cnt]
        save_db()
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": f"nx_srv_{srv}", "id": call["id"]})

    # ==========================================
    # Voltx Control Callbacks
    # ==========================================
    elif data == "voltx_control":
        edit_message(chat_id, msg_id, render_body_text(f"⚡ <b>Voltx Control Panel</b>\n\nTotal API Keys: {len(bot_settings.get('voltx_keys', []))}\nManage your Voltx API Keys below:"), reply_markup=voltx_control_keyboard())

    elif data == "add_voltx_key":
        user_states[chat_id] = "wait_for_add_voltx_key"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the new Voltx API Key:"), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "voltx_control", "style": "danger"}]]})

    elif data == "view_voltx_keys":
        kb = []
        for idx, key in enumerate(bot_settings.get("voltx_keys", [])):
            safe_name = key[:10] + "..." if len(key) > 10 else key
            kb.append([{"text": f"Delete {safe_name}", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"del_vtx_{idx}", "style": "danger"}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "voltx_control", "style": "primary"}])
        edit_message(chat_id, msg_id, render_body_text("🗑 <b>Select Voltx Key to Delete:</b>"), reply_markup={"inline_keyboard": kb})

    elif data.startswith("del_vtx_"):
        idx = int(data.split("_")[2])
        if 0 <= idx < len(bot_settings.get("voltx_keys", [])):
            del bot_settings["voltx_keys"][idx]
            save_db()
            answer_callback(call["id"], "✅ Voltx Key Deleted!", show_alert=True)
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "view_voltx_keys", "id": call["id"]})

    elif data == "voltx_search_country":
        kb = []
        for idx, c in enumerate(bot_settings.get("voltx_stex_search_countries", [])):
            kb.append([{"text": f"Delete {c}", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"del_vsc_{idx}", "style": "danger"}])
        kb.append([{"text": "Add Country Code", "icon_custom_emoji_id": "5420323438508155202", "callback_data": "add_voltx_search_country", "style": "success"}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "voltx_control", "style": "primary"}])
        edit_message(chat_id, msg_id, render_body_text("🌍 <b>Voltx Allowed Ranges:</b>\nOnly these ranges/codes will be allowed in Voltx Search Number."), reply_markup={"inline_keyboard": kb})

    elif data == "add_voltx_search_country":
        user_states[chat_id] = "wait_for_add_vsc"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the Voltx Range Code (e.g. 26134):"), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "voltx_search_country", "style": "danger"}]]})

    elif data.startswith("del_vsc_"):
        idx = int(data.split("_")[2])
        if 0 <= idx < len(bot_settings.get("voltx_stex_search_countries", [])):
            del bot_settings["voltx_stex_search_countries"][idx]
            save_db()
            answer_callback(call["id"], "✅ Voltx Range Deleted!", show_alert=True)
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "voltx_search_country", "id": call["id"]})

    elif data == "manage_voltx_srv":
        kb = []
        srvs = bot_settings.get("voltx_services", {})
        apps_db = bot_settings.get("premium_apps", {})
        for srv in srvs:
            emoji_id = "5257969839313526622"
            for app_key, app_data in apps_db.items():
                if srv.upper() == app_key or srv.upper() in app_key or app_key in srv.upper():
                    if "id" in app_data: emoji_id = app_data["id"]; break
            kb.append([{"text": f"{srv}", "icon_custom_emoji_id": emoji_id, "callback_data": f"vx_srv_{srv}", "style": "primary"}])
        kb.append([{"text": "Add New Service", "icon_custom_emoji_id": "5420323438508155202", "callback_data": "vx_add_srv", "style": "success"}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "voltx_control", "style": "danger"}])
        edit_message(chat_id, msg_id, render_body_text("⚡ <b>Voltx Services Manager</b>\nManage your API-based dynamic services below:"), reply_markup={"inline_keyboard": kb})

    elif data == "vx_add_srv":
        user_states[chat_id] = "wait_vx_srv_name"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Enter Service Name (e.g. TELEGRAM):"), reply_markup=get_cancel_kb())

    elif data.startswith("vx_srv_"):
        srv = data.replace("vx_srv_", "")
        kb = []
        countries = bot_settings["voltx_services"].get(srv, {})
        flags_db = bot_settings.get("premium_flags", {})
        for c in countries:
            emoji_id = "5780471598922337683"
            for flag_code, flag_data in flags_db.items():
                iso = flag_data.get("iso", "").upper()
                name = flag_data.get("name", "").upper()
                if c.upper() == iso or c.upper() == name or c.upper() in name or name in c.upper():
                    if "id" in flag_data: emoji_id = flag_data["id"]; break
            kb.append([{"text": f"{c} ({len(countries[c])} Ranges)", "icon_custom_emoji_id": emoji_id, "callback_data": f"vx_cnt_{srv}_{c}", "style": "primary"}])
        kb.append([{"text": "Add Country", "icon_custom_emoji_id": "5420323438508155202", "callback_data": f"vx_add_cnt_{srv}", "style": "success"}])
        kb.append([{"text": "Delete Service", "icon_custom_emoji_id": "5422557736330106570", "callback_data": f"vx_del_srv_{srv}", "style": "danger"}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "manage_voltx_srv", "style": "primary"}])
        edit_message(chat_id, msg_id, render_body_text(f"📂 <b>Service: {srv}</b>\nManage countries for this service:"), reply_markup={"inline_keyboard": kb})

    elif data.startswith("vx_add_cnt_"):
        srv = data.replace("vx_add_cnt_", "")
        user_states[chat_id] = "wait_vx_cnt_name"
        temp_data[chat_id] = {"msg_id": msg_id, "srv": srv}
        edit_message(chat_id, msg_id, render_body_text(f"🌍 Enter Country Name for <b>{srv}</b> (e.g. BD, INDIA):"), reply_markup=get_cancel_kb())

    elif data.startswith("vx_cnt_"):
        parts = data.split("_")
        srv, cnt = parts[2], parts[3]
        ranges = bot_settings["voltx_services"][srv].get(cnt, [])
        kb = []
        row = []
        for r in ranges:
            row.append({"text": f"Delete {r}", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"vx_dr_{srv}_{cnt}_{r}", "style": "danger"})
            if len(row) == 2: kb.append(row); row = []
        if row: kb.append(row)
        kb.append([{"text": "Add Range", "icon_custom_emoji_id": "5420323438508155202", "callback_data": f"vx_addr_{srv}_{cnt}", "style": "success"}])
        kb.append([{"text": "Delete Entire Country", "icon_custom_emoji_id": "5422557736330106570", "callback_data": f"vx_del_cnt_{srv}_{cnt}", "style": "danger"}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"vx_srv_{srv}", "style": "primary"}])
        txt = f"📍 <b>Service: {srv} | Country: {cnt}</b>\n\n<b>Total Ranges:</b> {len(ranges)}"
        edit_message(chat_id, msg_id, render_body_text(txt), reply_markup={"inline_keyboard": kb})

    elif data.startswith("vx_addr_"):
        parts = data.split("_")
        srv, cnt = parts[2], parts[3]
        user_states[chat_id] = "wait_vx_addr"
        temp_data[chat_id] = {"msg_id": msg_id, "srv": srv, "cnt": cnt}
        edit_message(chat_id, msg_id, render_body_text(f"📝 Send the new Range for <b>{cnt}</b> (e.g. 26134):"), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"vx_cnt_{srv}_{cnt}", "style": "danger"}]]})

    elif data.startswith("vx_dr_"):
        parts = data.split("_")
        srv, cnt, rng = parts[2], parts[3], parts[4]
        if rng in bot_settings["voltx_services"].get(srv, {}).get(cnt, []):
            bot_settings["voltx_services"][srv][cnt].remove(rng)
            save_db()
            answer_callback(call["id"], f"✅ Range {rng} deleted!", show_alert=True)
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": f"vx_cnt_{srv}_{cnt}", "id": call["id"]})

    elif data.startswith("vx_del_srv_"):
        srv = data.replace("vx_del_srv_", "")
        if srv in bot_settings["voltx_services"]: del bot_settings["voltx_services"][srv]
        save_db()
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "manage_voltx_srv", "id": call["id"]})

    elif data.startswith("vx_del_cnt_"):
        parts = data.split("_")
        srv, cnt = parts[3], parts[4]
        if cnt in bot_settings["voltx_services"].get(srv, {}): del bot_settings["voltx_services"][srv][cnt]
        save_db()
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": f"vx_srv_{srv}", "id": call["id"]})

    # ==========================================
    # Zenex Control Callbacks
    # ==========================================
    # ==========================================
    # 🦈 Shark Panel Callbacks
    # ==========================================
    elif data == "shark_control":
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        token_count = len(bot_settings.get("shark_tokens", []))
        status_txt = "🟢 RUNNING" if bot_settings.get("shark_panel_on") else "🔴 STOPPED"
        edit_message(chat_id, msg_id, render_body_text(
            f"🦈 <b>Shark Panel Direct API</b>\n\n"
            f"📡 <b>Status:</b> {status_txt}\n"
            f"🔑 <b>Tokens:</b> {token_count}\n"
            f"🌐 <b>API:</b> <code>{SHARK_API_URL}</code>\n\n"
            f"Shark Panel API দিয়ে সরাসরি OTP নেওয়া হবে।\n"
            f"Auto login/logout নেই — ২৪/৭ stable!"
        ), reply_markup=shark_control_keyboard())

    elif data == "tog_panel_alert":
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        bot_settings["panel_alert_on"] = not bot_settings.get("panel_alert_on", True)
        save_db()
        state_str = "🟢 চালু" if bot_settings["panel_alert_on"] else "🔴 বন্ধ"
        answer_callback(call["id"], f"Panel Alert {state_str} হয়েছে!", show_alert=True)
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "system_settings", "id": "internal"})

    elif data == "tog_user_otp_notify":
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        bot_settings["user_otp_notify"] = not bot_settings.get("user_otp_notify", True)
        save_db()
        state_str = "🟢 চালু" if bot_settings["user_otp_notify"] else "🔴 বন্ধ"
        answer_callback(call["id"], f"User OTP Notify {state_str} হয়েছে!", show_alert=True)
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "system_settings", "id": "internal"})

    elif data == "tog_no_match_alert":
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        bot_settings["no_match_alert_on"] = not bot_settings.get("no_match_alert_on", True)
        save_db()
        state_str = "🟢 চালু" if bot_settings["no_match_alert_on"] else "🔴 বন্ধ"
        answer_callback(call["id"], f"No-Match Alert {state_str} হয়েছে!", show_alert=True)
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "system_settings", "id": "internal"})

    elif data == "shark_toggle":
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        bot_settings["shark_panel_on"] = not bot_settings.get("shark_panel_on", False)
        save_db()
        state_str = "🟢 চালু" if bot_settings["shark_panel_on"] else "🔴 বন্ধ"
        answer_callback(call["id"], f"Shark Panel {state_str} হয়েছে!", show_alert=True)
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "shark_control", "id": "internal"})

    elif data == "shark_add_token":
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        user_states[chat_id] = "wait_for_add_shark_token"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text(
            "🔑 <b>Shark Panel Token</b>\n\n"
            "📝 Admin panel থেকে পাওয়া token পাঠান:\n\n"
            "Example: <code>hWxQRWhjhmtZiHKAe5NSemBzkFppU3lkd1eJV2JWk3w</code>"
        ), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "shark_control", "style": "danger"}]]})

    elif data == "shark_view_tokens":
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        kb = []
        tokens = bot_settings.get("shark_tokens", [])
        if not tokens:
            kb.append([{"text": "কোনো Token নেই", "callback_data": "ignore", "style": "primary"}])
        for idx, token in enumerate(tokens):
            masked = token[:6] + "..." + token[-4:] if len(token) > 12 else token
            kb.append([{"text": f"🗑 Delete {masked}", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"del_shark_{idx}", "style": "danger"}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "shark_control", "style": "primary"}])
        edit_message(chat_id, msg_id, render_body_text(f"🦈 <b>Shark Tokens ({len(tokens)}):</b>\nDelete করতে চাইলে বাটনে চাপুন:"), reply_markup={"inline_keyboard": kb})

    elif data.startswith("del_shark_"):
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        try:
            idx = int(data[len("del_shark_"):])
        except ValueError:
            answer_callback(call["id"], "❌ Invalid index!", show_alert=True); return
        tokens = bot_settings.get("shark_tokens", [])
        if 0 <= idx < len(tokens):
            del tokens[idx]
            save_db()
            answer_callback(call["id"], "✅ Token Deleted!", show_alert=True)
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "shark_view_tokens", "id": "internal"})

    elif data == "shark_live_test":
        # ── Shark Panel Live API Test — admin panel থেকে সরাসরি API call ──
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        answer_callback(call["id"], "⌛ API চেক হচ্ছে...", show_alert=False)
        tokens = bot_settings.get("shark_tokens", [])
        if not tokens:
            edit_message(chat_id, msg_id, render_body_text("❌ কোনো token নেই! প্রথমে token যোগ করুন।"), reply_markup=shark_control_keyboard())
            return
        results = []
        for token in tokens[:2]:  # সর্বোচ্চ ২টা token test করি
            try:
                params = {"token": token, "records": 10}
                headers = {"User-Agent": "Mozilla/5.0"}
                res = requests.get(SHARK_API_URL, params=params, headers=headers, timeout=12)
                masked_token = token[:6] + "..." + token[-4:]

                if res.status_code != 200:
                    results.append(f"🔴 Token <code>{masked_token}</code>: HTTP {res.status_code} error")
                    continue

                raw = res.text.strip() if res.text else ""
                if not raw:
                    results.append(f"🔴 Token <code>{masked_token}</code>: API <b>empty response</b> দিয়েছে (server busy বা token invalid)")
                    continue

                # Rate limit detection
                if "too many times" in raw or "Try again" in raw:
                    results.append(f"⚠️ Token <code>{masked_token}</code>: <b>Rate Limited!</b>\n       Server বলছে: <i>{raw[:120]}</i>\n       👉 ৩০-৬০ সেকেন্ড পর আবার চেষ্টা করুন। Bot polling বন্ধ করুন বা interval বাড়ান।")
                    continue

                try:
                    data_resp = res.json()
                except Exception as je:
                    results.append(f"🔴 Token <code>{masked_token}</code>: JSON parse error\n       Raw: <code>{raw[:120]}</code>")
                    continue

                if data_resp.get("status") != "success":
                    results.append(f"🔴 Token <code>{masked_token}</code>: <b>API Error</b> — {data_resp.get('msg', data_resp.get('status','?'))}")
                    continue
                items = data_resp.get("data", [])
                if not items:
                    results.append(f"🟡 Token <code>{masked_token}</code>: সংযোগ OK কিন্তু <b>0 record</b> পাওয়া গেছে (কোনো SMS নেই বা filternum মেলেনি)")
                    continue
                results.append(f"🟢 Token <code>{masked_token}</code>: <b>{len(items)} records</b> পাওয়া গেছে")
                for i, item in enumerate(items[:5]):
                    num = str(item.get("num","")).strip()
                    msg_txt = str(item.get("message",""))[:60]
                    dt = item.get("dt","")
                    otp_found = extract_otp_code(msg_txt)
                    # এই number কি batch_assigned_numbers বা user_active_sessions-এ আছে?
                    clean_n = num.replace("+","").replace(" ","").replace("-","").strip()
                    matched_uid = batch_assigned_numbers.get(clean_n)
                    if not matched_uid:
                        for uid, sess in user_active_sessions.items():
                            for sn in sess.get("nums", []):
                                sc = str(sn).replace("+","").replace(" ","").replace("-","").strip()
                                if sc == clean_n or (len(sc)>=8 and sc.endswith(clean_n[-8:])) or (len(clean_n)>=8 and clean_n.endswith(sc[-8:])):
                                    matched_uid = uid; break
                            if matched_uid: break
                    match_txt = f"✅ User {matched_uid} match" if matched_uid else "❌ কোনো user match নেই"
                    otp_txt = f"OTP: <b>{otp_found}</b>" if otp_found else "OTP: <i>extract হয়নি</i>"
                    results.append(f"  #{i+1} num=<code>{num}</code> | {otp_txt} | {match_txt}\n       msg: <i>{msg_txt}</i>")
            except Exception as e:
                results.append(f"🔴 Token poll error: {e}")
        # batch_assigned_numbers summary
        batch_count = len(batch_assigned_numbers)
        sess_count = len(user_active_sessions)
        summary = f"\n\n📊 <b>Matching DB:</b>\nbatch_assigned: {batch_count} numbers | active_sessions: {sess_count} users"
        final_txt = render_body_text(
            "🔍 <b>Shark Panel Live Test</b>\n\n" + "\n".join(results) + summary
        )
        edit_message(chat_id, msg_id, final_txt, reply_markup={"inline_keyboard": [[{"text": "🔄 আবার Test করুন", "callback_data": "shark_live_test", "style": "primary"}, {"text": "Back", "callback_data": "shark_control", "style": "danger"}]]})

    # ══════════════════════════════════════════
    # CR Panel Callbacks
    # ══════════════════════════════════════════
    elif data == "cr_control":
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        token_count = len(bot_settings.get("cr_tokens", []))
        status_txt = "🟢 RUNNING" if bot_settings.get("cr_panel_on") else "🔴 STOPPED"
        edit_message(chat_id, msg_id, render_body_text(
            f"🌐 <b>CR Panel Direct API</b>\n\n"
            f"📡 <b>Status:</b> {status_txt}\n"
            f"🔑 <b>Tokens:</b> {token_count}\n"
            f"🌐 <b>API:</b> <code>{CR_API_URL}</code>\n\n"
            f"CR Panel API দিয়ে সরাসরি OTP নেওয়া হবে।\n"
            f"Auto login/logout নেই — ২৪/৭ stable!"
        ), reply_markup=cr_control_keyboard())

    elif data == "cr_toggle":
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        bot_settings["cr_panel_on"] = not bot_settings.get("cr_panel_on", False)
        save_db()
        state_str = "🟢 চালু" if bot_settings["cr_panel_on"] else "🔴 বন্ধ"
        answer_callback(call["id"], f"CR Panel {state_str} হয়েছে!", show_alert=True)
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "cr_control", "id": "internal"})

    elif data == "cr_add_token":
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        user_states[chat_id] = "wait_for_add_cr_token"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text(
            "🔑 <b>CR Panel Token</b>\n\n"
            "📝 Admin panel থেকে পাওয়া token পাঠান:\n\n"
            "Example: <code>QlBPREhBUzRrZnFDg194i2JTaUh2...</code>"
        ), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "cr_control", "style": "danger"}]]})

    elif data == "cr_view_tokens":
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        kb = []
        tokens = bot_settings.get("cr_tokens", [])
        if not tokens:
            kb.append([{"text": "কোনো Token নেই", "callback_data": "ignore", "style": "primary"}])
        for idx, token in enumerate(tokens):
            masked = token[:6] + "..." + token[-4:] if len(token) > 12 else token
            kb.append([{"text": f"🗑 Delete {masked}", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"del_cr_{idx}", "style": "danger"}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "cr_control", "style": "primary"}])
        edit_message(chat_id, msg_id, render_body_text(f"🌐 <b>CR Tokens ({len(tokens)}):</b>\nDelete করতে চাইলে বাটনে চাপুন:"), reply_markup={"inline_keyboard": kb})

    elif data.startswith("del_cr_"):
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        try:
            idx = int(data[len("del_cr_"):])
        except ValueError:
            answer_callback(call["id"], "❌ Invalid index!", show_alert=True); return
        tokens = bot_settings.get("cr_tokens", [])
        if 0 <= idx < len(tokens):
            del tokens[idx]
            save_db()
            answer_callback(call["id"], "✅ Token Deleted!", show_alert=True)
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "cr_view_tokens", "id": "internal"})

    elif data == "cr_live_test":
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        answer_callback(call["id"], "⌛ API চেক হচ্ছে...", show_alert=False)
        tokens = bot_settings.get("cr_tokens", [])
        if not tokens:
            edit_message(chat_id, msg_id, render_body_text("❌ কোনো token নেই! প্রথমে token যোগ করুন।"), reply_markup=cr_control_keyboard())
            return
        results = []
        for token in tokens[:2]:
            try:
                params = {"token": token, "records": 10}
                headers = {"User-Agent": "Mozilla/5.0"}
                res = requests.get(CR_API_URL, params=params, headers=headers, timeout=12)
                masked_token = token[:6] + "..." + token[-4:]
                if res.status_code != 200:
                    results.append(f"🔴 Token <code>{masked_token}</code>: HTTP {res.status_code} error")
                    continue
                raw = res.text.strip() if res.text else ""
                if not raw:
                    results.append(f"🔴 Token <code>{masked_token}</code>: empty response (server busy বা token invalid)")
                    continue
                if "too many times" in raw or "Try again" in raw:
                    results.append(f"⚠️ Token <code>{masked_token}</code>: <b>Rate Limited!</b> ৩০-৬০ সেকেন্ড পর চেষ্টা করুন।")
                    continue
                try:
                    data_resp = res.json()
                except Exception:
                    results.append(f"🔴 Token <code>{masked_token}</code>: JSON parse error — Raw: <code>{raw[:120]}</code>")
                    continue
                if data_resp.get("status") != "success":
                    results.append(f"🔴 Token <code>{masked_token}</code>: API Error — {data_resp.get('msg', '?')}")
                    continue
                items = data_resp.get("data", [])
                if not items:
                    results.append(f"🟡 Token <code>{masked_token}</code>: সংযোগ OK কিন্তু 0 record (কোনো SMS নেই)")
                    continue
                results.append(f"🟢 Token <code>{masked_token}</code>: <b>{len(items)} records</b> পাওয়া গেছে")
                for i, item in enumerate(items[:5]):
                    num = str(item.get("num", "")).strip()
                    msg_txt = str(item.get("message", ""))[:60]
                    otp_found = extract_otp_code(msg_txt)
                    otp_txt = f"OTP: <b>{otp_found}</b>" if otp_found else "OTP: <i>extract হয়নি</i>"
                    results.append(f"  #{i+1} num=<code>{num}</code> | {otp_txt}\n       msg: <i>{msg_txt}</i>")
            except Exception as e:
                results.append(f"🔴 Token poll error: {e}")
        batch_count = len(batch_assigned_numbers)
        sess_count = len(user_active_sessions)
        summary = f"\n\n📊 <b>Matching DB:</b>\nbatch_assigned: {batch_count} | active_sessions: {sess_count}"
        final_txt = render_body_text("🔍 <b>CR Panel Live Test</b>\n\n" + "\n".join(results) + summary)
        edit_message(chat_id, msg_id, final_txt, reply_markup={"inline_keyboard": [[
            {"text": "🔄 আবার Test করুন", "callback_data": "cr_live_test", "style": "primary"},
            {"text": "Back", "callback_data": "cr_control", "style": "danger"}
        ]]})

    # ══════════════════════════════════════════
    # ⚡ Flex Panel Callbacks (Dynamic URL)
    # ══════════════════════════════════════════
    elif data == "flex_control":
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        token_count = len(bot_settings.get("flex_tokens", []))
        status_txt = "🟢 RUNNING" if bot_settings.get("flex_panel_on") else "🔴 STOPPED"
        current_url = bot_settings.get("flex_api_url", "") or "❌ Not Set Yet"
        edit_message(chat_id, msg_id, render_body_text(
            f"⚡ <b>Flex Panel (Dynamic URL)</b>\n\n"
            f"📡 <b>Status:</b> {status_txt}\n"
            f"🔑 <b>Tokens:</b> {token_count}\n"
            f"🔗 <b>API URL:</b> <code>{current_url}</code>\n\n"
            f"নিজে URL set করো — Shark/CR এর মতোই কাজ করবে!\n"
            f"Example: <code>http://168.119.13.175/crapi/xxx/viewstats</code>"
        ), reply_markup=flex_control_keyboard())

    elif data == "flex_toggle":
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        if not bot_settings.get("flex_api_url", ""):
            answer_callback(call["id"], "❌ আগে API URL set করো!", show_alert=True); return
        bot_settings["flex_panel_on"] = not bot_settings.get("flex_panel_on", False)
        save_db()
        state_str = "🟢 চালু" if bot_settings["flex_panel_on"] else "🔴 বন্ধ"
        answer_callback(call["id"], f"⚡ Flex Panel {state_str} হয়েছে!", show_alert=True)
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "flex_control", "id": "internal"})

    elif data == "flex_set_url":
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        user_states[chat_id] = "wait_for_set_flex_url"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text(
            "🔗 <b>Flex Panel API URL Set করো</b>\n\n"
            "পুরো URL পাঠাও:\n"
            "Example: <code>http://168.119.13.175/crapi/xxx/viewstats</code>\n\n"
            "⚠️ URL সঠিক না হলে OTP আসবে না!"
        ), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "flex_control", "style": "danger"}]]})

    elif data == "flex_add_token":
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        user_states[chat_id] = "wait_for_add_flex_token"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text(
            "🔑 <b>Flex Panel Token</b>\n\n"
            "API Token পাঠাও:\n"
            "Example: <code>RFBQSElBUz...</code>"
        ), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "flex_control", "style": "danger"}]]})

    elif data == "flex_view_tokens":
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        tokens = bot_settings.get("flex_tokens", [])
        if not tokens:
            edit_message(chat_id, msg_id, render_body_text("❌ কোনো token নেই!"), reply_markup=flex_control_keyboard()); return
        kb = []
        for idx, tok in enumerate(tokens):
            masked = tok[:6] + "..." + tok[-4:] if len(tok) > 10 else tok
            kb.append([{"text": f"🗑 Delete {masked}", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"del_flex_{idx}", "style": "danger"}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "flex_control", "style": "primary"}])
        edit_message(chat_id, msg_id, render_body_text(f"🔑 Flex Panel Tokens ({len(tokens)} টি):"), reply_markup={"inline_keyboard": kb})

    elif data.startswith("del_flex_"):
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        try:
            idx = int(data[len("del_flex_"):])
        except:
            return
        tokens = bot_settings.get("flex_tokens", [])
        if 0 <= idx < len(tokens):
            removed = tokens.pop(idx)
            bot_settings["flex_tokens"] = tokens
            save_db()
            answer_callback(call["id"], f"✅ Token deleted!", show_alert=True)
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "flex_view_tokens", "id": "internal"})

    # ══════════════════════════════════════════
    # 🔷 Nexus-X Panel Callbacks (REST Bearer API)
    # ══════════════════════════════════════════
    elif data == "nexus_control":
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        key_count = len(bot_settings.get("nexus_keys", []))
        status_txt = "🟢 RUNNING" if bot_settings.get("nexus_panel_on") else "🔴 STOPPED"
        edit_message(chat_id, msg_id, render_body_text(
            f"🔷 <b>Nexus-X Panel</b>\n\n"
            f"📡 <b>Status:</b> {status_txt}\n"
            f"🔑 <b>API Keys:</b> {key_count}\n\n"
            f"Nexus-X REST API দিয়ে OTP collect করে।\n"
            f"Example Key: <code>nx_AgYVC5ts1jvegsPRowe4Nu0MajvuC3DPw...</code>"
        ), reply_markup=nexus_control_keyboard())

    elif data == "nexus_toggle":
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        if not bot_settings.get("nexus_keys", []):
            answer_callback(call["id"], "❌ আগে API Key যোগ করো!", show_alert=True); return
        bot_settings["nexus_panel_on"] = not bot_settings.get("nexus_panel_on", False)
        save_db()
        state_str = "🟢 চালু" if bot_settings["nexus_panel_on"] else "🔴 বন্ধ"
        answer_callback(call["id"], f"🔷 Nexus-X Panel {state_str} হয়েছে!", show_alert=True)
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "nexus_control", "id": "internal"})

    elif data == "nexus_add_key":
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        user_states[chat_id] = "wait_for_add_nexus_key"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text(
            "🔑 <b>Nexus-X API Key</b>\n\n"
            "📝 Nexus-X panel থেকে পাওয়া API key পাঠান:\n\n"
            "Example: <code>nx_AgYVC5ts1jvegsPRowe4Nu0MajvuC3DPwZmttQ</code>"
        ), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "nexus_control", "style": "danger"}]]})

    elif data == "nexus_view_keys":
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        keys = bot_settings.get("nexus_keys", [])
        kb = []
        if not keys:
            kb.append([{"text": "কোনো Key নেই", "callback_data": "ignore", "style": "primary"}])
        for idx, key in enumerate(keys):
            masked = key[:8] + "..." + key[-4:] if len(key) > 14 else key
            kb.append([{"text": f"🗑 Delete {masked}", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"del_nexus_{idx}", "style": "danger"}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "nexus_control", "style": "primary"}])
        edit_message(chat_id, msg_id, render_body_text(f"🔷 <b>Nexus-X API Keys ({len(keys)}):</b>\nDelete করতে চাইলে বাটনে চাপুন:"), reply_markup={"inline_keyboard": kb})

    elif data.startswith("del_nexus_"):
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        try:
            idx = int(data[len("del_nexus_"):])
        except ValueError:
            answer_callback(call["id"], "❌ Invalid index!", show_alert=True); return
        keys = bot_settings.get("nexus_keys", [])
        if 0 <= idx < len(keys):
            del keys[idx]
            save_db()
            answer_callback(call["id"], "✅ Key Deleted!", show_alert=True)
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "nexus_view_keys", "id": "internal"})

    elif data == "nexus_live_test":
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        answer_callback(call["id"], "⌛ Nexus-X API চেক হচ্ছে...", show_alert=False)
        keys = bot_settings.get("nexus_keys", [])
        if not keys:
            edit_message(chat_id, msg_id, render_body_text("❌ কোনো API Key নেই! প্রথমে key যোগ করুন।"), reply_markup=nexus_control_keyboard())
            return
        results = []
        for api_key in keys[:2]:
            masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 14 else api_key
            try:
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                res = requests.get("https://v2.nexus-x.site/api/v1/inbox", headers=headers, timeout=12)
                if res.status_code == 401:
                    results.append(f"🔴 Key <code>{masked}</code>: <b>Unauthorized</b> — Key টি invalid বা expire হয়েছে")
                    continue
                if res.status_code != 200:
                    results.append(f"🔴 Key <code>{masked}</code>: HTTP {res.status_code} error")
                    continue
                try:
                    data_resp = res.json()
                except Exception:
                    results.append(f"🔴 Key <code>{masked}</code>: JSON parse error — Raw: <code>{res.text[:120]}</code>")
                    continue
                items = data_resp if isinstance(data_resp, list) else data_resp.get("data", data_resp.get("items", []))
                if not items:
                    results.append(f"🟡 Key <code>{masked}</code>: সংযোগ OK কিন্তু inbox খালি (কোনো SMS নেই)")
                    continue
                results.append(f"🟢 Key <code>{masked}</code>: <b>{len(items)} records</b> পাওয়া গেছে")
                for i, item in enumerate(items[:3]):
                    num = str(item.get("number", item.get("full_number", ""))).strip()
                    otp_txt = str(item.get("body", item.get("text", item.get("console", ""))))[:60]
                    service = item.get("service", item.get("access", item.get("sid", "?")))
                    results.append(f"  #{i+1} num=<code>{num}</code> | svc={service}\n       msg: <i>{otp_txt}</i>")
            except Exception as e:
                results.append(f"🔴 Key <code>{masked}</code> error: {e}")
        final_txt = render_body_text("🔍 <b>Nexus-X Panel Live Test</b>\n\n" + "\n".join(results))
        edit_message(chat_id, msg_id, final_txt, reply_markup={"inline_keyboard": [[
            {"text": "🔄 আবার Test করুন", "callback_data": "nexus_live_test", "style": "primary"},
            {"text": "Back", "callback_data": "nexus_control", "style": "danger"}
        ]]})

    # ══════════════════════════════════════════
    # 🔷 Nexus-X Services Manager Callbacks
    # ══════════════════════════════════════════
    elif data == "manage_nexus_srv":
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        kb = []
        srvs = bot_settings.get("nexus_services", {})
        apps_db = bot_settings.get("premium_apps", {})
        for srv in srvs:
            emoji_id = "5257969839313526622"
            for app_key, app_data in apps_db.items():
                if srv.upper() == app_key or srv.upper() in app_key or app_key in srv.upper():
                    if "id" in app_data: emoji_id = app_data["id"]; break
            kb.append([{"text": f"{srv}", "icon_custom_emoji_id": emoji_id, "callback_data": f"nxs_srv_{srv}", "style": "primary"}])
        kb.append([{"text": "Add New Service", "icon_custom_emoji_id": "5420323438508155202", "callback_data": "nxs_add_srv", "style": "success"}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "nexus_control", "style": "danger"}])
        edit_message(chat_id, msg_id, render_body_text("🔷 <b>Nexus Services Manager</b>\nManage your Nexus API-based services below:"), reply_markup={"inline_keyboard": kb})

    elif data == "nxs_add_srv":
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        user_states[chat_id] = "wait_nxs_srv_name"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Enter Service Name (e.g. TELEGRAM):"), reply_markup=get_cancel_kb())

    elif data.startswith("nxs_srv_"):
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        srv = data.replace("nxs_srv_", "")
        kb = []
        countries = bot_settings.get("nexus_services", {}).get(srv, {})
        flags_db = bot_settings.get("premium_flags", {})
        for c in countries:
            emoji_id = "5780471598922337683"
            for flag_code, flag_data in flags_db.items():
                iso = flag_data.get("iso", "").upper()
                name = flag_data.get("name", "").upper()
                if c.upper() == iso or c.upper() == name or c.upper() in name or name in c.upper():
                    if "id" in flag_data: emoji_id = flag_data["id"]; break
            kb.append([{"text": f"{c} ({len(countries[c])} Ranges)", "icon_custom_emoji_id": emoji_id, "callback_data": f"nxs_cnt_{srv}_{c}", "style": "primary"}])
        kb.append([{"text": "Add Country", "icon_custom_emoji_id": "5420323438508155202", "callback_data": f"nxs_add_cnt_{srv}", "style": "success"}])
        kb.append([{"text": "Delete Service", "icon_custom_emoji_id": "5422557736330106570", "callback_data": f"nxs_del_srv_{srv}", "style": "danger"}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "manage_nexus_srv", "style": "primary"}])
        edit_message(chat_id, msg_id, render_body_text(f"📂 <b>Nexus Service: {srv}</b>\nManage countries for this service:"), reply_markup={"inline_keyboard": kb})

    elif data.startswith("nxs_add_cnt_"):
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        srv = data.replace("nxs_add_cnt_", "")
        user_states[chat_id] = "wait_nxs_cnt_name"
        temp_data[chat_id] = {"msg_id": msg_id, "srv": srv}
        edit_message(chat_id, msg_id, render_body_text(f"🌍 Enter Country Name for <b>{srv}</b> (e.g. BD, INDIA):"), reply_markup=get_cancel_kb())

    elif data.startswith("nxs_del_srv_"):
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        srv = data.replace("nxs_del_srv_", "")
        if srv in bot_settings.get("nexus_services", {}): del bot_settings["nexus_services"][srv]
        save_db()
        answer_callback(call["id"], f"✅ Service {srv} deleted!", show_alert=True)
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "manage_nexus_srv", "id": "internal"})

    elif data.startswith("nxs_cnt_"):
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        parts = data.split("_")
        srv, cnt = parts[2], parts[3]
        ranges = bot_settings.get("nexus_services", {}).get(srv, {}).get(cnt, [])
        kb = []
        row = []
        for r in ranges:
            row.append({"text": f"Delete {r}", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"nxs_dr_{srv}_{cnt}_{r}", "style": "danger"})
            if len(row) == 2: kb.append(row); row = []
        if row: kb.append(row)
        kb.append([{"text": "Add Range", "icon_custom_emoji_id": "5420323438508155202", "callback_data": f"nxs_addr_{srv}_{cnt}", "style": "success"}])
        kb.append([{"text": "Delete Entire Country", "icon_custom_emoji_id": "5422557736330106570", "callback_data": f"nxs_del_cnt_{srv}_{cnt}", "style": "danger"}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"nxs_srv_{srv}", "style": "primary"}])
        txt = f"📍 <b>Nexus Service: {srv} | Country: {cnt}</b>\n\n<b>Total Ranges:</b> {len(ranges)}\n<i>Click on a range to delete it, or add a new one.</i>"
        edit_message(chat_id, msg_id, render_body_text(txt), reply_markup={"inline_keyboard": kb})

    elif data.startswith("nxs_addr_"):
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        parts = data.split("_")
        srv, cnt = parts[2], parts[3]
        user_states[chat_id] = "wait_nxs_addr"
        temp_data[chat_id] = {"msg_id": msg_id, "srv": srv, "cnt": cnt}
        edit_message(chat_id, msg_id, render_body_text(f"📝 Send the new Range for <b>{cnt}</b> (e.g. 88017):"), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"nxs_cnt_{srv}_{cnt}", "style": "danger"}]]})

    elif data.startswith("nxs_dr_"):
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        parts = data.split("_")
        srv, cnt, rng = parts[2], parts[3], parts[4]
        if rng in bot_settings.get("nexus_services", {}).get(srv, {}).get(cnt, []):
            bot_settings["nexus_services"][srv][cnt].remove(rng)
            save_db()
            answer_callback(call["id"], f"✅ Range {rng} deleted!", show_alert=True)
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": f"nxs_cnt_{srv}_{cnt}", "id": "internal"})

    elif data.startswith("nxs_del_cnt_"):
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        parts = data.split("_")
        srv, cnt = parts[3], parts[4]
        if cnt in bot_settings.get("nexus_services", {}).get(srv, {}): del bot_settings["nexus_services"][srv][cnt]
        save_db()
        answer_callback(call["id"], f"✅ Country {cnt} deleted!", show_alert=True)
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": f"nxs_srv_{srv}", "id": "internal"})

    elif data == "flex_live_test":
        if not is_admin(chat_id):
            answer_callback(call["id"], "❌ Admin only!", show_alert=True); return
        flex_url = bot_settings.get("flex_api_url", "")
        tokens = bot_settings.get("flex_tokens", [])
        if not flex_url:
            edit_message(chat_id, msg_id, render_body_text("❌ API URL set নেই! আগে URL set করো।"), reply_markup=flex_control_keyboard()); return
        if not tokens:
            edit_message(chat_id, msg_id, render_body_text("❌ কোনো token নেই! প্রথমে token যোগ করুন।"), reply_markup=flex_control_keyboard()); return
        results = []
        for token in tokens[:3]:
            masked_token = token[:6] + "..." + token[-4:] if len(token) > 10 else token
            try:
                params = {"token": token, "records": 5}
                headers = {"User-Agent": "Mozilla/5.0"}
                res = requests.get(flex_url, params=params, headers=headers, timeout=12)
                if res.status_code != 200:
                    results.append(f"🔴 Token <code>{masked_token}</code>: HTTP {res.status_code}")
                    continue
                raw_text = res.text.strip()
                if not raw_text:
                    results.append(f"🟡 Token <code>{masked_token}</code>: Empty response")
                    continue
                try:
                    data_resp = res.json()
                    if data_resp.get("status") == "error":
                        results.append(f"🔴 Token <code>{masked_token}</code>: {data_resp.get('message', 'API Error')}")
                        continue
                    items = data_resp.get("data", [])
                    if not items:
                        results.append(f"🟡 Token <code>{masked_token}</code>: সংযোগ OK কিন্তু 0 record")
                        continue
                    results.append(f"🟢 Token <code>{masked_token}</code>: <b>{len(items)} records</b>")
                    for i, item in enumerate(items[:3]):
                        num = str(item.get("num", "")).strip()
                        msg_txt = str(item.get("message", ""))[:50]
                        otp_found = extract_otp_code(msg_txt)
                        otp_txt = f"OTP: <b>{otp_found}</b>" if otp_found else "OTP: <i>extract হয়নি</i>"
                        results.append(f"  #{i+1} num=<code>{num}</code> | {otp_txt}")
                except:
                    results.append(f"🟡 Token <code>{masked_token}</code>: JSON parse error\n<code>{raw_text[:80]}</code>")
            except Exception as e:
                results.append(f"🔴 Token error: {e}")
        final_txt = render_body_text(f"🔍 <b>Flex Panel Live Test</b>\n🔗 <code>{flex_url}</code>\n\n" + "\n".join(results))
        edit_message(chat_id, msg_id, final_txt, reply_markup={"inline_keyboard": [[
            {"text": "🔄 আবার Test করুন", "callback_data": "flex_live_test", "style": "primary"},
            {"text": "Back", "callback_data": "flex_control", "style": "danger"}
        ]]})

    elif data == "zenex_control":
        edit_message(chat_id, msg_id, render_body_text(f"🌐 <b>Zenex Network Control Panel</b>\n\nTotal API Keys: {len(bot_settings.get('zenex_keys', []))}\nManage your Zenex API Keys below:"), reply_markup=zenex_control_keyboard())

    elif data == "add_zenex_key":
        user_states[chat_id] = "wait_for_add_zenex_key"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the new Zenex API Key (e.g. ZNX_...):"), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "zenex_control", "style": "danger"}]]})

    elif data == "view_zenex_keys":
        kb = []
        for idx, key in enumerate(bot_settings.get("zenex_keys", [])):
            safe_name = key[:10] + "..." if len(key) > 10 else key
            kb.append([{"text": f"Delete {safe_name}", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"del_znx_{idx}", "style": "danger"}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "zenex_control", "style": "primary"}])
        edit_message(chat_id, msg_id, render_body_text("🗑 <b>Select Zenex Key to Delete:</b>"), reply_markup={"inline_keyboard": kb})

    elif data.startswith("del_znx_"):
        idx = int(data.split("_")[2])
        if 0 <= idx < len(bot_settings.get("zenex_keys", [])):
            del bot_settings["zenex_keys"][idx]
            save_db()
            answer_callback(call["id"], "✅ Zenex Key Deleted!", show_alert=True)
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "view_zenex_keys", "id": call["id"]})

    elif data == "zenex_search_country":
        kb = []
        for idx, c in enumerate(bot_settings.get("zenex_stex_search_countries", [])):
            kb.append([{"text": f"Delete {c}", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"del_znx_sc_{idx}", "style": "danger"}])
        kb.append([{"text": "Add Country Code", "icon_custom_emoji_id": "5420323438508155202", "callback_data": "add_zenex_search_country", "style": "success"}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "zenex_control", "style": "primary"}])
        edit_message(chat_id, msg_id, render_body_text("🌍 <b>Zenex Allowed Country Codes:</b>\nOnly these codes will be routed to Zenex API."), reply_markup={"inline_keyboard": kb})

    elif data == "add_zenex_search_country":
        user_states[chat_id] = "wait_for_add_znx_sc"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the Country Code (e.g. 880 or 44):"), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "zenex_search_country", "style": "danger"}]]})

    elif data.startswith("del_znx_sc_"):
        idx = int(data.split("_")[3])
        if 0 <= idx < len(bot_settings.get("zenex_stex_search_countries", [])):
            del bot_settings["zenex_stex_search_countries"][idx]
            save_db()
            answer_callback(call["id"], "✅ Zenex Country Deleted!", show_alert=True)
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "zenex_search_country", "id": call["id"]})

    elif data == "manage_zenex_srv":
        kb = []
        srvs = bot_settings.get("zenex_services", {})
        apps_db = bot_settings.get("premium_apps", {})
        for srv in srvs:
            emoji_id = "5257969839313526622"
            for app_key, app_data in apps_db.items():
                if srv.upper() == app_key or srv.upper() in app_key or app_key in srv.upper():
                    if "id" in app_data:
                        emoji_id = app_data["id"]
                        break
            kb.append([{"text": f"{srv}", "icon_custom_emoji_id": emoji_id, "callback_data": f"znx_srv_{srv}", "style": "primary"}])
        kb.append([{"text": "Add New Service", "icon_custom_emoji_id": "5420323438508155202", "callback_data": "znx_add_srv", "style": "success"}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "zenex_control", "style": "danger"}])
        edit_message(chat_id, msg_id, render_body_text("🌐 <b>Zenex Services Manager</b>\nManage your Zenex API-based services below:"), reply_markup={"inline_keyboard": kb})

    elif data == "znx_add_srv":
        user_states[chat_id] = "wait_znx_srv_name"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Enter Service Name (e.g. TELEGRAM):"), reply_markup=get_cancel_kb())

    elif data.startswith("znx_srv_"):
        srv = data.replace("znx_srv_", "")
        kb = []
        countries = bot_settings.get("zenex_services", {}).get(srv, {})
        flags_db = bot_settings.get("premium_flags", {})
        for c in countries:
            emoji_id = "5780471598922337683"
            for flag_code, flag_data in flags_db.items():
                iso = flag_data.get("iso", "").upper()
                name = flag_data.get("name", "").upper()
                if c.upper() == iso or c.upper() == name or c.upper() in name or name in c.upper():
                    if "id" in flag_data: emoji_id = flag_data["id"]; break
            kb.append([{"text": f"{c} ({len(countries[c])} Ranges)", "icon_custom_emoji_id": emoji_id, "callback_data": f"znx_cnt_{srv}_{c}", "style": "primary"}])
        kb.append([{"text": "Add Country", "icon_custom_emoji_id": "5420323438508155202", "callback_data": f"znx_add_cnt_{srv}", "style": "success"}])
        kb.append([{"text": "Delete Service", "icon_custom_emoji_id": "5422557736330106570", "callback_data": f"znx_del_srv_{srv}", "style": "danger"}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "manage_zenex_srv", "style": "primary"}])
        edit_message(chat_id, msg_id, render_body_text(f"📂 <b>Zenex Service: {srv}</b>\nManage countries for this service:"), reply_markup={"inline_keyboard": kb})

    elif data.startswith("znx_add_cnt_"):
        srv = data.replace("znx_add_cnt_", "")
        user_states[chat_id] = "wait_znx_cnt_name"
        temp_data[chat_id] = {"msg_id": msg_id, "srv": srv}
        edit_message(chat_id, msg_id, render_body_text(f"🌍 Enter Country Name for <b>{srv}</b> (e.g. BD, INDIA):"), reply_markup=get_cancel_kb())

    elif data.startswith("znx_del_srv_"):
        srv = data.replace("znx_del_srv_", "")
        if srv in bot_settings.get("zenex_services", {}): del bot_settings["zenex_services"][srv]
        save_db()
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": "manage_zenex_srv", "id": call["id"]})

    elif data.startswith("znx_cnt_"):
        parts = data.split("_")
        srv, cnt = parts[2], parts[3]
        ranges = bot_settings.get("zenex_services", {}).get(srv, {}).get(cnt, [])
        kb = []
        row = []
        for r in ranges:
            row.append({"text": f"Delete {r}", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"znx_dr_{srv}_{cnt}_{r}", "style": "danger"})
            if len(row) == 2:
                kb.append(row)
                row = []
        if row: kb.append(row)
        kb.append([{"text": "Add Range", "icon_custom_emoji_id": "5420323438508155202", "callback_data": f"znx_addr_{srv}_{cnt}", "style": "success"}])
        kb.append([{"text": "Delete Entire Country", "icon_custom_emoji_id": "5422557736330106570", "callback_data": f"znx_del_cnt_{srv}_{cnt}", "style": "danger"}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"znx_srv_{srv}", "style": "primary"}])
        txt = f"📍 <b>Zenex Service: {srv} | Country: {cnt}</b>\n\n<b>Total Ranges:</b> {len(ranges)}\n<i>Click on a range to delete it, or add a new one.</i>"
        edit_message(chat_id, msg_id, render_body_text(txt), reply_markup={"inline_keyboard": kb})

    elif data.startswith("znx_addr_"):
        parts = data.split("_")
        srv, cnt = parts[2], parts[3]
        user_states[chat_id] = "wait_znx_addr"
        temp_data[chat_id] = {"msg_id": msg_id, "srv": srv, "cnt": cnt}
        edit_message(chat_id, msg_id, render_body_text(f"📝 Send the new Range for <b>{cnt}</b> (e.g. 26134):"), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275166", "callback_data": f"znx_cnt_{srv}_{cnt}", "style": "danger"}]]})

    elif data.startswith("znx_dr_"):
        parts = data.split("_")
        srv, cnt, rng = parts[2], parts[3], parts[4]
        if rng in bot_settings.get("zenex_services", {}).get(srv, {}).get(cnt, []):
            bot_settings["zenex_services"][srv][cnt].remove(rng)
            save_db()
            answer_callback(call["id"], f"✅ Range {rng} deleted!", show_alert=True)
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": f"znx_cnt_{srv}_{cnt}", "id": call["id"]})

    elif data.startswith("znx_del_cnt_"):
        parts = data.split("_")
        srv, cnt = parts[3], parts[4]
        if cnt in bot_settings.get("zenex_services", {}).get(srv, {}): del bot_settings["zenex_services"][srv][cnt]
        save_db()
        handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": f"znx_srv_{srv}", "id": call["id"]})

    elif data == "manage_fj":
        edit_message(chat_id, msg_id, render_body_text(f"{PEM['link']} <b>FORCE JOIN SYSTEM</b>\nManage channels below:"), reply_markup=fj_settings_keyboard())

    elif data == "toggle_fj":
        bot_settings["fj_on"] = not bot_settings["fj_on"]
        save_db()
        edit_message(chat_id, msg_id, render_body_text(f"{PEM['link']} <b>FORCE JOIN SYSTEM</b>\nManage channels below:"), reply_markup=fj_settings_keyboard())

    elif data == "add_fj":
        user_states[chat_id] = "wait_for_add_fj"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Send Channel Username or Invite Link:\n<i>(Note: For private channels, use the numeric ID like -100...)</i>"), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "manage_fj", "style": "danger"}]]})

    elif data.startswith("del_fj_"):
        idx = int(data.split("_")[2])
        if 0 <= idx < len(bot_settings["fj_channels"]):
            del bot_settings["fj_channels"][idx]
            save_db()
            answer_callback(call["id"], "✅ Channel deleted!", show_alert=True)
            edit_message(chat_id, msg_id, render_body_text(f"{PEM['link']} <b>FORCE JOIN SYSTEM</b>\nManage channels below:"), reply_markup=fj_settings_keyboard())

    elif data == "manage_admins":
        edit_message(chat_id, msg_id, render_body_text(f"{PEM['user']} <b>ADMIN MANAGEMENT</b>\nManage your bot admins below:"), reply_markup=admin_settings_keyboard())

    elif data == "add_adm":
        user_states[chat_id] = "wait_for_add_adm"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the User ID of the new Admin:"), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "manage_admins", "style": "danger"}]]})

    elif data.startswith("del_adm_"):
        idx = int(data.split("_")[2])
        if 0 <= idx < len(bot_settings["admins"]):
            del bot_settings["admins"][idx]
            save_db()
            answer_callback(call["id"], "✅ Admin deleted!", show_alert=True)
            edit_message(chat_id, msg_id, render_body_text(f"{PEM['user']} <b>ADMIN MANAGEMENT</b>\nManage your bot admins below:"), reply_markup=admin_settings_keyboard())

    elif data == "manage_otp_groups":
        edit_message(chat_id, msg_id, render_body_text("🛡 <b>OTP GROUP MANAGEMENT</b>\nManage settings below:"), reply_markup=otp_groups_list_keyboard())

    elif data == "add_fw":
        user_states[chat_id] = "wait_for_add_fw_id"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the Group ID/Username to forward messages to:"), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "manage_otp_groups", "style": "danger"}]]})

    elif data.startswith("manage_fw_"):
        idx = int(data.split("_")[2])
        if 0 <= idx < len(bot_settings["fw_groups"]):
            grp_id = bot_settings["fw_groups"][idx]["chat_id"]
            edit_message(chat_id, msg_id, render_body_text(f"🛡 <b>Manage Group:</b> {grp_id}"), reply_markup=specific_fw_group_keyboard(idx))

    elif data.startswith("add_fwbtn_"):
        idx = int(data.split("_")[2])
        user_states[chat_id] = "wait_for_add_fw_btn"
        temp_data[chat_id] = {"msg_id": msg_id, "fw_idx": idx}
        edit_message(chat_id, msg_id, render_body_text("📝 Send Custom Inline Button format:\n<code>Button Text - https://link.com</code>"), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"manage_fw_{idx}", "style": "danger"}]]})

    elif data.startswith("del_fwbtn_"):
        parts = data.split("_")
        idx, b_idx = int(parts[2]), int(parts[3])
        if 0 <= idx < len(bot_settings["fw_groups"]):
            if 0 <= b_idx < len(bot_settings["fw_groups"][idx]["buttons"]):
                del bot_settings["fw_groups"][idx]["buttons"][b_idx]
                save_db()
                answer_callback(call["id"], "✅ Button deleted!", show_alert=True)
                edit_message(chat_id, msg_id, render_body_text(f"🛡 <b>Manage Group:</b> {bot_settings['fw_groups'][idx]['chat_id']}"), reply_markup=specific_fw_group_keyboard(idx))

    elif data.startswith("del_fw_"):
        idx = int(data.split("_")[2])
        if 0 <= idx < len(bot_settings["fw_groups"]):
            del bot_settings["fw_groups"][idx]
            save_db()
            answer_callback(call["id"], "✅ Group deleted!", show_alert=True)
            edit_message(chat_id, msg_id, render_body_text("🛡 <b>OTP GROUP MANAGEMENT</b>\nManage settings below:"), reply_markup=otp_groups_list_keyboard())

    elif data == "edit_otp_link":
        user_states[chat_id] = "wait_for_otp_link"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the new OTP Group Link:"), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "manage_otp_groups", "style": "danger"}]]})

    elif data == "edit_main_channel":
        user_states[chat_id] = "wait_for_main_channel"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the new Main Channel Link:"), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "manage_otp_groups", "style": "danger"}]]})

    elif data == "manage_panels":
        api_count = len([p for p in bot_settings["panels"] if p.get("type") == "API Panel"])
        cpt_count = len([p for p in bot_settings["panels"] if p.get("type", "API Panel") == "Auto Captcha Panel"])
        text = f"{PEM['gear']} <b>Panel Management</b>\n\nSelect which type of panel system you want to manage:"
        kb = {"inline_keyboard": [
            [{"text": f"Manage API Panels ({api_count})", "icon_custom_emoji_id": "5336972142066047577", "callback_data": "manage_api_panels", "style": "primary"}],
            [{"text": f"Manage Auto Captcha Panels ({cpt_count})", "icon_custom_emoji_id": "5353022963132174959", "callback_data": "manage_cpt_panels", "style": "success"}],
            [{"text": "Back to System", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "system_settings", "style": "danger"}]
        ]}
        edit_message(chat_id, msg_id, render_body_text(text), reply_markup=kb)

    elif data in ["manage_api_panels", "manage_cpt_panels"]:
        p_type = "API Panel" if data == "manage_api_panels" else "Auto Captcha Panel"
        p_list = [p for p in bot_settings["panels"] if p.get("type", "API Panel") == p_type]
        icon = f"{PEM['world']} API" if p_type == 'API Panel' else f"{PEM['lock']} Auto Captcha"
        
        text = f"{icon} <b>{p_type}s Management</b>\n\n👀 <b>Active Monitors:</b> {len(p_list)}\n\n🟢 <b>Available Providers:</b>\n"
        for p in p_list:
            status = "Monitoring" if p['status'] == 'ON' else "Stopped"
            login_state = p.get('login_status', '')
            if p['type'] == 'Auto Captcha Panel':
                conf = f" {login_state}" if login_state else f"{PEM['ok']} Configured"
            else:
                conf = f"{PEM['ok']} Configured" if p.get('api_url') else f"{PEM['no']} Not Configured"
            text += f"• {p['name']}: {PEM['ok'] if p['status']=='ON' else PEM['no']} {status} | {conf}\n"
        edit_message(chat_id, msg_id, render_body_text(text), reply_markup=typed_panels_list_keyboard(p_type))

    elif data in ["add_api_panel", "add_cpt_panel"]:
        user_states[chat_id] = "wait_for_panel_name"
        p_type = "api" if data == "add_api_panel" else "logc"
        temp_data[chat_id] = {"msg_id": msg_id, "add_type": p_type}
        edit_message(chat_id, msg_id, render_body_text("📝 Please send the name of the New Provider:"), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"manage_{'api' if p_type=='api' else 'cpt'}_panels", "style": "danger"}]]})

    elif data.startswith("add_ptype_"):
        pass

    elif data in ["list_del_api", "list_del_cpt"]:
        p_type = "API Panel" if data == "list_del_api" else "Auto Captcha Panel"
        kb = []
        for idx, p in enumerate(bot_settings["panels"]):
            if p.get("type", "API Panel") == p_type:
                kb.append([{"text": f"Delete {p['name']}", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"do_del_pnl_{idx}", "style": "danger"}])
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"manage_{'api' if p_type=='API Panel' else 'cpt'}_panels", "style": "primary"}])
        edit_message(chat_id, msg_id, render_body_text(f"{PEM['trash']} <b>Select a Provider to Delete:</b>"), reply_markup={"inline_keyboard": kb})

    elif data.startswith("do_del_pnl_"):
        idx = int(data.split("_")[3])
        if 0 <= idx < len(bot_settings["panels"]):
            p_type = bot_settings["panels"][idx].get("type", "API Panel")
            del bot_settings["panels"][idx]
            save_db()
            answer_callback(call["id"], "✅ Provider Deleted!", show_alert=True)
            handle_callback({"message": {"chat": {"id": chat_id}, "message_id": msg_id}, "data": f"manage_{'api' if p_type=='API Panel' else 'cpt'}_panels", "id": "internal"})

    elif data.startswith("tog_pnl_"):
        idx = int(data.split("_")[2])
        if 0 <= idx < len(bot_settings["panels"]):
            p = bot_settings["panels"][idx]
            
            p["status"] = "ON" if p["status"] == "OFF" else "OFF"
            save_db()
            
            if p["type"] == "Auto Captcha Panel":
                text = f"⚙️ <b>Configure {p['name']}</b>\n\n<b>Type:</b> {p['type']}\n<b>Status:</b> {'🟢 Monitoring' if p['status'] == 'ON' else '🔴 Stopped'}\n<b>Login Status:</b> {p.get('login_status', 'Unknown')}\n<b>Login URL:</b> <code>{p.get('login_url', 'None')}</code>\n<b>User:</b> <code>{p.get('username', 'None')}</code>"
            else:
                text = f"⚙️ <b>Configure {p['name']}</b>\n\n<b>Type:</b> {p['type']}\n<b>Status:</b> {'🟢 Monitoring' if p['status'] == 'ON' else '🔴 Stopped'}\n<b>API URL:</b> <code>{p.get('api_url', 'None')}</code>\n<b>Token:</b> <code>{p.get('token', 'None')}</code>"
            edit_message(chat_id, msg_id, render_body_text(text), reply_markup=panel_config_keyboard(idx))

    elif data.startswith("conf_pnl_"):
        idx = int(data.split("_")[2])
        if 0 <= idx < len(bot_settings["panels"]):
            p = bot_settings["panels"][idx]
            if p["type"] == "Auto Captcha Panel":
                text = f"⚙️ <b>Configure {p['name']}</b>\n\n<b>Type:</b> {p['type']}\n<b>Status:</b> {'🟢 Monitoring' if p['status'] == 'ON' else '🔴 Stopped'}\n<b>Login Status:</b> {p.get('login_status', 'Unknown')}\n<b>Login URL:</b> <code>{p.get('login_url', 'None')}</code>\n<b>User:</b> <code>{p.get('username', 'None')}</code>\n<b>Num Col:</b> {p.get('num_col_name')} (Idx: {p.get('num_col_idx')})\n<b>Msg Col:</b> {p.get('msg_col_name')} (Idx: {p.get('msg_col_idx')})"
            else:
                text = f"⚙️ <b>Configure {p['name']}</b>\n\n<b>Type:</b> {p['type']}\n<b>Status:</b> {'🟢 Monitoring' if p['status'] == 'ON' else '🔴 Stopped'}\n<b>API URL:</b> <code>{p.get('api_url', 'None')}</code>\n<b>Token:</b> <code>{p.get('token', 'None')}</code>\n<b>Full API URL:</b> <code>{p.get('full_api_url', 'None')}</code>"
            edit_message(chat_id, msg_id, render_body_text(text), reply_markup=panel_config_keyboard(idx))

    elif data.startswith("set_p_api_"):
        idx = int(data.split("_")[3])
        user_states[chat_id] = "wait_for_p_api"
        temp_data[chat_id] = {"msg_id": msg_id, "p_idx": idx}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the API URL for this provider:"), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"conf_pnl_{idx}", "style": "danger"}]]})

    elif data.startswith("set_p_tok_"):
        idx = int(data.split("_")[3])
        user_states[chat_id] = "wait_for_p_tok"
        temp_data[chat_id] = {"msg_id": msg_id, "p_idx": idx}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the Token for this provider:"), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"conf_pnl_{idx}", "style": "danger"}]]})

    elif data.startswith("set_p_fapi_"):
        idx = int(data.split("_")[3])
        user_states[chat_id] = "wait_for_p_fapi"
        temp_data[chat_id] = {"msg_id": msg_id, "p_idx": idx}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the FULL API URL (Example: http://api.com/get?key=YOUR_TOKEN&start=0):"), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"conf_pnl_{idx}", "style": "danger"}]]})

    elif data.startswith("set_p_rec_"):
        idx = int(data.split("_")[3])
        user_states[chat_id] = "wait_for_p_rec"
        temp_data[chat_id] = {"msg_id": msg_id, "p_idx": idx}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the number of records to fetch (e.g. 10).\nType <code>0</code> for Unlimited:"), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": f"conf_pnl_{idx}", "style": "danger"}]]})

    elif data.startswith("test_p_conn_"):
        idx = int(data.split("_")[3])
        p = bot_settings["panels"][idx]
        wait_msg = send_message(chat_id, render_body_text("⏳ Testing connection. Please wait..."))
        wait_msg_id = wait_msg.get("result", {}).get("message_id") if wait_msg else None
        answer_callback(call["id"])
        
        try:
            parsed = []
            raw_text = ""
            
            if p["type"] == "Auto Captcha Panel":
                sess = panel_sessions.get(idx)
                if not sess:
                    success = attempt_auto_login(p, idx)
                    if not success:
                        if wait_msg_id: delete_message(chat_id, wait_msg_id)
                        send_message(chat_id, render_body_text(f"❌ <b>Auto Login Failed!</b>\nReason: {html.escape(str(p.get('login_status', 'Unknown')))}"))
                        return
                    sess = panel_sessions.get(idx)
                    
                login_url = p.get("login_url", "").strip()
                if not login_url.startswith("http"): login_url = "http://" + login_url
                msg_link = p.get("msg_link", "").strip()
                if not msg_link.startswith("http") and msg_link != "": msg_link = "http://" + msg_link
                check_url = msg_link if msg_link else f"{login_url.split('/login')[0]}/client/SMSCDRStats"
                
                # 🌟 test connection supports sAjaxSource & HTML table parser
                parsed, raw_text = fetch_cpt_panel_cdrs(p, sess, check_url)
                
            else:
                full_url = p.get("full_api_url", "").strip()
                url = p.get("api_url", "").strip()
                token = p.get("token", "").strip()
                if not full_url and not url:
                    if wait_msg_id: delete_message(chat_id, wait_msg_id)
                    send_message(chat_id, render_body_text("❌ Please Set API URL or Full API URL first!"))
                    return
                
                urls_to_try = []
                if full_url:
                    urls_to_try.append(full_url)
                else:
                    if "{token}" in url or "{key}" in url:
                        urls_to_try.append(url.replace("{token}", token).replace("{key}", token))
                    elif "token=" in url or "key=" in url:
                        urls_to_try.append(url)
                    else:
                        sep = '&' if '?' in url else '?'
                        urls_to_try.append(f"{url}{sep}token={token}")
                        urls_to_try.append(f"{url}{sep}key={token}&start=0")
                        urls_to_try.append(f"{url}{sep}key={token}")
                    
                parsed = []
                raw_text = ""
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
                for try_url in urls_to_try:
                    try:
                        res = requests.get(try_url, headers=headers, timeout=10)
                        raw_text = res.text
                        parsed = parse_panel_response(raw_text, p)
                        if parsed:
                            if not full_url and try_url != url and token:
                                p["api_url"] = try_url.replace(token, "{token}")
                                save_db()
                            break
                    except: pass
                 
            if wait_msg_id: delete_message(chat_id, wait_msg_id)
                 
            if parsed:
                txt = f"✅ <b>Connection Successful!</b>\n\n🎯 <b>Parsed Data Sample (Max 3):</b>\n\n"
                
                for i, sample in enumerate(parsed[:3]):
                    num = sample['number']
                    msg = sample['message']
                    otp = sample['otp']
                    
                    detected_app = detect_service(msg)
                    app_name = detected_app if detected_app else p.get("name", "Unknown")
                    app_full_name, prem_app_html = get_service_info_html(app_name, msg)
                    
                    txt += f"<b>{i+1}.</b> {prem_app_html} <b>{app_full_name}</b>\n"
                    txt += f"📱 Number: <code>{num}</code>\n"
                    txt += f"📝 Full Msg: <code>{html.escape(msg)}</code>\n"
                    txt += f"🔐 OTP: <code>{otp}</code>\n"
                    txt += "➖" * 12 + "\n"
                    
                send_message(chat_id, render_body_text(txt))
            else:
                if p["type"] == "Auto Captcha Panel":
                    try:
                        soup = BeautifulSoup(raw_text, 'html.parser')
                        tables = soup.find_all('table')
                        if tables:
                            full_table_data = "🔍 FULL TABLE DATA (A-Z)\n" + "="*50 + "\n\n"
                            for t_idx, table in enumerate(tables):
                                full_table_data += f"--- Table {t_idx+1} ---\n"
                                rows = table.find_all('tr')
                                for r_idx, row in enumerate(rows):
                                    cols = row.find_all(['th', 'td'])
                                    col_texts = [f"[{c_idx+1}] {c.get_text(separator=' ', strip=True)}" for c_idx, c in enumerate(cols)]
                                    full_table_data += f"Row {r_idx+1}: {' | '.join(col_texts)}\n"
                                full_table_data += "\n" + "="*50 + "\n"
                            
                            send_document(chat_id, f"Full_Panel_Data_{idx}.txt", full_table_data.encode('utf-8'))
                            fail_txt = f"⚠️ <b>Connected, but couldn't parse OTP data!</b>\n\n<i>আমি ওই লিংকের সম্পূর্ণ (A-Z) ডাটা একটি Text File এ পাঠিয়েছি। ফাইলটি ওপেন করে সঠিক Column Number (যেমন: [1], [3]) চেক করে প্যানেলে আপডেট করে নাও।</i>"
                            send_message(chat_id, render_body_text(fail_txt))
                        else:
                            send_message(chat_id, render_body_text(f"⚠️ <b>Connected, but no HTML Table found!</b>\nMake sure the message link is correct."))
                    except Exception as e:
                        send_message(chat_id, render_body_text(f"❌ <b>Error parsing HTML:</b> {html.escape(str(e))}"))
                else:
                    safe_html = html.escape(str(raw_text)[:300])
                    send_message(chat_id, render_body_text(f"⚠️ <b>Connected, but couldn't find/parse OTP data.</b>\n\n<i>Make sure your API config is correct.</i>\n\nRaw HTML/Data (excerpt):\n<code>{safe_html}...</code>"))
        except Exception as e:
            if wait_msg_id: delete_message(chat_id, wait_msg_id)
            send_message(chat_id, render_body_text(f"❌ <b>Connection Failed!</b>\nError: {html.escape(str(e))}"))

    elif data == "dxa_control":
        if chat_id in user_states: del user_states[chat_id]
        edit_message(chat_id, msg_id, render_body_text("🕹 <b>RAHIN CONTROL PANEL</b>"), reply_markup=dxa_control_keyboard())

    elif data == "dxa_service_rates":
        if chat_id in user_states: del user_states[chat_id]
        edit_message(chat_id, msg_id, render_body_text("⚙️ <b>SERVICE OTP RATES</b>\n\nSet per-service rewards. Unlisted services use global OTP Reward."), reply_markup=service_rates_keyboard())
        answer_callback(call["id"])

    elif data == "dxa_add_srv":
        user_states[chat_id] = "set_srv_name"
        temp_data[chat_id] = {"msg_id": msg_id}
        cancel_kb = {"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "dxa_service_rates", "style": "danger"}]]}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the service name (e.g. WHATSAPP, FACEBOOK):"), reply_markup=cancel_kb)
        answer_callback(call["id"])

    elif data.startswith("dxa_srv_rate_"):
        srv = data.replace("dxa_srv_rate_", "")
        current = bot_settings.get("service_otp_rates", {}).get(srv, 0)
        user_states[chat_id] = "set_srv_rate"
        temp_data[chat_id] = {"msg_id": msg_id, "srv": srv}
        cancel_kb = {"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "dxa_service_rates", "style": "danger"}]]}
        edit_message(chat_id, msg_id, render_body_text(f"📝 Send new reward rate for <b>{srv}</b> (current: {current} tk):"), reply_markup=cancel_kb)
        answer_callback(call["id"])

    elif data.startswith("dxa_srv_tog_"):
        srv = data.replace("dxa_srv_tog_", "")
        enabled = bot_settings.setdefault("service_reward_enabled", {})
        enabled[srv] = not enabled.get(srv, True)
        save_db()
        edit_message(chat_id, msg_id, render_body_text("⚙️ <b>SERVICE OTP RATES</b>"), reply_markup=service_rates_keyboard())
        answer_callback(call["id"], f"{'ON' if enabled[srv] else 'OFF'}: {srv}", show_alert=False)

    elif data.startswith("dxa_del_srv_"):
        srv = data.replace("dxa_del_srv_", "")
        bot_settings.get("service_otp_rates", {}).pop(srv, None)
        bot_settings.get("service_reward_enabled", {}).pop(srv, None)
        save_db()
        edit_message(chat_id, msg_id, render_body_text("⚙️ <b>SERVICE OTP RATES</b>"), reply_markup=service_rates_keyboard())
        answer_callback(call["id"], f"Deleted: {srv}", show_alert=True)
  
    elif data == "dxa_toggle_w":
        bot_settings["withdraw_on"] = not bot_settings["withdraw_on"]
        save_db()
        edit_message(chat_id, msg_id, render_body_text("🕹 <b>RAHIN CONTROL PANEL</b>"), reply_markup=dxa_control_keyboard())

    elif data == "dxa_set_rand_pass":
        if not is_admin(chat_id):
            answer_callback(call["id"], "🚫 Admin only!", show_alert=True)
            return
        user_states[chat_id] = "wait_for_rand_pass"
        temp_data[chat_id] = {"msg_id": msg_id}
        cur = bot_settings.get("rand_name_pass", "")
        cur_txt = f"\n⚙️ Current: <code>{cur}</code>" if cur else "\n⚙️ Currently not set."
        cancel_kb = {"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "dxa_control", "style": "danger"}]]}
        edit_message(chat_id, msg_id, render_body_text(
            f"{PEM['star']} <b>RANDOM NAME — PASS SET</b>\n\n"
            f"📝 যে Password/Text দেখাতে চান তা পাঠান:{cur_txt}\n\n"
            f"<i>এটি Random Name এর সাথে সব user দেখতে পাবে।</i>"
        ), reply_markup=cancel_kb)
        answer_callback(call["id"])

    elif data == "dxa_toggle_bulk_auto" or data == "bulk_toggle_auto":
        if not is_admin(chat_id):
            answer_callback(call["id"], "🚫 Admin only!", show_alert=True)
            return
        bot_settings["bulk_auto_approve"] = not bot_settings.get("bulk_auto_approve", False)
        save_db()
        status = "ON ✅" if bot_settings["bulk_auto_approve"] else "OFF ❌"
        answer_callback(call["id"], f"📦 Bulk Auto Approve: {status}", show_alert=True)
        if data == "dxa_toggle_bulk_auto":
            edit_message(chat_id, msg_id, render_body_text("🕹 <b>RAHIN CONTROL PANEL</b>"), reply_markup=dxa_control_keyboard())
        else:
            # Update the button label on the notification message itself
            new_lbl = "🟢 Auto: ON" if bot_settings["bulk_auto_approve"] else "🔴 Auto: OFF"
            try:
                existing = call["message"]
                orig_kb = existing.get("reply_markup", {}).get("inline_keyboard", [])
                if len(orig_kb) >= 2:
                    orig_kb[1] = [{"text": new_lbl, "callback_data": "bulk_toggle_auto", "style": "primary"}]
                edit_message(chat_id, msg_id, render_body_text(existing.get("text", "")), reply_markup={"inline_keyboard": orig_kb})
            except: pass

    elif data == "manage_w_methods":
        edit_message(chat_id, msg_id, render_body_text("💳 <b>WITHDRAWAL METHODS</b>\n\nManage your withdrawal methods below:"), reply_markup=w_methods_keyboard())

    elif data == "add_wm":
        user_states[chat_id] = "wait_for_add_wm"
        temp_data[chat_id] = {"msg_id": msg_id}
        edit_message(chat_id, msg_id, render_body_text("📝 Send the name of the new Withdrawal Method:"), reply_markup={"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "manage_w_methods", "style": "danger"}]]})

    elif data.startswith("del_wm_"):
        idx = int(data.split("_")[2])
        if 0 <= idx < len(bot_settings["w_methods"]):
            del bot_settings["w_methods"][idx]
            save_db()
            answer_callback(call["id"], "✅ Method deleted!", show_alert=True)
            edit_message(chat_id, msg_id, render_body_text("💳 <b>WITHDRAWAL METHODS</b>\n\nManage your withdrawal methods below:"), reply_markup=w_methods_keyboard())

    elif data.startswith("dxa_"):
        key = data.replace("dxa_", "")
        key_map = {"min_w": "min_withdraw", "otp_r": "otp_reward", "ref_r": "refer_reward", "cool": "cooldown", "num_req": "num_req", "num_share": "num_share", "sup_link": "support_link", "w_group": "w_group"}
        if key in key_map:
            temp_data[chat_id] = {"msg_id": msg_id, "key": key_map[key]}
            user_states[chat_id] = "set_dxa"
            cancel_kb = {"inline_keyboard": [[{"text": "Cancel", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "cancel_dxa_edit", "style": "danger"}]]}
            edit_message(chat_id, msg_id, render_body_text(f"📝 Please send the new value for <code>{key_map[key]}</code>:"), reply_markup=cancel_kb)
            answer_callback(call["id"])

    elif data.startswith("bulk100_s_"):
        # Step 1: Show country selection for this service
        service = data.replace("bulk100_s_", "")
        local_cnts = set([b["country"] for b in number_batches.values() if b["service"] == service and b["numbers"]])
        zenex_cnts = set(bot_settings.get("zenex_services", {}).get(service, {}).keys())
        stex_cnts  = set(bot_settings.get("stex_services",  {}).get(service, {}).keys())
        voltx_cnts = set(bot_settings.get("voltx_services", {}).get(service, {}).keys())
        nexus_cnts = set(bot_settings.get("nexus_services", {}).get(service, {}).keys())
        all_countries = local_cnts.union(zenex_cnts).union(stex_cnts).union(voltx_cnts).union(nexus_cnts)
        if not all_countries:
            edit_message(chat_id, msg_id, render_body_text(
                f"❌ <b>{service}</b> এর জন্য কোনো country configure করা নেই!"
            ))
        else:
            flags_db = bot_settings.get("premium_flags", {})
            kb = []
            for c in sorted(all_countries):
                emoji_id = "5780471598922337683"
                for flag_code, flag_data in flags_db.items():
                    iso = flag_data.get("iso", "").upper()
                    name = flag_data.get("name", "").upper()
                    if c.upper() == iso or c.upper() == name or c.upper() in name or name in c.upper():
                        if "id" in flag_data:
                            emoji_id = flag_data["id"]
                            break
                kb.append([{"text": f"{c}", "icon_custom_emoji_id": emoji_id,
                            "callback_data": f"bulk100_c_{service}_{c}", "style": "success"}])
            kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176",
                        "callback_data": "close_msg", "style": "danger"}])
            edit_message(chat_id, msg_id, render_body_text(
                f"📦 <b>100 BULK — {service}</b>\n━━━━━━━━━━━━\n🌍 একটি country বাছুন:"
            ), reply_markup={"inline_keyboard": kb})

    elif data.startswith("bulk100_c_"):
        # Step 2: Create a pending bulk request → notify admin for approval
        rest = data.replace("bulk100_c_", "")
        service = None
        country = None

        # সব চারটা provider এর services থেকে service+country খুঁজে বের করো
        all_svc_dicts = [
            bot_settings.get("zenex_services", {}),
            bot_settings.get("stex_services",  {}),
            bot_settings.get("voltx_services", {}),
            bot_settings.get("nexus_services", {}),
        ]
        for svc_dict in all_svc_dicts:
            for svc, cnt_dict in svc_dict.items():
                for cnt in cnt_dict.keys():
                    if rest == f"{svc}_{cnt}":
                        service, country = svc, cnt
                        break
                if service: break
            if service: break

        if not service:
            parts = rest.split("_")
            for i in range(len(parts) - 1, 0, -1):
                svc_try = "_".join(parts[:i])
                cnt_try = "_".join(parts[i:])
                local_cnts = set([b["country"] for b in number_batches.values() if b["service"] == svc_try])
                zenex_cnts = set(bot_settings.get("zenex_services", {}).get(svc_try, {}).keys())
                stex_cnts  = set(bot_settings.get("stex_services",  {}).get(svc_try, {}).keys())
                voltx_cnts = set(bot_settings.get("voltx_services", {}).get(svc_try, {}).keys())
                nexus_cnts = set(bot_settings.get("nexus_services", {}).get(svc_try, {}).keys())
                if cnt_try in local_cnts or cnt_try in zenex_cnts or cnt_try in stex_cnts or cnt_try in voltx_cnts or cnt_try in nexus_cnts:
                    service, country = svc_try, cnt_try
                    break
        if not service or not country:
            edit_message(chat_id, msg_id, render_body_text("❌ Invalid selection. Please try again."))
            return

        first_name = call["from"].get("first_name", "User")
        last_name = call["from"].get("last_name", "")
        full_name = f"{first_name} {last_name}".strip()

        req_id = f"B_{str(uuid.uuid4())[:6].upper()}"
        # সব তিন provider এর ranges merge করো — যেকোনো provider থেকে range থাকলেই কাজ করবে
        _z = bot_settings.get("zenex_services", {}).get(service, {}).get(country, [])
        _s = bot_settings.get("stex_services",  {}).get(service, {}).get(country, [])
        _v = bot_settings.get("voltx_services", {}).get(service, {}).get(country, [])
        _n = bot_settings.get("nexus_services", {}).get(service, {}).get(country, [])
        country_ranges = list(dict.fromkeys(_z + _s + _v + _n))  # merge, deduplicate, keep order
        pending_bulk_requests[req_id] = {
            "user_id": chat_id,
            "service": service,
            "country": country,
            "full_name": full_name,
            "ranges": country_ranges,
            "status": "pending"
        }

        # Notify all admins (and w_group if set)
        # ── Auto Approve if enabled ────────────────────────────────────────────
        if bot_settings.get("bulk_auto_approve"):
            kb = [[{"text": "Close", "icon_custom_emoji_id": "5420130255174145507", "callback_data": "close_msg", "style": "danger"}]]
            edit_message(chat_id, msg_id, render_body_text(
                f"📦 <b>BULK REQUEST AUTO-APPROVED!</b>\n"
                f"━━━━━━━━━━━━\n"
                f"🧾 <b>Req ID:</b> <code>{req_id}</code>\n"
                f"📱 <b>Service:</b> {service}\n"
                f"🌍 <b>Country:</b> {country}\n"
                f"🔢 <b>Amount:</b> 100 numbers\n"
                f"━━━━━━━━━━━━\n"
                f"⌛ আপনার 100টি number fetch হচ্ছে, একটু অপেক্ষা করুন..."
            ), reply_markup={"inline_keyboard": kb})
            # Trigger the same approved-bulk logic immediately
            fake_call = {
                "from": {"id": OWNER_ID},
                "message": {"chat": {"id": chat_id}, "message_id": msg_id},
                "data": f"bapp_{req_id}",
                "id": call.get("id", "auto")
            }
            threading.Thread(target=handle_callback, args=(fake_call,), daemon=True).start()
            return
        # ──────────────────────────────────────────────────────────────────────

        admin_msg = (
            f"📦 <b>NEW BULK NUMBER REQUEST</b>\n\n"
            f"👤 <b>USER:</b> <a href='tg://user?id={chat_id}'>{full_name}</a> (<code>{chat_id}</code>)\n"
            f"📱 <b>SERVICE:</b> {service}\n"
            f"🌍 <b>COUNTRY:</b> {country}\n"
            f"🔢 <b>AMOUNT:</b> 100 numbers\n\n"
            f"🧾 <b>REQ ID:</b> {req_id}"
        )
        auto_lbl = "🟢 Auto: ON" if bot_settings.get("bulk_auto_approve") else "🔴 Auto: OFF"
        approve_kb = {"inline_keyboard": [
            [
                {"text": "✅ APPROVE", "icon_custom_emoji_id": "5352694861990501856", "callback_data": f"bapp_{req_id}", "style": "success"},
                {"text": "❌ REJECT",  "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"brej_{req_id}", "style": "danger"}
            ],
            [
                {"text": auto_lbl, "callback_data": "bulk_toggle_auto", "style": "primary"}
            ]
        ]}
        if bot_settings.get("w_group"):
            send_message(bot_settings["w_group"], render_body_text(admin_msg), reply_markup=approve_kb)
        notified_bulk = set()
        for adm in bot_settings.get("admins", []):
            try:
                send_message(adm, render_body_text(admin_msg), reply_markup=approve_kb)
                notified_bulk.add(adm)
            except: pass
        if OWNER_ID not in notified_bulk:
            try: send_message(OWNER_ID, render_body_text(admin_msg), reply_markup=approve_kb)
            except: pass

        kb = [[{"text": "Close", "icon_custom_emoji_id": "5420130255174145507", "callback_data": "close_msg", "style": "danger"}]]
        edit_message(chat_id, msg_id, render_body_text(
            f"📦 <b>BULK REQUEST SUBMITTED</b>\n"
            f"━━━━━━━━━━━━\n"
            f"🧾 <b>Req ID:</b> <code>{req_id}</code>\n"
            f"📱 <b>Service:</b> {service}\n"
            f"🌍 <b>Country:</b> {country}\n"
            f"🔢 <b>Amount:</b> 100 numbers\n"
            f"━━━━━━━━━━━━\n"
            f"⏳ Admin approval এর অপেক্ষায় আছে। Approved হলে আপনাকে notify করা হবে!"
        ), reply_markup={"inline_keyboard": kb})

    elif data.startswith("g_s_"):
        service = data.split("g_s_")[1]
        local_cnts = set([b["country"] for b in number_batches.values() if b["service"] == service and b["numbers"]])
        zenex_cnts = set(bot_settings.get("zenex_services", {}).get(service, {}).keys())
        stex_cnts  = set(bot_settings.get("stex_services",  {}).get(service, {}).keys())
        voltx_cnts = set(bot_settings.get("voltx_services", {}).get(service, {}).keys())
        nexus_cnts = set(bot_settings.get("nexus_services", {}).get(service, {}).keys())
        all_countries = local_cnts.union(zenex_cnts).union(stex_cnts).union(voltx_cnts).union(nexus_cnts)
        
        c_msg = bot_settings["custom_messages"].get("select_country", {})
        raw_txt = c_msg.get("text", "📌 Select a country for {service}:").replace("{service}", service)
        txt = render_body_text(raw_txt)
        
        flags_db = bot_settings.get("premium_flags", {})
        kb = []
        _cnt_btns = []
        for c in all_countries:
            emoji_id = "5780471598922337683" # Default flag
            for flag_code, flag_data in flags_db.items():
                iso = flag_data.get("iso", "").upper()
                name = flag_data.get("name", "").upper()
                if c.upper() == iso or c.upper() == name or c.upper() in name or name in c.upper():
                    if "id" in flag_data:
                        emoji_id = flag_data["id"]
                        break
            _cnt_btns.append({"text": f"{c}", "icon_custom_emoji_id": emoji_id, "callback_data": f"g_c_{service}_{c}", "style": "success"})
        for i in range(0, len(_cnt_btns), 2):
            kb.append(_cnt_btns[i:i+2])
        
        for b in c_msg.get("buttons", []): 
            b_copy = b.copy()
            if "style" not in b_copy: b_copy["style"] = "primary"
            kb.append([b_copy])
            
        kb.append([{"text": "Back", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "close_msg", "style": "danger"}])
        edit_message(chat_id, msg_id, txt, reply_markup={"inline_keyboard": kb})

    elif data.startswith("c_custom_"):
        # Custom Range — Change Number (no country filter check needed)
        now = time.time()
        if now - user_cooldowns.get(chat_id, 0) < bot_settings["cooldown"]:
            answer_callback(call["id"], f"⌛ Please wait {int(bot_settings['cooldown'] - (now - user_cooldowns.get(chat_id, 0)))}s.", show_alert=True)
            return
        user_cooldowns[chat_id] = now

        range_text = data[len("c_custom_"):]  # e.g. "236X", "22507XXX", or "880"
        query = range_text.split("X")[0] if "X" in range_text else range_text  # digit-only prefix

        expire_previous_number(chat_id)
        edit_message(chat_id, msg_id, render_body_text("⌛ <i>Finding new number...</i>"))

        def _change_custom(chat_id, query, range_text, msg_id):
            global total_assigned_stats
            req_count = bot_settings.get("num_req", 1)
            assigned_nums = []

            # Step 1: local stock
            found_indices = []
            for b_id, b_data in number_batches.items():
                for idx, n_obj in enumerate(b_data["numbers"]):
                    if n_obj["num"].replace("+", "").startswith(query) and chat_id not in n_obj.get("used_by", []):
                        found_indices.append((b_id, idx))
            if found_indices:
                random.shuffle(found_indices)
                for b_id, idx in found_indices[:req_count]:
                    n_obj = number_batches[b_id]["numbers"][idx]
                    assigned_nums.append(n_obj["num"])
                    n_obj.setdefault("used_by", []).append(chat_id)
                    batch_assigned_numbers[str(n_obj["num"]).replace("+","").strip()] = chat_id
                save_db()
            else:
                # Step 2: Zenex fallback
                zenex_keys = bot_settings.get("zenex_keys", [])
                while len(assigned_nums) < req_count:
                    num_str, number_id, used_key = _fetch_zenex_parallel(range_text, zenex_keys)
                    if not num_str: break
                    # Filter: number must start with digit prefix
                    clean_fetched = str(num_str).replace("+", "").replace(" ", "").replace("-", "")
                    if not clean_fetched.startswith(query): continue
                    assigned_nums.append(num_str)
                    zenex_assigned_numbers[num_str] = chat_id
                    total_assigned_stats += 1
                    if number_id and used_key:
                        threading.Thread(target=poll_zenex_otp, args=(number_id, num_str, chat_id, used_key), daemon=True).start()
                save_db()

            if not assigned_nums:
                edit_message(chat_id, msg_id, render_body_text(f"❌ No number found for range <b>{range_text}</b>!"))
                return

            flags_db = bot_settings.get("premium_flags", {})
            kb = []
            for num in assigned_nums:
                _, iso = get_flag_and_code(num)
                display_num = f"+{num}" if not str(num).startswith("+") else str(num)
                emoji_id = "5780471598922337783"
                for _, flag_data in flags_db.items():
                    if iso == flag_data.get("iso"):
                        if "id" in flag_data: emoji_id = flag_data["id"]; break
                kb.append([{"text": display_num, "icon_custom_emoji_id": emoji_id, "copy_text": {"text": display_num}, "style": "primary"}])
            kb.append([{"text": "Change Number", "icon_custom_emoji_id": "5377774889723798543", "callback_data": f"c_custom_{range_text}", "style": "danger"},
                       {"text": "OTP Group", "icon_custom_emoji_id": "6235727781427155894", "url": bot_settings.get("otp_link", "https://t.me"), "style": "primary"}])
            kb.append([{"text": "Expire Number", "icon_custom_emoji_id": "5420130255174145507", "callback_data": "expire_num", "style": "danger"}])

            txt = render_body_text(
                f"{PEM['ok']} <b>নাম্বার নিছেন ভালো কথা অটিপি আনা লাগবে</b>\n\n"
                f"🎯 <b>Range:</b> {range_text}"
            )
            try:
                edit_message(chat_id, msg_id, txt, reply_markup={"inline_keyboard": kb})
                user_active_sessions[chat_id] = {"msg_id": msg_id, "nums": assigned_nums, "service": "Custom", "country": range_text, "reply_markup": {"inline_keyboard": kb}}
            except:
                res = send_message(chat_id, txt, reply_markup={"inline_keyboard": kb})
                new_id = res.get("result", {}).get("message_id")
                if new_id:
                    user_active_sessions[chat_id] = {"msg_id": new_id, "nums": assigned_nums, "service": "Custom", "country": range_text, "reply_markup": {"inline_keyboard": kb}}

        threading.Thread(target=_change_custom, args=(chat_id, query, range_text, msg_id), daemon=True).start()
        return

    elif data.startswith("g_c_") or data.startswith("c_n_"):
        # ১. গ্লোবাল কুলডাউন চেক (সকল নাম্বার মেথডের জন্য)
        now = time.time()
        if now - user_cooldowns.get(chat_id, 0) < bot_settings["cooldown"]:
            answer_callback(call["id"], f"⌛ Please wait {int(bot_settings['cooldown'] - (now - user_cooldowns.get(chat_id, 0)))}s.", show_alert=True)
            return
        
        # কুলডাউন আপডেট
        user_cooldowns[chat_id] = now
        
        # আগের নাম্বার এক্সপায়ার করা
        expire_previous_number(chat_id)

        # যদি সার্চ নাম্বার থেকে আসে
        if data.startswith("c_n_s_"):
            parts_s = data.split("_", 4)
            
            query = parts_s[3] if len(parts_s) > 3 else ""
            service_from_cb = parts_s[4] if len(parts_s) > 4 else None
            
            zenex_allowed_cb = bot_settings.get("zenex_stex_search_countries", [])
            is_zenex_allowed_cb = any(query.startswith(c) for c in zenex_allowed_cb) if zenex_allowed_cb else False
            
            if not is_zenex_allowed_cb:
                answer_callback(call["id"], "❌ This country code is not allowed for search!", show_alert=True)
                return
            
            edit_message(chat_id, msg_id, render_body_text("⌛ <i>Processing... Finding Number...</i>"))
            wait_msg_id = msg_id
            
            found_indices = []
            for b_id, b_data in number_batches.items():
                for idx, n_obj in enumerate(b_data["numbers"]):
                    if n_obj["num"].replace("+", "").startswith(query) and chat_id not in n_obj.get("used_by", []):
                        found_indices.append((b_id, idx))
            
            fetched_nums = []
            if not found_indices:
                api_found = False
                if is_zenex_allowed_cb:
                    # সব Zenex key parallel এ try করা হয়
                    zenex_keys = bot_settings.get("zenex_keys", [])
                    req_count_cb = bot_settings.get("num_req", 1)
                    while len(fetched_nums) < req_count_cb:
                        num_str, number_id, used_key = _fetch_zenex_parallel(query, zenex_keys)
                        if not num_str: break
                        fetched_nums.append(num_str)
                        zenex_assigned_numbers[num_str] = chat_id
                        api_found = True
                        total_assigned_stats += 1
                        if number_id and used_key:
                            threading.Thread(target=poll_zenex_otp, args=(number_id, num_str, chat_id, used_key), daemon=True).start()
                if not api_found:
                    answer_callback(call["id"], "❌ Number out of stock!", show_alert=True)
                    delete_message(chat_id, wait_msg_id)
                    return
                save_db()
            else:
                random.shuffle(found_indices)
                for b_id, idx in found_indices:
                    if len(fetched_nums) >= bot_settings.get("num_req", 1): break
                    n_obj = number_batches[b_id]["numbers"][idx]
                    num_str = n_obj["num"]
                    fetched_nums.append(num_str)
                    batch_assigned_numbers[str(num_str).replace("+","").strip()] = chat_id
                    n_obj["shares"] += 1
                    n_obj["used_by"].append(chat_id)
                    total_assigned_stats += 1
                    if n_obj["shares"] >= bot_settings.get("num_share", 1):
                        n_obj["to_remove"] = True
                        used_numbers_list.append(num_str)
                for b_id in number_batches:
                    number_batches[b_id]["numbers"] = [n for n in number_batches[b_id]["numbers"] if not n.get("to_remove")]
                save_db()
                
            kb = []
            if service_from_cb:
                app_full_name, _ = get_service_info_html(service_from_cb)
                emoji_id_srv = "5337302974806922068"
                for app_key, app_data in bot_settings.get("premium_apps", {}).items():
                    if service_from_cb.upper() == app_key or service_from_cb.upper() in app_key or app_key in service_from_cb.upper():
                        if "id" in app_data: emoji_id_srv = app_data["id"]; break
                kb.append([{"text": f"{app_full_name}", "icon_custom_emoji_id": emoji_id_srv, "callback_data": "ignore", "style": "success"}])

            flags_db = bot_settings.get("premium_flags", {})
            for num in fetched_nums:
                _, iso = get_flag_and_code(num)
                display_num = f"+{num}" if not str(num).startswith("+") else str(num)
                emoji_id = "5780471598922337683"
                for flag_code, flag_data in flags_db.items():
                    if iso == flag_data.get("iso"):
                        if "id" in flag_data: emoji_id = flag_data["id"]; break
                kb.append([{"text": f"{display_num}", "icon_custom_emoji_id": WAITING_NUMBER_EMOJI_ID, "copy_text": {"text": display_num}, "style": "primary"}])
            
            srv_ext = f"_{service_from_cb}" if service_from_cb else ""
            kb.append([{"text": "Change Number", "icon_custom_emoji_id": "5377774889723798543", "callback_data": f"c_n_s_{query}{srv_ext}", "style": "danger"},
                       {"text": "OTP Group", "icon_custom_emoji_id": "6235727781427155894", "url": bot_settings["otp_link"], "style": "primary"}])
            
            c_btns = bot_settings["custom_messages"].get("search_number", {}).get("buttons", [])
            for c_b in c_btns: 
                b_copy = c_b.copy()
                if "style" not in b_copy: b_copy["style"] = "primary"
                kb.append([b_copy])
            back_cb = f"g_s_{service_from_cb}" if service_from_cb else "close_msg"
            kb.append([{"text": "Back to Country", "icon_custom_emoji_id": "5253744033875915388", "callback_data": back_cb, "style": "danger"}])
            
            srvc_label = service_from_cb if service_from_cb else f"+{query}"
            cb_header = render_body_text(
                f"{PEM['ok']} <b>নাম্বার নিছেন ভালো কথা অটিপি আনা লাগবে</b>\n\n"
                f"🔍 <b>Search:</b> {srvc_label}"
            )
            edit_message(chat_id, wait_msg_id, cb_header, reply_markup={"inline_keyboard": kb})
            user_active_sessions[chat_id] = {"msg_id": wait_msg_id, "nums": fetched_nums, "reply_markup": {"inline_keyboard": kb}}
            return

        # যদি আপলোড করা বা সার্ভিস থেকে আসে
        parts = data.split("_")
        service = parts[2]
        country = parts[3]

        available_indices = []
        # Check Local Stock First
        for b_id, b_data in number_batches.items():
            if b_data["service"] == service and b_data["country"] == country:
                for idx, n_obj in enumerate(b_data["numbers"]):
                    if chat_id not in n_obj.get("used_by", []):
                        available_indices.append((b_id, idx))

        # IF NO LOCAL STOCK, Check Voltx → Zenex → Stex Services
        if not available_indices:
            voltx_srv_data = bot_settings.get("voltx_services", {}).get(service, {}).get(country)
            zenex_srv_data = bot_settings.get("zenex_services", {}).get(service, {}).get(country)
            stex_srv_data = bot_settings.get("stex_services", {}).get(service, {}).get(country)
            nexus_srv_data = bot_settings.get("nexus_services", {}).get(service, {}).get(country)

            target_range = None
            is_zenex = False
            is_voltx = False
            is_stex = False
            is_nexus = False

            if voltx_srv_data and len(voltx_srv_data) > 0:
                target_range = random.choice(voltx_srv_data)
                is_voltx = True
            elif zenex_srv_data and len(zenex_srv_data) > 0:
                target_range = random.choice(zenex_srv_data)
                is_zenex = True
            elif stex_srv_data and len(stex_srv_data) > 0:
                target_range = random.choice(stex_srv_data)
                is_stex = True
            elif nexus_srv_data and len(nexus_srv_data) > 0:
                target_range = random.choice(nexus_srv_data)
                is_nexus = True

            if target_range:
                user_cooldowns[chat_id] = 0
                def _show_fetched_numbers(fetched_nums, service, country, msg_id, chat_id, panel_label):
                    """Fetched numbers কে inline keyboard হিসেবে দেখায়।"""
                    save_db()
                    app_full_name, prem_app_html = get_service_info_html(service)
                    emoji_id_s = "5337302974806922068"
                    apps_db = bot_settings.get("premium_apps", {})
                    for app_key, app_data in apps_db.items():
                        if service.upper() == app_key or service.upper() in app_key or app_key in service.upper():
                            if "id" in app_data: emoji_id_s = app_data["id"]; break
                    kb = [[{"text": f"{app_full_name}", "icon_custom_emoji_id": emoji_id_s, "callback_data": "ignore", "style": "success"}]]
                    flags_db = bot_settings.get("premium_flags", {})
                    for num in fetched_nums:
                        clean_num = str(num).replace("+", "").strip()
                        _, iso = get_flag_and_code(clean_num)
                        display_num = f"+{clean_num}"
                        emoji_id_f = "5780471598922337683"
                        for flag_code, flag_data in flags_db.items():
                            if iso == flag_data.get("iso"):
                                if "id" in flag_data: emoji_id_f = flag_data["id"]; break
                        kb.append([{"text": f"{display_num}", "icon_custom_emoji_id": WAITING_NUMBER_EMOJI_ID, "copy_text": {"text": display_num}, "style": "primary"}])
                    kb.append([{"text": "Change Number", "icon_custom_emoji_id": "5377774889723798543", "callback_data": f"g_c_{service}_{country}", "style": "danger"},
                               {"text": "OTP Group", "icon_custom_emoji_id": "6235727781427155894", "url": bot_settings.get("otp_link", ""), "style": "primary"}])
                    c_btns = bot_settings["custom_messages"].get("get_number", {}).get("buttons", [])
                    for c_b in c_btns:
                        b_copy = c_b.copy()
                        if "style" not in b_copy: b_copy["style"] = "primary"
                        kb.append([b_copy])
                    kb.append([{"text": "Back to Country", "icon_custom_emoji_id": "5253744033875915388", "callback_data": f"g_s_{service}", "style": "danger"}])
                    header_txt = render_body_text(
                        f"{PEM['ok']} <b>নাম্বার নিছেন ভালো কথা অটিপি আনা লাগবে</b>\n\n"
                        f"📱 <b>Service:</b> {prem_app_html} {app_full_name}"
                    )
                    edit_message(chat_id, msg_id, header_txt, reply_markup={"inline_keyboard": kb})
                    user_active_sessions[chat_id] = {"msg_id": msg_id, "nums": fetched_nums, "reply_markup": {"inline_keyboard": kb}}

                edit_message(chat_id, msg_id, render_body_text("⌛ <i>VIP নম্বর দেওয়া হচ্ছে...</i>"))
                fetched_nums = []
                req_count = bot_settings.get("num_req", 1)

                if is_voltx:
                    voltx_keys = bot_settings.get("voltx_keys", [])
                    while len(fetched_nums) < req_count:
                        num_str, _ = _fetch_voltx_parallel(target_range, voltx_keys)
                        if not num_str: break
                        fetched_nums.append(num_str)
                        voltx_assigned_numbers[num_str] = chat_id
                        total_assigned_stats += 1
                    if not fetched_nums:
                        answer_callback(call["id"], "❌ Voltx number পাওয়া যায়নি!", show_alert=True)
                        return
                    _show_fetched_numbers(fetched_nums, service, country, msg_id, chat_id, "Voltx")
                    return

                elif is_zenex:
                    zenex_keys = bot_settings.get("zenex_keys", [])
                    while len(fetched_nums) < req_count:
                        num_str, number_id, used_key = _fetch_zenex_parallel(target_range, zenex_keys)
                        if not num_str: break
                        fetched_nums.append(num_str)
                        zenex_assigned_numbers[num_str] = chat_id
                        total_assigned_stats += 1
                        if number_id and used_key:
                            threading.Thread(target=poll_zenex_otp, args=(number_id, num_str, chat_id, used_key), daemon=True).start()
                    if not fetched_nums:
                        answer_callback(call["id"], "❌ Zenex number পাওয়া যায়নি! সব API key চেষ্টা করা হয়েছে।", show_alert=True)
                        return
                    _show_fetched_numbers(fetched_nums, service, country, msg_id, chat_id, "Zenex")
                    return

                elif is_stex:
                    stex_keys = bot_settings.get("stex_keys", [])
                    while len(fetched_nums) < req_count:
                        num_str, _ = _fetch_stex_parallel(target_range, stex_keys)
                        if not num_str: break
                        fetched_nums.append(num_str)
                        stex_assigned_numbers[num_str] = chat_id
                        total_assigned_stats += 1
                    if not fetched_nums:
                        answer_callback(call["id"], "❌ Stex number পাওয়া যায়নি!", show_alert=True)
                        return
                    _show_fetched_numbers(fetched_nums, service, country, msg_id, chat_id, "Stex")
                    return

                elif is_nexus:
                    nexus_keys = bot_settings.get("nexus_keys", [])
                    if not nexus_keys:
                        answer_callback(call["id"], "❌ Nexus API key configure করা নেই! Admin-কে জানান।", show_alert=True)
                        return
                    if not bot_settings.get("nexus_panel_on", False):
                        answer_callback(call["id"], "❌ Nexus panel এখন বন্ধ আছে! Admin-কে জানান।", show_alert=True)
                        return
                    # service_sid: Nexus API-তে service identifier (e.g. wa, tg, fb)
                    # nexus_services এ range হিসেবে যা দেওয়া আছে সেটাই range, service টা sid
                    service_sid = service.lower().strip()
                    edit_message(chat_id, msg_id, render_body_text("⌛ <i>VIP NUMBER PROVIDE</i>"))
                    while len(fetched_nums) < req_count:
                        num_str, number_id, used_key = _fetch_nexus_parallel(target_range, service_sid, nexus_keys)
                        if not num_str: break
                        fetched_nums.append(num_str)
                        nexus_assigned_numbers[num_str] = chat_id
                        total_assigned_stats += 1
                        if number_id and used_key:
                            threading.Thread(target=poll_nexus_otp, args=(number_id, num_str, chat_id, used_key), daemon=True).start()
                    if not fetched_nums:
                        answer_callback(call["id"], "❌ Nexus number পাওয়া যায়নি! পরে আবার চেষ্টা করুন।", show_alert=True)
                        return
                    save_db()
                    _show_fetched_numbers(fetched_nums, service, country, msg_id, chat_id, "Nexus")
                    return

            else:
                answer_callback(call["id"], "❌ Number out of stock or range missing!", show_alert=True)
                if data.startswith("c_n_"): delete_message(chat_id, msg_id)
                return

        random.shuffle(available_indices)
        
        fetched_nums = []
        for b_id, idx in available_indices:
            if len(fetched_nums) >= bot_settings["num_req"]: break
            n_obj = number_batches[b_id]["numbers"][idx]
            
            fetched_nums.append(n_obj["num"])
            batch_assigned_numbers[str(n_obj["num"]).replace("+","").strip()] = chat_id
            n_obj["shares"] += 1
            n_obj["used_by"].append(chat_id)
            total_assigned_stats += 1
            
            if n_obj["shares"] >= bot_settings.get("num_share", 1):
                n_obj["to_remove"] = True
                used_numbers_list.append(n_obj["num"])

        for b_id in number_batches:
            number_batches[b_id]["numbers"] = [n for n in number_batches[b_id]["numbers"] if not n.get("to_remove")]
        save_db()

        if not fetched_nums:
            answer_callback(call["id"], "❌ You have already taken all numbers or stock is empty!", show_alert=True)
            if data.startswith("c_n_"): delete_message(chat_id, msg_id)
            return

        app_full_name, _ = get_service_info_html(service)
        emoji_id = "5337302974806922068"
        apps_db = bot_settings.get("premium_apps", {})
        for app_key, app_data in apps_db.items():
            if service.upper() == app_key or service.upper() in app_key or app_key in service.upper():
                if "id" in app_data:
                    emoji_id = app_data["id"]
                    break
        kb = [[{"text": f"{app_full_name}", "icon_custom_emoji_id": emoji_id, "callback_data": "ignore", "style": "success"}]]
        
        flags_db = bot_settings.get("premium_flags", {})
        for num in fetched_nums:
            _, iso = get_flag_and_code(num)
            display_num = f"+{num}" if not num.startswith("+") else num
            
            emoji_id = "5780471598922337683" # Default Flag
            for flag_code, flag_data in flags_db.items():
                if iso == flag_data.get("iso"):
                    if "id" in flag_data: emoji_id = flag_data["id"]
                    break
            kb.append([{"text": f"{display_num}", "icon_custom_emoji_id": WAITING_NUMBER_EMOJI_ID, "copy_text": {"text": display_num}, "style": "primary"}])
            
        kb.append([{"text": "Change Number", "icon_custom_emoji_id": "5377774889723798543", "callback_data": f"c_n_{service}_{country}", "style": "danger"},
                   {"text": "OTP Group", "icon_custom_emoji_id": "6235727781427155894", "url": bot_settings["otp_link"], "style": "primary"}])
                   
        c_btns = bot_settings["custom_messages"].get("get_number", {}).get("buttons", [])
        for c_b in c_btns: 
            b_copy = c_b.copy()
            if "style" not in b_copy: b_copy["style"] = "primary"
            kb.append([b_copy])
            
        kb.append([{"text": "Back to Country", "icon_custom_emoji_id": "5253744033875915388", "callback_data": f"g_s_{service}", "style": "danger"}])
        
        _, _pfx = get_service_info_html(service)
        text_numbers = render_body_text(
            f"{PEM['ok']} <b>নাম্বার নিছেন ভালো কথা অটিপি আনা লাগবে</b>\n\n"
            f"📱 <b>Service:</b> {_pfx} {app_full_name}"
        )
        # সবসময় মেসেজ ইডিট করবে (Change Number করলেও নতুন মেসেজ আসবে না)
        try:
            edit_message(chat_id, msg_id, text_numbers, reply_markup={"inline_keyboard": kb})
            user_active_sessions[chat_id] = {"msg_id": msg_id, "nums": fetched_nums, "reply_markup": {"inline_keyboard": kb}}
        except:
            # যদি মেসেজ ইডিট করা সম্ভব না হয় (যেমন অনেক আগের মেসেজ), তবে নতুন মেসেজ দিবে
            msg_res = send_message(chat_id, text_numbers, reply_markup={"inline_keyboard": kb})
            if msg_res and "result" in msg_res:
                user_active_sessions[chat_id] = {"msg_id": msg_res["result"]["message_id"], "nums": fetched_nums, "reply_markup": {"inline_keyboard": kb}}
    elif data.startswith("wapp_") or data.startswith("wrej_"):
        # অ্যাডমিন চেক (User ID চেক করতে হবে)
        user_id_clicked = call["from"]["id"]
        if not is_admin(user_id_clicked):
            answer_callback(call["id"], "🚫 Only Bot Admins can process withdrawals!", show_alert=True)
            return
            
        action = "APPROVE" if data.startswith("wapp_") else "REJECT"
        req_id = data.replace("wapp_", "").replace("wrej_", "")
        
        if req_id in pending_withdrawals:
            req_data = pending_withdrawals[req_id]
            u_id, amt = req_data["user_id"], req_data["amount"]
            num = req_data["number"]
            full_name = req_data.get("full_name", u_id)
            
            if action == "APPROVE" and len(num) >= 7:
                masked_num = f"{num[:4]}❖XPNL❖{num[-3:]}"
            else:
                masked_num = num
            
            status_text = "APPROVED" if action == "APPROVE" else "REJECTED"

            if action == "REJECT":
                update_balance(u_id, amt)
                send_message(u_id, render_body_text(f"❌ Your {amt} TK withdrawal request was rejected. Balance refunded."))
            else:
                send_message(u_id, render_body_text(f"{PEM['ok']} Your {amt} TK withdrawal request has been paid successfully!"))

            if db:
                try: db.collection('withdrawals').document(req_id).update({"status": "approved" if action == "APPROVE" else "rejected"})
                except: pass

            del pending_withdrawals[req_id]
            answer_callback(call["id"], f"✅ {status_text}!", show_alert=False)

            # Admin panel pending list থেকে action নিলে → list refresh করো
            # notification message থেকে action নিলে → message update করো
            if not pending_withdrawals:
                edit_message(chat_id, msg_id,
                    render_body_text(f"💰 <b>Pending Withdrawals</b>\n\n✅ সব withdrawal process হয়ে গেছে!"),
                    reply_markup={"inline_keyboard": [[{"text": "🔙 Back to Admin", "icon_custom_emoji_id": "5267490665117275166", "callback_data": "back_to_admin", "style": "primary"}]]})
            else:
                # বাকি pending গুলো দেখাও
                kb2 = []
                txt2 = "💰 <b>PENDING WITHDRAWALS</b>\n━━━━━━━━━━━━━━━\n\n"
                for i, (rid, req) in enumerate(list(pending_withdrawals.items()), 1):
                    u2   = req.get("user_id", "?")
                    a2   = req.get("amount", 0)
                    m2   = req.get("method", "?")
                    n2   = req.get("number", "?")
                    nm2  = req.get("full_name", str(u2))
                    txt2 += (f"{i}. 👤 <a href='tg://user?id={u2}'>{nm2}</a>\n"
                             f"   💳 {a2} ৳ | 🏦 {m2}\n"
                             f"   📱 <code>{n2}</code>\n"
                             f"   🧾 <code>{rid}</code>\n\n")
                    kb2.append([
                        {"text": f"✅ APPROVE #{i}", "icon_custom_emoji_id": "5352694861990501856", "callback_data": f"wapp_{rid}", "style": "success"},
                        {"text": f"❌ REJECT #{i}",  "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"wrej_{rid}", "style": "danger"}
                    ])
                kb2.append([{"text": "🔄 Refresh", "icon_custom_emoji_id": "5420155432272438703", "callback_data": "adm_pending_w", "style": "primary"},
                            {"text": "🔙 Back",    "icon_custom_emoji_id": "5267490665117275166", "callback_data": "back_to_admin", "style": "danger"}])
                try:
                    edit_message(chat_id, msg_id, render_body_text(txt2), reply_markup={"inline_keyboard": kb2})
                except:
                    pass
        else:
            answer_callback(call["id"], "❌ Request already processed!", show_alert=True)

    elif data == "bulk_getotp":
        # Manual OTP check for bulk session numbers
        session = bulk_sessions.get(chat_id)
        if not session:
            answer_callback(call["id"], "❌ কোনো active bulk session নেই! নতুন করে bulk request করুন।", show_alert=True)
            return

        num_to_ids = session.get("num_to_ids", {})
        if not num_to_ids:
            answer_callback(call["id"], "ℹ️ এই bulk-এর numbers এ OTP tracking নেই।", show_alert=True)
            return

        answer_callback(call["id"], "⌛ OTP চেক হচ্ছে...")

        def _bulk_otp_check():
            found_otps = []
            for num_str, (number_id, api_key) in list(num_to_ids.items()):
                try:
                    headers = {"mapikey": api_key, "Content-Type": "application/json"}
                    res = requests.get(f"{ZENEX_BASE_URL}/v1/numbers/{number_id}/sms", headers=headers, timeout=8)
                    data_r = res.json()
                    if data_r.get("success") and data_r.get("otp"):
                        otp = str(data_r["otp"])
                        msg_txt = data_r.get("message", f"Code: {otp}")
                        extracted = extract_otp_code(msg_txt)
                        if extracted and len(extracted) > len(otp):
                            otp = extracted
                        detected = detect_service(msg_txt)
                        raw_app = data_r.get("service", "")
                        if detected:
                            app_name = detected
                        elif raw_app and raw_app.lower() not in ["zenex service", "zenex", ""]:
                            app_name = raw_app
                        else:
                            app_name = "OTP Service"
                        display_num = f"+{num_str}" if not str(num_str).startswith("+") else str(num_str)
                        found_otps.append((display_num, app_name or "Unknown", otp))
                except:
                    pass

            if not found_otps:
                send_message(chat_id, render_body_text(
                    "📭 <b>কোনো OTP পাওয়া যায়নি</b>\n"
                    "━━━━━━━━━━━━\n"
                    "এখনো কোনো number এ OTP আসেনি।\n"
                    "OTP আসলে <b>স্বয়ংক্রিয়ভাবে</b> inbox এ পাঠানো হবে।"
                ), reply_markup={"inline_keyboard": [[
                    {"text": "Get OTP", "icon_custom_emoji_id": "5251227707026470504", "callback_data": "bulk_getotp", "style": "success"}
                ]]})
            else:
                lines = ""
                for display_num, app_name, otp in found_otps[:20]:
                    lines += f"📱 <code>{display_num}</code>\n🔑 <b>{otp}</b> — {app_name}\n\n"
                send_message(chat_id, render_body_text(
                    f"📬 <b>OTP পাওয়া গেছে ({len(found_otps)} টি)</b>\n"
                    f"━━━━━━━━━━━━\n"
                    f"{lines}"
                ), reply_markup={"inline_keyboard": [[
                    {"text": "Refresh OTP", "icon_custom_emoji_id": "5251227707026470504", "callback_data": "bulk_getotp", "style": "success"}
                ]]})

        threading.Thread(target=_bulk_otp_check, daemon=True).start()

    elif data.startswith("bapp_") or data.startswith("brej_"):
        # Bulk number approve / reject (admin only)
        user_id_clicked = call["from"]["id"]
        if not is_admin(user_id_clicked):
            answer_callback(call["id"], "🚫 Only Bot Admins can approve bulk requests!", show_alert=True)
            return

        action = "APPROVE" if data.startswith("bapp_") else "REJECT"
        req_id = data.replace("bapp_", "").replace("brej_", "")

        if req_id not in pending_bulk_requests:
            answer_callback(call["id"], "❌ Request already processed!", show_alert=True)
            return

        req = pending_bulk_requests.pop(req_id)
        u_id      = req["user_id"]
        service   = req["service"]
        country   = req["country"]
        full_name = req["full_name"]
        ranges    = req["ranges"]

        # Update admin message
        status_text   = "APPROVED ✅" if action == "APPROVE" else "REJECTED ❌"
        emoji_icon_id = "5352694861990501856" if action == "APPROVE" else "5420130255174145507"
        new_admin_txt = (
            f"📦 <b>BULK REQUEST {status_text}</b>\n\n"
            f"👤 <b>USER:</b> <a href='tg://user?id={u_id}'>{full_name}</a> (<code>{u_id}</code>)\n"
            f"📱 <b>SERVICE:</b> {service}\n"
            f"🌍 <b>COUNTRY:</b> {country}\n"
            f"🔢 <b>AMOUNT:</b> 100 numbers\n\n"
            f"🧾 <b>REQ ID:</b> {req_id}"
        )
        done_kb = {"inline_keyboard": [[{"text": status_text, "icon_custom_emoji_id": emoji_icon_id, "callback_data": "ignore", "style": "success" if action == "APPROVE" else "danger"}]]}
        edit_message(chat_id, msg_id, render_body_text(new_admin_txt), reply_markup=done_kb)

        if action == "REJECT":
            send_message(u_id, render_body_text(
                f"❌ <b>Bulk Request Rejected</b>\n"
                f"━━━━━━━━━━━━\n"
                f"🧾 <b>Req ID:</b> <code>{req_id}</code>\n"
                f"📱 <b>Service:</b> {service} / {country}\n\n"
                f"Admin আপনার bulk request reject করেছেন।"
            ))
        else:
            # Approved → fetch numbers in background and send to user
            send_message(u_id, render_body_text(
                f"✅ <b>Bulk Request Approved!</b>\n"
                f"━━━━━━━━━━━━\n"
                f"🧾 <b>Req ID:</b> <code>{req_id}</code>\n"
                f"📱 <b>Service:</b> {service} / {country}\n\n"
                f"⌛ আপনার 100টি number fetch হচ্ছে, একটু অপেক্ষা করুন..."
            ))

            def _do_approved_bulk():
                global total_assigned_stats
                all_nums = []
                num_to_ids = {}

                # Expire any previous active session for this user before new bulk
                expire_previous_number(u_id)

                # Local stock first
                for b_id, b_data in number_batches.items():
                    if b_data.get("service") == service and b_data.get("country") == country:
                        for n_obj in b_data["numbers"]:
                            if u_id not in n_obj.get("used_by", []):
                                all_nums.append(n_obj["num"])
                            if len(all_nums) >= 100:
                                break
                    if len(all_nums) >= 100:
                        break

                # ── Switching fallback: Stex → VoltexSMS → Zenex ──────────────
                if len(all_nums) < 100:
                    needed    = 100 - len(all_nums)
                    seen_nums = set(all_nums)

                    # derive a query_prefix from configured zenex ranges (e.g. "880XXXXXXXX" → "880")
                    query_prefix = ""
                    if ranges:
                        rng0 = ranges[0].replace("+", "").strip()
                        query_prefix = rng0.split("X")[0] if "X" in rng0 else rng0

                    has_any_api = (bot_settings.get("stex_keys") or
                                   bot_settings.get("voltx_keys") or
                                   bot_settings.get("zenex_keys"))

                    if has_any_api and query_prefix:
                        def _fetch_one_smart(_):
                            zenex_range = random.choice(ranges) if ranges else query_prefix
                            return _smart_fetch_one(query_prefix, zenex_range, u_id)

                        with ThreadPoolExecutor(max_workers=min(20, needed)) as ex:
                            futs = [ex.submit(_fetch_one_smart, i) for i in range(needed * 3)]
                            try:
                                for f in as_completed(futs, timeout=180):
                                    try:
                                        num_str, source, number_id, used_key = f.result()
                                        if num_str and num_str not in seen_nums:
                                            seen_nums.add(num_str)
                                            all_nums.append(num_str)
                                            total_assigned_stats += 1
                                            if source == "zenex" and number_id and used_key:
                                                num_to_ids[num_str] = (number_id, used_key)
                                            if len(all_nums) >= 100:
                                                break
                                    except Exception:
                                        pass
                            except TimeoutError:
                                # Partial results collected — continue with what we have
                                pass

                if not all_nums:
                    send_message(u_id, render_body_text(
                        f"❌ দুঃখিত, <b>{service} / {country}</b> এর জন্য কোনো number পাওয়া যায়নি!\nAdmin এর সাথে যোগাযোগ করুন।"
                    ))
                    return

                for num_str, (number_id, used_key) in num_to_ids.items():
                    threading.Thread(target=poll_zenex_otp, args=(number_id, num_str, u_id, used_key), daemon=True).start()

                save_db()
                final_nums  = all_nums[:100]

                # Save bulk session for Get OTP button
                bulk_sessions[u_id] = {
                    "nums": final_nums,
                    "num_to_ids": {n: (nid, key) for n, (nid, key) in num_to_ids.items() if n in final_nums},
                    "service": service,
                    "country": country
                }

                file_bytes  = "\n".join(final_nums).encode("utf-8")
                send_document(u_id, f"bulk_{service}_{country}_numbers.txt", file_bytes)

                delivery_kb = [[
                    {"text": "Get OTP", "icon_custom_emoji_id": "5251227707026470504", "callback_data": "bulk_getotp", "style": "success"}
                ]]
                send_message(u_id, render_body_text(
                    f"📦 <b>BULK NUMBERS DELIVERED</b>\n"
                    f"━━━━━━━━━━━━\n"
                    f"✅ মোট: <b>{len(final_nums)}</b> টি নম্বর\n"
                    f"📄 উপরের TXT ফাইলটি ডাউনলোড করুন\n"
                    f"🔔 কোনো number এ OTP আসলে <b>Get OTP</b> চাপুন"
                ), reply_markup={"inline_keyboard": delivery_kb})

            threading.Thread(target=_do_approved_bulk, daemon=True).start()

# ==========================================
def _parse_zenex_getnum(resp_data):
    """
    Zenex API response নানা format এ আসতে পারে।
    এই function সব common format থেকে (number, number_id) বের করে দেয়।
    Returns (num_str, number_id) or (None, None) if not found.
    """
    if not isinstance(resp_data, dict):
        return None, None

    def _extract_num(d):
        return (d.get("full_number") or d.get("no_plus_number") or
                d.get("number") or d.get("num") or
                d.get("phone") or d.get("mobile") or d.get("copy"))

    def _extract_nid(d):
        return d.get("number_id") or d.get("id") or d.get("numId")

    # Format 1/2/3: top-level success flag
    success = resp_data.get("success") or resp_data.get("status") == "success" or resp_data.get("ok")
    if success:
        num = _extract_num(resp_data)
        if num:
            return str(num).replace("+", ""), _extract_nid(resp_data)

    # Format 4: {"data": {"full_number"|"number"|..., "id"|...}}
    data_block = resp_data.get("data")
    if isinstance(data_block, dict):
        num = _extract_num(data_block)
        if num:
            return str(num).replace("+", ""), _extract_nid(data_block)
    elif isinstance(data_block, list) and data_block:
        first = data_block[0] if isinstance(data_block[0], dict) else {}
        num = _extract_num(first)
        if num:
            return str(num).replace("+", ""), _extract_nid(first)

    # Format 5: top-level response IS the number object
    num = _extract_num(resp_data)
    if num and str(num).replace("+", "").isdigit():
        return str(num).replace("+", ""), _extract_nid(resp_data)

    return None, None


def poll_zenex_otp(number_id, num_str, owner_id, api_key):
    headers = {"mapikey": api_key, "Content-Type": "application/json"}
    for _ in range(150):
        try:
            res = requests.get(f"{ZENEX_BASE_URL}/v1/numbers/{number_id}/sms", headers=headers, timeout=10)
            data = res.json()
            if data.get("success") and data.get("otp"):
                otp = str(data["otp"])
                msg_text = data.get("message", f"Your code is {otp}")
                extracted_otp = extract_otp_code(msg_text)
                if extracted_otp and len(extracted_otp) > len(otp):
                    otp = extracted_otp
                detected_app = detect_service(msg_text)
                raw_app = data.get("service", "")
                if detected_app:
                    app_name = detected_app
                elif raw_app and raw_app.lower() not in ["zenex service", "zenex", ""]:
                    app_name = raw_app
                else:
                    app_name = "OTP Service"
                unique_id = f"ZENEX_POLL_{number_id}_{otp}"
                if unique_id not in processed_otps:
                    _safe_add_otp(unique_id)
                    char, iso = get_flag_and_code(num_str)
                    app_full_name, prem_app_html = get_service_info_html(app_name, msg_text)
                    global recent_traffic
                    current_time = time.time()
                    recent_traffic = [t for t in recent_traffic if current_time - t.get("time", 0) <= 3600]
                    recent_traffic.append({"service": app_full_name, "iso": iso, "flag": char, "number": num_str, "time": current_time})
                    save_local_db()
                    display_num = f"+{num_str}" if not str(num_str).startswith("+") else str(num_str)
                    masked = mask_number(display_num)
                    lang = detect_language(msg_text)
                    display_msg = render_body_text(f"{get_flag_info_html(iso) if iso else char} {get_country_name(iso)} {prem_app_html} {display_num}")
                    _fw_send_otp(bot_settings.get("fw_groups", []), app_full_name, prem_app_html, char, iso, display_num, lang, otp)
                    reward, reward_on = get_service_reward(app_full_name, owner_id)
                    if reward > 0 and reward_on:
                        update_balance(owner_id, reward)
                    _user_send_otp(owner_id, char, iso, prem_app_html, display_num, otp, reward if reward_on else 0, reward_on)
                    increment_total_otps(owner_id)
                break
        except: pass
        time.sleep(1)

def poll_nexus_otp(number_id, num_str, owner_id, api_key):
    """Nexus-X number এর OTP poll করে — GET /api/v1/numbers/{id}
    Status 'success' এবং otps non-empty হলে user-কে OTP পাঠায়।"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    for _ in range(150):  # ~10 মিনিট (4s interval × 150)
        try:
            res = requests.get(
                f"https://v2.nexus-x.site/api/v1/numbers/{number_id}",
                headers=headers, timeout=10
            )
            if res.status_code != 200:
                time.sleep(4)
                continue
            data = res.json()
            status = data.get("status", "")
            if status in ("failed", "expired"):
                break
            otps = data.get("otps", [])
            if status == "success" and otps:
                otp_item = otps[0]
                msg_text = (
                    otp_item.get("body") or otp_item.get("text") or
                    otp_item.get("full_text") or otp_item.get("console") or ""
                ).strip()
                sender = otp_item.get("sender", "")
                service_raw = (
                    data.get("service") or data.get("access") or data.get("sid") or ""
                )
                otp = extract_otp_code(msg_text)
                if not otp:
                    break
                # nexus_panel_listener এর মতো একই unique_id format ব্যবহার করি
                # যাতে listener আগে fire করলে poll block হয়, বা poll আগে হলে listener block হয়
                otp_item_id = otp_item.get("id", "")
                num_clean = str(num_str).replace("+", "").replace(" ", "").replace("-", "").strip()
                unique_id = f"NEXUS_{num_clean}_{otp}_{otp_item_id}"
                if not _safe_add_otp(unique_id):
                    break
                char, iso = get_flag_and_code(num_str)
                app_full_name, prem_app_html = get_service_info_html(sender or service_raw, msg_text)
                global recent_traffic
                current_time = time.time()
                recent_traffic = [t for t in recent_traffic if current_time - t.get("time", 0) <= 3600]
                recent_traffic.append({"service": app_full_name, "iso": iso, "flag": char, "number": num_str, "time": current_time})
                save_local_db()
                display_num = f"+{num_str}" if not str(num_str).startswith("+") else str(num_str)
                lang = detect_language(msg_text)
                _fw_send_otp(bot_settings.get("fw_groups", []), app_full_name, prem_app_html, char, iso, display_num, lang, otp)
                reward, reward_on = get_service_reward(app_full_name, owner_id)
                if reward > 0 and reward_on:
                    update_balance(owner_id, reward)
                _user_send_otp(owner_id, char, iso, prem_app_html, display_num, otp, reward if reward_on else 0, reward_on)
                increment_total_otps(owner_id)
                break
        except:
            pass
        time.sleep(4)


def stex_poll_otp(number_id, num_str, owner_id, api_key):
    # Stex uses 2oo9.cloud — global stex_sms_listener handles all OTPs.
    # Per-number polling not needed; this function is a no-op.
    return

def _stex_poll_otp_legacy(number_id, num_str, owner_id, api_key):
    global recent_traffic
    headers = {"mauthapi": api_key}
    for _ in range(150):
        try:
            res = requests.post(f"{STEX_BASE_URL}/success-otp", json={"rid": num_str}, headers=headers, timeout=10)
            data = res.json()
            if data.get("meta", {}).get("code") == 200 and data.get("data", {}).get("otps"):
                otp = str(data.get("otp", ""))
                msg_text = data.get("message", f"Your code is {otp}")
                extracted_otp = extract_otp_code(msg_text)
                if extracted_otp and len(extracted_otp) > len(otp):
                    otp = extracted_otp
                app_name = data.get("service", "Stex Service")
                detected_app = detect_service(msg_text)
                if detected_app:
                    app_name = detected_app
                unique_id = f"POLL_{number_id}_{otp}"
                if unique_id not in processed_otps:
                    processed_otps.add(unique_id)
                    char, iso = get_flag_and_code(num_str)
                    app_full_name, prem_app_html = get_service_info_html(app_name, msg_text)
                    current_time = time.time()
                    recent_traffic = [t for t in recent_traffic if current_time - t.get("time", 0) <= 3600]
                    recent_traffic.append({"service": app_full_name, "iso": iso, "flag": char, "number": num_str, "time": current_time})
                    save_local_db()
                    display_num = f"+{num_str}" if not str(num_str).startswith("+") else str(num_str)
                    masked = mask_number(display_num)
                    lang = detect_language(msg_text)
                    display_msg = render_body_text(f"╔═══════════════╗\n║ {prem_app_html} {get_flag_info_html(display_num)} {masked} {lang}\n╚═══════════════╝")
                    for fw in bot_settings.get("fw_groups", []):
                        kb = [[{"text": f"{otp}", "icon_custom_emoji_id": "5353022963132174959", "copy_text": {"text": otp}, "style": "success"}]]
                        for btn in fw.get("buttons", []):
                            b_obj = {"text": btn["text"], "url": btn["url"], "style": "primary"}
                            if "icon_custom_emoji_id" in btn: b_obj["icon_custom_emoji_id"] = btn["icon_custom_emoji_id"]
                            kb.append([b_obj])
                        send_message(fw["chat_id"], display_msg, reply_markup={"inline_keyboard": kb})
                    inbox_msg = render_body_text(f"╔═══════════════╗\n║ {prem_app_html} {get_flag_info_html(display_num)} {display_num} {lang}\n╚═══════════════╝")
                    inbox_kb = [[{"text": f"{otp}", "icon_custom_emoji_id": "5353022963132174959", "copy_text": {"text": otp}, "style": "success"}]]
                    reward, reward_on = get_service_reward(app_full_name, owner_id)
                    if reward > 0 and reward_on:
                        update_balance(owner_id, reward)
                        inbox_kb.append([{"text": f"Added {reward} tk", "icon_custom_emoji_id": "5420396762189831222", "callback_data": "ignore", "style": "primary"}])
                    send_message(owner_id, inbox_msg, reply_markup={"inline_keyboard": inbox_kb})
                    increment_total_otps(owner_id)
                break
        except: pass
        time.sleep(1)

def stex_sms_listener():
    """Stex Panel — Shark/CR/Flex-এর মতোই identical matching + reward + no-match admin alert।"""
    global processed_otps, recent_traffic, stex_assigned_numbers
    while True:
        try:
            stex_keys = bot_settings.get("stex_keys", [])
            for api_key in stex_keys:
                try:
                    headers = {"mauthapi": api_key}
                    try:
                        res = requests.get(f"{STEX_BASE_URL}/success-otp", headers=headers, timeout=10)
                        resp_data = res.json()
                    except Exception:
                        continue
                    if resp_data.get("meta", {}).get("code") == 200 and "otps" in resp_data.get("data", {}):
                        for item in resp_data["data"]["otps"]:
                            num = str(item.get("number", "")).replace("+", "")
                            msg_text = str(item.get("message", ""))

                            if not num or not msg_text:
                                continue

                            app_name = "Stex Service"
                            detected_app = detect_service(msg_text)
                            if detected_app:
                                app_name = detected_app

                            # Shark/CR/Flex-এর মতোই: OTP extract না হলে fake "CODE" না পাঠিয়ে skip করো
                            otp = extract_otp_code(msg_text)
                            otp_id = str(item.get("otp_id", "")) or f"{num}_{msg_text[:20]}"
                            if not otp:
                                _safe_add_otp(f"STEX_SKIP_{otp_id}")
                                continue

                            unique_id = f"STEX_{num}_{otp_id}"
                            if not _safe_add_otp(unique_id):
                                continue

                            char, iso = get_flag_and_code(num)
                            app_full_name, prem_app_html = get_service_info_html(app_name, msg_text)
                            current_time = time.time()

                            recent_traffic = [t for t in recent_traffic if current_time - t.get("time", 0) <= 3600]
                            recent_traffic.append({"service": app_full_name, "iso": iso, "flag": char, "number": num, "time": current_time})
                            save_local_db()

                            display_num = f"+{num}" if not str(num).startswith("+") else str(num)
                            lang = detect_language(msg_text)

                            print(f"📡 [Stex] নতুন OTP পেয়েছি → num={display_num} | service={app_full_name} | otp={otp}")

                            fw_groups = bot_settings.get("fw_groups", [])
                            try:
                                if fw_groups:
                                    _fw_send_otp(fw_groups, app_full_name, prem_app_html, char, iso, display_num, lang, otp)
                                else:
                                    print("📡 [Stex] fw_groups ফাঁকা, group forward skip।")
                            except Exception as e:
                                print(f"⚠️ [Stex] group forward failed: {e}")

                            clean_api_num = str(num).replace("+", "").replace(" ", "").replace("-", "").strip()
                            owners = []
                            for uid, session_data in list(user_active_sessions.items()):
                                for act_num in session_data.get("nums", []):
                                    act_clean = str(act_num).replace("+", "").replace(" ", "").replace("-", "").strip()
                                    if act_clean == clean_api_num or (len(act_clean) >= 8 and act_clean.endswith(clean_api_num[-8:])) or (len(clean_api_num) >= 8 and clean_api_num.endswith(act_clean[-8:])):
                                        if uid not in owners:
                                            owners.append(uid)

                            for assigned_dict in [batch_assigned_numbers, stex_assigned_numbers, voltx_assigned_numbers, zenex_assigned_numbers, nexus_assigned_numbers]:
                                for a_num, n_owner in list(assigned_dict.items()):
                                    clean_a = str(a_num).replace("+", "").replace(" ", "").replace("-", "").strip()
                                    if clean_a == clean_api_num or (len(clean_a) >= 8 and clean_a.endswith(clean_api_num[-8:])) or (len(clean_api_num) >= 8 and clean_api_num.endswith(clean_a[-8:])):
                                        if n_owner not in owners:
                                            owners.append(n_owner)

                            owners = list(set(owners))
                            if not owners:
                                print(f"📡 [Stex] {clean_api_num} → OTP={otp} | কোনো bot user match হয়নি (group only)")
                                if bot_settings.get("no_match_alert_on", True):
                                    try:
                                        _all_admins = list(bot_settings.get("admins", []))
                                        if OWNER_ID not in _all_admins:
                                            _all_admins.append(OWNER_ID)
                                        _dbg_msg = render_body_text(
                                            f"📡 <b>Stex Panel — OTP পেয়েছি কিন্তু কোনো user match নেই!</b>\n\n"
                                            f"📱 <b>Number:</b> <code>+{clean_api_num}</code>\n"
                                            f"🔑 <b>OTP:</b> <code>{otp}</code>\n"
                                            f"📊 stex_assigned: {len(stex_assigned_numbers)} | sessions: {len(user_active_sessions)}\n\n"
                                            f"⚠️ এই number bot-এ কোনো user-কে দেওয়া হয়নি।"
                                        )
                                        for _adm in _all_admins:
                                            try: send_message(_adm, _dbg_msg)
                                            except: pass
                                    except: pass
                            else:
                                print(f"📡 [Stex] {clean_api_num} → OTP={otp} | {len(owners)} জন user-কে পাঠাচ্ছি")

                            for owner_id in owners:
                                try:
                                    reward, reward_on = get_service_reward(app_full_name, owner_id)
                                    if reward > 0 and reward_on:
                                        update_balance(owner_id, reward)
                                    _user_send_otp(owner_id, char, iso, prem_app_html, display_num, otp, reward if reward_on else 0, reward_on)
                                    increment_total_otps(owner_id)
                                except Exception as e:
                                    print(f"⚠️ [Stex] user {owner_id}-কে পাঠাতে ব্যর্থ: {e}")
                except: continue
        except: pass
        time.sleep(1)

def voltx_sms_listener():
    """Voltx Panel — Shark/CR/Flex-এর মতোই identical matching + reward + no-match admin alert।"""
    global processed_otps, recent_traffic, voltx_assigned_numbers
    while True:
        try:
            voltx_keys = bot_settings.get("voltx_keys", [])
            for api_key in voltx_keys:
                try:
                    headers = {"mauthapi": api_key}
                    res = requests.get(f"{VOLTX_BASE_URL}/success-otp", headers=headers, timeout=10)
                    resp_data = res.json()

                    if resp_data.get("meta", {}).get("code") == 200 and "data" in resp_data and "otps" in resp_data["data"]:
                        for item in resp_data["data"]["otps"]:
                            num = str(item.get("number", "")).replace("+", "")
                            msg_text = str(item.get("message", ""))

                            if not num or not msg_text:
                                continue

                            app_name = "Voltx Service"
                            detected_app = detect_service(msg_text)
                            if detected_app: app_name = detected_app

                            otp = extract_otp_code(msg_text)
                            otp_id = str(item.get("otp_id", "")) or f"{num}_{msg_text[:20]}"
                            if not otp:
                                _safe_add_otp(f"VOLTX_SKIP_{otp_id}")
                                continue

                            unique_id = f"VOLTX_{num}_{otp_id}"
                            if not _safe_add_otp(unique_id):
                                continue

                            char, iso = get_flag_and_code(num)
                            app_full_name, prem_app_html = get_service_info_html(app_name, msg_text)
                            current_time = time.time()

                            recent_traffic = [t for t in recent_traffic if current_time - t.get("time", 0) <= 3600]
                            recent_traffic.append({"service": app_full_name, "iso": iso, "flag": char, "number": num, "time": current_time})
                            save_local_db()

                            display_num = f"+{num}" if not str(num).startswith("+") else str(num)
                            lang = detect_language(msg_text)

                            print(f"📡 [Voltx] নতুন OTP পেয়েছি → num={display_num} | service={app_full_name} | otp={otp}")

                            fw_groups = bot_settings.get("fw_groups", [])
                            try:
                                if fw_groups:
                                    _fw_send_otp(fw_groups, app_full_name, prem_app_html, char, iso, display_num, lang, otp)
                                else:
                                    print("📡 [Voltx] fw_groups ফাঁকা, group forward skip।")
                            except Exception as e:
                                print(f"⚠️ [Voltx] group forward failed: {e}")

                            clean_api_num = str(num).replace("+", "").replace(" ", "").replace("-", "").strip()
                            owners = []
                            for uid, session_data in list(user_active_sessions.items()):
                                for act_num in session_data.get("nums", []):
                                    act_clean = str(act_num).replace("+", "").replace(" ", "").replace("-", "").strip()
                                    if act_clean == clean_api_num or (len(act_clean) >= 8 and act_clean.endswith(clean_api_num[-8:])) or (len(clean_api_num) >= 8 and clean_api_num.endswith(act_clean[-8:])):
                                        if uid not in owners:
                                            owners.append(uid)

                            for assigned_dict in [batch_assigned_numbers, stex_assigned_numbers, voltx_assigned_numbers, zenex_assigned_numbers, nexus_assigned_numbers]:
                                for a_num, n_owner in list(assigned_dict.items()):
                                    clean_a = str(a_num).replace("+", "").replace(" ", "").replace("-", "").strip()
                                    if clean_a == clean_api_num or (len(clean_a) >= 8 and clean_a.endswith(clean_api_num[-8:])) or (len(clean_api_num) >= 8 and clean_api_num.endswith(clean_a[-8:])):
                                        if n_owner not in owners:
                                            owners.append(n_owner)

                            owners = list(set(owners))
                            if not owners:
                                print(f"📡 [Voltx] {clean_api_num} → OTP={otp} | কোনো bot user match হয়নি (group only)")
                                if bot_settings.get("no_match_alert_on", True):
                                    try:
                                        _all_admins = list(bot_settings.get("admins", []))
                                        if OWNER_ID not in _all_admins:
                                            _all_admins.append(OWNER_ID)
                                        _dbg_msg = render_body_text(
                                            f"📡 <b>Voltx Panel — OTP পেয়েছি কিন্তু কোনো user match নেই!</b>\n\n"
                                            f"📱 <b>Number:</b> <code>+{clean_api_num}</code>\n"
                                            f"🔑 <b>OTP:</b> <code>{otp}</code>\n"
                                            f"📊 voltx_assigned: {len(voltx_assigned_numbers)} | sessions: {len(user_active_sessions)}\n\n"
                                            f"⚠️ এই number bot-এ কোনো user-কে দেওয়া হয়নি।"
                                        )
                                        for _adm in _all_admins:
                                            try: send_message(_adm, _dbg_msg)
                                            except: pass
                                    except: pass
                            else:
                                print(f"📡 [Voltx] {clean_api_num} → OTP={otp} | {len(owners)} জন user-কে পাঠাচ্ছি")

                            for owner_id in owners:
                                try:
                                    reward, reward_on = get_service_reward(app_full_name, owner_id)
                                    if reward > 0 and reward_on:
                                        update_balance(owner_id, reward)
                                    _user_send_otp(owner_id, char, iso, prem_app_html, display_num, otp, reward if reward_on else 0, reward_on)
                                    increment_total_otps(owner_id)
                                except Exception as e:
                                    print(f"⚠️ [Voltx] user {owner_id}-কে পাঠাতে ব্যর্থ: {e}")
                except: pass
        except: pass
        time.sleep(1)

def zenex_sms_listener():
    """Zenex Panel — Shark/CR/Flex-এর মতোই identical matching + reward + no-match admin alert।"""
    global processed_otps, recent_traffic, zenex_assigned_numbers
    while True:
        try:
            zenex_keys = bot_settings.get("zenex_keys", [])
            for api_key in zenex_keys:
                try:
                    headers = {"mapikey": api_key, "Content-Type": "application/json"}
                    res = requests.get(f"{ZENEX_BASE_URL}/v1/numsuccess/info", headers=headers, timeout=10)
                    resp_data = res.json()
                    meta_ok = resp_data.get("meta", {}).get("code") == 200 or resp_data.get("meta", {}).get("status") == "success"
                    items = []
                    if meta_ok and "data" in resp_data:
                        raw = resp_data["data"]
                        if isinstance(raw, dict):
                            items = raw.get("otps", [])
                        elif isinstance(raw, list):
                            items = raw
                    for item in items:
                        num = str(item.get("number", "")).replace("+", "")
                        msg_text = str(item.get("otp", item.get("sms", item.get("message", ""))))

                        if not num or not msg_text:
                            continue

                        detected_app = detect_service(msg_text)
                        raw_app = item.get("app_name", item.get("service", ""))
                        if detected_app:
                            app_name = detected_app
                        elif raw_app and raw_app.lower() not in ["zenex service", "zenex", ""]:
                            app_name = raw_app
                        else:
                            app_name = "OTP Service"

                        otp = extract_otp_code(msg_text)
                        rec_id = str(item.get('nid', item.get('id', ''))) or f"{num}_{msg_text[:20]}"
                        if not otp:
                            _safe_add_otp(f"ZENEX_SKIP_{rec_id}")
                            continue

                        unique_id = f"ZENEX_{num}_{rec_id}"
                        if not _safe_add_otp(unique_id):
                            continue

                        char, iso = get_flag_and_code(num)
                        app_full_name, prem_app_html = get_service_info_html(app_name, msg_text)
                        current_time = time.time()
                        recent_traffic = [t for t in recent_traffic if current_time - t.get("time", 0) <= 3600]
                        recent_traffic.append({"service": app_full_name, "iso": iso, "flag": char, "number": num, "time": current_time})
                        save_local_db()
                        display_num = f"+{num}" if not str(num).startswith("+") else str(num)
                        lang = detect_language(msg_text)

                        print(f"📡 [Zenex] নতুন OTP পেয়েছি → num={display_num} | service={app_full_name} | otp={otp}")

                        fw_groups = bot_settings.get("fw_groups", [])
                        try:
                            if fw_groups:
                                _fw_send_otp(fw_groups, app_full_name, prem_app_html, char, iso, display_num, lang, otp)
                            else:
                                print("📡 [Zenex] fw_groups ফাঁকা, group forward skip।")
                        except Exception as e:
                            print(f"⚠️ [Zenex] group forward failed: {e}")

                        clean_api_num = str(num).replace("+", "").replace(" ", "").replace("-", "").strip()
                        owners = []
                        for uid, session_data in list(user_active_sessions.items()):
                            for act_num in session_data.get("nums", []):
                                act_clean = str(act_num).replace("+", "").replace(" ", "").replace("-", "").strip()
                                if act_clean == clean_api_num or (len(act_clean) >= 8 and act_clean.endswith(clean_api_num[-8:])) or (len(clean_api_num) >= 8 and clean_api_num.endswith(act_clean[-8:])):
                                    if uid not in owners:
                                        owners.append(uid)

                        for assigned_dict in [batch_assigned_numbers, stex_assigned_numbers, voltx_assigned_numbers, zenex_assigned_numbers, nexus_assigned_numbers]:
                            for a_num, n_owner in list(assigned_dict.items()):
                                clean_a = str(a_num).replace("+", "").replace(" ", "").replace("-", "").strip()
                                if clean_a == clean_api_num or (len(clean_a) >= 8 and clean_a.endswith(clean_api_num[-8:])) or (len(clean_api_num) >= 8 and clean_api_num.endswith(clean_a[-8:])):
                                    if n_owner not in owners:
                                        owners.append(n_owner)

                        owners = list(set(owners))
                        if not owners:
                            print(f"📡 [Zenex] {clean_api_num} → OTP={otp} | কোনো bot user match হয়নি (group only)")
                            if bot_settings.get("no_match_alert_on", True):
                                try:
                                    _all_admins = list(bot_settings.get("admins", []))
                                    if OWNER_ID not in _all_admins:
                                        _all_admins.append(OWNER_ID)
                                    _dbg_msg = render_body_text(
                                        f"📡 <b>Zenex Panel — OTP পেয়েছি কিন্তু কোনো user match নেই!</b>\n\n"
                                        f"📱 <b>Number:</b> <code>+{clean_api_num}</code>\n"
                                        f"🔑 <b>OTP:</b> <code>{otp}</code>\n"
                                        f"📊 zenex_assigned: {len(zenex_assigned_numbers)} | sessions: {len(user_active_sessions)}\n\n"
                                        f"⚠️ এই number bot-এ কোনো user-কে দেওয়া হয়নি।"
                                    )
                                    for _adm in _all_admins:
                                        try: send_message(_adm, _dbg_msg)
                                        except: pass
                                except: pass
                        else:
                            print(f"📡 [Zenex] {clean_api_num} → OTP={otp} | {len(owners)} জন user-কে পাঠাচ্ছি")

                        for owner_id in owners:
                            try:
                                reward, reward_on = get_service_reward(app_full_name, owner_id)
                                if reward > 0 and reward_on:
                                    update_balance(owner_id, reward)
                                _user_send_otp(owner_id, char, iso, prem_app_html, display_num, otp, reward if reward_on else 0, reward_on)
                                increment_total_otps(owner_id)
                            except Exception as e:
                                print(f"⚠️ [Zenex] user {owner_id}-কে পাঠাতে ব্যর্থ: {e}")
                except: pass
        except: pass
        time.sleep(1)

# ==========================================
# 🦈 Shark Panel API Direct Listener
# ==========================================
def shark_panel_listener():
    """Shark Panel API থেকে সরাসরি OTP poll করে। Auto login/logout নেই।"""
    global processed_otps, recent_traffic
    print("🦈 Shark Panel Listener started!")
    last_seen_dt = {}       # token → last seen dt string (newest successfully processed record dt)
    _fw_warn_logged = False  # fw_groups empty warning একবারই print করার জন্য

    while True:
        try:
            if not bot_settings.get("shark_panel_on", False):
                time.sleep(5)
                continue

            tokens = bot_settings.get("shark_tokens", [])
            if not tokens:
                time.sleep(5)
                continue

            # ── fw_groups empty হলে warning দাও — শুধু একবার (log spam এড়াতে) ──
            fw_groups = bot_settings.get("fw_groups", [])
            if not fw_groups and not _fw_warn_logged:
                print("⚠️ [Shark] fw_groups ফাঁকা! Admin panel থেকে OTP forward group chat ID যোগ করুন।")
                _fw_warn_logged = True
            elif fw_groups:
                _fw_warn_logged = False  # group যোগ হলে warning reset

            for token in tokens:
                try:
                    # FIX: dt1 বাদ — same-second OTP miss ঠেকাতে, processed_otps দিয়ে dedup
                    params = {"token": token, "records": 100}

                    headers = {"User-Agent": "Mozilla/5.0"}
                    res = requests.get(SHARK_API_URL, params=params, headers=headers, timeout=12)

                    # BUG FIX: empty body হলে res.json() crash করে।
                    # HTTP status check + text guard আগে করো।
                    if res.status_code != 200:
                        print(f"⚠️ [Shark] HTTP {res.status_code} for token ...{token[-6:]}")
                        time.sleep(5)
                        continue

                    raw_text = res.text.strip() if res.text else ""
                    if not raw_text:
                        # Empty body — silent skip
                        continue

                    # Rate limit detection — "accessed this site too many times"
                    if "too many times" in raw_text or "Try again" in raw_text:
                        print(f"⏳ [Shark] Rate limited! ৩০ সেকেন্ড অপেক্ষা করছি...")
                        time.sleep(30)
                        continue

                    try:
                        data = res.json()
                    except Exception as json_err:
                        print(f"⚠️ [Shark] JSON parse failed for token ...{token[-6:]}: {json_err} | body={raw_text[:120]}")
                        time.sleep(10)
                        continue

                    if data.get("status") != "success":
                        print(f"⚠️ [Shark] API error for token ...{token[-6:]}: {data.get('msg','?')}")
                        continue

                    items = data.get("data", [])
                    if not items:
                        continue

                    # BUG FIX: last_seen_dt item loop-এর পরে update করি।
                    # আগে loop-এর আগে update হত — মাঝপথে exception হলে unprocessed
                    # records-এর dt চলে যেত, পরের poll-এ সেগুলো আর আসত না।
                    # এখন সব item successfully process হলে dt advance হবে।
                    max_processed_dt = None  # loop-এ সর্বোচ্চ dt track করব

                    for item in items:
                        num = str(item.get("num", "")).replace("+", "").strip()
                        msg_text = str(item.get("message", "")).strip()
                        item_dt = item.get("dt", "")
                        cli = item.get("cli", "")

                        if not num or not msg_text:
                            # valid record না হলেও dt advance করি (ফাঁকা record আটকাতে)
                            if item_dt and (max_processed_dt is None or item_dt > max_processed_dt):
                                max_processed_dt = item_dt
                            continue

                        # BUG FIX: OTP extract না হলে এই record-কে SKIP হিসেবে mark করো
                        # নইলে প্রতি 5 সেকেন্ডে বারবার এই record process হয়, API limit নষ্ট হয়
                        otp = extract_otp_code(msg_text)
                        if not otp:
                            skip_id = f"SHARK_SKIP_{item_dt}_{num}"
                            _safe_add_otp(skip_id)  # mark as seen, আর process করবে না
                            if item_dt and (max_processed_dt is None or item_dt > max_processed_dt):
                                max_processed_dt = item_dt
                            continue

                        # dt + num + otp → unique key (same OTP same number same time → skip)
                        unique_id = f"SHARK_{item_dt}_{num}_{otp}"
                        if not _safe_add_otp(unique_id):
                            # already processed — dt advance করি
                            if item_dt and (max_processed_dt is None or item_dt > max_processed_dt):
                                max_processed_dt = item_dt
                            continue

                        char, iso = get_flag_and_code(num)
                        app_full_name, prem_app_html = get_service_info_html(cli, msg_text)

                        current_time = time.time()
                        try:
                            recent_traffic[:] = [t for t in recent_traffic if current_time - t.get("time", 0) <= 3600]
                            recent_traffic.append({"service": app_full_name, "iso": iso, "flag": char, "number": num, "time": current_time})
                            save_local_db()
                        except Exception:
                            pass

                        display_num = f"+{num}" if not num.startswith("+") else num
                        lang = detect_language(msg_text)

                        print(f"🦈 [Shark] নতুন OTP পেয়েছি → num={display_num} | service={app_full_name} | otp={otp}")

                        # ── Group Forward ─────────────────────────────
                        try:
                            if fw_groups:
                                _fw_send_otp(fw_groups, app_full_name, prem_app_html, char, iso, display_num, lang, otp)
                                print(f"🦈 [Shark] Group-এ forward করা হয়েছে ({len(fw_groups)} group)")
                            else:
                                print(f"🦈 [Shark] fw_groups ফাঁকা, group forward skip।")
                        except Exception as e:
                            print(f"⚠️ [Shark] group forward failed: {e} | fw_groups={fw_groups}")

                        # ── Active user খোঁজা ─────────────────────────
                        clean_api_num = num.replace("+", "").replace(" ", "").replace("-", "").strip()
                        owners = []

                        # 1) Local active sessions (memory)
                        for uid, session_data in list(user_active_sessions.items()):
                            for act_num in session_data.get("nums", []):
                                clean_act = str(act_num).replace("+", "").replace(" ", "").replace("-", "").strip()
                                if clean_act == clean_api_num or \
                                   (len(clean_act) >= 8 and clean_act.endswith(clean_api_num[-8:])) or \
                                   (len(clean_api_num) >= 8 and clean_api_num.endswith(clean_act[-8:])):
                                    if uid not in owners:
                                        owners.append(uid)

                        # 2) Batch / Stex / Voltx / Zenex assigned (DB থেকে load হয়, restart-এ থাকে)
                        # batch_assigned_numbers = local upload করা Shark Panel numbers
                        # BUG FIX: প্রতিটি dict আলাদাভাবে check করো — early-exit সরিয়ে সব provider চেক
                        for assigned_dict in [batch_assigned_numbers, stex_assigned_numbers, voltx_assigned_numbers, zenex_assigned_numbers, nexus_assigned_numbers]:
                            for a_num, n_owner in list(assigned_dict.items()):
                                clean_a = str(a_num).replace("+", "").replace(" ", "").replace("-", "").strip()
                                if clean_a == clean_api_num or \
                                   (len(clean_a) >= 8 and clean_a.endswith(clean_api_num[-8:])) or \
                                   (len(clean_api_num) >= 8 and clean_api_num.endswith(clean_a[-8:])):
                                    if n_owner not in owners:
                                        owners.append(n_owner)

                        owners = list(set(owners))
                        if not owners:
                            print(f"🦈 [Shark] {clean_api_num} → OTP={otp} | কোনো bot user match হয়নি (group only)")
                            if bot_settings.get("no_match_alert_on", True):
                                try:
                                    _all_admins = list(bot_settings.get("admins", []))
                                    if OWNER_ID not in _all_admins:
                                        _all_admins.append(OWNER_ID)
                                    _dbg_msg = render_body_text(
                                        f"🦈 <b>Shark Panel — OTP পেয়েছি কিন্তু কোনো user match নেই!</b>\n\n"
                                        f"📱 <b>Number:</b> <code>+{clean_api_num}</code>\n"
                                        f"🔑 <b>OTP:</b> <code>{otp}</code>\n"
                                        f"📊 batch_assigned: {len(batch_assigned_numbers)} | sessions: {len(user_active_sessions)}\n\n"
                                        f"⚠️ এই number bot-এ কোনো user-কে দেওয়া হয়নি।\n"
                                        f"→ Admin panel → Shark Panel → 🔍 Live API Test চাপুন।"
                                    )
                                    for _adm in _all_admins:
                                        try: send_message(_adm, _dbg_msg)
                                        except: pass
                                except: pass
                        else:
                            print(f"🦈 [Shark] {clean_api_num} → OTP={otp} | {len(owners)} জন user-কে পাঠাচ্ছি")

                        for owner_id in owners:
                            try:
                                reward, reward_on = get_service_reward(app_full_name, owner_id)
                                if reward > 0 and reward_on:
                                    update_balance(owner_id, reward)
                                _user_send_otp(owner_id, char, iso, prem_app_html, display_num, otp,
                                               reward if reward_on else 0, reward_on)
                                increment_total_otps(owner_id)
                            except Exception as e:
                                print(f"⚠️ [Shark] user {owner_id}-কে পাঠাতে ব্যর্থ: {e}")

                        # এই item সফলভাবে process হয়েছে — dt advance করি
                        if item_dt and (max_processed_dt is None or item_dt > max_processed_dt):
                            max_processed_dt = item_dt

                    # BUG FIX: loop শেষে last_seen_dt update — এখন আর মাঝপথের
                    # exception-এ dt এগিয়ে যাবে না, শুধু process হওয়া records-এর dt রাখব
                    if max_processed_dt:
                        last_seen_dt[token] = max_processed_dt

                except Exception as e:
                    print(f"⚠️ [Shark] token poll failed ...{token[-6:] if len(token) >= 6 else token}: {e}")

        except Exception as e:
            print(f"⚠️ shark_panel_listener crashed: {e}")

        time.sleep(5)  # 5s poll interval — fast OTP delivery


def flex_panel_listener():
    """Flex Panel — Dynamic URL থেকে OTP poll করে। URL bot UI থেকে set হয়।
    এখন Shark/CR Panel-এর সাথে identical matching + reward + admin-alert লজিক ব্যবহার করে।"""
    global processed_otps, recent_traffic
    print("⚡ Flex Panel Listener started!")
    last_seen_dt = {}
    _fw_warn_logged = False

    while True:
        try:
            if not bot_settings.get("flex_panel_on", False):
                time.sleep(5)
                continue

            flex_url = bot_settings.get("flex_api_url", "")
            if not flex_url:
                time.sleep(5)
                continue

            tokens = bot_settings.get("flex_tokens", [])
            if not tokens:
                time.sleep(5)
                continue

            fw_groups = bot_settings.get("fw_groups", [])
            if not fw_groups and not _fw_warn_logged:
                print("⚠️ [Flex] fw_groups ফাঁকা! Admin panel থেকে OTP forward group chat ID যোগ করুন।")
                _fw_warn_logged = True
            elif fw_groups:
                _fw_warn_logged = False

            for token in tokens:
                try:
                    # FIX: dt1 বাদ — same-second OTP miss ঠেকাতে, processed_otps দিয়ে dedup
                    params = {"token": token, "records": 100}

                    headers = {"User-Agent": "Mozilla/5.0"}
                    res = requests.get(flex_url, params=params, headers=headers, timeout=12)

                    if res.status_code != 200:
                        print(f"⚠️ [Flex] HTTP {res.status_code} for token ...{token[-6:]}")
                        time.sleep(5)
                        continue

                    raw_text = res.text.strip() if res.text else ""
                    if not raw_text:
                        continue

                    if "too many times" in raw_text or "Try again" in raw_text:
                        print(f"⏳ [Flex] Rate limited! ৩০ সেকেন্ড অপেক্ষা করছি...")
                        time.sleep(30)
                        continue

                    try:
                        data_resp = res.json()
                    except Exception as json_err:
                        print(f"⚠️ [Flex] JSON parse failed for token ...{token[-6:]}: {json_err} | body={raw_text[:120]}")
                        time.sleep(10)
                        continue

                    if data_resp.get("status") == "error":
                        print(f"⚠️ [Flex] API Error: {data_resp.get('message', '')} (token: ...{token[-6:]})")
                        time.sleep(10)
                        continue

                    items = data_resp.get("data", [])
                    if not items:
                        continue

                    max_processed_dt = None

                    for item in items:
                        num = str(item.get("num", "")).replace("+", "").strip()
                        msg_text = str(item.get("message", "")).strip()
                        item_dt = item.get("dt", "")
                        cli = item.get("cli", "")

                        if not num or not msg_text:
                            if item_dt and (max_processed_dt is None or item_dt > max_processed_dt):
                                max_processed_dt = item_dt
                            continue

                        # Shark/CR-এর মতোই: OTP extract না হলে skip করে mark করে দাও
                        otp = extract_otp_code(msg_text)
                        if not otp:
                            skip_id = f"FLEX_SKIP_{item_dt}_{num}"
                            _safe_add_otp(skip_id)
                            if item_dt and (max_processed_dt is None or item_dt > max_processed_dt):
                                max_processed_dt = item_dt
                            continue

                        unique_id = f"FLEX_{item_dt}_{num}_{otp}"
                        if not _safe_add_otp(unique_id):
                            if item_dt and (max_processed_dt is None or item_dt > max_processed_dt):
                                max_processed_dt = item_dt
                            continue

                        char, iso = get_flag_and_code(num)
                        app_full_name, prem_app_html = get_service_info_html(cli, msg_text)

                        current_time = time.time()
                        try:
                            recent_traffic[:] = [t for t in recent_traffic if current_time - t.get("time", 0) <= 3600]
                            recent_traffic.append({"service": app_full_name, "iso": iso, "flag": char, "number": num, "time": current_time})
                            save_local_db()
                        except Exception:
                            pass

                        display_num = f"+{num}" if not num.startswith("+") else num
                        lang = detect_language(msg_text)

                        print(f"⚡ [Flex] নতুন OTP পেয়েছি → num={display_num} | service={app_full_name} | otp={otp}")

                        # ── Group Forward (Shark/CR-এর মতোই) ─────────────
                        try:
                            if fw_groups:
                                _fw_send_otp(fw_groups, app_full_name, prem_app_html, char, iso, display_num, lang, otp)
                                print(f"⚡ [Flex] Group-এ forward করা হয়েছে ({len(fw_groups)} group)")
                            else:
                                print(f"⚡ [Flex] fw_groups ফাঁকা, group forward skip।")
                        except Exception as e:
                            print(f"⚠️ [Flex] group forward failed: {e} | fw_groups={fw_groups}")

                        # ── Active user খোঁজা (Shark/CR-এর মতোই সব provider মিলিয়ে) ──
                        clean_api_num = num.replace("+", "").replace(" ", "").replace("-", "").strip()
                        owners = []

                        for uid, session_data in list(user_active_sessions.items()):
                            for act_num in session_data.get("nums", []):
                                clean_act = str(act_num).replace("+", "").replace(" ", "").replace("-", "").strip()
                                if clean_act == clean_api_num or \
                                   (len(clean_act) >= 8 and clean_act.endswith(clean_api_num[-8:])) or \
                                   (len(clean_api_num) >= 8 and clean_api_num.endswith(clean_act[-8:])):
                                    if uid not in owners:
                                        owners.append(uid)

                        for assigned_dict in [batch_assigned_numbers, stex_assigned_numbers, voltx_assigned_numbers, zenex_assigned_numbers, nexus_assigned_numbers]:
                            for a_num, n_owner in list(assigned_dict.items()):
                                clean_a = str(a_num).replace("+", "").replace(" ", "").replace("-", "").strip()
                                if clean_a == clean_api_num or \
                                   (len(clean_a) >= 8 and clean_a.endswith(clean_api_num[-8:])) or \
                                   (len(clean_api_num) >= 8 and clean_api_num.endswith(clean_a[-8:])):
                                    if n_owner not in owners:
                                        owners.append(n_owner)

                        owners = list(set(owners))
                        if not owners:
                            print(f"⚡ [Flex] {clean_api_num} → OTP={otp} | কোনো bot user match হয়নি (group only)")
                            if bot_settings.get("no_match_alert_on", True):
                                try:
                                    _all_admins = list(bot_settings.get("admins", []))
                                    if OWNER_ID not in _all_admins:
                                        _all_admins.append(OWNER_ID)
                                    _dbg_msg = render_body_text(
                                        f"⚡ <b>Flex Panel — OTP পেয়েছি কিন্তু কোনো user match নেই!</b>\n\n"
                                        f"📱 <b>Number:</b> <code>+{clean_api_num}</code>\n"
                                        f"🔑 <b>OTP:</b> <code>{otp}</code>\n"
                                        f"📊 batch_assigned: {len(batch_assigned_numbers)} | sessions: {len(user_active_sessions)}\n\n"
                                        f"⚠️ এই number bot-এ কোনো user-কে দেওয়া হয়নি।"
                                    )
                                    for _adm in _all_admins:
                                        try: send_message(_adm, _dbg_msg)
                                        except: pass
                                except: pass
                        else:
                            print(f"⚡ [Flex] {clean_api_num} → OTP={otp} | {len(owners)} জন user-কে পাঠাচ্ছি")

                        # ── Reward: Shark/CR-এর মতোই per-service/per-user rate (flat rate নয়) ──
                        for owner_id in owners:
                            try:
                                reward, reward_on = get_service_reward(app_full_name, owner_id)
                                if reward > 0 and reward_on:
                                    update_balance(owner_id, reward)
                                _user_send_otp(owner_id, char, iso, prem_app_html, display_num, otp,
                                               reward if reward_on else 0, reward_on)
                                increment_total_otps(owner_id)
                            except Exception as e:
                                print(f"⚠️ [Flex] user {owner_id}-কে পাঠাতে ব্যর্থ: {e}")

                        if item_dt and (max_processed_dt is None or item_dt > max_processed_dt):
                            max_processed_dt = item_dt

                    if max_processed_dt:
                        last_seen_dt[token] = max_processed_dt

                except Exception as e:
                    print(f"⚠️ [Flex] token poll failed ...{token[-6:] if len(token) >= 6 else token}: {e}")

            time.sleep(5)  # 5s poll interval — fast OTP delivery

        except Exception as e:
            print(f"⚠️ flex_panel_listener crashed: {e}")
            time.sleep(5)


def cr_panel_listener():
    """CR/HADI Panel API থেকে সরাসরি OTP poll করে। Auto login/logout নেই।"""
    global processed_otps, recent_traffic
    print("🌐 CR Panel Listener started!")
    last_seen_dt = {}
    _fw_warn_logged = False

    while True:
        try:
            if not bot_settings.get("cr_panel_on", False):
                time.sleep(5)
                continue

            tokens = bot_settings.get("cr_tokens", [])
            if not tokens:
                time.sleep(5)
                continue

            fw_groups = bot_settings.get("fw_groups", [])
            if not fw_groups and not _fw_warn_logged:
                print("⚠️ [CR] fw_groups ফাঁকা! Admin panel থেকে OTP forward group chat ID যোগ করুন।")
                _fw_warn_logged = True
            elif fw_groups:
                _fw_warn_logged = False

            for token in tokens:
                try:
                    # FIX: dt1 বাদ — same-second OTP miss ঠেকাতে, processed_otps দিয়ে dedup
                    params = {"token": token, "records": 100}

                    headers = {"User-Agent": "Mozilla/5.0"}
                    res = requests.get(CR_API_URL, params=params, headers=headers, timeout=12)

                    if res.status_code != 200:
                        print(f"⚠️ [CR] HTTP {res.status_code} for token ...{token[-6:]}")
                        time.sleep(5)
                        continue

                    raw_text = res.text.strip() if res.text else ""
                    if not raw_text:
                        continue

                    if "too many times" in raw_text or "Try again" in raw_text:
                        print(f"⏳ [CR] Rate limited! ৩০ সেকেন্ড অপেক্ষা করছি...")
                        time.sleep(30)
                        continue

                    try:
                        data = res.json()
                    except Exception as json_err:
                        print(f"⚠️ [CR] JSON parse failed for token ...{token[-6:]}: {json_err} | body={raw_text[:120]}")
                        time.sleep(10)
                        continue

                    if data.get("status") != "success":
                        print(f"⚠️ [CR] API error for token ...{token[-6:]}: {data.get('msg','?')}")
                        continue

                    items = data.get("data", [])
                    if not items:
                        continue

                    max_processed_dt = None

                    for item in items:
                        num = str(item.get("num", "")).replace("+", "").strip()
                        msg_text = str(item.get("message", "")).strip()
                        item_dt = item.get("dt", "")
                        cli = item.get("cli", "")

                        if not num or not msg_text:
                            if item_dt and (max_processed_dt is None or item_dt > max_processed_dt):
                                max_processed_dt = item_dt
                            continue

                        otp = extract_otp_code(msg_text)
                        if not otp:
                            skip_id = f"CR_SKIP_{item_dt}_{num}"
                            _safe_add_otp(skip_id)
                            if item_dt and (max_processed_dt is None or item_dt > max_processed_dt):
                                max_processed_dt = item_dt
                            continue

                        unique_id = f"CR_{item_dt}_{num}_{otp}"
                        if not _safe_add_otp(unique_id):
                            if item_dt and (max_processed_dt is None or item_dt > max_processed_dt):
                                max_processed_dt = item_dt
                            continue

                        char, iso = get_flag_and_code(num)
                        app_full_name, prem_app_html = get_service_info_html(cli, msg_text)

                        current_time = time.time()
                        try:
                            recent_traffic[:] = [t for t in recent_traffic if current_time - t.get("time", 0) <= 3600]
                            recent_traffic.append({"service": app_full_name, "iso": iso, "flag": char, "number": num, "time": current_time})
                            save_local_db()
                        except Exception:
                            pass

                        display_num = f"+{num}" if not num.startswith("+") else num
                        lang = detect_language(msg_text)

                        print(f"🌐 [CR] নতুন OTP পেয়েছি → num={display_num} | service={app_full_name} | otp={otp}")

                        try:
                            if fw_groups:
                                _fw_send_otp(fw_groups, app_full_name, prem_app_html, char, iso, display_num, lang, otp)
                                print(f"🌐 [CR] Group-এ forward করা হয়েছে ({len(fw_groups)} group)")
                            else:
                                print(f"🌐 [CR] fw_groups ফাঁকা, group forward skip।")
                        except Exception as e:
                            print(f"⚠️ [CR] group forward failed: {e}")

                        clean_api_num = num.replace("+", "").replace(" ", "").replace("-", "").strip()
                        owners = []

                        for uid, session_data in list(user_active_sessions.items()):
                            for act_num in session_data.get("nums", []):
                                clean_act = str(act_num).replace("+", "").replace(" ", "").replace("-", "").strip()
                                if clean_act == clean_api_num or \
                                   (len(clean_act) >= 8 and clean_act.endswith(clean_api_num[-8:])) or \
                                   (len(clean_api_num) >= 8 and clean_api_num.endswith(clean_act[-8:])):
                                    if uid not in owners:
                                        owners.append(uid)

                        for assigned_dict in [batch_assigned_numbers, stex_assigned_numbers, voltx_assigned_numbers, zenex_assigned_numbers, nexus_assigned_numbers]:
                            for a_num, n_owner in list(assigned_dict.items()):
                                clean_a = str(a_num).replace("+", "").replace(" ", "").replace("-", "").strip()
                                if clean_a == clean_api_num or \
                                   (len(clean_a) >= 8 and clean_a.endswith(clean_api_num[-8:])) or \
                                   (len(clean_api_num) >= 8 and clean_api_num.endswith(clean_a[-8:])):
                                    if n_owner not in owners:
                                        owners.append(n_owner)

                        owners = list(set(owners))
                        if not owners:
                            print(f"🌐 [CR] {clean_api_num} → OTP={otp} | কোনো bot user match হয়নি (group only)")
                            if bot_settings.get("no_match_alert_on", True):
                                try:
                                    _all_admins = list(bot_settings.get("admins", []))
                                    if OWNER_ID not in _all_admins:
                                        _all_admins.append(OWNER_ID)
                                    _dbg_msg = render_body_text(
                                        f"🌐 <b>CR/Hadi Panel — OTP পেয়েছি কিন্তু কোনো user match নেই!</b>\n\n"
                                        f"📱 <b>Number:</b> <code>+{clean_api_num}</code>\n"
                                        f"🔑 <b>OTP:</b> <code>{otp}</code>\n"
                                        f"📊 batch_assigned: {len(batch_assigned_numbers)} | sessions: {len(user_active_sessions)}\n\n"
                                        f"⚠️ এই number bot-এ কোনো user-কে দেওয়া হয়নি।"
                                    )
                                    for _adm in _all_admins:
                                        try: send_message(_adm, _dbg_msg)
                                        except: pass
                                except: pass
                        else:
                            print(f"🌐 [CR] {clean_api_num} → OTP={otp} | {len(owners)} জন user-কে পাঠাচ্ছি")

                        for owner_id in owners:
                            try:
                                reward, reward_on = get_service_reward(app_full_name, owner_id)
                                if reward > 0 and reward_on:
                                    update_balance(owner_id, reward)
                                _user_send_otp(owner_id, char, iso, prem_app_html, display_num, otp,
                                               reward if reward_on else 0, reward_on)
                                increment_total_otps(owner_id)
                            except Exception as e:
                                print(f"⚠️ [CR] user {owner_id}-কে পাঠাতে ব্যর্থ: {e}")

                        if item_dt and (max_processed_dt is None or item_dt > max_processed_dt):
                            max_processed_dt = item_dt

                    if max_processed_dt:
                        last_seen_dt[token] = max_processed_dt

                except Exception as e:
                    print(f"⚠️ [CR] token poll failed ...{token[-6:] if len(token) >= 6 else token}: {e}")

        except Exception as e:
            print(f"⚠️ cr_panel_listener crashed: {e}")

        time.sleep(5)  # 5s poll interval — fast OTP delivery


def nexus_panel_listener():
    """Nexus-X REST API (Bearer token) থেকে OTP poll করে।"""
    global processed_otps, recent_traffic, nexus_assigned_numbers
    print("🔷 Nexus-X Panel Listener started!")
    _fw_warn_logged = False
    seen_otp_ids = set()  # inbox item id বা (number+body) দিয়ে dedup

    while True:
        try:
            if not bot_settings.get("nexus_panel_on", False):
                time.sleep(5)
                continue

            keys = bot_settings.get("nexus_keys", [])
            if not keys:
                time.sleep(5)
                continue

            fw_groups = bot_settings.get("fw_groups", [])
            if not fw_groups and not _fw_warn_logged:
                print("⚠️ [Nexus-X] fw_groups ফাঁকা! Admin panel থেকে OTP forward group যোগ করুন।")
                _fw_warn_logged = True
            elif fw_groups:
                _fw_warn_logged = False

            for api_key in keys:
                try:
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "User-Agent": "Mozilla/5.0"
                    }
                    res = requests.get(
                        "https://v2.nexus-x.site/api/v1/inbox",
                        headers=headers,
                        timeout=12
                    )

                    if res.status_code == 401:
                        print(f"⚠️ [Nexus-X] Key ...{api_key[-6:]}: Unauthorized — key invalid বা expired")
                        time.sleep(30)
                        continue

                    if res.status_code != 200:
                        print(f"⚠️ [Nexus-X] HTTP {res.status_code} for key ...{api_key[-6:]}")
                        time.sleep(5)
                        continue

                    raw_text = res.text.strip() if res.text else ""
                    if not raw_text:
                        continue

                    try:
                        data_resp = res.json()
                    except Exception as je:
                        print(f"⚠️ [Nexus-X] JSON parse failed: {je} | body={raw_text[:120]}")
                        time.sleep(10)
                        continue

                    # inbox returns list directly or nested in "data"/"items"
                    if isinstance(data_resp, list):
                        items = data_resp
                    elif isinstance(data_resp, dict):
                        items = data_resp.get("data", data_resp.get("items", data_resp.get("otps", [])))
                    else:
                        items = []

                    if not items:
                        continue

                    for item in items:
                        # number field aliases
                        num_raw = (item.get("number") or item.get("full_number") or
                                   item.get("no_plus_number") or item.get("national_number") or "")
                        num = str(num_raw).replace("+", "").replace(" ", "").replace("-", "").strip()

                        # message text aliases
                        msg_text = (item.get("body") or item.get("text") or
                                    item.get("full_text") or item.get("console") or "").strip()

                        # service aliases
                        service_raw = (item.get("service") or item.get("access") or
                                       item.get("sid") or "")
                        sender = item.get("sender", "")

                        # unique dedup key
                        item_id = item.get("id", "")
                        dedup_key = f"NEXUS_{item_id}_{num}" if item_id else f"NEXUS_{num}_{msg_text[:30]}"

                        if not num or not msg_text:
                            continue

                        if dedup_key in seen_otp_ids:
                            continue

                        otp = extract_otp_code(msg_text)
                        if not otp:
                            seen_otp_ids.add(dedup_key)
                            continue

                        unique_id = f"NEXUS_{num}_{otp}_{item_id}"
                        if not _safe_add_otp(unique_id):
                            seen_otp_ids.add(dedup_key)
                            continue

                        seen_otp_ids.add(dedup_key)
                        # limit seen set size
                        if len(seen_otp_ids) > 2000:
                            seen_otp_ids.clear()

                        char, iso = get_flag_and_code(num)
                        app_full_name, prem_app_html = get_service_info_html(
                            sender or service_raw, msg_text
                        )

                        current_time = time.time()
                        try:
                            recent_traffic[:] = [t for t in recent_traffic if current_time - t.get("time", 0) <= 3600]
                            recent_traffic.append({"service": app_full_name, "iso": iso, "flag": char, "number": num, "time": current_time})
                            save_local_db()
                        except Exception:
                            pass

                        display_num = f"+{num}" if not num.startswith("+") else num
                        lang = detect_language(msg_text)

                        print(f"🔷 [Nexus-X] নতুন OTP পেয়েছি → num={display_num} | service={app_full_name} | otp={otp}")

                        # Group forward
                        try:
                            if fw_groups:
                                _fw_send_otp(fw_groups, app_full_name, prem_app_html, char, iso, display_num, lang, otp)
                                print(f"🔷 [Nexus-X] Group-এ forward করা হয়েছে ({len(fw_groups)} group)")
                        except Exception as e:
                            print(f"⚠️ [Nexus-X] group forward failed: {e}")

                        # Active user matching
                        clean_api_num = num
                        owners = []

                        for uid, session_data in list(user_active_sessions.items()):
                            for act_num in session_data.get("nums", []):
                                clean_act = str(act_num).replace("+", "").replace(" ", "").replace("-", "").strip()
                                if clean_act == clean_api_num or \
                                   (len(clean_act) >= 8 and clean_act.endswith(clean_api_num[-8:])) or \
                                   (len(clean_api_num) >= 8 and clean_api_num.endswith(clean_act[-8:])):
                                    if uid not in owners:
                                        owners.append(uid)

                        for assigned_dict in [batch_assigned_numbers, stex_assigned_numbers, voltx_assigned_numbers, zenex_assigned_numbers, nexus_assigned_numbers]:
                            for a_num, n_owner in list(assigned_dict.items()):
                                clean_a = str(a_num).replace("+", "").replace(" ", "").replace("-", "").strip()
                                if clean_a == clean_api_num or \
                                   (len(clean_a) >= 8 and clean_a.endswith(clean_api_num[-8:])) or \
                                   (len(clean_api_num) >= 8 and clean_api_num.endswith(clean_a[-8:])):
                                    if n_owner not in owners:
                                        owners.append(n_owner)

                        owners = list(set(owners))
                        if not owners:
                            print(f"🔷 [Nexus-X] {clean_api_num} → OTP={otp} | কোনো bot user match হয়নি (group only)")
                        else:
                            print(f"🔷 [Nexus-X] {clean_api_num} → OTP={otp} | {len(owners)} জন user-কে পাঠাচ্ছি")

                        for owner_id in owners:
                            try:
                                reward, reward_on = get_service_reward(app_full_name, owner_id)
                                if reward > 0 and reward_on:
                                    update_balance(owner_id, reward)
                                _user_send_otp(owner_id, char, iso, prem_app_html, display_num, otp,
                                               reward if reward_on else 0, reward_on)
                                increment_total_otps(owner_id)
                            except Exception as e:
                                print(f"⚠️ [Nexus-X] user {owner_id}-কে পাঠাতে ব্যর্থ: {e}")

                except Exception as e:
                    print(f"⚠️ [Nexus-X] key poll failed ...{api_key[-6:] if len(api_key) >= 6 else api_key}: {e}")

        except Exception as e:
            print(f"⚠️ nexus_panel_listener crashed: {e}")

        time.sleep(5)


def main():
    global BOT_USERNAME
    res = api_call("getMe")
    if res.get("ok"): BOT_USERNAME = res["result"]["username"]
    print(f"🤖 Bot is starting... @{BOT_USERNAME}")
    
    threading.Thread(target=panel_monitor_thread, daemon=True).start()
    threading.Thread(target=panel_keepalive_thread, daemon=True).start()
    threading.Thread(target=stex_sms_listener, daemon=True).start()
    threading.Thread(target=voltx_sms_listener, daemon=True).start()
    threading.Thread(target=zenex_sms_listener, daemon=True).start()
    threading.Thread(target=shark_panel_listener, daemon=True).start()
    threading.Thread(target=cr_panel_listener, daemon=True).start()
    threading.Thread(target=flex_panel_listener, daemon=True).start()
    threading.Thread(target=nexus_panel_listener, daemon=True).start()
    print("📡 Background APIs & Global SMS Listener + KeepAlive + Shark Panel + CR Panel + Flex Panel + Nexus-X Panel Started!")
    
    # Optimized for Windows RDP: 50 workers saves RAM while keeping bot fast
    executor = ThreadPoolExecutor(max_workers=500)
    
    offset = 0
    consecutive_errors = 0
    print("Bot polling started. Press Ctrl+C to stop.")
    while True:
        try:
            updates = api_call(f"getUpdates?timeout=50&offset={offset}")
            if updates and "result" in updates:
                consecutive_errors = 0
                for update in updates["result"]:
                    offset = update["update_id"] + 1
                    if "message" in update: 
                        executor.submit(handle_message, update["message"])
                    elif "callback_query" in update: 
                        executor.submit(handle_callback, update["callback_query"])
            elif updates and updates.get("error_code") == 409:
                print("[WARN] Conflict: Another bot instance is running. Waiting 10s...")
                time.sleep(10)
        except KeyboardInterrupt:
            print("Bot stopped by user.")
            break
        except Exception as e:
            consecutive_errors += 1
            wait = min(30, consecutive_errors * 2)
            print(f"[ERROR] Polling error #{consecutive_errors}: {e}. Retrying in {wait}s...")
            time.sleep(wait)

if __name__ == "__main__":
    main()    
