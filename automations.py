import datetime
import urllib.parse
import threading
import time
import logging
from config import Config
from database import get_db

logger = logging.getLogger(__name__)

def clean_phone_number(phone: str) -> str:
    """Standardize Indian phone numbers for WhatsApp/SMS."""
    if not phone:
        return ""
    digits = "".join(filter(str.isdigit, str(phone)))
    if len(digits) == 10:
        return f"91{digits}"
    elif len(digits) == 12 and digits.startswith("91"):
        return digits
    elif len(digits) == 11 and digits.startswith("0"):
        return f"91{digits[1:]}"
    return digits

def generate_whatsapp_url(phone: str, message: str) -> str:
    """Generate direct click-to-chat WhatsApp link with prefilled text."""
    clean_phone = clean_phone_number(phone)
    encoded_text = urllib.parse.quote(message)
    return f"https://wa.me/{clean_phone}?text={encoded_text}"

def send_sms_gateway(phone: str, message: str) -> dict:
    """
    SMS Gateway Interface.
    Simulates sending or integrates with Twilio / Fast2SMS / MSG91.
    """
    clean_phone = clean_phone_number(phone)
    # If a real provider API key is configured, invoke HTTP post here.
    # Otherwise simulate successful gateway dispatch.
    return {
        "success": True,
        "channel": "sms",
        "phone": clean_phone,
        "dispatched_at": datetime.datetime.now().isoformat(),
        "provider": "Fast2SMS_Simulated"
    }

def render_template(template_str: str, context: dict) -> str:
    """Render placeholders like {{name}} or {{end_date}} in template string."""
    rendered = template_str
    for key, value in context.items():
        placeholder = f"{{{{{key}}}}}"
        rendered = rendered.replace(placeholder, str(value if value is not None else ""))
    return rendered

def get_template(cursor, trigger_type: str) -> dict:
    cursor.execute("SELECT * FROM message_templates WHERE trigger_type = ? AND is_active = 1", (trigger_type,))
    row = cursor.fetchone()
    if row:
        return dict(row)
    return None

def dispatch_notification(conn, member_id: int, member_name: str, phone: str, 
                          channel: str, trigger_type: str, message_text: str) -> dict:
    """Log and dispatch an automated or manual notification."""
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO notification_logs (member_id, member_name, recipient_phone, channel, trigger_type, message_text, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 'sent', ?)
    """, (member_id, member_name, phone, channel, trigger_type, message_text, now_str))
    conn.commit()
    log_id = cursor.lastrowid

    whatsapp_url = None
    if channel == "whatsapp":
        whatsapp_url = generate_whatsapp_url(phone, message_text)
    elif channel == "sms":
        send_sms_gateway(phone, message_text)

    return {
        "id": log_id,
        "member_id": member_id,
        "member_name": member_name,
        "phone": phone,
        "channel": channel,
        "trigger_type": trigger_type,
        "message": message_text,
        "whatsapp_url": whatsapp_url,
        "created_at": now_str
    }

def run_daily_automations(target_date=None) -> dict:
    """
    Scans members for subscription & locker expirations and triggers automated messages.
    Can be run automatically on a schedule or manually triggered via API/dashboard.
    """
    if target_date is None:
        target_date = datetime.date.today()
    elif isinstance(target_date, str):
        target_date = datetime.date.fromisoformat(target_date)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM members WHERE status != 'cancelled'")
    members = [dict(row) for row in cursor.fetchall()]

    today_str = target_date.isoformat()
    generated = []

    for m in members:
        member_id = m["id"]
        member_name = m["name"]
        phone = m["phone"]
        plan = m["plan_name"]

        # Base context for templates
        context = {
            "name": member_name,
            "plan": plan,
            "gym_phone": Config.GYM_PHONE,
            "gym_name": Config.GYM_NAME,
            "gym_address": Config.GYM_ADDRESS,
            "phone": phone,
            "end_date": m["end_date"],
            "locker_number": m.get("locker_number"),
            "locker_end_date": m.get("locker_end_date")
        }

        # -------------------------------------------------------------
        # 1. SUBSCRIPTION EXPIRY EVALUATION
        # -------------------------------------------------------------
        if m["end_date"]:
            try:
                sub_end = datetime.date.fromisoformat(m["end_date"])
                sub_diff = (sub_end - target_date).days
                context["days_left"] = sub_diff

                trigger = None
                if sub_diff == 3:
                    trigger = "sub_warning_3d"
                elif sub_diff == 1:
                    trigger = "sub_warning_1d"
                elif sub_diff == 0:
                    trigger = "sub_expired"
                    # Update status in db to expired if target_date >= sub_end
                    cursor.execute("UPDATE members SET status = 'expired' WHERE id = ?", (member_id,))
                elif sub_diff == -Config.SUB_OVERDUE_DAYS:
                    trigger = "sub_overdue_3d"

                if trigger:
                    # Prevent duplicate messages for the same trigger today
                    cursor.execute("""
                        SELECT id FROM notification_logs
                        WHERE member_id = ? AND trigger_type = ? AND created_at LIKE ?
                    """, (member_id, trigger, f"{today_str}%"))
                    if not cursor.fetchone():
                        template_data = get_template(cursor, trigger)
                        if template_data:
                            msg = render_template(template_data["template_text"], context)
                            channel = template_data.get("channel", "whatsapp")
                            res = dispatch_notification(conn, member_id, member_name, phone, channel, trigger, msg)
                            generated.append(res)
            except Exception as e:
                logger.error(f"Error evaluating subscription for member {member_id}: {e}")

        # -------------------------------------------------------------
        # 2. LOCKER EXPIRY EVALUATION
        # -------------------------------------------------------------
        if m.get("locker_number") and m.get("locker_end_date"):
            try:
                locker_end = datetime.date.fromisoformat(m["locker_end_date"])
                locker_diff = (locker_end - target_date).days
                context["locker_days_left"] = locker_diff

                locker_trigger = None
                if locker_diff == 3:
                    locker_trigger = "locker_warning_3d"
                elif locker_diff == 1:
                    locker_trigger = "locker_warning_1d"
                elif locker_diff == 0:
                    locker_trigger = "locker_expired"

                if locker_trigger:
                    cursor.execute("""
                        SELECT id FROM notification_logs
                        WHERE member_id = ? AND trigger_type = ? AND created_at LIKE ?
                    """, (member_id, locker_trigger, f"{today_str}%"))
                    if not cursor.fetchone():
                        template_data = get_template(cursor, locker_trigger)
                        if template_data:
                            msg = render_template(template_data["template_text"], context)
                            channel = template_data.get("channel", "whatsapp")
                            res = dispatch_notification(conn, member_id, member_name, phone, channel, locker_trigger, msg)
                            generated.append(res)
            except Exception as e:
                logger.error(f"Error evaluating locker for member {member_id}: {e}")

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "scanned_members": len(members),
        "target_date": today_str,
        "messages_generated_count": len(generated),
        "messages": generated
    }

class AutomationScheduler:
    """Background scheduler thread running periodic scans."""
    def __init__(self, interval_seconds=3600):
        self.interval = interval_seconds
        self.stop_event = threading.Event()
        self.thread = None

    def start(self):
        if self.thread is None or not self.thread.is_alive():
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            logger.info("Automation background scheduler started.")

    def stop(self):
        if self.thread and self.thread.is_alive():
            self.stop_event.set()
            self.thread.join(timeout=2)
            logger.info("Automation background scheduler stopped.")

    def _run_loop(self):
        # Initial run after slight startup delay
        time.sleep(5)
        while not self.stop_event.is_set():
            try:
                run_daily_automations()
            except Exception as e:
                logger.error(f"Scheduler run exception: {e}")
            self.stop_event.wait(self.interval)

scheduler = AutomationScheduler(interval_seconds=Config.AUTOMATION_INTERVAL_SECONDS)
