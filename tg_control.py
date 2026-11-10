"""
টেলিগ্রাম কন্ট্রোল সিস্টেম
─────────────────────────
Environment Variable:
  TELEGRAM_BOT_TOKEN  = BotFather থেকে পাওয়া টোকেন
  TELEGRAM_ADMIN_IDS  = আপনার টেলিগ্রাম ইউজার আইডি (একাধিক হলে কমা দিয়ে)

শুধু ADMIN_IDS-এর ভেতরের ইউজাররাই বট কন্ট্রোল করতে পারবে।
"""
import asyncio
import os
import time

import aiohttp

API = "https://api.telegram.org/bot{token}/{method}"

HELP_TEXT = """🤖 বট কন্ট্রোল প্যানেল

📊 অবস্থা
/status — বটের বর্তমান অবস্থা
/on — বট চালু (গেম-চ্যাট কমান্ড)
/off — বট বন্ধ (গেম-চ্যাট কমান্ড)
/restart — গেম সেশন রিস্টার্ট
/debug on|off — ইনভাইট সমস্যা ধরার জন্য প্যাকেট দেখা
/gamectl all|admin|off — গেম-চ্যাট থেকে কন্ট্রোল কারা করতে পারবে

👥 স্কোয়াড
/join <কোড> — স্কোয়াডে জয়েন
/exit — স্কোয়াড ত্যাগ

🎭 ইমোট
/emote <uid> [uid2 ...] <ইমোট> — ইমোট পাঠানো
/evo <uid> [uid2 ...] <ইমোট> — ইভো ইমোট
/evos <uid> [uid2 ...] — ইভো সাইকেল চালু
/sevos — ইভো সাইকেল বন্ধ
/bundle <১-১২> — বান্ডেল

🏅 ব্যাজ
/badge <s1-s5> <uid>

🔑 গেম অ্যাকাউন্ট
/setaccount <uid> <password> [region] — UID/পাসওয়ার্ড সেট করে লগইন
/account — বর্তমান অ্যাকাউন্ট দেখুন
/delaccount — সেভ করা অ্যাকাউন্ট মুছুন

👤 ফ্রেন্ড ও তথ্য
/add <uid> — ফ্রেন্ড রিকোয়েস্ট
/remove <uid> — ফ্রেন্ড রিমুভ
/info <uid> — প্লেয়ার তথ্য
/check <uid> — ব্যান চেক
"""

BUNDLE_IDS = {
    "1": 914000002, "2": 914000003, "3": 914038001, "4": 914039001,
    "5": 914042001, "6": 914044001, "7": 914047001, "8": 914047002,
    "9": 914048001, "10": 914050001, "11": 914051001, "12": 914053001,
}


MODE_NAMES = {"all": "সবাই", "admin": "শুধু অ্যাডমিন", "off": "বন্ধ"}


def _btn(text, data):
    return {"text": text, "callback_data": data}


MENU_BTN = {"inline_keyboard": [[_btn("📋 মেনু", "menu")]]}

MAIN_MENU = {"inline_keyboard": [
    [_btn("📊 স্ট্যাটাস", "run:/status"), _btn("🔄 রিস্টার্ট", "run:/restart")],
    [_btn("✅ বট চালু", "run:/on"), _btn("⛔ বট বন্ধ", "run:/off")],
    [_btn("👥 স্কোয়াড জয়েন", "ask:/join"), _btn("🚪 স্কোয়াড এক্সিট", "run:/exit")],
    [_btn("🎭 ইমোট", "ask:/emote"), _btn("⚡ ইভো ইমোট", "ask:/evo")],
    [_btn("🔁 ইভো সাইকেল চালু", "ask:/evos"), _btn("⏹ সাইকেল বন্ধ", "run:/sevos")],
    [_btn("🎁 বান্ডেল", "sub:bundle"), _btn("🏅 ব্যাজ", "sub:badge")],
    [_btn("➕ ফ্রেন্ড অ্যাড", "ask:/add"), _btn("➖ ফ্রেন্ড রিমুভ", "ask:/remove")],
    [_btn("ℹ️ প্লেয়ার ইনফো", "ask:/info"), _btn("🔍 ব্যান চেক", "ask:/check")],
    [_btn("🔑 অ্যাকাউন্ট সেট", "ask:/setaccount"), _btn("👁 অ্যাকাউন্ট দেখুন", "run:/account")],
    [_btn("🎮 গেম কন্ট্রোল", "sub:gamectl"), _btn("🗑 অ্যাকাউন্ট মুছুন", "run:/delaccount")],
    [_btn("❓ সাহায্য", "run:/help")],
]}


def bundle_menu():
    rows, row = [], []
    for i in range(1, 13):
        row.append(_btn(str(i), f"run:/bundle {i}"))
        if len(row) == 4:
            rows.append(row); row = []
    rows.append([_btn("🔙 মেনু", "menu")])
    return {"inline_keyboard": rows}


def gamectl_menu():
    return {"inline_keyboard": [
        [_btn("🌐 সবাই ব্যবহার করতে পারবে", "run:/gamectl all")],
        [_btn("👑 শুধু অ্যাডমিন (গেম UID)", "run:/gamectl admin")],
        [_btn("⛔ গেম থেকে কন্ট্রোল বন্ধ", "run:/gamectl off")],
        [_btn("🔙 মেনু", "menu")],
    ]}


def badge_menu():
    return {"inline_keyboard": [
        [_btn(f"{n.upper()}", f"ask:/badge {n}") for n in ("s1", "s2", "s3")],
        [_btn(f"{n.upper()}", f"ask:/badge {n}") for n in ("s4", "s5")],
        [_btn("🔙 মেনু", "menu")],
    ]}


# বাটন চাপলে ইনপুটের জন্য যে প্রম্পট দেখাবে
PROMPTS = {
    "/join": "👥 স্কোয়াড কোডটি লিখে পাঠান:",
    "/emote": "🎭 লিখুন: <uid> [uid2 ...] <ইমোট নম্বর/নাম>\nউদাহরণ: 123456789 ak",
    "/evo": "⚡ লিখুন: <uid> [uid2 ...] <ইমোট নম্বর>",
    "/evos": "🔁 যাদের উপর ইভো সাইকেল চলবে তাদের UID লিখুন (একাধিক হলে স্পেস দিয়ে):",
    "/add": "➕ যাকে ফ্রেন্ড রিকোয়েস্ট পাঠাবেন তার UID লিখুন:",
    "/remove": "➖ যাকে রিমুভ করবেন তার UID লিখুন:",
    "/info": "ℹ️ প্লেয়ারের UID লিখুন:",
    "/check": "🔍 ব্যান চেকের জন্য UID লিখুন:",
    "/setaccount": "🔑 লিখুন: <uid> <password> [region]\n(পাঠানোর পর মেসেজটি স্বয়ংক্রিয়ভাবে মুছে যাবে)",
}
CANCEL_MARKUP = {"inline_keyboard": [[_btn("❌ বাতিল", "menu")]]}


class TgController:
    def __init__(self, bot, token, admin_ids):
        self.bot = bot            # main.py মডিউল (লাইভ স্টেট পড়ার জন্য)
        self.token = token
        self.admin_ids = admin_ids
        self.offset = 0
        self.pending = {}   # chat_id -> অপেক্ষমান কমান্ড (বাটন চাপার পর ইনপুটের জন্য)

    # ───────────── Telegram API ─────────────
    async def _call(self, session, method, **params):
        url = API.format(token=self.token, method=method)
        async with session.post(url, json=params, timeout=aiohttp.ClientTimeout(total=70)) as r:
            return await r.json()

    async def _reply(self, session, chat_id, text, markup="default"):
        if markup == "default":
            markup = MENU_BTN
        try:
            params = dict(chat_id=chat_id, text=text[:4000])
            if markup:
                params["reply_markup"] = markup
            await self._call(session, "sendMessage", **params)
        except Exception as e:
            print(f"[TG] reply error: {e}")

    # ───────────── বটের অবস্থা ─────────────
    def _ready(self):
        b = self.bot
        return bool(b.bot_key and b.bot_iv and b.online_writer and b.whisper_writer)

    def _need_ready_msg(self):
        return "⏳ বট এখনো গেমে লগইন/কানেক্ট হয়নি। কিছুক্ষণ পর আবার চেষ্টা করুন।"

    def _resolve_emote(self, key):
        b = self.bot
        key = key.lower().strip()
        if key in b.GENERAL_EMOTES_MAP:
            return b.GENERAL_EMOTES_MAP[key]
        if key in b.NAME_EMOTES:
            return b.NAME_EMOTES[key]
        return None

    async def _send_emote(self, uids, emote_id):
        b = self.bot
        sent = 0
        for t in uids:
            try:
                pkt = await b.Emote_k(int(t), int(emote_id), b.bot_key, b.bot_iv, b.region)
                await b.SEndPacKeT(b.whisper_writer, b.online_writer, "OnLine", pkt)
                sent += 1
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"[TG] emote error: {e}")
        return sent

    # ───────────── কমান্ড হ্যান্ডলার ─────────────
    async def handle(self, session, chat_id, text, msg_id=None):
        b = self.bot
        parts = text.strip().split()
        if not parts:
            return
        cmd = parts[0].lower().split("@")[0]
        args = parts[1:]

        if cmd in ("/start", "/menu"):
            return await self._reply(session, chat_id, "🤖 বট কন্ট্রোল মেনু\nনিচের বাটন চেপে কন্ট্রোল করুন 👇", MAIN_MENU)

        if cmd == "/help":
            return await self._reply(session, chat_id, HELP_TEXT)

        if cmd == "/status":
            up = int(time.time() - b.started_at)
            evo = bool(b.evo_cycle_task and not b.evo_cycle_task.done())
            msg = (
                "📊 বটের অবস্থা\n"
                f"🔌 গেম কানেকশন: {'✅ সংযুক্ত' if self._ready() else '❌ সংযুক্ত নয়'}\n"
                f"🆔 বট UID: {b.bot_uid}\n"
                f"👤 নাম: {b.bot_nickname}\n"
                f"🌍 অঞ্চল: {b.region}\n"
                f"⚙️ গেম-চ্যাট কমান্ড: {'চালু' if b.bot_enabled else 'বন্ধ'}\n"
                f"🎮 গেম কন্ট্রোল মোড: {MODE_NAMES.get(b.game_control_mode, b.game_control_mode)}\n"
                f"🔁 ইভো সাইকেল: {'চলছে' if evo else 'বন্ধ'}\n"
                f"⏱ আপটাইম: {up // 3600} ঘণ্টা {(up % 3600) // 60} মিনিট"
            )
            return await self._reply(session, chat_id, msg)

        if cmd == "/debug":
            on = bool(args) and args[0].lower() in ("on", "1", "yes")
            b.debug_packets = on
            return await self._reply(session, chat_id, f"🐞 ডিবাগ প্যাকেট: {'চালু (৩ সেকেন্ড পরপর একটা)' if on else 'বন্ধ'}\nউদাহরণ: /debug on  |  /debug off")

        if cmd == "/gamectl":
            names = {"all": "সবাই", "admin": "শুধু অ্যাডমিন", "off": "বন্ধ"}
            if not args or args[0].lower() not in names:
                return await self._reply(session, chat_id, "ব্যবহার: /gamectl all | admin | off")
            b.game_control_mode = args[0].lower()
            note = ""
            if b.game_control_mode == "admin" and not getattr(b, "admin_uid", ""):
                note = "\n⚠️ ADMIN_UID সেট নেই, তাই গেম থেকে কেউই কমান্ড দিতে পারবে না। Environment-এ ADMIN_UID দিন।"
            return await self._reply(session, chat_id, f"🎮 গেম কন্ট্রোল: {names[b.game_control_mode]}{note}")

        if cmd == "/on":
            b.bot_enabled = True
            return await self._reply(session, chat_id, "✅ বট চালু করা হয়েছে")

        if cmd == "/off":
            b.bot_enabled = False
            return await self._reply(session, chat_id, "⛔ বট বন্ধ করা হয়েছে")

        if cmd == "/setaccount":
            import RAFIN
            if len(args) < 2 or not args[0].isdigit():
                return await self._reply(session, chat_id, "ব্যবহার: /setaccount <uid> <password> [region]\nউদাহরণ: /setaccount 123456789 ABCDEF... BD")
            region = args[2].upper() if len(args) >= 3 else None
            RAFIN.save_account(args[0], args[1], region)
            # পাসওয়ার্ড চ্যাটে থেকে না যাওয়ার জন্য মেসেজ মুছে ফেলা
            try:
                await self._call(session, "deleteMessage", chat_id=chat_id, message_id=msg_id)
            except Exception:
                pass
            await self._reply(session, chat_id, f"✅ অ্যাকাউন্ট সেভ হয়েছে (UID: {args[0]})\n🔄 নতুন অ্যাকাউন্টে লগইন হচ্ছে ...\n(নিরাপত্তার জন্য আপনার মেসেজটি মুছে দেওয়া হয়েছে)")
            if b.session_task and not b.session_task.done():
                b.session_task.cancel()
            return

        if cmd == "/account":
            import RAFIN
            uid_, pw_, reg_ = RAFIN.get_account()
            if not uid_:
                return await self._reply(session, chat_id, "ℹ️ কোনো অ্যাকাউন্ট সেট নেই। /setaccount ব্যবহার করুন।")
            return await self._reply(session, chat_id, f"🔑 বর্তমান অ্যাকাউন্ট\nUID: {uid_}\nপাসওয়ার্ড: {pw_[:4]}****{pw_[-4:] if len(pw_) > 8 else ''}\nঅঞ্চল: {reg_}")

        if cmd == "/delaccount":
            import RAFIN
            RAFIN.clear_account()
            return await self._reply(session, chat_id, "🗑 সেভ করা অ্যাকাউন্ট মুছে ফেলা হয়েছে (ডিফল্ট Environment মান থাকলে সেটা ব্যবহার হবে)। /restart দিন।")

        if cmd == "/restart":
            await self._reply(session, chat_id, "🔄 রিস্টার্ট হচ্ছে ...")
            if b.session_task and not b.session_task.done():
                b.session_task.cancel()
            return

        if cmd == "/sevos":
            if b.evo_cycle_task and not b.evo_cycle_task.done():
                b.evo_cycle_running = False
                b.evo_cycle_task.cancel()
                return await self._reply(session, chat_id, "✅ ইভো সাইকেল বন্ধ করা হয়েছে")
            return await self._reply(session, chat_id, "ℹ️ ইভো সাইকেল চলছে না")

        # নিচের কমান্ডগুলোর জন্য গেম কানেকশন লাগবে
        game_cmds = ("/join", "/exit", "/leave", "/emote", "/e", "/evo", "/evos", "/bundle", "/b", "/badge")
        if cmd in game_cmds and not self._ready():
            return await self._reply(session, chat_id, self._need_ready_msg())

        key, iv = b.bot_key, b.bot_iv

        if cmd == "/join":
            if not args:
                return await self._reply(session, chat_id, "ব্যবহার: /join <স্কোয়াড কোড>")
            pkt = await b.JoinSq_original(args[0], key, iv)
            await b.SEndPacKeT(b.whisper_writer, b.online_writer, "OnLine", pkt)
            return await self._reply(session, chat_id, f"✅ স্কোয়াডে জয়েন করা হয়েছে: {args[0]}")

        if cmd in ("/exit", "/leave"):
            pkt = await b.ExiT(None, key, iv)
            await b.SEndPacKeT(b.whisper_writer, b.online_writer, "OnLine", pkt)
            return await self._reply(session, chat_id, "✅ স্কোয়াড ত্যাগ করা হয়েছে")

        if cmd in ("/emote", "/e"):
            if len(args) < 2:
                return await self._reply(session, chat_id, "ব্যবহার: /emote <uid> [uid2 ...] <ইমোট নম্বর/নাম>")
            emote_id = self._resolve_emote(args[-1])
            if emote_id is None:
                return await self._reply(session, chat_id, f"❌ ইমোট '{args[-1]}' পাওয়া যায়নি")
            uids = [a for a in args[:-1] if a.isdigit()]
            if not uids:
                return await self._reply(session, chat_id, "❌ কমপক্ষে একটি সঠিক UID দিন")
            n = await self._send_emote(uids, emote_id)
            return await self._reply(session, chat_id, f"✅ {n} জনকে ইমোট পাঠানো হয়েছে")

        if cmd == "/evo":
            if len(args) < 2:
                return await self._reply(session, chat_id, "ব্যবহার: /evo <uid> [uid2 ...] <ইমোট নম্বর>")
            emote_id = self._resolve_emote(args[-1])
            if emote_id is None:
                return await self._reply(session, chat_id, f"❌ ইমোট '{args[-1]}' পাওয়া যায়নি")
            uids = [a for a in args[:-1] if a.isdigit()]
            if not uids:
                return await self._reply(session, chat_id, "❌ কমপক্ষে একটি সঠিক UID দিন")
            n = await self._send_emote(uids, emote_id)
            return await self._reply(session, chat_id, f"✅ ইভো ইমোট {args[-1]} পাঠানো হয়েছে ({n} জন)")

        if cmd == "/evos":
            uids = [a for a in args if a.isdigit() and len(a) >= 7]
            if not uids:
                return await self._reply(session, chat_id, "ব্যবহার: /evos <uid> [uid2 ...]")
            if b.evo_cycle_task and not b.evo_cycle_task.done():
                b.evo_cycle_running = False
                b.evo_cycle_task.cancel()
                await asyncio.sleep(0.3)
            b.evo_cycle_running = True
            b.evo_cycle_task = asyncio.create_task(
                b.evo_gun_cycle(uids, b.EVO_IDS, key, iv, b.region)
            )
            return await self._reply(session, chat_id, "✅ ইভো সাইকেল চালু হয়েছে (বন্ধ করতে /sevos)")

        if cmd in ("/bundle", "/b"):
            if not args or args[0] not in BUNDLE_IDS:
                return await self._reply(session, chat_id, "ব্যবহার: /bundle <১-১২>")
            bid = BUNDLE_IDS[args[0]]
            anim = await b.animation_packet(bid, key, iv)
            if anim and b.online_writer:
                b.online_writer.write(anim)
                await b.online_writer.drain()
            await asyncio.sleep(3)
            pkt = await b.Look_Changer(bid, key, iv, look_type=1, region=b.region)
            if pkt and b.online_writer:
                b.online_writer.write(pkt)
                await b.online_writer.drain()
            return await self._reply(session, chat_id, f"✅ বান্ডেল {args[0]} পাঠানো হয়েছে")

        if cmd == "/badge":
            if len(args) < 2 or args[0].lower() not in b.BADGE_VALUES or not args[1].isdigit():
                return await self._reply(session, chat_id, "ব্যবহার: /badge <s1-s5> <uid>")
            pkt = await b.request_join_with_badge(args[1], b.BADGE_VALUES[args[0].lower()], key, iv, b.region)
            if not pkt:
                return await self._reply(session, chat_id, "❌ প্যাকেট তৈরি ব্যর্থ")
            for _ in range(5):
                await b.SEndPacKeT(b.whisper_writer, b.online_writer, "OnLine", pkt)
                await asyncio.sleep(0.2)
            return await self._reply(session, chat_id, f"✅ ব্যাজ {args[0]} → {args[1]} (৫ বার)")

        if cmd in ("/add", "/remove"):
            if not args or not args[0].isdigit():
                return await self._reply(session, chat_id, f"ব্যবহার: {cmd} <uid>")
            if not b.ToKen:
                return await self._reply(session, chat_id, self._need_ready_msg())
            fn = b.send_friend_request if cmd == "/add" else b.remove_friend
            ok, msg = await fn(args[0], b.ToKen, b.region)
            return await self._reply(session, chat_id, f"{'✅' if ok else '❌'} {msg}")

        if cmd == "/info":
            if not args or not args[0].isdigit():
                return await self._reply(session, chat_id, "ব্যবহার: /info <uid>")
            ok, data = await b.get_player_info(args[0])
            if not ok:
                return await self._reply(session, chat_id, f"❌ {data}")
            basic = data.get("basicInfo", {})
            captain = data.get("captainBasicInfo", {})
            clan = data.get("clanBasicInfo", {})
            msg = (
                "🎮 প্লেয়ার তথ্য\n"
                f"নাম: {captain.get('nickname', basic.get('nickname', 'অজানা'))}\n"
                f"UID: {captain.get('accountId', basic.get('accountId', args[0]))}\n"
                f"লেভেল: {captain.get('level', basic.get('level', '0'))}\n"
                f"লাইক: {captain.get('liked', basic.get('liked', '0'))}\n"
                f"অঞ্চল: {captain.get('region', basic.get('region', 'অজানা'))}\n"
                f"গিল্ড: {clan.get('clanName', 'নেই')}"
            )
            return await self._reply(session, chat_id, msg)

        if cmd == "/check":
            if not args or not args[0].isdigit():
                return await self._reply(session, chat_id, "ব্যবহার: /check <uid>")
            ok, data = await b.check_banned(args[0])
            if not ok:
                return await self._reply(session, chat_id, f"❌ {data}")
            return await self._reply(
                session, chat_id,
                f"🔍 ব্যান চেক\nধরন: {data.get('ban_type', 'অজানা')}\nসময়কাল: {data.get('ban_duration', 'অজানা')}",
            )

        await self._reply(session, chat_id, "❓ অজানা কমান্ড। /help দিয়ে তালিকা দেখুন।")

    # ───────────── বাটন (callback) হ্যান্ডলার ─────────────
    async def on_callback(self, session, cq):
        user = (cq.get("from") or {}).get("id")
        chat = ((cq.get("message") or {}).get("chat") or {}).get("id")
        data = cq.get("data") or ""
        try:
            await self._call(session, "answerCallbackQuery", callback_query_id=cq["id"])
        except Exception:
            pass
        if chat is None or user not in self.admin_ids:
            return
        try:
            kind, _, arg = data.partition(":")
            if data == "menu":
                self.pending.pop(chat, None)
                await self._reply(session, chat, "🤖 বট কন্ট্রোল মেনু\nনিচের বাটন চেপে কন্ট্রোল করুন 👇", MAIN_MENU)
            elif kind == "run":
                self.pending.pop(chat, None)
                await self.handle(session, chat, arg)
            elif kind == "ask":
                self.pending[chat] = arg
                base = arg.split()[0]
                prompt = PROMPTS.get(base, "ইনপুট লিখুন:")
                if base == "/badge":
                    prompt = f"🏅 {arg.split()[1].upper()} ব্যাজ — যাকে পাঠাবেন তার UID লিখুন:"
                await self._reply(session, chat, prompt, CANCEL_MARKUP)
            elif kind == "sub":
                if arg == "bundle":
                    await self._reply(session, chat, "🎁 বান্ডেল নম্বর বেছে নিন:", bundle_menu())
                elif arg == "gamectl":
                    mode = getattr(self.bot, "game_control_mode", "all")
                    names = {"all": "সবাই", "admin": "শুধু অ্যাডমিন", "off": "বন্ধ"}
                    await self._reply(session, chat, f"🎮 গেম-চ্যাট কন্ট্রোল\nবর্তমান: {names.get(mode, mode)}\n\nকে গেমের চ্যাট থেকে বটকে কমান্ড দিতে পারবে বেছে নিন:", gamectl_menu())
                elif arg == "badge":
                    await self._reply(session, chat, "🏅 ব্যাজ টাইপ বেছে নিন:", badge_menu())
        except Exception as e:
            await self._reply(session, chat, f"⚠️ ত্রুটি: {str(e)[:200]}")

    # ───────────── পোলিং লুপ ─────────────
    async def run(self):
        print(f"[TG] টেলিগ্রাম কন্ট্রোল চালু — অ্যাডমিন: {sorted(self.admin_ids)}")
        async with aiohttp.ClientSession() as session:
            try:
                await self._call(session, "setMyCommands", commands=[
                    {"command": "menu", "description": "কন্ট্রোল মেনু (বাটন)"},
                    {"command": "status", "description": "বটের অবস্থা"},
                    {"command": "help", "description": "সব কমান্ডের তালিকা"},
                ])
            except Exception:
                pass
            while True:
                try:
                    res = await self._call(
                        session, "getUpdates", offset=self.offset, timeout=50,
                        allowed_updates=["message", "callback_query"],
                    )
                    for upd in res.get("result", []):
                        self.offset = upd["update_id"] + 1
                        cq = upd.get("callback_query")
                        if cq:
                            await self.on_callback(session, cq)
                            continue
                        msg = upd.get("message") or {}
                        text = msg.get("text")
                        user = (msg.get("from") or {}).get("id")
                        chat = (msg.get("chat") or {}).get("id")
                        if not text or chat is None:
                            continue
                        if user not in self.admin_ids:
                            await self._reply(session, chat, "⛔ আপনার অনুমতি নেই।")
                            continue
                        # বাটন চাপার পর ইনপুটের অপেক্ষায় থাকলে সেটা কমান্ডের সাথে জুড়ে দেওয়া
                        if text.startswith("/"):
                            self.pending.pop(chat, None)
                        elif chat in self.pending:
                            text = f"{self.pending.pop(chat)} {text}"
                        try:
                            await self.handle(session, chat, text, msg.get("message_id"))
                        except Exception as e:
                            await self._reply(session, chat, f"⚠️ ত্রুটি: {str(e)[:200]}")
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    print(f"[TG] polling error: {e}")
                    await asyncio.sleep(5)


_active = None


async def notify(text):
    """সব অ্যাডমিনকে মেসেজ পাঠায়"""
    c = _active
    if not c:
        return
    try:
        async with aiohttp.ClientSession() as session:
            for chat in c.admin_ids:
                await c._reply(session, chat, text, None)
    except Exception as e:
        print(f"[TG] notify error: {e}")


def start(bot_module):
    """main.py থেকে কল হয়। টোকেন/অ্যাডমিন সেট না থাকলে কন্ট্রোল বন্ধ থাকে।"""
    import RAFIN
    token = (RAFIN.TELEGRAM_BOT_TOKEN or "").strip()
    ids_raw = (RAFIN.TELEGRAM_ADMIN_IDS or "").strip()
    if token.startswith("PASTE_"):
        token = ""
    admin_ids = {int(x) for x in ids_raw.replace(" ", "").split(",") if x.lstrip("-").isdigit()}
    if not token or not admin_ids:
        print("[TG] RAFIN.py-তে TELEGRAM_BOT_TOKEN / TELEGRAM_ADMIN_IDS সেট নেই — টেলিগ্রাম কন্ট্রোল বন্ধ")
        return None
    global _active
    _active = TgController(bot_module, token, admin_ids)
    return asyncio.create_task(_active.run())
