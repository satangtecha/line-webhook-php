import psutil
import time  # เพื่อหน่วงเวลาในการแสดงผล

def display_usage():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    battery = psutil.sensors_battery()
    battery_percent = battery.percent if battery else "No battery"

    print("-" * 30)
    print(f"🖥️  CPU Usage    : {cpu}%")
    print(f"🧠  RAM Usage    : {ram}%")
    print(f"💽  Disk Usage   : {disk}%")
    print(f"🔋  Battery      : {battery_percent}%")
    print("-" * 30)
    print()

while True:
    display_usage()
    time.sleep(1)
