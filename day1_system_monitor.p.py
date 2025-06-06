import psutil
import time  # เพื่อหน่วงเวลาในการแสดงผล
import matplotlib.pyplot as plt
from datetime import datetime
import csv
import os
import json
import requests

USER_ID = "LINE_USER_ID_YOU_WANT_TO_ALERT" 
CPU_LIMIT = 80
RAM_LIMIT = 80
DISK_LIMIT = 90
cpu_history = []
ram_history = []
disk_history = []
MAX_HISTORY = 30
trend_alert_sent = {
    "CPU": False,
    "RAM": False,
    "Disk": False
}





def get_usage_data():
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    battery = psutil.sensors_battery()
    battery_percent = battery.percent if battery and battery.percent is not None else "No battery"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (timestamp, cpu, ram, disk, battery_percent)

    

def log_data(data):
    with open("log.txt", "a") as f:
        f.write(f"{data[0]}, CPU: {data[1]}%, RAM: {data[2]}%, Disk: {data[3]}%, Battery: {data[4]}%\n")
       


def display_data(data):
    timestamp, cpu, ram, disk, battery_percent = data
    print("-" * 30)
    print(f"🖥️  CPU Usage    : {cpu}%")
    print(f"🧠  RAM Usage    : {ram}%")
    print(f"💽  Disk Usage   : {disk}%")
    if isinstance(battery_percent,(int, float)):
        print(f"🔋  Battery      : {battery_percent}%")
    else:
        print(f"🔋  Battery      : {battery_percent}")
    print("-" * 30)
    print()


def check_alerts(data):
    timestamp, cpu, ram, disk, battery_percent = data
    alerts = []
    if cpu > CPU_LIMIT:
        alerts.append(f"⚠️ ALERT! CPU usage too high {CPU_LIMIT}%: {cpu}%")
    if ram > RAM_LIMIT:
        alerts.append(f"⚠️ ALERT! RAM usage too high {RAM_LIMIT}%: {ram}%")
    if disk > DISK_LIMIT:
        alerts.append(f"⚠️ ALERT! Disk usage too high {DISK_LIMIT}%: {disk}%")
   
    for alert in alerts:
        print(alert)

def check_trend(data_list, label):
    global trend_alert_sent

    if len(data_list) >= MAX_HISTORY:
        avg_start = sum(data_list[:3]) / 3
        avg_end = sum(data_list[-3:]) / 3
        change = avg_end - avg_start

        if change > 15:
            print(f"📈 แนวโน้ม {label} เพิ่มขึ้นต่อเนื่อง: {data_list}")

            if not trend_alert_sent[label]:
                msg = f"📈 แนวโน้ม {label} เพิ่มขึ้นมากกว่า 15%\nจากเฉลี่ย {avg_start:.1f}% ➡️ {avg_end:.1f}%"
                send_line_alert(USER_ID, msg)
                trend_alert_sent[label] = True
        else:
            trend_alert_sent[label] = False

    if len(data_list) >= MAX_HISTORY:
        avg_start = sum(data_list[:3]) / 3
        avg_end = sum(data_list[-3:]) / 3
        if avg_end > avg_start + 15:
            print(f"📈 แนวโน้ม {label} เพิ่มขึ้นต่อเนื่อง: {data_list}")




def plot_usage_history(cpu, ram, disk):
    plt.gcf().canvas.manager.set_window_title("System Monitor Realtime")
    plt.clf()  # เคลียร์กราฟก่อน
    plt.plot(cpu, label="CPU", color='red')
    plt.plot(ram, label="RAM", color='blue')
    plt.plot(disk, label="Disk", color='green')
    plt.ylim(0, 100)
    plt.xlabel("Time")
    plt.ylabel("Usage (%)")
    plt.title("System Resource Usage (Recent History)")
    plt.legend(loc="upper right")
    plt.pause(0.01)  # ให้กราฟอัปเดตแบบเรียลไทม์

def log_data_csv(data):
    file_exists = os.path.isfile("log.csv")
    with open("log.csv", "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "CPU", "RAM", "Disk", "Battery"])
        writer.writerow(data)

def log_data_json(data):
    log_entry = {
        "timestamp": data[0],
        "cpu": data[1],
        "ram": data[2],
        "disk": data[3],
        "battery": data[4]
    }
    with open("log.json", "a") as f:
        json.dump(log_entry, f)
        f.write("\n")

def send_line_alert(user_id, message):
    url = "http://localhost:5000/send-alert"  # ถ้าใช้ ngrok เปลี่ยนเป็น URL ngrok เช่น "https://abc123.ngrok.io/send-alert"
    data = {"user_id": user_id, "message": message}
    try:
        requests.post(url, json=data)
    except Exception as e:
        print(f"❌ Error sending LINE alert: {e}")

try:
    plt.ion()
    while True:
        data = get_usage_data()
        log_data(data)
        log_data_csv(data)
        display_data(data)
        check_alerts(data)
        log_data_json(data)

                # ⬇️ เก็บข้อมูลย้อนหลัง
        cpu_history.append(data[1])
        ram_history.append(data[2])
        disk_history.append(data[3])

        # ⬇️ ควบคุมความยาวของ list ไม่ให้เกิน MAX_HISTORY
        if len(cpu_history) > MAX_HISTORY:
            cpu_history.pop(0)
            ram_history.pop(0)
            disk_history.pop(0)

        # ⬇️ เช็คแนวโน้ม
        check_trend(cpu_history, "CPU")
        check_trend(ram_history, "RAM")
        check_trend(disk_history, "Disk")
        plot_usage_history(cpu_history, ram_history, disk_history)

        time.sleep(2)
        
except KeyboardInterrupt:
    print("\nMonitoring stopped by user.")

