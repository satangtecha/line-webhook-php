    <?php
    // กำหนดค่า Channel Access Token (ยังคงจำเป็นสำหรับการตอบกลับ)
    $accessToken = '24+yWuIZvh8f4Zav5giuYlpSZ5j3ZdIF2iPACt+PdF0Wo24kGQUTBgX+wjYWCmn09OKxxzX1HK4za3O5hfHkVYn1oCGZqLE2cXkHxpWMUEH4NK04LLFsBwOUkk1/5KDHAHUOjChCHuwRFEVLU46SZwdB04t89/1O/w1cDnyilFU=';

    $logFile = __DIR__ . '/webhook_activity.log';

    // --- ส่วน Debugging: บันทึกทุก Request ที่เข้ามาอย่างละเอียด ---
    $logMessage = date('Y-m-d H:i:s') . " - --- Incoming Request Start ---\n";
    $logMessage .= "Method: " . $_SERVER['REQUEST_METHOD'] . "\n";
    $logMessage .= "Request URI: " . $_SERVER['REQUEST_URI'] . "\n";
    
    // บันทึก Headers ทั้งหมด
    $headers = [];
    foreach ($_SERVER as $key => $value) {
        if (str_starts_with($key, 'HTTP_')) {
            $headerName = str_replace(' ', '-', ucwords(strtolower(str_replace('_', ' ', substr($key, 5)))));
            $headers[$headerName] = $value;
        }
    }
    // เพิ่ม Content-Type ด้วยถ้ามี
    if (isset($_SERVER['CONTENT_TYPE'])) {
        $headers['Content-Type'] = $_SERVER['CONTENT_TYPE'];
    }
    $logMessage .= "Headers: " . json_encode($headers, JSON_PRETTY_PRINT) . "\n";

    // บันทึก Raw Input (Payload)
    $rawInput = file_get_contents('php://input');
    $logMessage .= "Raw Input (Payload): " . $rawInput . "\n";
    $logMessage .= "--- Incoming Request End ---\n\n";
    file_put_contents($logFile, $logMessage, FILE_APPEND);
    // --- สิ้นสุดส่วน Debugging ---


    // -----------------------------------------------------------
    // ส่วนที่ 1: รับ Webhook จาก LINE (สำหรับการตอบกลับข้อความ "เชื่อมต่อหรือยัง")
    // -----------------------------------------------------------
    // อ่านข้อมูลที่ LINE ส่งมา
    $lineContent = $rawInput; // ใช้ rawInput ที่อ่านมาแล้ว
    $lineEvents = json_decode($lineContent, true);

    // ตรวจสอบว่าข้อมูลที่ได้รับจาก LINE ไม่ใช่ค่าว่างและมาจาก LINE จริงๆ
    // LINE จะส่ง HTTP_X_LINE_SIGNATURE ใน Headers
    if (!is_null($lineEvents) && isset($lineEvents['events']) && isset($_SERVER['HTTP_X_LINE_SIGNATURE'])) {
        $logMessage = date('Y-m-d H:i:s') . " - Successfully entered LINE Webhook processing block.\n";
        file_put_contents($logFile, $logMessage, FILE_APPEND);

        foreach ($lineEvents['events'] as $event) {
            // ดึง User ID ของผู้ส่งและบันทึกลง Log
            if (isset($event['source']['userId'])) {
                $senderUserId = $event['source']['userId'];
                $logMessage = date('Y-m-d H:i:s') . " - === FOUND SENDER USER ID: " . $senderUserId . " ===\n"; // เน้นข้อความนี้
                file_put_contents($logFile, $logMessage, FILE_APPEND);
            } else {
                $logMessage = date('Y-m-d H:i:s') . " - User ID not found in event source.\n";
                file_put_contents($logFile, $logMessage, FILE_APPEND);
            }

            // ตรวจสอบว่าเป็นข้อความประเภท text และเป็นคำว่า "เชื่อมต่อหรือยัง"
            if ($event['type'] == 'message' && $event['message']['type'] == 'text' && strtolower($event['message']['text']) == 'เชื่อมต่อหรือยัง') {
                $replyToken = $event['replyToken'];
                $messages = [
                    'type' => 'text',
                    'text' => 'เชื่อมต่อเเล้วค้าบบบ พร้อมลุยยยเเล้วค้าบบลูกเพ้'
                ];

                // ส่งข้อความตอบกลับไปยัง LINE (Reply Message)
                sendLineMessage('reply', $replyToken, $messages, $accessToken, $logFile);
            }
        }
    } else {
        $logMessage = date('Y-m-d H:i:s') . " - DID NOT ENTER LINE Webhook processing block. (Signature/Events missing or payload malformed)\n";
        file_put_contents($logFile, $logMessage, FILE_APPEND);
    }

    // -----------------------------------------------------------
    // ส่วนที่ 2: รับ POST Request จาก Python (สำหรับการส่งแจ้งเตือน)
    // -----------------------------------------------------------
    // ตรวจสอบว่าเป็น POST Request จาก Python (ไม่ใช่จาก LINE Webhook)
    // Python จะส่ง Content-Type เป็น application/json และไม่มี HTTP_X_LINE_SIGNATURE
    if ($_SERVER['REQUEST_METHOD'] === 'POST' && 
        isset($_SERVER['CONTENT_TYPE']) && 
        strpos($_SERVER['CONTENT_TYPE'], 'application/json') !== false &&
        !isset($_SERVER['HTTP_X_LINE_SIGNATURE'])) {
        
        // Use rawInput from earlier
        $pythonData = json_decode($rawInput, true);

        $logMessage = date('Y-m-d H:i:s') . " - Received Python POST: " . $rawInput . "\n";
        file_put_contents($logFile, $logMessage, FILE_APPEND);

        if (isset($pythonData['message']) && isset($pythonData['userId'])) {
            $alertMessage = $pythonData['message'];
            $targetUserId = $pythonData['userId']; // User ID ที่ Python ส่งมาให้ PHP

            // สร้างข้อความที่จะส่ง
            $messages = [
                'type' => 'text',
                'text' => $alertMessage
            ];

            // ส่งข้อความแบบ Push Message ไปยัง User ID ที่ Python ส่งมา
            sendLineMessage('push', $targetUserId, $messages, $accessToken, $logFile);

            http_response_code(200); // บอก Python ว่ารับข้อมูลสำเร็จ
            echo "Message sent successfully.";
        } else {
            $logMessage = date('Y-m-d H:i:s') . " - Python POST: Missing 'message' or 'userId'.\n";
            file_put_contents($logFile, $logMessage, FILE_APPEND);
            http_response_code(400); // Bad Request
            echo "Missing 'message' or 'userId'.";
        }
    } else {
        // ถ้าไม่ใช่ Webhook จาก LINE และไม่ใช่ POST จาก Python
        // อาจเป็นเพียงการเรียกเข้าถึง URL โดยตรง หรือมีการส่งข้อมูลที่ไม่คาดคิด
        // Log นี้จะถูกบันทึกในส่วน Debugging ข้างบนแล้ว
        // $logMessage = date('Y-m-d H:i:s') . " - Unexpected request received. (Method: " . $_SERVER['REQUEST_METHOD'] . ")\n";
        // file_put_contents($logFile, $logMessage, FILE_APPEND);
        // http_response_code(200); // หรือไม่ตอบอะไรเลยก็ได้
    }

    // -----------------------------------------------------------
    // ฟังก์ชันสำหรับส่งข้อความ LINE (รวม Reply และ Push)
    // -----------------------------------------------------------
    function sendLineMessage($type, $target, $messages, $accessToken, $logFile) {
        $url = '';
        $data = [];

        if ($type === 'reply') {
            $url = 'https://api.line.me/v2/bot/message/reply';
            $data = [
                'replyToken' => $target,
                'messages' => [$messages],
            ];
        } elseif ($type === 'push') {
            $url = 'https://api.line.me/v2/bot/message/push';
            $data = [
                'to' => $target,
                'messages' => [$messages],
            ];
        } else {
            file_put_contents($logFile, date('Y-m-d H:i:s') . " - Invalid message type for sendLineMessage.\n", FILE_APPEND);
            return false;
        }

        $post = json_encode($data);

        $headers = array(
            'Content-Type: application/json',
            'Authorization: Bearer ' . $accessToken,
        );

        $ch = curl_init($url);
        curl_setopt($ch, CURLOPT_CUSTOMREQUEST, "POST");
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $post);
        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
        curl_setopt($ch, CURLOPT_FOLLOWLOCATION, 1);
        $result = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE); // รับ HTTP Status Code
        curl_close($ch);

        $logMessage = date('Y-m-d H:i:s') . " - LINE API Response ({$type}, HTTP {$httpCode}): " . $result . "\n";
        file_put_contents($logFile, $logMessage, FILE_APPEND);

        return $httpCode >= 200 && $httpCode < 300; // ส่งคืน true ถ้าสำเร็จ (โค้ด 2xx)
    }

    ?>
    