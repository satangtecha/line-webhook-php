    # ใช้ base image ที่มี PHP CLI (Command Line Interface)
    # php:8.2-cli-alpine เป็น image ขนาดเล็กและเหมาะสมสำหรับการรัน PHP Development Server
    FROM php:8.2-cli-alpine

    # กำหนด Working Directory ภายใน Container
    # ไฟล์ทั้งหมดจะถูกคัดลอกไปที่นี่
    WORKDIR /app

    # คัดลอกเนื้อหาทั้งหมดในโฟลเดอร์ 'apple' ของคุณ
    # (ซึ่งมีไฟล์ webhook.php อยู่ข้างใน)
    # ไปยัง Working Directory (/app) ภายใน Container
    # สังเกต: เรา COPY โฟลเดอร์ apple จาก Root ของ GitHub ไปยัง /app
    COPY apple/ .

    # บอก Docker ว่า Container นี้จะเปิด Port 80 (เป็น Port มาตรฐาน)
    # Render จะทำการ map $PORT ของมันเข้ากับ Port นี้โดยอัตโนมัติ
    EXPOSE 80

    # คำสั่งที่จะรันเมื่อ Container เริ่มทำงาน
    # /bin/sh -c ใช้เพื่อรันคำสั่ง Shell เพื่อให้สามารถใช้ตัวแปร Environment $PORT ได้
    # php -S 0.0.0.0:$PORT webhook.php คือการรัน PHP Development Server
    # โดยฟังทุก IP Address และใช้ Port ที่ Render กำหนด ($PORT) และรันไฟล์ webhook.php
    CMD ["/bin/sh", "-c", "php -S 0.0.0.0:$PORT webhook.php"]
    