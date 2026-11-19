import sqlite3
import datetime
from config import Config

def get_db():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(seed=True):
    conn = get_db()
    cursor = conn.cursor()

    # 1. Members table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT,
        plan_name TEXT NOT NULL,
        plan_amount REAL DEFAULT 0,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        locker_number INTEGER,
        locker_end_date TEXT,
        emergency_contact TEXT,
        notes TEXT,
        status TEXT DEFAULT 'active',
        created_at TEXT NOT NULL
    );
    """)

    # 2. Lockers table (Fixed bay of lockers)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lockers (
        locker_number INTEGER PRIMARY KEY,
        member_id INTEGER,
        status TEXT DEFAULT 'available', -- 'available', 'assigned', 'maintenance'
        assigned_date TEXT,
        end_date TEXT,
        FOREIGN KEY(member_id) REFERENCES members(id) ON DELETE SET NULL
    );
    """)

    # 3. Message Templates table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS message_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trigger_type TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        template_text TEXT NOT NULL,
        channel TEXT DEFAULT 'whatsapp',
        is_active INTEGER DEFAULT 1
    );
    """)

    # 4. Notification Audit Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notification_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER,
        member_name TEXT NOT NULL,
        recipient_phone TEXT NOT NULL,
        channel TEXT NOT NULL, -- 'whatsapp', 'sms'
        trigger_type TEXT NOT NULL,
        message_text TEXT NOT NULL,
        status TEXT DEFAULT 'sent', -- 'sent', 'queued', 'failed'
        error_details TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(member_id) REFERENCES members(id) ON DELETE SET NULL
    );
    """)

    # 5. Free 1-Day Trial Passes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trial_passes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT,
        pass_code TEXT UNIQUE NOT NULL,
        workout_date TEXT NOT NULL,
        status TEXT DEFAULT 'active', -- 'active', 'redeemed', 'expired'
        created_at TEXT NOT NULL
    );
    """)

    # 6. Contact & Inquiry submissions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contact_inquiries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT,
        message TEXT NOT NULL,
        status TEXT DEFAULT 'new',
        created_at TEXT NOT NULL
    );
    """)

    conn.commit()

    if seed:
        seed_data(conn)

    conn.close()

def seed_data(conn):
    cursor = conn.cursor()

    # Seed Lockers (1 to 30) if empty
    cursor.execute("SELECT COUNT(*) FROM lockers")
    if cursor.fetchone()[0] == 0:
        for i in range(1, 31):
            cursor.execute("INSERT INTO lockers (locker_number, status) VALUES (?, 'available')", (i,))
        conn.commit()

    # Seed Templates if empty
    cursor.execute("SELECT COUNT(*) FROM message_templates")
    if cursor.fetchone()[0] == 0:
        default_templates = [
            (
                "sub_warning_3d",
                "Subscription Expiring in 3 Days",
                "Hi {{name}}! 🏋️ Your Kross 9 Gym membership ({{plan}}) expires in 3 days on {{end_date}}. Renew today to keep your fitness streak uninterrupted! Call {{gym_phone}} or visit reception.",
                "whatsapp"
            ),
            (
                "sub_warning_1d",
                "Subscription Expiring Tomorrow",
                "Reminder: Hi {{name}}, tomorrow ({{end_date}}) is the last day of your Kross 9 Gym {{plan}} plan. Don't lose your workout momentum! Renew at reception today.",
                "whatsapp"
            ),
            (
                "sub_expired",
                "Subscription Expired Today",
                "Hi {{name}}, your Kross 9 Gym membership has expired today ({{end_date}}). We miss you on the gym floor! Re-activate your membership today at our desk: {{gym_phone}}.",
                "whatsapp"
            ),
            (
                "sub_overdue_3d",
                "Subscription Overdue (3 Days)",
                "Action Required: {{name}}, your Kross 9 Gym subscription has been expired for 3 days. To avoid account deactivation or re-registration fees, please renew soon.",
                "whatsapp"
            ),
            (
                "locker_warning_3d",
                "Locker Rental Expiring in 3 Days",
                "Notice from Kross 9 Gym: Your locker #{{locker_number}} rental ends in 3 days on {{locker_end_date}}. Please renew your locker or arrange to collect your belongings.",
                "whatsapp"
            ),
            (
                "locker_warning_1d",
                "Locker Rental Expiring Tomorrow",
                "Urgent: Locker #{{locker_number}} at Kross 9 Gym expires tomorrow ({{locker_end_date}}). Please renew at the front desk today to keep your locker reserved.",
                "whatsapp"
            ),
            (
                "locker_expired",
                "Locker Rental Expired Today",
                "Alert: Locker #{{locker_number}} at Kross 9 Gym has expired today. Unrenewed lockers are scheduled for clearing. Please visit reception or call {{gym_phone}}.",
                "whatsapp"
            ),
            (
                "welcome_member",
                "New Member Welcome Onboarding",
                "Welcome to the Kross 9 Gym family, {{name}}! 💥 Your {{plan}} membership is active until {{end_date}}. Our hours are Mon-Sat 6 AM to 10 PM at Bakultala More, Cooch Behar. Let's conquer your fitness goals together!",
                "whatsapp"
            )
        ]
        cursor.executemany("""
            INSERT INTO message_templates (trigger_type, title, template_text, channel)
            VALUES (?, ?, ?, ?)
        """, default_templates)
        conn.commit()

    # Seed Sample Members if empty
    cursor.execute("SELECT COUNT(*) FROM members")
    if cursor.fetchone()[0] == 0:
        today = datetime.date.today()
        
        sample_members = [
            # 1. Active Member (Long term)
            (
                "Rahul Roy",
                "9832014560",
                "rahul.roy@gmail.com",
                "Annual Champion",
                11999.0,
                (today - datetime.timedelta(days=60)).isoformat(),
                (today + datetime.timedelta(days=305)).isoformat(),
                5,
                (today + datetime.timedelta(days=305)).isoformat(),
                "9832014561 (Father)",
                "Focus on powerlifting and hypertrophy",
                "active",
                (today - datetime.timedelta(days=60)).isoformat()
            ),
            # 2. Member Expiring in 3 Days (Triggers sub_warning_3d)
            (
                "Priya Sen",
                "9733088921",
                "priya.sen@outlook.com",
                "Quarterly Pro",
                3999.0,
                (today - datetime.timedelta(days=87)).isoformat(),
                (today + datetime.timedelta(days=3)).isoformat(),
                12,
                (today + datetime.timedelta(days=3)).isoformat(),
                "9733088920 (Spouse)",
                "Prefers morning slots 7-8 AM",
                "active",
                (today - datetime.timedelta(days=87)).isoformat()
            ),
            # 3. Member Expiring in 1 Day (Triggers sub_warning_1d)
            (
                "Sourav Chakraborty",
                "9474023189",
                "sourav.c@gmail.com",
                "Monthly Kickstart",
                1499.0,
                (today - datetime.timedelta(days=29)).isoformat(),
                (today + datetime.timedelta(days=1)).isoformat(),
                None,
                None,
                "9474023188",
                "CrossFit and functional training enthusiast",
                "active",
                (today - datetime.timedelta(days=29)).isoformat()
            ),
            # 4. Member Expired Today (Triggers sub_expired)
            (
                "Aniket Ghosh",
                "9647812904",
                "aniket.g@gmail.com",
                "Monthly Kickstart",
                1499.0,
                (today - datetime.timedelta(days=30)).isoformat(),
                today.isoformat(),
                18,
                today.isoformat(),
                "9647812900",
                "Requested reminder via WhatsApp",
                "active",
                (today - datetime.timedelta(days=30)).isoformat()
            ),
            # 5. Member Overdue by 3 Days (Triggers sub_overdue_3d)
            (
                "Dipankar Das",
                "9800412387",
                "dipankar.das@yahoo.com",
                "Quarterly Pro",
                3999.0,
                (today - datetime.timedelta(days=93)).isoformat(),
                (today - datetime.timedelta(days=3)).isoformat(),
                None,
                None,
                "9800412380",
                "Travelled for exam, needs follow up",
                "expired",
                (today - datetime.timedelta(days=93)).isoformat()
            ),
            # 6. Active Subscription but Locker Expiring in 3 Days (Triggers locker_warning_3d)
            (
                "Sneha Paul",
                "9126743912",
                "sneha.paul@gmail.com",
                "Half-Yearly Elite",
                6999.0,
                (today - datetime.timedelta(days=40)).isoformat(),
                (today + datetime.timedelta(days=140)).isoformat(),
                8,
                (today + datetime.timedelta(days=3)).isoformat(),
                "9126743900 (Mother)",
                "Locker rental was added on separate 1-month term",
                "active",
                (today - datetime.timedelta(days=40)).isoformat()
            ),
            # 7. Active Member with Locker Expired Today (Triggers locker_expired)
            (
                "Subhashish Barman",
                "9933156782",
                "subhashish.b@gmail.com",
                "Quarterly Pro",
                3999.0,
                (today - datetime.timedelta(days=45)).isoformat(),
                (today + datetime.timedelta(days=45)).isoformat(),
                22,
                today.isoformat(),
                "9933156780",
                "Locker key kept at reception",
                "active",
                (today - datetime.timedelta(days=45)).isoformat()
            ),
            # 8. Another Active Member
            (
                "Debolina Sarkar",
                "9434871234",
                "debolina.sarkar@gmail.com",
                "Half-Yearly Elite",
                6999.0,
                (today - datetime.timedelta(days=20)).isoformat(),
                (today + datetime.timedelta(days=160)).isoformat(),
                15,
                (today + datetime.timedelta(days=160)).isoformat(),
                "9434871200",
                "Personal Training with Coach Amit",
                "active",
                (today - datetime.timedelta(days=20)).isoformat()
            )
        ]

        for m in sample_members:
            cursor.execute("""
                INSERT INTO members (name, phone, email, plan_name, plan_amount, start_date, end_date, locker_number, locker_end_date, emergency_contact, notes, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, m)
            member_id = cursor.lastrowid
            
            # If member has a locker assigned, update locker table
            locker_num = m[7]
            locker_end = m[8]
            if locker_num:
                cursor.execute("""
                    UPDATE lockers
                    SET member_id = ?, status = 'assigned', assigned_date = ?, end_date = ?
                    WHERE locker_number = ?
                """, (member_id, m[5], locker_end, locker_num))

        conn.commit()
