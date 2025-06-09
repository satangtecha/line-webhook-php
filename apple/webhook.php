    <?php
    $logFile = __DIR__ . '/webhook_activity.log';
    $message = "Test Log: " . date('Y-m-d H:i:s') . " - This is a test log entry.\n";
    
    // ลองเขียน Log
    file_put_contents($logFile, $message, FILE_APPEND);
    
    // แสดงผลบนหน้าเว็บ (จะเห็นเมื่อเข้าถึง URL โดยตรง)
    echo "Hello PHP from Render! Check logs for '" . $logFile . "'\n";
    echo "Log written: " . ($message) . "\n"; // แสดงข้อความที่เขียน
    
    // ตั้งค่า Response Code ให้เป็น 200 เสมอ
    http_response_code(200);
    ?>
    