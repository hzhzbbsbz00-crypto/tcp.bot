# ═══════════════════════════════════════════════════════════════
#   কনফিগ ফাইল
#   • টেলিগ্রাম বট টোকেন ও অ্যাডমিন আইডি নিচে সরাসরি বসাতে পারেন
#   • গেম UID/পাসওয়ার্ড টেলিগ্রাম থেকে /setaccount দিয়ে সেট করা যায়
#     (accounts.json ফাইলে সেভ হয়; না থাকলে Environment থেকে নেয়)
# ═══════════════════════════════════════════════════════════════
import os
import json

# ─── টেলিগ্রাম ───
# এখানে BotFather-এর টোকেন বসান (Environment Variable থাকলে সেটাই আগে নেবে)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or "PASTE_TELEGRAM_BOT_TOKEN_HERE"
# আপনার টেলিগ্রাম ইউজার আইডি (একাধিক হলে কমা দিয়ে: "1111,2222")
TELEGRAM_ADMIN_IDS = os.environ.get("TELEGRAM_ADMIN_IDS") or "PASTE_YOUR_TELEGRAM_USER_ID_HERE"

# ─── গেম অ্যাকাউন্ট (ডিফল্ট; টেলিগ্রাম থেকে বদলানো যাবে) ───
UID = os.environ.get("BOT_UID", "")
PW = os.environ.get("BOT_PASSWORD", "")
REGION_PREF = os.environ.get("BOT_REGION", "BD")
ADMIN_UID = os.environ.get("ADMIN_UID", "")

ACCOUNT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "accounts.json")


def get_account():
    """(uid, password, region) — accounts.json আগে, না থাকলে ডিফল্ট"""
    try:
        with open(ACCOUNT_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        if d.get("uid") and d.get("password"):
            return str(d["uid"]), str(d["password"]), str(d.get("region") or REGION_PREF)
    except Exception:
        pass
    return UID, PW, REGION_PREF


def save_account(uid, password, region=None):
    with open(ACCOUNT_FILE, "w", encoding="utf-8") as f:
        json.dump({"uid": str(uid), "password": str(password), "region": region or REGION_PREF}, f)


def clear_account():
    try:
        os.remove(ACCOUNT_FILE)
    except FileNotFoundError:
        pass
