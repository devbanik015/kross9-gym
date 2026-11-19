import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "kross9-secret-key-coochbehar-fit-2026")
    DATABASE_PATH = os.path.join(BASE_DIR, "kross9.db")
    DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "t")

    # Kross 9 Gym Business Info (Official Cooch Behar Details)
    GYM_NAME = "Kross 9 Gym"
    GYM_TAGLINE = "Unleash Your Ultimate Strength"
    GYM_ADDRESS = "Bakultala More, Debibari Road, Bara Debi Bari, Bhabaniganj Bazar, Cooch Behar, West Bengal – 736101"
    GYM_PHONE = "+91 74780 13363"
    GYM_PHONE_RAW = "917478013363"
    GYM_EMAIL = "contact@kross9gym.com"
    GYM_MAP_URL = "https://maps.google.com/?q=Kross+9+Gym+Coochbehar"
    GYM_HOURS_WEEKDAY = "6:00 AM – 10:00 PM"
    GYM_HOURS_SUNDAY = "Closed"
    
    # Automation & Notification Settings
    SMS_GATEWAY_SIMULATE = True
    AUTOMATION_INTERVAL_SECONDS = 3600 # 1 hour background scan
    
    # Notification Expiration Thresholds
    SUB_EXPIRING_WARNING_DAYS = [3, 1]  # 3 days and 1 day before
    LOCKER_EXPIRING_WARNING_DAYS = [3, 1]
    SUB_OVERDUE_DAYS = 3 # 3 days after expiry
