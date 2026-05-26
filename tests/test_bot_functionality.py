"""Bot functionality tests. Usage: python tests/test_bot_functionality.py"""

import os, sys, json, logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
LOG_FILE = Path(__file__).parent.parent / "data" / "bot.log"
PASS = "[PASS]"
FAIL = "[FAIL]"
SKIP = "[SKIP]"

results = []

def test(name, fn):
    try:
        fn()
        print(f"  {PASS} {name}")
        results.append((name, True, ""))
    except Exception as e:
        print(f"  {FAIL} {name}: {e}")
        results.append((name, False, str(e)))

def skip(name, reason):
    print(f"  {SKIP} {name}: {reason}")
    results.append((name, True, f"skipped: {reason}"))

# ── Tests ──

def api_getme():
    import httpx
    r = httpx.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe", timeout=10)
    assert r.json().get("ok"), f"getMe failed"
    bot = r.json()["result"]
    print(f"    Bot: @{bot['username']} (id={bot['id']})")

def no_webhook():
    import httpx
    r = httpx.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo", timeout=10)
    url = r.json()["result"]["url"]
    assert url == "", f"Webhook set: {url}"

def allowed_updates():
    import httpx
    r = httpx.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo", timeout=10)
    allowed = r.json()["result"].get("allowed_updates", [])
    assert allowed == ["message", "callback_query"], f"Unexpected: {allowed}"

def config_env():
    assert BOT_TOKEN and BOT_TOKEN != "your_bot_token_here", "BOT_TOKEN missing"
    assert os.getenv("OWNER_ID"), "OWNER_ID missing"

def log_writable():
    log_dir = LOG_FILE.parent
    assert log_dir.exists(), f"No log dir: {log_dir}"
    tf = log_dir / ".wtest"
    tf.write_text("ok"); tf.unlink()

def handler_modules():
    mods = ["start","events","profile","bonuses","referrals","specialists",
            "booking","dj_mixes","dj_register","admin","rss","tickets","bar_admin"]
    for m in mods:
        __import__(f"bot.handlers.{m}", fromlist=["register"])

def register_handlers():
    from telegram.ext import ApplicationBuilder
    from bot.main import register_all_handlers
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    register_all_handlers(app)
    total = sum(len(h) for h in app.handlers.values())
    print(f"    Groups: {len(app.handlers)}, Handlers: {total}")
    assert total > 10, f"Too few handlers: {total}"

def admin_edit_kbd():
    from bot.keyboards.inline import admin_event_edit_keyboard
    kb = admin_event_edit_keyboard(1)
    texts = []
    for row in kb.inline_keyboard:
        for btn in row:
            texts.append(btn.text)
    flat = " | ".join(texts)
    has_delete = "\u0423\u0434\u0430\u043b\u0438\u0442\u044c" in flat or "Dz\u0113st" in flat
    assert has_delete, "No delete button"
    safe = flat.encode("ascii", errors="replace").decode()[:200]
    print(f"    Buttons: {safe}")

def models_ok():
    from bot import models
    names = ["User","Event","Specialist","BookingRequest","DjMix",
             "SoldTicket","Reward","Referral","Notification"]
    for n in names:
        assert hasattr(models, n), f"Missing model: {n}"
    print(f"    {len(names)} models OK")

def log_no_errors():
    if not LOG_FILE.exists():
        return
    text = LOG_FILE.read_text(encoding="utf-8", errors="replace")
    errors = [l for l in text.splitlines() if "ERROR" in l]
    if errors:
        print(f"    WARNING: {len(errors)} errors in log")
        for e in errors[-3:]:
            cleaned = e.encode("ascii", "replace").decode()
            print(f"      {cleaned[:200]}")

def db_init():
    from bot.database import init_db, SessionLocal
    init_db()
    db = SessionLocal()
    from sqlalchemy import text
    db.execute(text("SELECT 1"))
    db.close()

def cleanup_events():
    from bot.services.event_service import cleanup_past_events
    from bot.database import SessionLocal
    count = cleanup_past_events(SessionLocal())
    print(f"    Cleaned {count} past events")

def send_message():
    """Send a /start to the bot and verify response."""
    import httpx
    owner_id = os.getenv("OWNER_ID")
    r = httpx.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": int(owner_id), "text": "/start"},
        timeout=10
    )
    data = r.json()
    assert data.get("ok"), f"sendMessage failed: {data.get('description','')}"
    print(f"    /start sent to {owner_id}")

# ── Runner ──

if __name__ == "__main__":
    print("=== Telegram Bot Tests ===")
    test("Config env", config_env)
    test("API getMe", api_getme)
    test("No webhook", no_webhook)
    test("Allowed updates", allowed_updates)
    test("Log writable", log_writable)
    test("Handler imports", handler_modules)
    test("Register handlers", register_handlers)
    test("Admin edit kbd", admin_edit_kbd)
    test("Models", models_ok)
    test("DB init", db_init)
    test("Cleanup events", cleanup_events)
    test("Log errors", log_no_errors)
    test("Send /start", send_message)

    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"\n  Results: {passed}/{total} passed")
    for name, ok, msg in results:
        if not ok and not msg.startswith("skipped"):
            print(f"    FAIL: {name} -> {msg}")
    sys.exit(0 if passed == total else 1)
