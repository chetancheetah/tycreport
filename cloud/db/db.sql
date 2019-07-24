
CREATE TABLE transactions
  (
	`Name` VARCHAR(32),
	`Applied to Bill` INT,
	`Tip` INT,
	`Payment Amount` INT,
	`Gratuity` INT,
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
	 `Duration` INT,
	 `Hourly Rate` INT,
	 `Pay`  INT,
	 PRIMARY KEY ( `Name`, `Clock-In`)
 );
