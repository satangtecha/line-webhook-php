<?php
// // คุณสามารถใช้ LINE Bot SDK ได้ตามที่ผมแนะนำก่อนหน้า (ถ้าติดตั้ง Composer แล้ว)
// // require_once(__DIR__ . '/vendor/autoload.php');
// // use LINE\LINEBot;
// // use LINE\LINEBot\HTTPClient\CurlHTTPClient;
// // use LINE\LINEBot\MessageBuilder\TextMessageBuilder;

// กำหนดค่า Channel Access Token
// *** สำคัญ: ควรเก็บ Token นี้ให้ปลอดภัย ไม่ควร hardcode ในโค้ดจริงใน Production ***
// หาก Deploy บน Render.com แนะนำให้ไปตั้งค่าใน Environment Variables ของ Render Service นั้นๆ
// แล้วดึงมาใช้ด้วย getenv('LINE_CHANNEL_ACCESS_TOKEN')
$accessToken = 'xccQkq8aSNTTM1OpOgkNR/pVI5UszUXf/45pfziWJ/igGTnbToexKngo0ZWIe22CF7p39wx+nZnamdeeM6o8W/4RXEyvb969Mh3iNoHpqYv+yz20y2BCRRCl+VK71rf8q7b/s+2jH5h02LDPCyt2ogdB04t89/1O/w1cDnyilFU=';

// สร้างไฟล์ log เพื่อดูข้อมูลที่ได้รับ (ช่วยในการ Debug)
// บน Render.com, error_log() จะไปโผล่ในส่วนของ Logs ของ Service
// ดังนั้นจึงเปลี่ยนมาใช้ error_log() แทน file_put_contents() สำหรับการ Log
// $logFile = __DIR__ . '/webhook_activity.log'; 

// -----------------------------------------------------------
// ส่วน Debugging: บันทึกทุก Request ที่เข้ามาอย่างละเอียด (จะไปโผล่ใน Render Logs)
// -----------------------------------------------------------
$logMessageDebug = date('Y-m-d H:i:s') . " - --- Incoming Request Start ---\n";
$logMessageDebug .= "Method: " . $_SERVER['REQUEST_METHOD'] . "\n";
$logMessageDebug .= "Request URI: " . $_SERVER['REQUEST_URI'] . "\n";

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
$logMessageDebug .= "Headers: " . json_encode($headers, JSON_PRETTY_PRINT) . "\n";

// บันทึก Raw Input (Payload)
$rawInput = file_get_contents('php://input');
$logMessageDebug .= "Raw Input (Payload): " . $rawInput . "\n";
$logMessageDebug .= "--- Incoming Request End ---\n\n";
error_log($logMessageDebug); // เปลี่ยนมาใช้ error_log() แทน file_put_contents()


// -----------------------------------------------------------
// ส่วนที่ 1: รับ Webhook จาก LINE (สำหรับการตอบกลับข้อความ)
// -----------------------------------------------------------
// อ่านข้อมูลที่ LINE ส่งมา
$lineContent = $rawInput; // ใช้ rawInput ที่อ่านมาแล้ว
$lineEvents = json_decode($lineContent, true);

// ตรวจสอบว่าข้อมูลที่ได้รับจาก LINE ไม่ใช่ค่าว่างและมาจาก LINE จริงๆ
// LINE จะส่ง HTTP_X_LINE_SIGNATURE ใน Headers
if (!is_null($lineEvents) && isset($lineEvents['events']) && isset($_SERVER['HTTP_X_LINE_SIGNATURE'])) {
    error_log(date('Y-m-d H:i:s') . " - Successfully entered LINE Webhook processing block.\n"); // Log

    foreach ($lineEvents['events'] as $event) {
        // ดึง User ID ของผู้ส่ง (Sender)
        $senderUserId = null;
        if (isset($event['source']['userId'])) {
            $senderUserId = $event['source']['userId'];
            error_log(date('Y-m-d H:i:s') . " - === FOUND SENDER USER ID: " . $senderUserId . " ===\n"); // Log User ID
        } else {
            error_log(date('Y-m-d H:i:s') . " - User ID not found in event source.\n"); // Log
        }

        // ตรวจสอบว่าเป็นข้อความประเภท text
        if ($event['type'] == 'message' && $event['message']['type'] == 'text') {
            $receivedMessage = strtolower($event['message']['text']);
            $replyToken = $event['replyToken'];

            // Logic สำหรับตอบกลับข้อความ "เชื่อมต่อหรือยัง"
            if ($receivedMessage == 'เชื่อมต่อหรือยัง') {
                $messages = [
                    'type' => 'text',
                    'text' => 'เชื่อมต่อเเล้วค้าบบบ พร้อมลุยยยเเล้วค้าบบลูกเพ้'
                ];
                sendLineMessage('reply', $replyToken, $messages, $accessToken);
            } 
            // NEW LOGIC: สำหรับตอบกลับ User ID เมื่อผู้ใช้ส่ง "My ID" หรือ "ขอ user id"
            elseif ($receivedMessage == 'my id' || $receivedMessage == 'ขอ user id') {
                if ($senderUserId) {
                    $messages = [
                        'type' => 'text',
                        'text' => 'LINE User ID ของคุณคือ: ' . $senderUserId . "\n\n" . 'โปรดคัดลอกรหัสนี้ไปวางในช่อง "LINE Target User ID" ในแอป PreBreak ของคุณ'
                    ];
                    sendLineMessage('reply', $replyToken, $messages, $accessToken);
                } else {
                    $messages = [
                        'type' => 'text',
                        'text' => 'ไม่พบ LINE User ID ของคุณ โปรดลองอีกครั้งหรือตรวจสอบสิทธิ์'
                    ];
                    sendLineMessage('reply', $replyToken, $messages, $accessToken);
                }
            }
            // สามารถเพิ่มเงื่อนไขอื่นๆ ได้ที่นี่
        }
    }
} else {
    error_log(date('Y-m-d H:i:s') . " - DID NOT ENTER LINE Webhook processing block. (Signature/Events missing or payload malformed)\n"); // Log
}

// -----------------------------------------------------------
// ส่วนที่ 2: รับ POST Request จาก Python (สำหรับการส่งแจ้งเตือน)
// -----------------------------------------------------------
if ($_SERVER['REQUEST_METHOD'] === 'POST' && 
    isset($_SERVER['CONTENT_TYPE']) && 
    strpos($_SERVER['CONTENT_TYPE'], 'application/json') !== false &&
    !isset($_SERVER['HTTP_X_LINE_SIGNATURE'])) {
    
    $pythonData = json_decode($rawInput, true);

    error_log(date('Y-m-d H:i:s') . " - Received Python POST: " . $rawInput . "\n"); // Log

    if (isset($pythonData['message']) && isset($pythonData['userId'])) {
        $alertMessage = $pythonData['message'];
        $targetUserId = $pythonData['userId'];

        $messages = [
            'type' => 'text',
            'text' => $alertMessage
        ];

        sendLineMessage('push', $targetUserId, $messages, $accessToken);

        http_response_code(200);
        echo "Message sent successfully.";
    } else {
        error_log(date('Y-m-d H:i:s') . " - Python POST: Missing 'message' or 'userId'.\n"); // Log
        http_response_code(400);
        echo "Missing 'message' or 'userId'.";
    }
}

// -----------------------------------------------------------
// ฟังก์ชันสำหรับส่งข้อความ LINE (รวม Reply และ Push)
// -----------------------------------------------------------
function sendLineMessage($type, $target, $messages, $accessToken) { 
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
        error_log(date('Y-m-d H:i:s') . " - Invalid message type for sendLineMessage.\n"); // Log
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
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    error_log(date('Y-m-d H:i:s') . " - LINE API Response ({$type}, HTTP {$httpCode}): " . $result . "\n"); // Log API Response

    return $httpCode >= 200 && $httpCode < 300;
}

?>
