"""Bonuses and rewards handlers."""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from sqlalchemy.orm import Session

from bot.database import SessionLocal
from bot.models import User
from bot.keyboards.inline import bonuses_keyboard, back_keyboard
from bot.config import POINTS
from bot.services.bonus_service import (
    get_available_rewards, redeem_reward, get_user_transactions,
    get_user_redemptions
)


async def bonuses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user:
            await update.message.reply_text("Сначала используй /start")
            return
        lang = user.language
        rewards = get_available_rewards(db)

        rules_ru = (
            f"📝 Регистрация — **+{POINTS['REGISTRATION']}**\n"
            f"🎤 Регистрация DJ — **+{POINTS['DJ_REGISTRATION']}**\n"
            f"🎧 Загрузка микса — **+{POINTS['DJ_UPLOAD_MIX']}**\n"
            f"👥 Пригласить друга — **+{POINTS['REFERRAL']}**\n"
            f"🎉 Посетить вечеринку — **+{POINTS['VISIT_PARTY']}**\n"
            f"🎫 Купить билет — **+{POINTS['TICKET_PURCHASE']}**\n"
            f"🍹 Заказ в баре от 20€ — **+{POINTS['BAR_ORDER_20']}**\n"
            f"🎂 В день рождения **×{POINTS['BIRTHDAY_WEEK_MULTIPLIER']}**"
        )
        rules_lv = (
            f"📝 Reģistrācija — **+{POINTS['REGISTRATION']}**\n"
            f"🎤 DJ reģistrācija — **+{POINTS['DJ_REGISTRATION']}**\n"
            f"🎧 Miksa augšupielāde — **+{POINTS['DJ_UPLOAD_MIX']}**\n"
            f"👥 Uzaicināt draugu — **+{POINTS['REFERRAL']}**\n"
            f"🎉 Apmeklēt ballīti — **+{POINTS['VISIT_PARTY']}**\n"
            f"🎫 Iegādāties biļeti — **+{POINTS['TICKET_PURCHASE']}**\n"
            f"🍹 Pasūtījums bārā no 20€ — **+{POINTS['BAR_ORDER_20']}**\n"
            f"🎂 Dzimšanas dienā **×{POINTS['BIRTHDAY_WEEK_MULTIPLIER']}**"
        )

        text = (
            f"⭐ *{'Бонусы и награды' if lang == 'ru' else 'Bonusi un balvas'}*\n\n"
            f"💰 *{'Баланс' if lang == 'ru' else 'Bilance'}:* {user.points_balance} points\n\n"
            f"━━━━ *{'Как заработать' if lang == 'ru' else 'Kā nopelnīt'}* ━━━━\n"
            f"{rules_ru if lang == 'ru' else rules_lv}\n\n"
            f"━━━━━━━━━━━━━━━━\n\n"
            f"{'Доступные награды:' if lang == 'ru' else 'Pieejamās balvas:'}"
        )
        await update.message.reply_text(
            text, parse_mode="Markdown",
            reply_markup=bonuses_keyboard(rewards, lang),
        )
    finally:
        db.close()


async def bonuses_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
        if not user:
            return
        lang = user.language

        if data == "menu_bonuses":
            await bonuses(update, context)
        elif data == "bonus_howto":
            await _bonus_howto(query, lang)
        elif data.startswith("redeem_"):
            reward_id = int(data.split("_")[1])
            from bot.models import Reward
            reward = db.query(Reward).filter(Reward.id == reward_id).first()
            if not reward:
                await query.answer("Награда не найдена / Balva nav atrasta", show_alert=True)
                return
            if user.points_balance < reward.points_required:
                await query.answer(
                    f"❌ {'Недостаточно баллов' if lang == 'ru' else 'Nepietiek punktu'}! "
                    f"Нужно: {reward.points_required}, у тебя: {user.points_balance}",
                    show_alert=True
                )
                return
            try:
                redeem_reward(db, user, reward)
                title = reward.title_lv if lang == "lv" else reward.title_ru
                await query.edit_message_text(
                    f"✅ *{'Награда активирована' if lang == 'ru' else 'Balva aktivizēta'}!*\n\n"
                    f"{title}\n"
                    f"💰 {'Потрачено' if lang == 'ru' else 'Iztērēts'}: {reward.points_required} points\n"
                    f"💰 {'Остаток' if lang == 'ru' else 'Atlikums'}: {user.points_balance} points",
                    parse_mode="Markdown",
                    reply_markup=back_keyboard("menu_bonuses"),
                )
            except ValueError as e:
                await query.answer(str(e), show_alert=True)
        elif data == "bonus_history":
            txns = get_user_transactions(db, user)
            if not txns:
                await query.edit_message_text(
                    "📭 История пуста / Vēsture ir tukša",
                    reply_markup=back_keyboard("menu_bonuses"),
                )
                return
            lines = ["📊 *История / Vēsture*:\n"]
            for t in txns:
                emoji = "➕" if t.type == "earn" else "➖"
                desc = t.description_lv if lang == "lv" and t.description_lv else t.description
                lines.append(f"{emoji} {t.amount} pts — {desc}")
            await query.edit_message_text(
                "\n".join(lines), parse_mode="Markdown",
                reply_markup=back_keyboard("menu_bonuses"),
            )
    finally:
        db.close()


async def _bonus_howto(query, lang):
    rules_ru = (
        "ℹ️ *Как заработать бонусные очки*\n\n"
        f"📝 Регистрация в боте — **+{POINTS['REGISTRATION']} pts**\n"
        f"🎤 Регистрация DJ — **+{POINTS['DJ_REGISTRATION']} pts**\n"
        f"🎧 Загрузка микса — **+{POINTS['DJ_UPLOAD_MIX']} pts**\n"
        f"👥 Пригласить друга — **+{POINTS['REFERRAL']} pts**\n"
        f"🎉 Посетить вечеринку — **+{POINTS['VISIT_PARTY']} pts**\n"
        f"🎫 Купить билет — **+{POINTS['TICKET_PURCHASE']} pts**\n"
        f"🍹 Заказ в баре от 20€ — **+{POINTS['BAR_ORDER_20']} pts**\n"
        f"🎂 В день рождения ×{POINTS['BIRTHDAY_WEEK_MULTIPLIER']} все баллы\n\n"
        "💡 Копи баллы и обменивай на награды!"
    )
    rules_lv = (
        "ℹ️ *Kā nopelnīt bonusus*\n\n"
        f"📝 Reģistrācija botā — **+{POINTS['REGISTRATION']} pts**\n"
        f"🎤 DJ reģistrācija — **+{POINTS['DJ_REGISTRATION']} pts**\n"
        f"🎧 Miksa augšupielāde — **+{POINTS['DJ_UPLOAD_MIX']} pts**\n"
        f"👥 Uzaicināt draugu — **+{POINTS['REFERRAL']} pts**\n"
        f"🎉 Apmeklēt ballīti — **+{POINTS['VISIT_PARTY']} pts**\n"
        f"🎫 Iegādāties biļeti — **+{POINTS['TICKET_PURCHASE']} pts**\n"
        f"🍹 Pasūtījums bārā no 20€ — **+{POINTS['BAR_ORDER_20']} pts**\n"
        f"🎂 Dzimšanas dienā ×{POINTS['BIRTHDAY_WEEK_MULTIPLIER']} visi punkti\n\n"
        "💡 Krāj punktus un apmaini pret balvām!"
    )
    await query.edit_message_text(
        rules_ru if lang == "ru" else rules_lv,
        parse_mode="Markdown",
        reply_markup=back_keyboard("menu_bonuses"),
    )


def register(application):
    application.add_handler(CommandHandler("bonuses", bonuses))
    application.add_handler(CallbackQueryHandler(bonuses_callback, pattern=r"^(menu_bonuses|redeem_|bonus_history|bonus_howto)"))
