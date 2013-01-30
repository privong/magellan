-- MySQL dump 10.13  Distrib 5.5.29, for Linux (armv6l)
--
-- Host: localhost    Database: magellan
-- ------------------------------------------------------
-- Server version	5.5.29-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `analysis_monthly`
--

DROP TABLE IF EXISTS `analysis_monthly`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `analysis_monthly` (
  `year` int(11) DEFAULT NULL,
  `month` tinyint(4) DEFAULT NULL,
  `home` float DEFAULT NULL,
  `homefrac` float DEFAULT NULL,
  `travel` float DEFAULT NULL,
  `travelfrac` float DEFAULT NULL,
  `away` float DEFAULT NULL,
  `awayfrac` float DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `analysis_weekly`
--

DROP TABLE IF EXISTS `analysis_weekly`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `analysis_weekly` (
  `year` int(11) DEFAULT NULL,
  `week` tinyint(4) DEFAULT NULL COMMENT 'ISO week',
  `home` float DEFAULT NULL COMMENT 'minutes',
  `homefrac` float DEFAULT NULL COMMENT 'fraction',
  `travel` float DEFAULT NULL COMMENT 'minutes',
  `travelfrac` float DEFAULT NULL COMMENT 'fraction',
  `away` float DEFAULT NULL COMMENT 'minutes',
  `awayfrac` float DEFAULT NULL COMMENT 'fraction'
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `homeloc`
--

DROP TABLE IF EXISTS `homeloc`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `homeloc` (
  `startdate` date NOT NULL,
  `enddate` date NOT NULL,
  `lat` float NOT NULL,
  `long` float NOT NULL,
  `homeradiu` float NOT NULL DEFAULT '60' COMMENT 'home radius in km'
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `locations`
--

DROP TABLE IF EXISTS `locations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `locations` (
  `UTC` datetime DEFAULT NULL COMMENT 'UTC time as reported by the phone',
  `Lat` float DEFAULT NULL COMMENT 'decimal latitude',
  `Lon` float DEFAULT NULL COMMENT 'decimal longitude',
  `hacc` float DEFAULT NULL COMMENT 'horizontal accuracy in m',
  `Alt` float DEFAULT NULL COMMENT 'altitude in m',
  `vacc` float DEFAULT NULL COMMENT 'vertical accuracy in m',
  `speed` float DEFAULT NULL COMMENT 'speed in m/s',
  `heading` float DEFAULT NULL COMMENT 'heading in degrees',
  `batt` tinyint(4) DEFAULT NULL COMMENT 'percentage of battery remaining',
  UNIQUE KEY `UTC` (`UTC`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `locations_spec`
--

DROP TABLE IF EXISTS `locations_spec`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `locations_spec` (
  `UTC` datetime NOT NULL COMMENT 'UTC time as reported by the phone',
  `Type` enum('home','away','travel') NOT NULL COMMENT 'designation for this timestamp',
  PRIMARY KEY (`UTC`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2013-01-30  1:15:44
