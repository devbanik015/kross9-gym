# Kross 9 Gym — Full Stack Web Platform & Automation Engine

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://python.org)
[![Framework](https://img.shields.io/badge/Framework-Flask_3.1-orange.svg)](https://palletsprojects.com/p/flask/)
[![Styling](https://img.shields.io/badge/Styling-Tailwind_CSS-38bdf8.svg)](https://tailwindcss.com/)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](#testing)
[![Location](https://img.shields.io/badge/Location-Cooch_Behar,_West_Bengal-red.svg)](https://maps.google.com/?q=Kross+9+Gym+Coochbehar)

A modern, high-performance, full-stack web application and automated member management system built specifically for **Kross 9 Gym** located at **Bakultala More, Debibari Road, Cooch Behar, West Bengal – 736101**.

---

## 🏋️ Gym Profile & Business Context
* **Official Name:** Kross 9 Gym (Kross Nine Fitness)
* **Tagline:** *Unleash Your Ultimate Strength*
* **Location:** Bakultala More, Debibari Road, Bara Debi Bari, Bhabaniganj Bazar, Cooch Behar, West Bengal – 736101
* **Contact Phone:** +91 74780 13363
* **Operating Hours:** Monday – Saturday: 6:00 AM – 10:00 PM (Sunday: Closed)
* **Facilities:** Heavy Iron & Free Weights (up to 50kg DBs), Biomechanical Plate-Loaded Machines, Cardio Theater, CrossFit / Functional Turf, 30 Dedicated Private Lockers, Steam & Showers, Certified Personal Trainers.

---

## ⚡ Key Features

### 1. Modern Public Website
* **High-Impact Athletic Aesthetic:** Dark slate theme with energetic crimson/amber gradients, neon glow accents, and responsive layout.
* **Interactive Facility Tour:** Highlights free weights, selectorized cables, cardio zone, functional turf, and private lockers.
* **Transparent Membership Packages:**
  * **Monthly Kickstart:** ₹1,499 / month
  * **Quarterly Pro:** ₹3,999 / 3 months (Most Popular — includes 1-month free locker)
  * **Half-Yearly Elite:** ₹6,999 / 6 months (Includes dedicated locker + 2 free PT sessions)
  * **Annual Champion:** ₹11,999 / year (Includes full 1-year free locker, customized diet blueprint & official tee)
  * **Add-ons:** Dedicated Locker Rental (₹400/mo), Personal Training (₹3,000/mo)
* **Interactive BMI & Calorie Target Calculator:**
  * Calculates BMI, BMR (Mifflin-St Jeor), Total Daily Energy Expenditure (TDEE).
  * Generates personalized calorie & protein targets based on specific goals (Fat Loss, Muscle Hypertrophy, Maintenance) and recommends a workout split.
* **Digital Free 1-Day Trial Pass Generator:**
  * Generates instant personalized pass codes (e.g. `K9-PASS-8392`) with a printable ticket and 1-click WhatsApp confirmation.
* **Class & Floor Timings:** Morning shift (6:00 AM – 11:30 AM) and Evening shift (4:30 PM – 10:00 PM) with peak/off-peak congestion indicators.
* **Google Reviews Showcase:** Authentic feedback highlighting trainers, equipment quality, and locker facilities.
* **Location & Contact:** Google Maps integration, direct click-to-call, click-to-WhatsApp, and callback request form.

---

### 2. Intelligent Notification & Automation Engine
The platform includes an automated daemon and on-demand audit engine designed to prevent revenue leakage and keep members informed:

```
[Daily Scheduler Daemon (Every hour / 08:00 AM)]
                     │
                     ▼
       Scan Members in Database
                     │
       ┌─────────────┴─────────────┐
       ▼                           ▼
Subscription Evaluation       Locker Evaluation
  • T-3 Days Warning            • T-3 Days Warning
  • T-1 Day Reminder            • T-1 Day Notice
  • T-0 Expired Today           • T-0 Expired / Clearance
  • T+3 Days Overdue Notice
       │                           │
       └─────────────┬─────────────┘
                     ▼
       Deduplication Check
       (1 alert per trigger/member/day)
                     │
                     ▼
       Template Token Interpolation
       ({{name}}, {{plan}}, {{end_date}}, {{locker_number}}, etc.)
                     │
                     ▼
       Multi-Channel Dispatch
       ┌───────────────────────────┐
       │ 1. WhatsApp Click-to-Chat │ (https://wa.me/91...?text=...)
       │ 2. SMS Gateway Interface  │ (Fast2SMS / Twilio ready)
       │ 3. Notification Audit Log │ (Logged with timestamps)
       └───────────────────────────┘
```

#### Automation Triggers:
1. `sub_warning_3d` — 3 days before membership end date.
2. `sub_warning_1d` — Tomorrow is the last day of membership.
3. `sub_expired` — Membership expired today; updates status to `expired`.
4. `sub_overdue_3d` — 3 days overdue; final notice before deactivation.
5. `locker_warning_3d` — Locker rental ends in 3 days; prompt to renew or clear.
6. `locker_warning_1d` — Locker rental ends tomorrow.
7. `locker_expired` — Locker expired today; clearance alert.
8. `welcome_member` — Automatically triggered upon member registration.

---

### 3. Staff & Management Portal ("Kross 9 Command Center")
* **Executive Dashboard:** Live counters for active members, expiring this week, expired accounts, locker occupancy, and daily messages dispatched.
* **Priority Attention List:** Highlights members needing immediate renewal follow-up.
* **Member CRM (`/admin/members`):** Complete member registry with search, status filters (Active, Expired), registration modal with automated welcome dispatch, renewal/edit modal, and delete.
* **Interactive Locker Bay (`/admin/lockers`):** Visual 30-locker bay with real-time status badges (Assigned & Active, Expiring Soon, Expired, Available), 1-click assign, renewal, and release.
* **Automations Console (`/admin/automations`):** 
  * "Run Expiry Audit Now" manual execution button.
  * Simulation date picker (test any future date).
  * Template editor for WhatsApp & SMS with live variable placeholder support.
  * Complete audit history stream with direct WhatsApp links.

---

## 🛠️ Architecture & Tech Stack

* **Backend:** Python 3.13, Flask 3.1
* **Database:** SQLite3 (Zero configuration, persistent ACID storage)
* **Frontend:** HTML5, Jinja2, Tailwind CSS (via CDN), Lucide Icons, Custom CSS
* **Scheduler:** Python daemon background thread with configurable polling intervals
* **Testing:** Python `unittest` suite with complete route, CRUD, and automation coverage

---

## 🚀 Getting Started

### 1. Prerequisites
* Python 3.10+ (Tested on Python 3.13)
* Git

### 2. Installation & Setup
```bash
# Clone the repository
git clone https://github.com/devbanik015/kross9-gym.git
cd kross9-gym

# Optional: Create virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python app.py
```
Open your browser and navigate to:
* **Public Website:** `http://localhost:5000`
* **Admin Command Center:** `http://localhost:5000/admin`
* **Member CRM:** `http://localhost:5000/admin/members`
* **Locker Bay:** `http://localhost:5000/admin/lockers`
* **Automations Console:** `http://localhost:5000/admin/automations`

---

## 🧪 Testing

Run the automated test suite:
```bash
python -m unittest discover -s tests -v
```

All 10 unit and integration tests test:
1. Public homepage rendering & business info
2. Trial pass generation & digital view
3. Contact inquiry submission
4. Admin portal routes & KPI stats API
5. Complete member CRUD lifecycle
6. Locker bay allocation and release
7. Automated subscription expiry triggers (`sub_warning_3d`, `sub_warning_1d`, `sub_expired`)
8. Automated locker expiry triggers (`locker_warning_3d`, `locker_expired`)
9. Daily deduplication (prevents spamming members)
10. Template rendering and variable interpolation

---

## 📄 License
MIT License. Developed for Kross 9 Gym, Cooch Behar.
