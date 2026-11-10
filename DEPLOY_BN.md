# GitHub + Render + Telegram কন্ট্রোল গাইড

## ১) Telegram বট বানান
1. Telegram-এ **@BotFather** → `/newbot` → নাম দিন → **টোকেন** কপি করুন।
2. **@userinfobot**-এ `/start` দিয়ে আপনার **ইউজার আইডি** (সংখ্যা) নিন।
3. নিজের নতুন বটে একবার `/start` পাঠান।

## ২) GitHub-এ আপলোড
এই ফোল্ডারের সব ফাইল repo-র root-এ আপলোড করুন (কোনো ফোল্ডার নেই)। Repo **Private** রাখুন।

## ৩) Render → Environment
| Key | মান |
|---|---|
| `BOT_UID` | গেম অ্যাকাউন্টের UID |
| `BOT_PASSWORD` | গেম অ্যাকাউন্টের পাসওয়ার্ড |
| `BOT_REGION` | `BD` |
| `ADMIN_UID` | গেমে অ্যাডমিন হিসেবে যে UID থাকবে |
| `TELEGRAM_BOT_TOKEN` | (ঐচ্ছিক) RAFIN.py-তে বসালে লাগবে না |
| `TELEGRAM_ADMIN_IDS` | আপনার টেলিগ্রাম ইউজার আইডি (একাধিক হলে কমা দিয়ে) |

Build: `pip install -r requirements.txt` · Start: `python main.py` · Python 3.12

## ৪) বন্ধ হয়ে যাওয়া ঠেকাতে
Free Web Service ১৫ মিনিট নিষ্ক্রিয় থাকলে ঘুমায়। UptimeRobot-এ
`https://আপনার-অ্যাপ.onrender.com/health` প্রতি ৫ মিনিটে পিং করান।

## ৫) টেলিগ্রাম কমান্ড
`/help` দিলেই পুরো তালিকা পাবেন: `/status /on /off /restart /join /exit /emote /evo /evos /sevos /bundle /badge /add /remove /info /check`
