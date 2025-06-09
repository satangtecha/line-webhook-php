# monitor_app.py

import streamlit as st
import psutil
from datetime import datetime
import time
import matplotlib.pyplot as plt
import requests  # <-- เพิ่มบรรทัดนี้
import json      # <-- เพิ่มบรรทัดนี้

st.set_page_config(page_title="PreBreak Monitor", layout="wide")

st.title("💻 PreBreak System Monitor")
st.markdown("ตรวจสอบการใช้งาน CPU, RAM, Disk และ Battery แบบเรียลไทม์")

# --- ส่วนการตั้งค่าสำหรับ LINE Alert (เพิ่มตรงนี้) ---
# *** สำคัญ: ต้องเปลี่ยนค่าเหล่านี้ด้วยข้อมูลจริงของคุณ ***
LINE_WEBHOOK_URL = "https://line-webhook-php.onrender.com" # <-- แทนที่ด้วย URL ngrok และ Path ของ webhook.php ของคุณ
LINE_TARGET_USER_ID = ".0937466471" # <-- แทนที่ด้วย User ID ของ LINE ของคุณเอง

# กำหนดค่า Threshold (ขีดจำกัด) สำหรับการแจ้งเตือน
# ตอนนี้ Hardcode ไว้ก่อน (ตามแผนจะย้ายไป config.json ทีหลัง)
CPU_LIMIT = 1 # เปอร์เซ็นต์ CPU ที่ถือว่าสูง
RAM_LIMIT = 1 # เปอร์เซ็นต์ RAM ที่ถือว่าสูง
DISK_LIMIT = 1 # เปอร์เซ็นต์ Disk ที่ถือว่าสูง

# ตัวแปรสำหรับป้องกันการแจ้งเตือนซ้ำๆ (แจ้งเตือนครั้งเดียวจนกว่าจะกลับมาปกติ)
alert_sent_cpu = False
alert_sent_ram = False
alert_sent_disk = False
# --- สิ้นสุดส่วนการตั้งค่า ---


placeholder = st.empty()

cpu_data = []
ram_data = []
disk_data = []
MAX_POINTS = 30

monitoring = st.checkbox("เริ่ม Monitoring", value=True)

while monitoring:
    # 1. อ่านข้อมูล
    cpu = psutil.cpu_percent(interval=1) # เพิ่ม interval เพื่อความแม่นยำ
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    battery = psutil.sensors_battery()
    battery_percent = battery.percent if battery else "N/A"

    # 2. บันทึกข้อมูลสำหรับกราฟ
    cpu_data.append(cpu)
    ram_data.append(ram)
    disk_data.append(disk)

    if len(cpu_data) > MAX_POINTS:
        cpu_data.pop(0)
        ram_data.pop(0)
        disk_data.pop(0)

    # 3. แสดงข้อมูลบน Streamlit UI
    with placeholder.container():
        st.metric("🖥️ CPU (%)", f"{cpu:.1f}")
        st.metric("🧠 RAM (%)", f"{ram:.1f}")
        st.metric("💽 Disk (%)", f"{disk:.1f}")
        st.metric("🔋 Battery (%)", f"{battery_percent}")

        st.line_chart({
            "CPU": cpu_data,
            "RAM": ram_data,
            "Disk": disk_data
        })

    # --- ส่วนการตรวจจับและส่งแจ้งเตือน LINE (เพิ่มตรงนี้) ---
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    alert_messages = []

    # ตรวจสอบ CPU
    if cpu > CPU_LIMIT:
        if not alert_sent_cpu:
            alert_messages.append(f"🖥️ CPU usage is high: {cpu:.1f}% (Limit: {CPU_LIMIT}%)")
            alert_sent_cpu = True
    else:
        alert_sent_cpu = False # Reset เมื่อกลับมาปกติ

    # ตรวจสอบ RAM
    if ram > RAM_LIMIT:
        if not alert_sent_ram:
            alert_messages.append(f"🧠 RAM usage is high: {ram:.1f}% (Limit: {RAM_LIMIT}%)")
            alert_sent_ram = True
    else:
        alert_sent_ram = False # Reset เมื่อกลับมาปกติ

    # ตรวจสอบ Disk
    if disk > DISK_LIMIT:
        if not alert_sent_disk:
            alert_messages.append(f"💽 Disk usage is high: {disk:.1f}% (Limit: {DISK_LIMIT}%)")
            alert_sent_disk = True
    else:
        alert_sent_disk = False # Reset เมื่อกลับมาปกติ

    # ถ้ามีข้อความแจ้งเตือน ให้ส่งไปยัง LINE webhook
    if alert_messages:
        full_alert_message = f"🚨 PreBreak Alert ({current_time}):\n" + "\n".join(alert_messages)

        payload = {
            "message": full_alert_message,
            "userId": LINE_TARGET_USER_ID
        }
        headers = {'Content-Type': 'application/json'}

        try:
            response = requests.post(LINE_WEBHOOK_URL, data=json.dumps(payload), headers=headers)
            response.raise_for_status() # ตรวจสอบ HTTP status code (ถ้าไม่ใช่ 2xx จะเกิด exception)
            st.write(f"Alert sent to LINE: {full_alert_message}") # แสดงใน Streamlit ด้วย
            print(f"[{current_time}] Alert sent to LINE: {full_alert_message}") # แสดงใน Console/Terminal ด้วย
        except requests.exceptions.RequestException as e:
            st.warning(f"Error sending alert to LINE: {e}") # แสดงใน Streamlit ด้วย
            print(f"[{current_time}] Error sending alert to LINE: {e}") # แสดงใน Console/Terminal ด้วย
    # --- สิ้นสุดส่วนการตรวจจับและส่งแจ้งเตือน ---

    time.sleep(2)

    # หยุด loop ถ้า checkbox ถูกยกเลิก
    if not monitoring:
        st.stop() # หยุดการทำงานของ Streamlit loop