#import psutil
import time
from datetime import datetime

def get_usage_data():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    battery = psutil.sensors_battery()
    battery_percent = battery.percent if battery else "No battery"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (timestamp, cpu, ram, disk, battery_percent)

def log_data(data):
    battery_str = f"{data[4]}%" if isinstance(data[4], (int, float)) else data[4]
    with open("log.txt", "a") as f:
        f.write(f"{data[0]}, CPU: {data[1]}%, RAM: {data[2]}%, Disk: {data[3]}%, Battery: {battery_str}\n")

def display_data(data):
    timestamp, cpu, ram, disk, battery_percent = data
    battery_str = f"{battery_percent}%" if isinstance(battery_percent, (int, float)) else battery_percent
    print("-" * 30)
    print(f"⏰  Time         : {timestamp}")
    print(f"🖥️  CPU Usage    : {cpu}%")
    print(f"🧠  RAM Usage    : {ram}%")
    print(f"💽  Disk Usage   : {disk}%")
    print(f"🔋  Battery      : {battery_str}")
    print("-" * 30)
    print()


while True:
    data = get_usage_data()
    log_data(data)
    display_data(data)
    time.sleep()
