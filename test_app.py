# test_app.py
import streamlit as st

st.set_page_config(page_title="Test App", layout="centered")
st.title("✅ Hello from PyInstaller!")
st.write("ถ้าคุณเห็นหน้านี้ได้ แปลว่า Streamlit Server ทำงานสำเร็จ")

if st.button("Click Me!"):
    st.balloons()