import telebot
from telebot import types
import sqlite3

# =============== SOZLAMALAR ===============
TOKEN = "8224112508:AAHUE3dwCZZBbNHnKA9yHaCE4aev6J3Uvdc"
ADMIN_ID = 7249489494
ADMIN_USERNAME = "@xudrganov"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# =============== DATABASE ===============
conn = sqlite3.connect("my_bot_base.db", check_same_thread=False)
cur = conn.cursor()

# USERS
cur.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")

# PROJECTS
cur.execute("""
CREATE TABLE IF NOT EXISTS projects(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    link TEXT,
    photo TEXT
)
""")

# SERVICES
cur.execute("""
CREATE TABLE IF NOT EXISTS services(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    link TEXT,
    photo TEXT
)
""")
conn.commit()

admin_step = {}
support_wait = {}

# =============== BUTTONS ===============
def main_buttons(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📂 Loyihalarim", "🧑‍💻 Y. Xizmatlar")
    kb.row("👤 Admin haqida", "📞 Admin murojaat")
    if uid == ADMIN_ID:
        kb.row("🛠 Admin Panel")
    return kb

def admin_panel():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("➕ Loyiha qo‘shish", callback_data="add_project"))
    kb.add(types.InlineKeyboardButton("🗂 Loyihalarni boshqarish", callback_data="manage_projects"))
    kb.add(types.InlineKeyboardButton("⚙️ Xizmatlarni boshqarish", callback_data="manage_services"))
    kb.add(types.InlineKeyboardButton("📢 Xabar yuborish", callback_data="send_all"))
    kb.add(types.InlineKeyboardButton("📊 Statistika", callback_data="stats"))
    return kb

# =============== START ==================
@bot.message_handler(commands=["start"])
def start(m):
    cur.execute("INSERT OR IGNORE INTO users VALUES (?)", (m.chat.id,))
    conn.commit()
    bot.send_message(
        m.chat.id,
        f"Salom <b>{m.from_user.first_name}</b> 👋\nBotimizga xush kelibsiz!",
        reply_markup=main_buttons(m.chat.id)
    )

# =============== TEXT HANDLER ==================
@bot.message_handler(func=lambda m: True)
def texts(m):
    uid = m.chat.id
    txt = m.text

    # USER → ADMIN SUPPORT
    if uid in support_wait:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("✉️ Javob berish", callback_data=f"reply_{uid}"))
        bot.send_message(ADMIN_ID, f"📩 <b>Yangi xabar:</b>\n\n{txt}", reply_markup=kb)
        bot.send_message(uid, "✅ Xabaringiz yuborildi.")
        del support_wait[uid]
        return

    # ADMIN STEPS
    if uid == ADMIN_ID and uid in admin_step:
        step = admin_step[uid].get("step")
        
        if step == "support_reply":
            bot.send_message(admin_step[uid]["to"], f"👨‍💻 <b>Admin javobi:</b>\n{txt}")
            bot.send_message(uid, "✅ Javob yuborildi")
            del admin_step[uid]
            return

        if step == "name":
            admin_step[uid].update({"name": txt, "step": "desc"})
            bot.send_message(uid, "📝 Loyiha tavsifini yuboring:")
            return
        elif step == "desc":
            admin_step[uid].update({"desc": txt, "step": "link"})
            bot.send_message(uid, "🔗 Loyiha linkini yuboring:")
            return
        elif step == "link":
            admin_step[uid].update({"link": txt, "step": "photo"})
            bot.send_message(uid, "🖼 Loyiha rasmini yuboring:")
            return

        if step == "service_name":
            admin_step[uid].update({"name": txt, "step": "service_desc"})
            bot.send_message(uid, "📝 Xizmat tavsifini yuboring:")
            return
        elif step == "service_desc":
            admin_step[uid].update({"desc": txt, "step": "service_link"})
            bot.send_message(uid, "🔗 Bog'lanish linkini yuboring:")
            return
        elif step == "service_link":
            admin_step[uid].update({"link": txt, "step": "service_photo"})
            bot.send_message(uid, "🖼 Xizmat rasmini yuboring:")
            return

        if step == "send_all":
            cur.execute("SELECT user_id FROM users")
            users = cur.fetchall()
            for u in users:
                try: bot.copy_message(u[0], uid, m.message_id)
                except: pass
            bot.send_message(uid, f"✅ {len(users)} ta foydalanuvchiga yuborildi.")
            del admin_step[uid]
            return

    # MENYU QISMI
    if txt == "📂 Loyihalarim":
        cur.execute("SELECT id, name FROM projects")
        res = cur.fetchall()
        if not res:
            bot.send_message(uid, "❌ Hozircha loyihalar yo‘q.")
            return
        kb = types.InlineKeyboardMarkup()
        for r in res: kb.add(types.InlineKeyboardButton(r[1], callback_data=f"view_{r[0]}"))
        bot.send_message(uid, "📂 Loyihalar ro‘yxati:", reply_markup=kb)

    elif txt == "🧑‍💻 Y. Xizmatlar":
        cur.execute("SELECT id, name FROM services")
        res = cur.fetchall()
        if not res:
            bot.send_message(uid, "❌ Hozircha xizmatlar mavjud emas.")
            return
        kb = types.InlineKeyboardMarkup()
        for r in res: kb.add(types.InlineKeyboardButton(r[1], callback_data=f"v_ser_{r[0]}"))
        bot.send_message(uid, "🧑‍💻 Mavjud xizmatlar:", reply_markup=kb)

    elif txt == "👤 Admin haqida":
        bot.send_message(uid, f"<b>👤 Admin haqida</b>\n\nIsm: Anvarbek\nFamilya: Xudarganov\nYosh: 11.04.2008\nYo‘nalish: IT soxasi ⚡")

    elif txt == "📞 Admin murojaat":
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("✉️ Xabar yuborish", callback_data="contact_admin"))
        bot.send_message(uid, "Admin bilan bog‘lanish uchun pastdagi tugmani bosing:", reply_markup=kb)

    elif txt == "🛠 Admin Panel" and uid == ADMIN_ID:
        bot.send_message(uid, "🛠 Admin Panelga xush kelibsiz:", reply_markup=admin_panel())

# ================== PHOTO HANDLER ==================
@bot.message_handler(content_types=["photo"])
def photo_handler(m):
    uid = m.chat.id
    if uid == ADMIN_ID and uid in admin_step:
        step = admin_step[uid].get("step")
        fid = m.photo[-1].file_id
        
        if step == "photo":
            cur.execute("INSERT INTO projects (name, description, link, photo) VALUES (?,?,?,?)",
                        (admin_step[uid]["name"], admin_step[uid]["desc"], admin_step[uid]["link"], fid))
            conn.commit()
            bot.send_message(uid, "✅ Yangi loyiha saqlandi!")
            del admin_step[uid]
            
        elif step == "service_photo":
            cur.execute("INSERT INTO services (name, description, link, photo) VALUES (?,?,?,?)",
                        (admin_step[uid]["name"], admin_step[uid]["desc"], admin_step[uid]["link"], fid))
            conn.commit()
            bot.send_message(uid, "✅ Yangi xizmat saqlandi!")
            del admin_step[uid]

# ================== CALLBACK HANDLER ==================
@bot.callback_query_handler(func=lambda c: True)
def callback_handler(c):
    uid = c.message.chat.id
    data = c.data
    bot.answer_callback_query(c.id)

    # Aloqa
    if data == "contact_admin":
        support_wait[uid] = True
        bot.send_message(uid, "✍️ Admin uchun xabaringizni yozing:")

    elif data.startswith("reply_"):
        admin_step[uid] = {"step": "support_reply", "to": int(data.split("_")[1])}
        bot.send_message(uid, "✍️ Javobingizni yozing:")

    # LOYIHA KO'RISH
    elif data.startswith("view_"):
        pid = data.split("_")[1]
        cur.execute("SELECT * FROM projects WHERE id=?", (pid,))
        p = cur.fetchone()
        if p:
            kb = types.InlineKeyboardMarkup()
            url = p[3] if p[3].startswith("http") else f"https://t.me/{p[3].replace('@','')}"
            kb.add(types.InlineKeyboardButton("🔗 Loyihani ko'rish", url=url))
            bot.send_photo(uid, p[4], f"<b>{p[1]}</b>\n\n{p[2]}", reply_markup=kb)

    # XIZMAT KO'RISH (Sizda xato shu yerda edi)
    elif data.startswith("v_ser_"):
        sid = data.split("_")[2]
        cur.execute("SELECT * FROM services WHERE id=?", (sid,))
        s = cur.fetchone()
        if s:
            kb = types.InlineKeyboardMarkup()
            url = s[3] if s[3].startswith("http") else f"https://t.me/{s[3].replace('@','')}"
            kb.add(types.InlineKeyboardButton("🔗 Bog‘lanish / Buyurtma", url=url))
            bot.send_photo(uid, s[4], f"<b>{s[1]}</b>\n\n{s[2]}", reply_markup=kb)

    # ADMIN: Boshqarish
    elif data == "manage_projects":
        cur.execute("SELECT id, name FROM projects")
        kb = types.InlineKeyboardMarkup()
        for r in cur.fetchall():
            kb.row(types.InlineKeyboardButton(f"🗑 {r[1]}", callback_data=f"del_pro_{r[0]}"))
        bot.send_message(uid, "O'chirmoqchi bo'lgan loyihangizni tanlang:", reply_markup=kb)

    elif data == "manage_services":
        cur.execute("SELECT id, name FROM services")
        kb = types.InlineKeyboardMarkup()
        for r in cur.fetchall():
            kb.row(types.InlineKeyboardButton(f"🗑 {r[1]}", callback_data=f"del_ser_{r[0]}"))
        bot.send_message(uid, "O'chirmoqchi bo'lgan xizmatni tanlang:", reply_markup=kb)

    elif data.startswith("del_pro_"):
        cur.execute("DELETE FROM projects WHERE id=?", (data.split("_")[2],))
        conn.commit()
        bot.edit_message_text("✅ Loyiha o'chirildi", uid, c.message.message_id)

    elif data.startswith("del_ser_"):
        cur.execute("DELETE FROM services WHERE id=?", (data.split("_")[2],))
        conn.commit()
        bot.edit_message_text("✅ Xizmat o'chirildi", uid, c.message.message_id)

    elif data == "add_project":
        admin_step[uid] = {"step": "name"}
        bot.send_message(uid, "📌 Loyiha nomini yozing:")

    elif data == "add_service":
        admin_step[uid] = {"step": "service_name"}
        bot.send_message(uid, "📌 Xizmat nomini yozing:")

    elif data == "stats":
        cur.execute("SELECT COUNT(*) FROM users")
        u_count = cur.fetchone()[0]
        bot.send_message(uid, f"📊 Bot a'zolari: {u_count} ta")

# ================== RUN ==================
print("BOT ISHGA TUSHDI 🚀")
bot.infinity_polling()
