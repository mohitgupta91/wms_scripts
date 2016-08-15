<?php
//include 'common.php';
error_reporting(E_ALL);

//1-Date
//2-email_id
//3-courier_name

if(count($argv) == 5){
    $file_atr = $argv[1];
    $fileatt_type = "text/csv"; // File Type
    $fileatt_name =	$argv[5]; // Filename that will be used for the file as the attachment

    $email_from = "Snapdeal Support"; // Who the email is from
    $email_subject = $argv[4]; // The Subject of the email
    $email_message = $argv[3];


    $email_to = $argv[2];

    $headers = 'From: '.$email_from;


    $file = fopen($file_atr,'rb');
    $data = fread($file,filesize($file_atr));
    fclose($file);

    $semi_rand = md5(time());
    $mime_boundary = "==Multipart_Boundary_x{$semi_rand}x";
    $headers .= "\nMIME-Version: 1.0\n"."Content-Type: multipart/mixed;\n"." boundary=\"{$mime_boundary}\"";

    $email_message .= "This is a multi-part message in MIME format.\n\n"."--{$mime_boundary}\n"."Content-Type:text/html; charset=\"iso-8859-1\"\n". "Content-Transfer-Encoding: 7bit\n\n".$email_message .= "\n\n";

    $data = chunk_split(base64_encode($data));

    $email_message .= "--{$mime_boundary}\n"."Content-Type: {$fileatt_type};\n"." name=\"{$fileatt_name}\"\n"."Content-Transfer-Encoding: base64\n\n".$data .= "\n\n"."--{$mime_boundary}--\n";
}
else if(count($argv) == 6){
    $email_to = $argv[1];
    $email_subject = $argv[3];
    $email_message = $argv[2];
    $email_cc = $argv[4];
    $email_from = 'Snapdeal Support'; // Who the email is from
    $headers = 'From: '.$email_from. "\r\n";
    $headers .= 'CC: '.$email_cc. "\r\n";
    $headers .= 'MIME-Version: 1.0'."\r\n";
    $headers .= 'Content-Type: text/html; charset=iso-8859-1'."\r\n";
}
else{

    $email_to = $argv[1];
    $email_subject = $argv[3];
    $email_message = $argv[2];

    $email_from = 'Snapdeal Support'; // Who the email is from
    $headers = 'From: '.$email_from. "\r\n";

    $headers .= 'MIME-Version: 1.0'."\r\n";
    $headers .= 'Content-Type: text/html; charset=iso-8859-1'."\r\n";
}

$ok = @mail($email_to, $email_subject,$email_message, $headers);

if($ok) {
    echo "Sent";
} else {
    echo "NOt Sent";
}

?>
