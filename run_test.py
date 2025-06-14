# run_test.py
import streamlit.web.bootstrap
from streamlit.web import cli as stcli
import sys
import os

def run():
    # กำหนด Path ไปยัง Script หลัก
    main_script_path = os.path.join(os.path.dirname(__file__), 'test_app.py')

    # ตั้งค่า sys.argv เหมือนกับการรัน command line
    sys.argv = [
        "streamlit",
        "run",
        main_script_path,
        "--server.headless=true",
        "--server.enableCORS=false",
    ]

    # เรียกใช้ฟังก์ชัน main ของ Streamlit CLI
    # นี่คือวิธีที่ถูกต้องสำหรับ Streamlit เวอร์ชันใหม่
    sys.exit(stcli.main())

if __name__ == "__main__":
    run()