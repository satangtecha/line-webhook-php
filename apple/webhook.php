<?php
// กำหนดค่า Channel Access Token
$accessToken = '';
$accessToken = '24+yWuIZvh8f4Zav5giuYlpSZ5j3ZdIF2iPACt+PdF0Wo24kGQUTBgX+wjYWCmn09OKxxzX1HK4za3O5hfHkVYn1oCGZqLE2cXkHxpWMUEH4NK04LLFsBwOUkk1/5KDHAHUOjChCHuwRFEVLU46SZwdB04t89/1O/w1cDnyilFU=';

// รับข้อมูลจาก LINE webhook
$content = file_get_contents('php://input');
$events = json_decode($content, true);

// ตรวจสอบว่าข้อมูลที่ได้รับไม่ใช่ค่าว่าง
if (!is_null($events)) {
// วนลูปข้อมูลที่ได้รับมา
foreach ($events['events'] as $event) {
// ตรวจสอบว่าเป็นข้อความประเภท text และเป็นคำว่า "เชื่อมต่อหรือยัง"
if ($event['type'] == 'message' && $event['message']['type'] == 'text' && strtolower($event['message']['text']) == 'เชื่อมต่อหรือยัง') {

// ข้อมูลการตอบกลับ
$replyToken = $event['replyToken'];
$messages = [
'type' => 'text',
'text' => 'เชื่อมต่อเเล้วค้าบบบ พร้อมลุยยยเเล้วค้าบบลูกเพ้'
];

// ส่งข้อความตอบกลับ
$url = 'https://api.line.me/v2/bot/message/reply';
$data = [
'replyToken' => $replyToken,
'messages' => [$messages],
];
$post = json_encode($data);

// กำหนด Header ของ cURL
$headers = array(
'Content-Type: application/json',
'Authorization: Bearer ' . $accessToken,
);

// ใช้ cURL ในการส่งข้อความกลับไป
$ch = curl_init($url);
curl_setopt($ch, CURLOPT_CUSTOMREQUEST, "POST");
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, $post);
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
curl_setopt($ch, CURLOPT_FOLLOWLOCATION, 1);
$result = curl_exec($ch);
curl_close($ch);

// แสดงผลลัพธ์ที่ส่งกลับมา
echo $result . "\r\n";
}
}
}
?>
