# Student Attendance System

A production-oriented Flask + SQLAlchemy + SQLite student attendance platform with role-based authentication, parent isolation, RFID/ESP32 REST integration, reporting, and CSV export. The ESP32 provides visual feedback on an SSD1306 OLED; no audio hardware is required.

## Features
- Admin and parent roles with secure password hashing and session authorization.
- Student CRUD, search and grade/class filters.
- Parent CRUD and student assignment.
- One attendance record per student per calendar day, protected by a database uniqueness constraint.
- ESP32 RFID API secured with `X-API-Key`.
- Responsive dashboards for desktop, tablet and mobile.
- Attendance filters and date-range reports with CSV export.
- ESP32 Arduino sketch for MFRC522 + SSD1306 OLED, with check/cross status indicators.
- Automated tests for authentication, authorization, CRUD, API behavior and parent isolation.

## Tech Stack
Python 3.11+ (3.13 supported), Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF, SQLite, Jinja2, HTML/CSS/JavaScript, ESP32 Arduino/C++, MFRC522, SSD1306 OLED.

## Project Structure
```text
student-attendance-system/
├── app.py
├── config.py
├── seed.py
├── requirements.txt
├── .env.example
├── models/
├── routes/
├── services/
├── templates/
├── static/
├── esp32/StudentAttendanceESP32.ino
├── instance/
└── tests/
```

## Installation
1. Install Python 3.11 or newer.
2. Create a virtual environment:
   - Windows: `py -m venv .venv` then `.venv\Scripts\activate`
   - Linux/macOS: `python3 -m venv .venv` then `source .venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`.
4. Copy `.env.example` to `.env` and replace the development secrets.
5. Create the database automatically by starting the app, or run `python -c "from app import app; print('database ready')"`.

## Environment Variables
```text
SECRET_KEY=long-random-secret
DATABASE_URL=sqlite:///attendance.db
ESP32_API_KEY=long-random-device-key
```
For a deployment, use a strong random `SECRET_KEY` and a dedicated API key. Never commit `.env`.

## Create the First Admin
Run:
```bash
python seed.py
```
It prompts for a username and password. Passwords are stored using Werkzeug's password hashing and never as plaintext. For automation, `SEED_ADMIN_USERNAME` and `SEED_ADMIN_PASSWORD` may be supplied in the process environment; do not put them in Git.

## Run Flask
```bash
python app.py
```
Open `http://127.0.0.1:5000`.

## Database
SQLite is the default. The app calls `db.create_all()` at startup for this self-contained initial release. For future production migrations, adopt Alembic/Flask-Migrate before changing existing schemas.

## Roles and Access
- Admin: `/admin/*` only.
- Parent: `/parent/*` only, and only students linked to that parent's `Parent` record are exposed.
- Anonymous users are redirected to `/login` for protected browser routes.

## ESP32 Setup
Install these Arduino libraries using Arduino IDE Library Manager:
- MFRC522
- ArduinoJson (version 7 compatible)
- Adafruit GFX Library
- Adafruit SSD1306

Open `esp32/StudentAttendanceESP32.ino` and change `WIFI_SSID`, `WIFI_PASSWORD`, `SERVER_URL`, and `API_KEY` at the top. The server must be reachable from the ESP32 over the LAN; do not use `127.0.0.1` in `SERVER_URL` because that points to the ESP32 itself.

### Typical wiring
The sketch supports a 0.96-inch or similar SSD1306 I2C OLED (128x64, usually address `0x3C`) and shows a check mark for successful/already-recorded cards and an X for unknown cards or server errors.

| Module | Module pin | ESP32 pin |
|---|---|---|
| SSD1306 OLED | SDA | GPIO21 |
| SSD1306 OLED | SCL | GPIO22 |
| SSD1306 OLED | VCC / GND | Match module rating / GND |
| MFRC522 | SDA/SS | GPIO5 |
| MFRC522 | RST | GPIO27 |
| MFRC522 | SCK / MOSI / MISO | GPIO18 / GPIO23 / GPIO19 (typical VSPI) |

The OLED SCL uses GPIO22, so the RFID reset pin is GPIO27 to avoid a pin conflict. If your board or wiring differs, update the pin constants at the top of `esp32/StudentAttendanceESP32.ino`. Ensure the OLED and RFID share GND and check voltage requirements before connecting. Power the MFRC522 from 3.3V. Some OLED modules use a different I2C address; update `OLED_ADDRESS` if needed.

OLED messages are in English because the standard Adafruit GFX font does not support Persian shaping. `SUCCESS` + check mark means attendance was recorded; `ALREADY OK` + check mark means the student already has a record for today; `UNKNOWN` + X means the UID is not registered; `SERVER ERR` / `BAD REPLY` + X indicates a connection or API response problem. No DFPlayer Mini, speaker, microSD card, or audio library is needed.

## RFID Setup
Create a student in Admin → Students and enter the UID printed by the ESP32 serial monitor. The backend normalizes whitespace and hexadecimal casing. The UID must be unique.

## REST API
### POST `/api/attendance`
Headers:
```text
Content-Type: application/json
X-API-Key: YOUR_ESP32_API_KEY
```
Body:
```json
{"rfid_uid":"A1B2C3D4"}
```
Success:
```json
{"success":true,"message":"Attendance recorded","student":{"id":1,"name":"Ali Ahmadi","student_code":"S001","date":"2026-10-04","time":"08:10:00","status":"present","duplicate":false}}
```
Unknown UID returns HTTP 404 with `{"success":false,"message":"Unknown RFID card"}`. Invalid API keys return HTTP 401. A second scan for the same student on the same date is accepted as an idempotent response and does not create a duplicate record.

## Reports
Admin → Reports supports start/end dates, student and class filters, plus CSV export. The dashboard also shows today's present count and today's inferred absent count (`total students - present records`).

## Tests
Run:
```bash
pytest -q
```
The test suite uses an isolated in-memory SQLite database.

## Troubleshooting
- **Import error:** activate `.venv` and rerun `pip install -r requirements.txt`.
- **Database permissions:** ensure the `instance/` directory is writable.
- **ESP32 cannot connect:** verify the PC LAN IP, firewall, Flask bind address, Wi-Fi network, and API key. For LAN hardware testing run Flask with `app.run(host="0.0.0.0", port=5000)` and restrict access at the network/firewall level.
- **RFID UID differs:** read the exact UID from Serial Monitor; the server accepts hexadecimal UID text with or without spaces.

## Security Notes
Use HTTPS and a reverse proxy in production, rotate the ESP32 API key when devices are replaced, keep `.env` out of version control, use strong passwords, and place the ESP32/API on a trusted network or behind an authenticated gateway. The browser forms use Flask-WTF CSRF protection; the device API uses an explicit API key and is CSRF-exempt because it is not a browser session endpoint.


## نسخه فارسی و OLED فارسی
- رابط کاربری وب راست‌چین و متن‌های اصلی فارسی شده‌اند.
- در پوشه `esp32` فایل `StudentAttendanceESP32.ino` و فایل `PersianOLED.h` باید کنار هم باشند.
- برای OLED از تصویرهای تک‌رنگ از پیش رندرشده استفاده شده تا اتصال حروف فارسی و راست‌به‌چپ درست نمایش داده شود.
- متن پیام‌های ثابت روی OLED فارسی است؛ نام پویای دانش‌آموز به‌صورت متن روی OLED نمایش داده نمی‌شود و در Serial Monitor قابل مشاهده است.
- در فایل ESP32 مقدار `WIFI_SSID`، `WIFI_PASSWORD` و `API_KEY` را با اطلاعات جدید خودتان تنظیم کنید. کلید `API_KEY` باید دقیقاً با متغیر محیطی `ESP32_API_KEY` در Deplexo یکی باشد.
- مقدار `SERVER_URL` از قبل به آدرس `/api/attendance` روی سایت Deplexo تنظیم شده است.
- برای ساخت ادمین، در متغیرهای محیطی سرور `ADMIN_USERNAME` و `ADMIN_PASSWORD` را تنظیم کنید.
- برای جلوگیری از پاک‌شدن داده‌ها، در محیط میزبانی از دیتابیس پایدار استفاده کنید و `DATABASE_URL` را روی آن تنظیم کنید؛ مسیر محلی SQLite ممکن است با استقرار مجدد پاک شود.

### کتابخانه‌های Arduino
`Adafruit GFX Library`, `Adafruit SSD1306`, `MFRC522`, `ArduinoJson` و پشتیبانی ESP32 در Arduino IDE نصب باشند.
