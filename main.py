import discord
from discord.ext import commands, tasks
from datetime import datetime
import threading
from flask import Flask
import os
import json

# ==========================
# CONFIG
# ==========================
TOKEN = os.getenv("DISCORD_TOKEN")  # Token từ biến môi trường
TIME_FORMAT = "%Y-%m-%d %H:%M"
EVENTS_FILE = "events.json"

# ==========================
# DATA STORAGE
# ==========================
# events = {
#   event_id: {
#       "time": datetime,
#       "users": set(),
#       "ticket_msg": int | None,
#       "channel_id": int,
#       "reminded": bool,
#       "canceled": bool
#   }
# }
events = {}
event_counter = 1

# ==========================
# BOT SETUP
# ==========================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ==========================
# JSON PERSISTENCE
# ==========================
def load_events():
    global events, event_counter
    if not os.path.exists(EVENTS_FILE):
        return

    with open(EVENTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    events = {}
    max_id = 0
    for k, v in data.items():
        eid = int(k)
        max_id = max(max_id, eid)
        events[eid] = {
            "time": datetime.strptime(v["time"], TIME_FORMAT),
            "users": set(v.get("users", [])),
            "ticket_msg": v.get("ticket_msg"),
            "channel_id": v["channel_id"],
            "reminded": v.get("reminded", False),
            "canceled": v.get("canceled", False),
        }

    event_counter = max_id + 1


def save_events():
    data = {}
    for eid, v in events.items():
        data[str(eid)] = {
            "time": v["time"].strftime(TIME_FORMAT),
            "users": list(v["users"]),
            "ticket_msg": v["ticket_msg"],
            "channel_id": v["channel_id"],
            "reminded": v["reminded"],
            "canceled": v["canceled"],
        }

    with open(EVENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ==========================
# HELPER FUNCTIONS
# ==========================
async def send_event_reminder(event_id):
    event = events[event_id]
    channel = bot.get_channel(event["channel_id"])

    if not channel:
        return

    if event["canceled"]:
        return

    if not event["users"]:
        await channel.send(f"⏰ Event **#{event_id}** đến giờ nhưng không có ai đăng ký.")
        event["reminded"] = True
        save_events()
        return

    mentions = " ".join([f"<@{uid}>" for uid in event["users"]])
    await channel.send(f"⏰ **REMIND EVENT #{event_id}!**\n{mentions}")

    event["reminded"] = True
    save_events()


# ==========================
# BACKGROUND TASK
# ==========================
@tasks.loop(seconds=30)
async def event_checker():
    now = datetime.now()
    for event_id, data in list(events.items()):
        if data["canceled"]:
            continue
        if not data["reminded"] and now >= data["time"]:
            await send_event_reminder(event_id)


# ==========================
# COMMANDS
# ==========================

@bot.command()
async def create_event(ctx, date: str, time: str):
    """
    Tạo event mới.
    Ví dụ: !create_event 2025-01-20 20:00
    """
    global event_counter

    try:
        dt = datetime.strptime(f"{date} {time}", TIME_FORMAT)
    except ValueError:
        await ctx.send("❌ Sai định dạng. Dùng: YYYY-MM-DD HH:MM")
        return

    event_id = event_counter
    event_counter += 1

    events[event_id] = {
        "time": dt,
        "users": set(),
        "ticket_msg": None,
        "channel_id": ctx.channel.id,
        "reminded": False,
        "canceled": False,
    }

    save_events()

    await ctx.send(
        f"🎉 **Event #{event_id}** đã được tạo!\n"
        f"⏰ Thời gian: {dt}\n"
        f"📢 Remind tại kênh: <#{ctx.channel.id}>"
    )


@bot.command()
async def ticket(ctx, event_id: int):
    """Tạo ticket đăng ký cho event."""
    if event_id not in events:
        await ctx.send("❌ Event không tồn tại.")
        return

    event = events[event_id]
    if event["canceled"]:
        await ctx.send("❌ Event này đã bị hủy.")
        return

    msg = await ctx.send(
        f"🎫 **Đăng ký Event #{event_id}**\n"
        f"React 👍 để tham gia."
    )
    await msg.add_reaction("👍")

    event["ticket_msg"] = msg.id
    save_events()

    await ctx.send(f"Ticket cho event #{event_id} đã tạo.")


@bot.command()
async def list_events(ctx):
    """Liệt kê tất cả event."""
    if not events:
        await ctx.send("Chưa có event nào.")
        return

    lines = []
    for eid, e in events.items():
        status = "✅" if not e["canceled"] else "❌ CANCELED"
        reminded = "🔔" if e["reminded"] else "⏳"
        lines.append(
            f"#{eid} | {e['time']} | Channel: <#{e['channel_id']}> | {status} | {reminded}"
        )

    await ctx.send("**Danh sách event:**\n" + "\n".join(lines))


@bot.command()
async def list_reg(ctx, event_id: int):
    """Liệt kê danh sách đăng ký."""
    if event_id not in events:
        await ctx.send("❌ Event không tồn tại.")
        return

    users = events[event_id]["users"]
    if not users:
        await ctx.send("Chưa có ai đăng ký.")
        return

    names = []
    for uid in users:
        user = await bot.fetch_user(uid)
        names.append(f"- {user.name}")

    await ctx.send(f"**Danh sách đăng ký Event #{event_id}:**\n" + "\n".join(names))


@bot.command()
async def edit_event(ctx, event_id: int, date: str, time: str):
    """
    Sửa thời gian event.
    Ví dụ: !edit_event 1 2025-01-21 19:00
    """
    if event_id not in events:
        await ctx.send("❌ Event không tồn tại.")
        return

    try:
        dt = datetime.strptime(f"{date} {time}", TIME_FORMAT)
    except ValueError:
        await ctx.send("❌ Sai định dạng. Dùng: YYYY-MM-DD HH:MM")
        return

    events[event_id]["time"] = dt
    events[event_id]["reminded"] = False
    save_events()

    await ctx.send(f"✏️ Đã sửa thời gian Event #{event_id} thành: {dt}")


@bot.command()
async def cancel_event(ctx, event_id: int):
    """Hủy event (không remind nữa, nhưng giữ trong danh sách)."""
    if event_id not in events:
        await ctx.send("❌ Event không tồn tại.")
        return

    events[event_id]["canceled"] = True
    save_events()

    await ctx.send(f"❌ Event #{event_id} đã bị hủy.")


@bot.command()
async def delete_event(ctx, event_id: int):
    """Xóa hoàn toàn event."""
    if event_id not in events:
        await ctx.send("❌ Event không tồn tại.")
        return

    del events[event_id]
    save_events()

    await ctx.send(f"🗑️ Event #{event_id} đã bị xóa.")


@bot.command()
async def force_remind(ctx, event_id: int):
    """Gửi remind thủ công."""
    if event_id not in events:
        await ctx.send("❌ Event không tồn tại.")
        return

    await send_event_reminder(event_id)


# ==========================
# EVENTS
# ==========================
@bot.event
async def on_ready():
    print(f"Bot đã đăng nhập: {bot.user}")
    load_events()
    event_checker.start()


@bot.event
async def on_raw_reaction_add(payload):
    """Thêm user vào danh sách đăng ký."""
    for event_id, data in events.items():
        if data["ticket_msg"] == payload.message_id and str(payload.emoji) == "👍":
            data["users"].add(payload.user_id)
            save_events()


@bot.event
async def on_raw_reaction_remove(payload):
    """Xóa user khỏi danh sách đăng ký."""
    for event_id, data in events.items():
        if data["ticket_msg"] == payload.message_id and str(payload.emoji) == "👍":
            data["users"].discard(payload.user_id)
            save_events()


# ==========================
# FLASK KEEP-ALIVE (Render)
# ==========================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=10000)


# ==========================
# START BOT
# ==========================
if __name__ == "__main__":
    load_events()
    threading.Thread(target=run_flask).start()
    bot.run(TOKEN)
