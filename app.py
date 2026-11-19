import datetime
import random
import string
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from config import Config
from database import get_db, init_db
from automations import (
    run_daily_automations, 
    generate_whatsapp_url, 
    render_template as render_msg_template, 
    dispatch_notification,
    get_template,
    clean_phone_number,
    scheduler
)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database schema and seed default data on launch
with app.app_context():
    init_db(seed=True)

# Start background automation scheduler
try:
    scheduler.start()
except Exception as e:
    app.logger.warning(f"Could not start background scheduler: {e}")

# Context processor for global template variables
@app.context_processor
def inject_gym_info():
    return {
        "gym_name": Config.GYM_NAME,
        "gym_tagline": Config.GYM_TAGLINE,
        "gym_address": Config.GYM_ADDRESS,
        "gym_phone": Config.GYM_PHONE,
        "gym_phone_raw": Config.GYM_PHONE_RAW,
        "gym_email": Config.GYM_EMAIL,
        "gym_hours_weekday": Config.GYM_HOURS_WEEKDAY,
        "gym_hours_sunday": Config.GYM_HOURS_SUNDAY,
        "gym_map_url": Config.GYM_MAP_URL,
        "current_year": datetime.date.today().year
    }

# -----------------------------------------------------------------------------
# PUBLIC ROUTES
# -----------------------------------------------------------------------------

@app.route("/")
def index():
    """Kross 9 Gym Public Website."""
    return render_template("index.html")

@app.route("/pass/<pass_code>")
def view_pass(pass_code):
    """View generated digital free pass."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trial_passes WHERE pass_code = ?", (pass_code,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return "Pass Not Found", 404
    return render_template("pass_confirmation.html", trial_pass=dict(row))

# -----------------------------------------------------------------------------
# ADMIN & MANAGEMENT PORTAL ROUTES
# -----------------------------------------------------------------------------

@app.route("/admin")
def admin_dashboard():
    """Admin Overview & Key Performance Indicators."""
    conn = get_db()
    cursor = conn.cursor()
    today = datetime.date.today()

    # Active members
    cursor.execute("SELECT COUNT(*) FROM members WHERE status = 'active'")
    active_members = cursor.fetchone()[0]

    # Expiring within 7 days
    seven_days = (today + datetime.timedelta(days=7)).isoformat()
    cursor.execute("""
        SELECT COUNT(*) FROM members 
        WHERE status = 'active' AND end_date >= ? AND end_date <= ?
    """, (today.isoformat(), seven_days))
    expiring_soon = cursor.fetchone()[0]

    # Expired
    cursor.execute("SELECT COUNT(*) FROM members WHERE status = 'expired' OR end_date < ?", (today.isoformat(),))
    expired_count = cursor.fetchone()[0]

    # Locker stats
    cursor.execute("SELECT COUNT(*) FROM lockers WHERE status = 'assigned'")
    occupied_lockers = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM lockers")
    total_lockers = cursor.fetchone()[0]

    # Messages dispatched today
    cursor.execute("SELECT COUNT(*) FROM notification_logs WHERE created_at LIKE ?", (f"{today.isoformat()}%",))
    messages_today = cursor.fetchone()[0]

    # Recent notifications
    cursor.execute("SELECT * FROM notification_logs ORDER BY id DESC LIMIT 5")
    recent_logs = [dict(r) for r in cursor.fetchall()]

    # Members needing immediate attention
    cursor.execute("""
        SELECT * FROM members 
        WHERE (end_date <= ? OR locker_end_date <= ?) AND status != 'cancelled'
        ORDER BY end_date ASC LIMIT 6
    """, (seven_days, seven_days))
    priority_members = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return render_template("admin.html", 
        active_members=active_members,
        expiring_soon=expiring_soon,
        expired_count=expired_count,
        occupied_lockers=occupied_lockers,
        total_lockers=total_lockers,
        messages_today=messages_today,
        recent_logs=recent_logs,
        priority_members=priority_members
    )

@app.route("/admin/members")
def admin_members():
    """Member CRM directory."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM members ORDER BY id DESC")
    members = [dict(r) for r in cursor.fetchall()]

    # Available lockers for assignment modal
    cursor.execute("SELECT locker_number FROM lockers WHERE status = 'available' ORDER BY locker_number ASC")
    available_lockers = [r[0] for r in cursor.fetchall()]

    conn.close()
    return render_template("members.html", members=members, available_lockers=available_lockers)

@app.route("/admin/lockers")
def admin_lockers():
    """Interactive Locker Bay."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT l.*, m.name as member_name, m.phone as member_phone, m.end_date as member_sub_end
        FROM lockers l
        LEFT JOIN members m ON l.member_id = m.id
        ORDER BY l.locker_number ASC
    """)
    lockers = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT id, name, phone FROM members WHERE status = 'active' ORDER BY name ASC")
    members = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return render_template("lockers.html", lockers=lockers, members=members)

@app.route("/admin/automations")
def admin_automations():
    """Automation Rules, Message Templates & Notification Audit History."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM message_templates ORDER BY id ASC")
    templates = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM notification_logs ORDER BY id DESC LIMIT 50")
    logs = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT id, name, phone, plan_name, end_date, locker_number, locker_end_date FROM members ORDER BY name ASC")
    members = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return render_template("automations.html", templates=templates, logs=logs, members=members)

# -----------------------------------------------------------------------------
# REST APIS (AJAX & EXTERNAL CLIENTS)
# -----------------------------------------------------------------------------

@app.route("/api/stats", methods=["GET"])
def api_stats():
    """API: Dashboard stats."""
    conn = get_db()
    cursor = conn.cursor()
    today = datetime.date.today()
    seven_days = (today + datetime.timedelta(days=7)).isoformat()

    cursor.execute("SELECT COUNT(*) FROM members WHERE status = 'active'")
    active = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM members WHERE status = 'active' AND end_date >= ? AND end_date <= ?", (today.isoformat(), seven_days))
    expiring_soon = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM members WHERE status = 'expired' OR end_date < ?", (today.isoformat(),))
    expired = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM lockers WHERE status = 'assigned'")
    occupied_lockers = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM notification_logs WHERE created_at LIKE ?", (f"{today.isoformat()}%",))
    notifications_today = cursor.fetchone()[0]

    conn.close()
    return jsonify({
        "active_members": active,
        "expiring_soon": expiring_soon,
        "expired": expired,
        "occupied_lockers": occupied_lockers,
        "notifications_today": notifications_today
    })

@app.route("/api/members", methods=["GET", "POST"])
def api_members():
    """API: Member listing & creation."""
    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
        data = request.json or request.form
        name = data.get("name", "").strip()
        phone = data.get("phone", "").strip()
        email = data.get("email", "").strip()
        plan_name = data.get("plan_name", "Monthly Kickstart")
        plan_amount = float(data.get("plan_amount", 1499.0))
        start_date = data.get("start_date") or datetime.date.today().isoformat()
        end_date = data.get("end_date")
        locker_number = data.get("locker_number")
        locker_end_date = data.get("locker_end_date")
        emergency_contact = data.get("emergency_contact", "").strip()
        notes = data.get("notes", "").strip()

        if not name or not phone or not end_date:
            return jsonify({"error": "Name, phone, and subscription end date are required"}), 400

        locker_num_val = int(locker_number) if locker_number and str(locker_number).isdigit() else None

        cursor.execute("""
            INSERT INTO members (name, phone, email, plan_name, plan_amount, start_date, end_date, locker_number, locker_end_date, emergency_contact, notes, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)
        """, (name, phone, email, plan_name, plan_amount, start_date, end_date, locker_num_val, locker_end_date, emergency_contact, notes, datetime.date.today().isoformat()))
        member_id = cursor.lastrowid

        # If locker assigned, update locker record
        if locker_num_val:
            cursor.execute("""
                UPDATE lockers
                SET member_id = ?, status = 'assigned', assigned_date = ?, end_date = ?
                WHERE locker_number = ?
            """, (member_id, start_date, locker_end_date or end_date, locker_num_val))

        conn.commit()

        # Trigger Automated Welcome Message
        welcome_template = get_template(cursor, "welcome_member")
        welcome_res = None
        if welcome_template:
            ctx = {
                "name": name,
                "plan": plan_name,
                "end_date": end_date,
                "gym_phone": Config.GYM_PHONE,
                "gym_name": Config.GYM_NAME,
                "gym_address": Config.GYM_ADDRESS
            }
            welcome_msg = render_msg_template(welcome_template["template_text"], ctx)
            welcome_res = dispatch_notification(conn, member_id, name, phone, "whatsapp", "welcome_member", welcome_msg)

        conn.close()
        return jsonify({
            "status": "success",
            "member_id": member_id,
            "message": "Member registered successfully",
            "welcome_notification": welcome_res
        }), 201

    # GET
    query = "SELECT * FROM members WHERE 1=1"
    params = []
    status = request.args.get("status")
    search = request.args.get("search")

    if status and status != "all":
        query += " AND status = ?"
        params.append(status)

    if search:
        query += " AND (name LIKE ? OR phone LIKE ? OR email LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])

    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    members = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({"members": members})

@app.route("/api/members/<int:member_id>", methods=["GET", "PUT", "DELETE"])
def api_member_detail(member_id):
    """API: Single member operations."""
    conn = get_db()
    cursor = conn.cursor()

    if request.method == "DELETE":
        cursor.execute("SELECT locker_number FROM members WHERE id = ?", (member_id,))
        row = cursor.fetchone()
        if row and row[0]:
            cursor.execute("UPDATE lockers SET member_id = NULL, status = 'available', assigned_date = NULL, end_date = NULL WHERE locker_number = ?", (row[0],))
        cursor.execute("DELETE FROM members WHERE id = ?", (member_id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Member deleted"})

    if request.method == "PUT":
        data = request.json or request.form
        cursor.execute("SELECT * FROM members WHERE id = ?", (member_id,))
        existing = cursor.fetchone()
        if not existing:
            conn.close()
            return jsonify({"error": "Member not found"}), 404

        name = data.get("name", existing["name"]).strip()
        phone = data.get("phone", existing["phone"]).strip()
        email = data.get("email", existing["email"]).strip()
        plan_name = data.get("plan_name", existing["plan_name"])
        plan_amount = float(data.get("plan_amount", existing["plan_amount"]))
        start_date = data.get("start_date", existing["start_date"])
        end_date = data.get("end_date", existing["end_date"])
        status = data.get("status", existing["status"])
        notes = data.get("notes", existing["notes"])

        # Locker handling
        new_locker = data.get("locker_number")
        new_locker_end = data.get("locker_end_date")
        new_locker_val = int(new_locker) if new_locker and str(new_locker).isdigit() else None

        old_locker = existing["locker_number"]

        if old_locker and old_locker != new_locker_val:
            # Release old locker
            cursor.execute("UPDATE lockers SET member_id = NULL, status = 'available', assigned_date = NULL, end_date = NULL WHERE locker_number = ?", (old_locker,))

        if new_locker_val:
            cursor.execute("""
                UPDATE lockers
                SET member_id = ?, status = 'assigned', assigned_date = ?, end_date = ?
                WHERE locker_number = ?
            """, (member_id, start_date, new_locker_end or end_date, new_locker_val))

        cursor.execute("""
            UPDATE members
            SET name = ?, phone = ?, email = ?, plan_name = ?, plan_amount = ?, start_date = ?, end_date = ?, locker_number = ?, locker_end_date = ?, status = ?, notes = ?
            WHERE id = ?
        """, (name, phone, email, plan_name, plan_amount, start_date, end_date, new_locker_val, new_locker_end, status, notes, member_id))

        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Member updated successfully"})

    # GET
    cursor.execute("SELECT * FROM members WHERE id = ?", (member_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Member not found"}), 404
    return jsonify(dict(row))

@app.route("/api/lockers", methods=["GET"])
def api_lockers():
    """API: List all lockers."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT l.*, m.name as member_name, m.phone as member_phone
        FROM lockers l
        LEFT JOIN members m ON l.member_id = m.id
        ORDER BY l.locker_number ASC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({"lockers": rows})

@app.route("/api/lockers/assign", methods=["POST"])
def api_assign_locker():
    """API: Assign or renew locker."""
    data = request.json or request.form
    locker_number = int(data.get("locker_number"))
    member_id = int(data.get("member_id"))
    end_date = data.get("end_date")

    if not locker_number or not member_id or not end_date:
        return jsonify({"error": "Locker number, member ID, and end date required"}), 400

    conn = get_db()
    cursor = conn.cursor()
    today_str = datetime.date.today().isoformat()

    # Clear any previous locker for this member
    cursor.execute("SELECT locker_number FROM members WHERE id = ?", (member_id,))
    curr = cursor.fetchone()
    if curr and curr[0] and curr[0] != locker_number:
        cursor.execute("UPDATE lockers SET member_id = NULL, status = 'available', assigned_date = NULL, end_date = NULL WHERE locker_number = ?", (curr[0],))

    # Assign to locker
    cursor.execute("""
        UPDATE lockers
        SET member_id = ?, status = 'assigned', assigned_date = ?, end_date = ?
        WHERE locker_number = ?
    """, (member_id, today_str, end_date, locker_number))

    # Update member record
    cursor.execute("""
        UPDATE members
        SET locker_number = ?, locker_end_date = ?
        WHERE id = ?
    """, (locker_number, end_date, member_id))

    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": f"Locker #{locker_number} assigned successfully"})

@app.route("/api/lockers/release", methods=["POST"])
def api_release_locker():
    """API: Release a locker back to available pool."""
    data = request.json or request.form
    locker_number = int(data.get("locker_number"))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT member_id FROM lockers WHERE locker_number = ?", (locker_number,))
    row = cursor.fetchone()
    if row and row[0]:
        cursor.execute("UPDATE members SET locker_number = NULL, locker_end_date = NULL WHERE id = ?", (row[0],))

    cursor.execute("""
        UPDATE lockers
        SET member_id = NULL, status = 'available', assigned_date = NULL, end_date = NULL
        WHERE locker_number = ?
    """, (locker_number,))

    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": f"Locker #{locker_number} released"})

@app.route("/api/automations/run", methods=["POST"])
def api_run_automations():
    """
    API: Trigger automated scan for subscription and locker expirations.
    Optional 'target_date' in request body to simulate dates.
    """
    data = request.json or {}
    target_date = data.get("target_date")
    result = run_daily_automations(target_date=target_date)
    return jsonify(result)

@app.route("/api/notifications/send-custom", methods=["POST"])
def api_send_custom_notification():
    """API: Dispatch a custom message via WhatsApp or SMS."""
    data = request.json or request.form
    member_id = data.get("member_id")
    member_name = data.get("member_name", "Member")
    phone = data.get("phone")
    channel = data.get("channel", "whatsapp")
    message = data.get("message")
    trigger_type = data.get("trigger_type", "custom_notice")

    if not phone or not message:
        return jsonify({"error": "Phone and message content required"}), 400

    conn = get_db()
    res = dispatch_notification(conn, member_id, member_name, phone, channel, trigger_type, message)
    conn.close()
    return jsonify({"status": "success", "data": res})

@app.route("/api/templates", methods=["GET"])
def api_get_templates():
    """API: List all message templates."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM message_templates")
    templates = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({"templates": templates})

@app.route("/api/templates/<trigger_type>", methods=["PUT"])
def api_update_template(trigger_type):
    """API: Update message template."""
    data = request.json or request.form
    template_text = data.get("template_text")
    title = data.get("title")

    if not template_text:
        return jsonify({"error": "template_text is required"}), 400

    conn = get_db()
    cursor = conn.cursor()
    if title:
        cursor.execute("UPDATE message_templates SET template_text = ?, title = ? WHERE trigger_type = ?", (template_text, title, trigger_type))
    else:
        cursor.execute("UPDATE message_templates SET template_text = ? WHERE trigger_type = ?", (template_text, trigger_type))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Template updated"})

@app.route("/api/trial-pass", methods=["POST"])
def api_create_trial_pass():
    """Public API: Request Free 1-Day Trial Pass."""
    data = request.json or request.form
    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    email = data.get("email", "").strip()
    workout_date = data.get("workout_date") or datetime.date.today().isoformat()

    if not name or not phone:
        return jsonify({"error": "Name and phone number are required"}), 400

    pass_code = f"K9-PASS-{''.join(random.choices(string.digits, k=4))}"

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO trial_passes (name, phone, email, pass_code, workout_date, status, created_at)
        VALUES (?, ?, ?, ?, ?, 'active', ?)
    """, (name, phone, email, pass_code, workout_date, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "pass_code": pass_code,
        "name": name,
        "workout_date": workout_date,
        "view_url": f"/pass/{pass_code}"
    }), 201

@app.route("/api/contact", methods=["POST"])
def api_contact():
    """Public API: Submit contact inquiry."""
    data = request.json or request.form
    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    email = data.get("email", "").strip()
    message = data.get("message", "").strip()

    if not name or not phone or not message:
        return jsonify({"error": "Name, phone, and message are required"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO contact_inquiries (name, phone, email, message, status, created_at)
        VALUES (?, ?, ?, ?, 'new', ?)
    """, (name, phone, email, message, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Thank you! We will get in touch shortly."})

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "False").lower() in ("true", "1", "t")
    app.run(host="0.0.0.0", port=port, debug=debug)
