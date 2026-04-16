import discord
from discord.ext import tasks
from discord import app_commands
from datetime import datetime, timedelta
import os
import json
import threading
from flask import Flask

# ==========================
# CONFIG
# ==========================
TOKEN = os.getenv("DISCORD_TOKEN")
TIME_FORMAT = "%Y-%m-%d %H:%M"
EVENTS_FILE = "events.json"

events: dict[int, dict] = {}
event_counter = 1

# ==========================
# BOT SETUP
# ==========================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

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
            "title": v["title"],
            "description": v["description"],
            "time": datetime.strptime(v["time"], TIME_FORMAT),
            "remind_type": v.get("remind_type", "none"),
            "remind_value": v.get("remind_value"),
            "next_remind": datetime.strptime(v["next_remind"], TIME_FORMAT) if v.get("next_remind") else None,
            "users": set(v.get("users", [])),
            "ticket_msg": v.get("ticket_msg"),
            "remind_channel_id": v["remind_channel_id"],
            "reminded": v.get("reminded", False),
            "canceled": v.get("canceled", False),
        }

    event_counter = max_id + 1


def save_events():
    data = {}
    for eid, v in events.items():
        data[str(eid)] = {
            "title": v["title"],
            "description": v["description"],
            "time": v["time"].strftime(TIME_FORMAT),
            "remind_type": v["remind_type"],
            "remind_value": v["remind_value"],
            "next_remind": v["next_remind"].strftime(TIME_FORMAT) if v["next_remind"] else None,
            "users": list(v["users"]),
            "ticket_msg": v["ticket_msg"],
            "remind_channel_id": v["remind_channel_id"],
            "reminded": v["reminded"],
            "canceled": v["canceled"],
        }

    with open(EVENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ==========================
# FIXED: REMIND LOGIC
# ==========================
def compute_next_remind(ev: dict) -> datetime | None:
    now = datetime.now()
    start = ev["time"]
    rtype = ev["remind_type"]
    rval = ev["remind_value"]

    if ev["canceled"]:
        return None

    # --- NONE ---
    if rtype == "none":
        if ev["reminded"]:
            return None
        if start <= now:
            return None
        return start

    # --- BEFORE ---
    if rtype == "before":
        if ev["reminded"]:
            return None
        remind_time = start - timedelta(minutes=rval)
        if remind_time <= now:
            return None
        return remind_time

    # --- DAILY ---
    if rtype == "daily":
        base = start.replace(year=now.year, month=now.month, day=now.day)
        if base <= now:
            base += timedelta(days=1)
        return base

    # --- WEEKLY ---
    if rtype == "weekly":
        base = start.replace(year=now.year, month=now.month, day=now.day)
        diff = (start.weekday() - base.weekday()) % 7
        base += timedelta(days=diff)
        if base <= now:
            base += timedelta(weeks=1)
        return base

    return None


async def send_event_reminder(event_id: int):
    ev = events[event_id]
    channel = bot.get_channel(ev["remind_channel_id"])
    if not channel:
        return

    if not ev["users"]:
        await channel.send(f"⏰ Event **#{event_id} — {ev['title']}** đến giờ nhưng chưa có ai đăng ký.")
    else:
        mentions = " ".join([f"<@{uid}>" for uid in ev["users"]])
        await channel.send(
            f"⏰ **REMIND EVENT #{event_id} — {ev['title']}**\n"
            f"{mentions}\n"
            f"🕒 {ev['time'].strftime(TIME_FORMAT)}\n"
            f"📄 {ev['description']}"
        )


async def create_ticket_message(ev_id: int):
    ev = events[ev_id]
    channel = bot.get_channel(ev["remind_channel_id"])
    if not channel:
        return

    # Xóa ticket cũ
    if ev["ticket_msg"]:
        try:
            old = await channel.fetch_message(ev["ticket_msg"])
            await old.delete()
        except:
            pass

    embed = discord.Embed(
        title=f"🎫 Đăng ký Event #{ev_id} — {ev['title']}",
        description=ev["description"],
        color=discord.Color.blue(),
    )
    embed.add_field(name="🕒 Thời gian", value=ev["time"].strftime(TIME_FORMAT), inline=False)

    rtype = ev["remind_type"]
    if rtype == "none":
        rtext = "Không nhắc"
    elif rtype == "daily":
        rtext = "Nhắc hàng ngày"
    elif rtype == "weekly":
        rtext = "Nhắc hàng tuần"
    else:
        rtext = f"Nhắc trước {ev['remind_value']} phút"

    embed.add_field(name="🔔 Remind", value=rtext, inline=False)
    embed.set_footer(text="React 👍 để đăng ký")

    msg = await channel.send(embed=embed)
    await msg.add_reaction("👍")

    ev["ticket_msg"] = msg.id
    save_events()


# ==========================
# BACKGROUND REMIND LOOP
# ==========================
@tasks.loop(seconds=30)
async def event_checker():
    now = datetime.now()
    for event_id, ev in list(events.items()):
        nr = ev["next_remind"]
        if not nr or ev["canceled"]:
            continue

        if now >= nr:
            await send_event_reminder(event_id)

            if ev["remind_type"] in ("none", "before"):
                ev["reminded"] = True
                ev["next_remind"] = None
            elif ev["remind_type"] == "daily":
                ev["next_remind"] = nr + timedelta(days=1)
            elif ev["remind_type"] == "weekly":
                ev["next_remind"] = nr + timedelta(weeks=1)

            save_events()


# ==========================
# SLASH COMMANDS
# ==========================
@tree.command(name="create_event", description="Tạo event mới")
@app_commands.describe(
    title="Tiêu đề",
    description="Nội dung",
    start_time="YYYY-MM-DD HH:MM",
    remind_type="none/daily/weekly/before",
    minutes_before="Phút nhắc trước (nếu dùng before)",
    remind_channel="Kênh nhắc & ticket"
)
async def create_event(
    interaction: discord.Interaction,
    title: str,
    description: str,
    start_time: str,
    remind_type: str,
    remind_channel: discord.TextChannel,
    minutes_before: int | None = None,
):
    global event_counter
    await interaction.response.defer(ephemeral=True)

    remind_type = remind_type.lower()
    if remind_type not in ("none", "daily", "weekly", "before"):
        return await interaction.followup.send("❌ remind_type sai.", ephemeral=True)

    if remind_type == "before" and (not minutes_before or minutes_before <= 0):
        return await interaction.followup.send("❌ minutes_before phải > 0.", ephemeral=True)

    try:
        dt = datetime.strptime(start_time, TIME_FORMAT)
    except:
        return await interaction.followup.send("❌ Sai định dạng thời gian.", ephemeral=True)

    eid = event_counter
    event_counter += 1

    ev = {
        "title": title,
        "description": description,
        "time": dt,
        "remind_type": remind_type,
        "remind_value": minutes_before if remind_type == "before" else None,
        "next_remind": None,
        "users": set(),
        "ticket_msg": None,
        "remind_channel_id": remind_channel.id,
        "reminded": False,
        "canceled": False,
    }

    ev["next_remind"] = compute_next_remind(ev)
    events[eid] = ev
    save_events()

    await create_ticket_message(eid)

    await interaction.followup.send(
        f"✅ Event #{eid} đã tạo tại {remind_channel.mention}.",
        ephemeral=True
    )


@tree.command(name="edit_event", description="Chỉnh sửa event")
@app_commands.describe(
    event_id="ID event",
    title="Tiêu đề mới",
    description="Nội dung mới",
    start_time="YYYY-MM-DD HH:MM",
    remind_type="none/daily/weekly/before",
    minutes_before="Phút nhắc trước",
    remind_channel="Kênh nhắc mới"
)
async def edit_event(
    interaction: discord.Interaction,
    event_id: int,
    title: str | None = None,
    description: str | None = None,
    start_time: str | None = None,
    remind_type: str | None = None,
    remind_channel: discord.TextChannel | None = None,
    minutes_before: int | None = None,
):
    await interaction.response.defer(ephemeral=True)

    if event_id not in events:
        return await interaction.followup.send("❌ Event không tồn tại.", ephemeral=True)

    ev = events[event_id]

    if title:
        ev["title"] = title
    if description:
        ev["description"] = description
    if start_time:
        try:
            ev["time"] = datetime.strptime(start_time, TIME_FORMAT)
        except:
            return await interaction.followup.send("❌ Sai thời gian.", ephemeral=True)

    if remind_type:
        r = remind_type.lower()
        if r not in ("none", "daily", "weekly", "before"):
            return await interaction.followup.send("❌ remind_type sai.", ephemeral=True)
        ev["remind_type"] = r
        if r == "before":
            if not minutes_before or minutes_before <= 0:
                return await interaction.followup.send("❌ minutes_before sai.", ephemeral=True)
            ev["remind_value"] = minutes_before
        else:
            ev["remind_value"] = None

    if remind_channel:
        ev["remind_channel_id"] = remind_channel.id

    ev["reminded"] = False
    ev["next_remind"] = compute_next_remind(ev)
    save_events()

    await create_ticket_message(event_id)

    await interaction.followup.send(
        f"✏️ Event #{event_id} đã cập nhật.",
        ephemeral=True
    )


@tree.command(name="list_events", description="Danh sách event")
async def list_events(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    if not events:
        return await interaction.followup.send("Không có event.", ephemeral=True)

    msg = ""
    for eid, ev in events.items():
        rtype = ev["remind_type"]
        if rtype == "none":
            rtext = "Không nhắc"
        elif rtype == "daily":
            rtext = "Nhắc hàng ngày"
        elif rtype == "weekly":
            rtext = "Nhắc hàng tuần"
        else:
            rtext = f"Nhắc trước {ev['remind_value']} phút"

        msg += (
            f"**#{eid} — {ev['title']}**\n"
            f"🕒 {ev['time'].strftime(TIME_FORMAT)}\n"
            f"🔔 {rtext}\n"
            f"📢 Kênh: <#{ev['remind_channel_id']}>\n\n"
        )

    await interaction.followup.send(msg, ephemeral=True)


@tree.command(name="list_member", description="Danh sách đăng ký")
async def list_member(interaction: discord.Interaction, event_id: int):
    await interaction.response.defer(ephemeral=True)

    if event_id not in events:
        return await interaction.followup.send("❌ Event không tồn tại.", ephemeral=True)

    ev = events[event_id]
    if not ev["users"]:
        return await interaction.followup.send("Chưa ai đăng ký.", ephemeral=True)

    msg = "\n".join([f"- <@{uid}>" for uid in ev["users"]])
    await interaction.followup.send(msg, ephemeral=True)


@tree.command(name="cancel_event", description="Hủy event")
async def cancel_event(interaction: discord.Interaction, event_id: int):
    await interaction.response.defer(ephemeral=True)

    if event_id not in events:
        return await interaction.followup.send("❌ Event không tồn tại.", ephemeral=True)

    ev = events[event_id]
    ev["canceled"] = True
    ev["next_remind"] = None
    save_events()

    await interaction.followup.send(f"❌ Event #{event_id} đã hủy.", ephemeral=True)


@tree.command(name="delete_event", description="Xóa event")
async def delete_event(interaction: discord.Interaction, event_id: int):
    await interaction.response.defer(ephemeral=True)

    if event_id not in events:
        return await interaction.followup.send("❌ Event không tồn tại.", ephemeral=True)

    ev = events[event_id]
    channel = bot.get_channel(ev["remind_channel_id"])
    if channel and ev["ticket_msg"]:
        try:
            msg = await channel.fetch_message(ev["ticket_msg"])
            await msg.delete()
        except:
            pass

    del events[event_id]
    save_events()

    await interaction.followup.send(f"🗑️ Event #{event_id} đã xóa.", ephemeral=True)


# ==========================
# REACTION HANDLERS
# ==========================
@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return
    for eid, ev in events.items():
        if ev["ticket_msg"] == payload.message_id and str(payload.emoji) == "👍":
            ev["users"].add(payload.user_id)
            save_events()


@bot.event
async def on_raw_reaction_remove(payload):
    for eid, ev in events.items():
        if ev["ticket_msg"] == payload.message_id and str(payload.emoji) == "👍":
            ev["users"].discard(payload.user_id)
            save_events()


# ==========================
# BOT READY
# ==========================
@bot.event
async def on_ready():
    print(f"Bot đã đăng nhập: {bot.user}")

    load_events()

    for ev in events.values():
        ev["next_remind"] = compute_next_remind(ev)
    save_events()

    event_checker.start()

    await tree.sync()
    print("Slash commands synced.")


# ==========================
# FLASK KEEP-ALIVE
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
    threading.Thread(target=run_flask).start()
    bot.run(TOKEN)
