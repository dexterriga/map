"""Referral system handlers."""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from sqlalchemy.orm import Session

from bot.database import SessionLocal
from bot.models import User
from bot.keyboards.inline import back_keyboard
from bot.services.referral_service import get_referrals, count_referrals
from bot.utils.helpers import generate_referral_link


async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user:
            await update.message.reply_text("Сначала используй /start")
            return
        lang = user.language
        ref_count = count_referrals(db, user)
        link = generate_referral_link(user_tg.id)
        share_url = f"https://t.me/share/url?url={link}&text={'Присоединяйся к Party Map Daugavpils!' if lang == 'ru' else 'Pievienojies Party Map Daugavpils!'}"

        referred_list = get_referrals(db, user)
        friends_text = ""
        if referred_list:
            names = []
            for ref in referred_list[:10]:
                u = db.query(User).filter(User.id == ref.referred_id).first()
                if u:
                    names.append(f"@{u.username or u.first_name or u.telegram_id}")
            if names:
                friends_text = "\n" + ("\n".join(f"• {n}" for n in names))

        text = (
            f"👥 *{'Пригласи друга' if lang == 'ru' else 'Uzaicini draugu'}*\n\n"
            f"{'Приглашай друзей и получай бонусы!' if lang == 'ru' else 'Uzaicini draugus un saņem bonusus!'}\n\n"
            f"🎁 {'За каждого друга — 40 points' if lang == 'ru' else 'Par katru draugu — 40 punkti'}\n"
            f"🎁 {'За первый визит друга — ещё 30 points' if lang == 'ru' else 'Par drauga pirmo apmeklējumu — vēl 30 punkti'}\n\n"
            f"👥 {'Приглашено:' if lang == 'ru' else 'Uzaicināti:'} {ref_count} {'друзей' if lang == 'ru' else 'draugi'}"
            + (f"\n{friends_text}" if friends_text else "")
        )
        buttons = [
            [InlineKeyboardButton("📤 Поделиться ссылкой / Dalīties", url=share_url)],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")],
        ]
        await update.message.reply_text(
            text, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    finally:
        db.close()


async def referral_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
        if not user:
            return
        lang = user.language

        if data == "menu_referrals":
            await referral(update, context)
    finally:
        db.close()


def register(application):
    application.add_handler(CommandHandler("referral", referral))
    application.add_handler(CallbackQueryHandler(referral_callback, pattern=r"^menu_referrals$"))
