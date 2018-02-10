SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";

--
-- Database: `magellan`
--

-- --------------------------------------------------------

--
-- Table structure for table `analysis_monthly`
--

CREATE TABLE IF NOT EXISTS `analysis_monthly` (
  `timeID` int(11) NOT NULL,
  `year` int(11) DEFAULT NULL,
  `month` tinyint(4) DEFAULT NULL,
  `home` float DEFAULT NULL,
  `homefrac` float DEFAULT NULL,
  `travel` float DEFAULT NULL,
  `travelfrac` float DEFAULT NULL,
  `away` float DEFAULT NULL,
  `awayfrac` float DEFAULT NULL,
  UNIQUE KEY `timeID` (`timeID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `analysis_weekly`
--

CREATE TABLE IF NOT EXISTS `analysis_weekly` (
  `timeID` int(11) NOT NULL,
  `year` int(11) DEFAULT NULL,
  `week` tinyint(4) DEFAULT NULL COMMENT 'ISO week',
  `home` float DEFAULT NULL COMMENT 'minutes',
  `homefrac` float DEFAULT NULL COMMENT 'fraction',
  `travel` float DEFAULT NULL COMMENT 'minutes',
  `travelfrac` float DEFAULT NULL COMMENT 'fraction',
  `away` float DEFAULT NULL COMMENT 'minutes',
  `awayfrac` float DEFAULT NULL COMMENT 'fraction',
  UNIQUE KEY `timeID` (`timeID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `homeloc`
--

CREATE TABLE IF NOT EXISTS `homeloc` (
  `startdate` date NOT NULL,
  `enddate` date NOT NULL,
  `lat` float NOT NULL,
  `lon` float NOT NULL,
  `homeradiu` float NOT NULL DEFAULT '60' COMMENT 'home radius in km',
  `comment` varchar(120),
  UNIQUE KEY `startdate` (`startdate`,`enddate`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `locations`
--

CREATE TABLE IF NOT EXISTS `locations` (
  `UTC` datetime DEFAULT NULL COMMENT 'UTC time as reported by the phone',
  `Lat` float DEFAULT NULL COMMENT 'decimal latitude',
  `Lon` float DEFAULT NULL COMMENT 'decimal longitude',
  `hacc` float DEFAULT NULL COMMENT 'horizontal accuracy in m',
  `Alt` float DEFAULT NULL COMMENT 'altitude in m',
  `vacc` float DEFAULT NULL COMMENT 'vertical accuracy in m',
  `speed` float DEFAULT NULL COMMENT 'speed in m/s',
  `heading` float DEFAULT NULL COMMENT 'heading in degrees',
  `batt` tinyint(4) DEFAULT NULL COMMENT 'percentage of battery remaining',
  UNIQUE KEY `UTC` (`UTC`),
  KEY `UTC_2` (`UTC`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `locations_spec`
--

CREATE TABLE IF NOT EXISTS `locations_spec` (
  `UTC` datetime NOT NULL COMMENT 'UTC time as reported by the phone',
  `Type` enum('home','away','travel') NOT NULL COMMENT 'designation for this timestamp',
  PRIMARY KEY (`UTC`),
  KEY `UTC` (`UTC`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

