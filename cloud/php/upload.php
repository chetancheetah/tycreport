<?php
$conn = new mysqli('localhost', 'tycscreports', 'TYCSC123', 'tycscreports');


$name=$_POST['name'];
$email=$_POST['email'];
$sql="INSERT INTO `data` (`id`, `name`, `email`) VALUES (NULL, '$name', '$email')";
if ($conn->query($sql) === TRUE) {
    echo "data inserted";
}
else 
{
    echo "failed";
}
?>