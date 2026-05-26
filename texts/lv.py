"""Latvian language texts for Party Map Daugavpils Bot."""

WELCOME = (
    "🎉 *Laipni lūdzam Party Map Daugavpils!* 🎉\n"
    "🎉 *Добро пожаловать в Party Map Daugavpils!* 🎉\n\n"
    "Tava galvenā naktsdzīves ceļvede Daugavpilī! 🍸\n"
    "Твой главный гид по ночной жизни Даугавпилса! 🍸\n\n"
    "📅 *Afiša / Афиша* — ballītes, koncerti / вечеринки, концерты\n"
    "⭐ *Bonusi / Бонусы* — krāj punktus un saņem balvas / копи баллы и получай награды\n"
    "🎭 *Speciālisti / Специалисты* — DJ, fotogrāfi, vadītāji / DJ, фотографы, ведущие\n"
    "🎧 *Miksi / DJ Миксы* — klausies un atklāj jaunus māksliniekus / слушай и открывай новых артистов\n"
    "👤 *Profils / Профиль* — tavi punkti un sasniegumi / твои баллы и достижения\n"
    "👥 *Uzaicini draugu / Пригласи друга* — uzaicini draugus un saņem bonusus / приглашай друзей и получай бонусы\n\n"
    "📋 *Komandas / Команды:*\n"
    "/menu — Galvenā izvēlne / Главное меню\n"
    "/events — Afiša / Афиша\n"
    "/bonuses — Mani bonusi / Мои бонусы\n"
    "/profile — Profils / Профиль\n"
    "/specialists — Speciālisti / Специалисты\n"
    "/mixes — DJ Miksi / DJ Миксы\n"
    "/djregister — Kļūt par DJ / Стать DJ\n"
    "/help — Palīdzība / Помощь\n"
    "/language — Mainīt valodu / Сменить язык\n\n"
    "👇 *Pogas ekrāna apakšā / Кнопки внизу экрана*"
)

MENU_TITLE = "🎯 *Galvenā izvēlne*"
PROFILE_TITLE = "👤 *Tavs profils*"
EVENTS_TITLE = "📅 *Pasākumu afiša*"
BONUSES_TITLE = "⭐ *Bonusi un balvas*"
SPECIALISTS_TITLE = "🎭 *Speciālisti*"
DJ_MIXES_TITLE = "🎧 *DJ Miksi*"
BOOKINGS_TITLE = "📋 *Mani pieteikumi*"
REFERRALS_TITLE = "👥 *Referālu programma*"
ADMIN_TITLE = "⚙️ *Admin panelis*"

BACK = "◀️ Atpakaļ"
MAIN_MENU = "🏠 Galvenā izvēlne"
CLOSE = "❌ Aizvērt"
CONFIRM = "✅ Apstiprināt"
CANCEL = "❌ Atcelt"
SHARE = "📤 Dalīties"
SAVE = "💾 Saglabāt"
BOOK = "📅 Rezervēt"
LISTEN = "🎵 Klausīties"
GET_BONUS = "🎁 Saņemt bonusu"
GET_TICKET = "🎫 Saņemt biļeti"
SUBMIT = "📨 Nosūtīt"

NO_EVENTS = "😕 Pašlaik nav gaidāmu pasākumu."
NO_SPECIALISTS = "😕 Šajā kategorijā vēl nav speciālistu."
NO_DJ_MIXES = "😕 Vēl nav publicētu miksu."
NO_BOOKINGS = "📭 Tev vēl nav pieteikumu."
NO_SAVED = "📭 Tev vēl nav saglabātu pasākumu."
NO_NOTIFICATIONS = "🔔 Nav jaunu paziņojumu."
NO_REFERRALS = "👥 Tev vēl nav uzaicinātu draugu."

POINTS_BALANCE = "💰 *Bilance:* {points} punkti"
POINTS_EARNED = "📈 *Kopā nopelnīts:* {points}"
POINTS_SPENT = "📉 *Kopā iztērēts:* {points}"

REGISTRATION_SUCCESS = (
    "✅ *Reģistrācija pabeigta!*\n\n"
    "🎁 Tu saņēmi 50 punktus par reģistrāciju!\n"
    "💰 Tava bilance: 50 punkti\n\n"
    "Izmanto /menu navigācijai."
)

PROFILE_INFO = (
    "👤 *Profils*\n\n"
    "Vārds: {name}\n"
    "Username: @{username}\n"
    "Pilsēta: {city}\n"
    "Loma: {role}\n"
    "Valoda: {language}\n\n"
    "💰 Bilance: {points} punkti\n"
    "📈 Nopelnīts: {earned}\n"
    "📉 Iztērēts: {spent}\n"
    "👥 Referāli: {referrals}\n"
    "📅 Reģistrēts: {reg_date}"
)

REFERRAL_INFO = (
    "👥 *Referālu programma*\n\n"
    "Uzaicini draugus un saņem bonusus!\n\n"
    "🎁 Par katru draugu — 40 punkti\n"
    "🎁 Par drauga pirmo apmeklējumu — vēl 30 punkti\n\n"
    "Tava referāla saite:\n"
    "`{link}`\n\n"
    "Uzaicināti draugi: {count}"
)

EVENT_DETAIL = (
    "📅 *{title}*\n\n"
    "📆 {date}\n"
    "🕒 {time}\n"
    "📍 {venue}\n"
    "🏷️ {price}\n\n"
    "{description}\n\n"
    "{bonus_info}"
)

SPECIALIST_DETAIL = (
    "🎭 *{name}*\n\n"
    "Kategorija: {category}\n"
    "📍 {city}\n"
    "⭐ Pieredze: {experience} gadi\n"
    "🔧 Specializācija: {specialization}\n\n"
    "{description}\n\n"
    "💰 Cena no: {price} EUR\n"
    "📞 {contacts}"
)

DJ_MIX_DETAIL = (
    "🎧 *{title}*\n\n"
    "DJ: {artist}\n"
    "🎵 Žanrs: {genre}\n"
    "📅 {date}\n"
    "👁️ Klausījumu: {plays}\n\n"
    "{description}"
)

BOOKING_FORM = (
    "📝 *Rezervācijas pieteikums*\n\n"
    "Aizpildi formu, un mēs ar tevi sazināsimies:"
)

BOOKING_CONFIRMED = (
    "✅ *Pieteikums nosūtīts!*\n\n"
    "Pieteikuma nr.: #{id}\n"
    "Mēs ar tevi sazināsimies tuvākajā laikā."
)

BONUS_REDEEMED = "✅ *Balva aktivizēta!*"
POINTS_ADDED = "🎉 *+{amount} punkti*\n{reason}"
ADMIN_ACCESS_DENIED = "🚫 Pieeja liegta. Tikai administratoriem."
USER_BLOCKED = "🚫 Tavs konts ir bloķēts. Sazinies ar administratoru."
UNKNOWN_COMMAND = "🤷 Nezināma komanda. Izmanto /menu"
LANGUAGE_CHANGED = "✅ Valoda mainīta uz latviešu."

HELP_TEXT = (
    "ℹ️ *Palīdzība*\n\n"
    "/start — Pārstartēt botu\n"
    "/menu — Galvenā izvēlne\n"
    "/events — Pasākumu afiša\n"
    "/profile — Mans profils\n"
    "/bonuses — Bonusi\n"
    "/referral — Referāla saite\n"
    "/specialists — Speciālisti\n"
    "/mixes — DJ Miksi\n"
    "/bookings — Mani pieteikumi\n"
    "/language — Mainīt valodu\n"
    "/about — Par botu\n"
    "/help — Palīdzība"
)

DESCRIPTION = (
    "🤖 *Party Map Daugavpils*\n\n"
    "🎉 *Par botu:*\n"
    "Party Map Daugavpils ir galvenais naktsdzīves ceļvedis Daugavpilī. "
    "Atrodi pasākumus, rezervē speciālistus, klausies vietējo DJ miksus, "
    "krāj bonusus un apmaini tos pret balvām!\n\n"
    "📅 *Afiša* — visas gaidāmās ballītes un koncerti\n"
    "🎭 *Speciālisti* — DJ, fotogrāfi, organizatori, vadītāji\n"
    "🎧 *Miksi* — vietējo izpildītāju treki un miksi\n"
    "⭐ *Bonusi* — lojalitātes programma ar balvām\n"
    "👥 *Uzaicini draugu* — saņem bonusus par draugiem\n"
    "🎤 *Kļūt par DJ* — reģistrācija māksliniekiem\n\n"
    "👑 *Administratoriem:*\n"
    "Pasākumu izveide, miksu moderācija, lietotāju pārvaldība\n\n"
    "🔗 *Kontakti:* @mapdaugavpilsbot"
)

# ---- Dating module texts ----
DATING_MENU = "💕 *Iepazīšanās*"
DATING_CREATE = "📝 *Profila izveide*"
DATING_EDIT = "✏️ *Rediģēt profilu*"
DATING_MY_PROFILE = "📋 *Mans profils*"
DATING_BROWSE = "👀 *Profilu apskate*"
DATING_BUY = "⭐ *Pirkt skatījumus*"
DATING_PURCHASES = "📦 *Mani pirkumi*"
DATING_RULES = (
    "📋 *Iepazīšanās sadaļas noteikumi*\n\n"
    "1. Aizliegti apvainojumi un nepieklājīga uzvedība\n"
    "2. Aizliegta reklāma un surogātpasts\n"
    "3. Fotoattēliem jābūt reāliem\n"
    "4. Nedrīkst uzdoties par citu personu\n"
    "5. Administrācijai ir tiesības bloķēt profilu bez paskaidrojuma\n\n"
    "Noteikumu pārkāpšana noved pie profila bloķēšanas."
)
DATING_NO_PROFILE = "Tev vēl nav profila. Izveido to, lai sāktu iepazīties!"
DATING_PENDING = "⏳ Tavs profils tiek moderēts. Gaidi administratora pārbaudi."
DATING_REJECTED = "❌ Tavs profils ir noraidīts. Sazinies ar administratoru, lai uzzinātu iemeslus."
DATING_BLOCKED = "🚫 Tavs profils ir bloķēts. Sazinies ar administratoru."
DATING_ACTIVE = "✅ Profils aktīvs"
DATING_VIEWS_LEFT = "📸 Atlikuši skatījumi: {count}"
DATING_NO_VIEWS = "😕 Tev nav aktīvu skatījumu. Pērc skatījumu paketi, lai redzētu profilus!"
DATING_NO_CANDIDATES = "😕 Pašlaik nav jaunu profilu. Ieskaties vēlāk!"
DATING_ALL_VIEWED = "🎉 Tu esi apskatījis visus pieejamos profilus! Pērc vēl skatījumus, lai turpinātu!"
DATING_PHOTO_PROMPT = "📤 Nosūti foto (līdz 3 gab.). Pēc visu foto nosūtīšanas nospied /done."
DATING_RULES_ACCEPT = "Apstiprini piekrišanu noteikumiem?"
DATING_SUPPORT = "📩 Visos jautājumos sazinies ar administratoru caur pogu «📩 Administratoram» galvenajā izvēlnē."
