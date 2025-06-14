# run_app.py
import streamlit.web.bootstrap
import sys
import os

def run_streamlit():
    # กำหนด path ไปยัง script หลักของ Streamlit
    main_script_path = os.path.join(os.path.dirname(__file__), 'monitor_app.py')

    # ตั้งค่า sys.argv เพื่อจำลองการรัน 'streamlit run monitor_app.py --server.headless=true'
    sys.argv = [
        "streamlit",
        "run",
        main_script_path,
        "--server.headless=true",  # ป้องกันไม่ให้ Streamlit พยายามเปิดเบราว์เซอร์เอง
        "--server.enableCORS=false", # อาจช่วยในบางกรณี
    ]

    # เรียกใช้ฟังก์ชันหลักของ Streamlit เพื่อสตาร์ทเซิร์ฟเวอร์
    streamlit.web.bootstrap.run()

if __name__ == '__main__':
    run_streamlit()