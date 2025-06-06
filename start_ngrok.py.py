from pyngrok import ngrok
import time
import os

# กำหนด Port ที่ Local Web Server ของคุณรันอยู่ (ที่ใช้ serve webhook.php)
# *** สำคัญ: เปลี่ยนค่านี้ให้ตรงกับ Port ที่คุณรัน PHP Web Server ของคุณจริงๆ ***
# ตัวอย่าง:
# ถ้าคุณรัน 'php -S localhost:8000' ให้ใส่ 8000
# ถ้าคุณใช้ Apache/Nginx และ Webhook อยู่ที่ Port 80 ให้ใส่ 80
LOCAL_WEBHOOK_PORT = 8000 

def start_ngrok_tunnel(port):
    """
    เริ่มต้น Ngrok Tunnel และคืนค่า Public URL
    """
    print("--- Project PreBreak Ngrok Automation ---")
    print("กำลังเริ่มต้น Ngrok Tunnel...")
    try:
        # เชื่อมต่อ Ngrok ไปยัง Port ที่ระบุ
        # ngrok.set_auth_token("YOUR_AUTH_TOKEN_HERE") # หากยังไม่ได้ตั้งค่า authtoken สามารถใส่ตรงนี้ได้
        public_url = ngrok.connect(port).public_url
        print(f"✅ Ngrok Tunnel เริ่มทำงานแล้ว ที่ Port: {port}")
        print(f"🔗 Public URL ของคุณคือ: {public_url}")
        print(f"   (นี่คือ URL ที่ LINE จะใช้เรียก Webhook ของคุณ)")
        print("\n*** สำคัญ: คัดลอก URL นี้ไปวางใน LINE Developers Console: Webhook URL ***")
        print("   จากนั้นกด 'Verify' เพื่อยืนยัน")
        print("\nกด Ctrl+C เพื่อหยุดการทำงานของ Ngrok และ Script นี้")
        return public_url
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการเริ่มต้น Ngrok: {e}")
        print("โปรดตรวจสอบ:")
        print("1. คุณได้ติดตั้ง ngrok และตั้งค่า authtoken ถูกต้องแล้วหรือไม่?")
        print("2. Port ที่ระบุ ({}) มีโปรแกรมอื่นใช้งานอยู่หรือไม่?".format(port))
        print("3. Local Web Server (เช่น 'php -S localhost:{}') กำลังรันอยู่หรือไม่?".format(port))
        return None

if __name__ == "__main__":
    # ตรวจสอบว่า Local Web Server ของคุณรันอยู่หรือไม่ ก่อนเริ่ม Ngrok
    # (ขั้นตอนนี้จะแค่แจ้งเตือน ไม่ได้บังคับ)
    print(f"⚠️ ตรวจสอบให้แน่ใจว่า Local Web Server ของคุณกำลังรันอยู่ที่ Port {LOCAL_WEBHOOK_PORT}")
    print(f"   ตัวอย่าง: รัน 'php -S localhost:{LOCAL_WEBHOOK_PORT}' ในโฟลเดอร์ webhook.php")
    print("---------------------------------------")
    
    public_url = start_ngrok_tunnel(LOCAL_WEBHOOK_PORT)
    if public_url:
        try:
            # รัน loop ค้างไว้เพื่อให้ Ngrok Tunnel ทำงานต่อไปเรื่อยๆ
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nกำลังปิด Ngrok Tunnel...")
            ngrok.disconnect() # ปิด Ngrok Tunnel อย่างถูกต้อง
            print("Ngrok Tunnel ถูกปิดแล้ว. ขอบคุณที่ใช้งาน!")