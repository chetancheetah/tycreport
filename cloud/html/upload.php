<?php
$conn = new mysqli('localhost', 'tycscreports', 'TYCSC123', 'tycscreports');

$transactions = $_POST['RequestItems']['Transactions']; 
$shifts       = $_POST['RequestItems']['Shifts']; 

foreach ($transactions as $t) {
      $t = $t['PutRequest']['Item'];
      $name = $t['Name'];
      $atobill = $t['Applied to Bill'];
      $tip = $t['Tip'];
      $pamt = $t['Payment Amount'];
      $grat = $t['Gratuity'];
      $bd = $t['Bill Date'];
      $bdt = $t['Bill Date Time'];
      $bn = $t['Bill Number'];
      $staff = $t['Staff'];
      $sql = "INSERT IGNORE INTO `transactions` (`Name`,`Applied to Bill`, `Tip`, `Payment Amount`, `Gratuity`, `Bill Date`, `Bill Date Time`, `Bill Number`,`Staff`) VALUES ( '$name', '$atobill', '$tip', '$pamt', '$grat', '$bd', '$bdt', '$bn', '$staff' );";
    $result = $conn->query($sql);
    if ($result) {
    } else {
        echo "Fail";
        return;
    }
}
foreach ($shifts as $s) {
      $s = $s['PutRequest']['Item'];
      $dow = $s['dow'];
      $name = $s['Name'];
      $st = $s['Staff Type'];
      $cid = $s['Clock-In-Date'];
      $ci = $s['Clock-In'];
      $co = $s['Clock-Out'];
      $dur = $s['Duration'];
      $hr = $s['Hourly Rate'];
      $pay = $s['Pay'];
      $sql = "INSERT IGNORE INTO `shifts` (`dow`, `Name`, `Staff Type`, `Clock-In-Date`, `Clock-In`, `Clock-Out`, `Duration`, `Hourly Rate`, `Pay`) VALUES ( '$dow', '$name', '$st', '$cid', '$ci', '$co', '$dur', '$hr', '$pay'  );";
    $result = $conn->query($sql);
    if ($result) {
    } else {
        echo "Fail";
        return;
    }
}

echo "Success";

?>