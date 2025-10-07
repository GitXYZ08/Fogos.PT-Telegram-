import logging
import requests
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, ContextTypes,
    CallbackQueryHandler, MessageHandler, filters
)

# Token do bot
TOKEN = "TOKEN_DO_TELEGRAM"
FOGOS_API = "https://api.fogos.pt/v2/incidents/active?all=1"

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ficheiros JSON
USERS_FILE = "users.json"
INCIDENTS_FILE = "incidents.json"

# Dados em memória
user_preferences = {}
previous_incidents = {}

# Lista de distritos
DISTRICTS = [
    "Todos", "Aveiro", "Beja", "Braga", "Bragança", "Castelo Branco",
    "Coimbra", "Évora", "Faro", "Guarda", "Leiria", "Lisboa", "Portalegre",
    "Porto", "Santarém", "Setúbal", "Viana do Castelo", "Vila Real", "Viseu",
    "Açores", "Madeira"
]

WELCOME_TEXT = (
    "🔥 *Bem-vindo ao Bot Fogos.PT* 🔥\n\n"
    "Comandos disponíveis:\n"
    "/start - Menu inicial\n"
    "/ver - Ver ocorrências\n"
    "/alterar - Alterar distrito\n\n"
    "🌐 Site: [Fogos.PT](https://fogos.pt)"
)

# ========= Utilitários =========

def carregar_dados():
    global user_preferences, previous_incidents
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            user_preferences = json.load(f)
    if os.path.exists(INCIDENTS_FILE):
        with open(INCIDENTS_FILE, "r") as f:
            previous_incidents = json.load(f)

def guardar_dados():
    with open(USERS_FILE, "w") as f:
        json.dump(user_preferences, f)
    with open(INCIDENTS_FILE, "w") as f:
        json.dump(previous_incidents, f)

def fetch_incidents():
    try:
        response = requests.get(FOGOS_API)
        response.raise_for_status()
        return response.json()["data"]
    except Exception as e:
        logger.error(f"Erro ao buscar dados: {e}")
        return []

def format_location(inc):
    loc = inc.get('location')
    if loc and loc.strip():
        return loc.strip()
    parts = [
        inc.get('locality', '').strip(),
        inc.get('parish', '').strip(),
        inc.get('municipality', '').strip(),
        inc.get('district', '').strip()
    ]
    return ", ".join([p for p in parts if p])

# ========= Comandos =========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Selecionar Distrito", callback_data="select_district")]]
    await update.message.reply_markdown(WELCOME_TEXT, reply_markup=InlineKeyboardMarkup(keyboard))

async def alterar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await select_district(update, context)

async def ver_ocorrencias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    district = user_preferences.get(user_id, "Todos")

    incidents = fetch_incidents()
    filtered = [i for i in incidents if district == "Todos" or i["district"] == district]

    if not filtered:
        await update.message.reply_text("Sem ocorrências no momento.")
        return

    for inc in filtered:
        local = format_location(inc)
        inicio = f"{inc.get('date', 'N/A')} {inc.get('hour', '')}".strip()

        msg = (
            f"📍 *Local:* {local}\n"
            f"🕒 *Início:* {inicio}\n"
            f"🚒 *Meios:* 👨 {inc['man']} | 🚒 {inc['terrain']} | ✈️ {inc['aerial']}\n"
            f"📊 *Estado:* {inc.get('status', 'N/A')}"
        )
        await update.message.reply_markdown(msg)

# ========= Seleção de distrito =========

async def select_district(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(d, callback_data=f"district_{d}")] for d in DISTRICTS]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("Escolha o seu distrito:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text("Escolha o seu distrito:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("district_"):
        district = query.data.split("_", 1)[1]
        user_id = str(query.from_user.id)
        user_preferences[user_id] = district
        guardar_dados()

        await query.edit_message_text(f"✅ Distrito definido para *{district}*", parse_mode="Markdown")

        # Buscar e enviar ocorrências diretamente após seleção
        incidents = fetch_incidents()
        filtered = [i for i in incidents if district == "Todos" or i["district"] == district]

        if not filtered:
            await context.bot.send_message(chat_id=int(user_id), text="Sem ocorrências no momento.")
        else:
            for inc in filtered:
                local = format_location(inc)
                inicio = f"{inc.get('date', 'N/A')} {inc.get('hour', '')}".strip()

                msg = (
                    f"📍 *Local:* {local}\n"
                    f"🕒 *Início:* {inicio}\n"
                    f"🚒 *Meios:* 👨 {inc['man']} | 🚒 {inc['terrain']} | ✈️ {inc['aerial']}\n"
                    f"📊 *Estado:* {inc.get('status', 'N/A')}"
                )
                await context.bot.send_message(chat_id=int(user_id), text=msg, parse_mode="Markdown")

    elif query.data == "select_district":
        await select_district(update, context)

# ========= Notificações =========

async def check_updates(context: ContextTypes.DEFAULT_TYPE):
    global previous_incidents
    current = fetch_incidents()
    new_dict = {str(inc["id"]): inc for inc in current}

    for user_id, district in user_preferences.items():
        user_incidents = [i for i in current if district == "Todos" or i["district"] == district]

        for inc in user_incidents:
            inc_id = str(inc["id"])
            was_known = inc_id in previous_incidents
            has_changed = not was_known or inc != previous_incidents[inc_id]

            if has_changed:
                local = format_location(inc)
                inicio = f"{inc.get('date', 'N/A')} {inc.get('hour', '')}".strip()
                tipo_alerta = "🚨 *Nova Ocorrência*" if not was_known else "🔄 *Atualização de Ocorrência*"

                msg = (
                    f"{tipo_alerta}\n"
                    f"📍 *Local:* {local}\n"
                    f"🕒 *Início:* {inicio}\n"
                    f"🚒 *Meios:* 👨 {inc['man']} | 🚒 {inc['terrain']} | ✈️ {inc['aerial']}\n"
                    f"📊 *Estado:* {inc.get('status', 'N/A')}"
                )
                try:
                    await context.bot.send_message(chat_id=int(user_id), text=msg, parse_mode="Markdown")
                except Exception as e:
                    logger.warning(f"Erro ao enviar para {user_id}: {e}")

    previous_incidents = new_dict
    guardar_dados()

# ========= JobQueue =========

async def setup_jobs(app):
    app.job_queue.run_repeating(check_updates, interval=60, first=10)

# ========= Main =========

def main():
    carregar_dados()
    app = Application.builder().token(TOKEN).post_init(setup_jobs).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ver", ver_ocorrencias))
    app.add_handler(CommandHandler("alterar", alterar))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))
    app.add_handler(MessageHandler(filters.COMMAND, lambda update, context: update.message.reply_text("❌ Comando não reconhecido. Use /start para ver as opções.")))

    print("Bot em execução...")
    app.run_polling()

if __name__ == "__main__":
    main()
