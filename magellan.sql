CREATE TABLE `analysis_monthly` (
  `timeID` integer NOT NULL
,  `year` integer DEFAULT NULL
,  `month` integer DEFAULT NULL
,  `home` float DEFAULT NULL
,  `homefrac` float DEFAULT NULL
,  `travel` float DEFAULT NULL
,  `travelfrac` float DEFAULT NULL
,  `away` float DEFAULT NULL
,  `awayfrac` float DEFAULT NULL
,  UNIQUE (`timeID`)
);
CREATE TABLE `analysis_weekly` (
  `timeID` integer NOT NULL
,  `year` integer DEFAULT NULL
,  `week` integer DEFAULT NULL
,  `home` float DEFAULT NULL
,  `homefrac` float DEFAULT NULL
,  `travel` float DEFAULT NULL
,  `travelfrac` float DEFAULT NULL
,  `away` float DEFAULT NULL
,  `awayfrac` float DEFAULT NULL
,  UNIQUE (`timeID`)
);
CREATE TABLE `homeloc` (
  `startdate` date NOT NULL
,  `enddate` date NOT NULL
,  `lat` float NOT NULL
,  `lon` float NOT NULL
,  `ref_alt` float DEFAULT NULL
,  `homeradius` float NOT NULL DEFAULT 60
,  `locID` integer DEFAULT NULL
,  `comment` varchar(120) DEFAULT NULL
,  UNIQUE (`startdate`,`enddate`)
);
CREATE TABLE `locations` (
  `UTC` datetime DEFAULT NULL
,  `Lat` float DEFAULT NULL
,  `Lon` float DEFAULT NULL
,  `hacc` float DEFAULT NULL
,  `Alt` float DEFAULT NULL
,  `vacc` float DEFAULT NULL
,  `speed` float DEFAULT NULL
,  `heading` float DEFAULT NULL
,  `batt` integer DEFAULT NULL
,  UNIQUE (`UTC`)
);
CREATE TABLE `locations_spec` (
  `UTC` datetime NOT NULL
,  `Type` text  NOT NULL
,  PRIMARY KEY (`UTC`)
);
CREATE INDEX "idx_locations_spec_UTC" ON "locations_spec" (`UTC`);
CREATE INDEX "idx_locations_UTC_2" ON "locations" (`UTC`);
