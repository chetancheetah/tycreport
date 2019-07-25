<?php

header('Content-type: application/json');

$conn = new mysqli('localhost', 'tycscreports', 'TYCSC123', 'tycscreports');
$table = $_POST['TableName'];

if ($table == 'Transactions') {
   $from = $_POST['ExpressionAttributeValues'][':start_dt'];
   $to   = $_POST['ExpressionAttributeValues'][':end_dt'];
   $sql = "SELECT * FROM `transactions` WHERE `Bill Date` >= '$from' AND `Bill Date` <= '$to';";
   $result = $conn->query($sql);
   if ($result) {
       $rows = array();
       while($r = mysqli_fetch_assoc($result)) {
          $rows[] = $r;
       }
       print json_encode($rows);
       return;
   } else {
      echo "Fail";
      return;
   }
}
if ($table == 'Shifts') {
   $from = $_POST['ExpressionAttributeValues'][':start_dt'];
   $to   = $_POST['ExpressionAttributeValues'][':end_dt'];
   $sql = "SELECT * FROM `shifts` WHERE `Clock-In-Date` >= '$from' AND `Clock-In-Date` <= '$to';";
   $result = $conn->query($sql);
   if ($result) {
       $rows = array();
       while($r = mysqli_fetch_assoc($result)) {
          $rows[] = $r;
       }
       print json_encode($rows);
       return;
   } else {
      echo "Fail";
      return;
   }
}
?>