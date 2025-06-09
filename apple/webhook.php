    <?php
    $logFile = __DIR__ . '/webhook_activity.log';
    $logMessage = date('Y-m-d H:i:s') . " - Request received!\n";
    $logMessage .= "Method: " . $_SERVER['REQUEST_METHOD'] . "\n";
    $logMessage .= "Headers: " . json_encode(apache_request_headers()) . "\n"; // บันทึก Headers ทั้งหมด
    $logMessage .= "Input: " . file_get_contents('php://input') . "\n"; // บันทึก Body ของ Request
    file_put_contents($logFile, $logMessage, FILE_APPEND);

    http_response_code(200); // ตอบกลับ 200 OK เสมอ
    echo "OK"; // ส่งข้อความตอบกลับ
    ?>
    