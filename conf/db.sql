
CREATE TABLE transactions
  (
	`Name` VARCHAR(32),
	`Applied to Bill` FLOAT,
	`Tip` FLOAT,
	`Payment Amount` FLOAT,
	`Gratuity` FLOAT,
	`Bill Date` DATE,
	`Bill Date Time` DATETIME,
	`Bill Number` VARCHAR(32),
	`Staff` VARCHAR(64),
	PRIMARY KEY ( `Bill Number` )
   );

CREATE TABLE shifts
  (
	 `dow` VARCHAR(8),
	 `Name` VARCHAR(64),
	 `Staff Type` VARCHAR(32),
	 `Clock-In-Date` DATE,
	 `Clock-In` DATETIME,
	 `Clock-Out` DATETIME,
	 `Duration` FLOAT,
	 `Hourly Rate` FLOAT,
	 `Pay`  FLOAT,
	 PRIMARY KEY ( `Name`, `Clock-In`)
 );

CREATE TABLE employees
  (
	 `Name` VARCHAR(64),
	 `pass` VARCHAR(10),
         PRIMARY KEY ( `name` )
 );
