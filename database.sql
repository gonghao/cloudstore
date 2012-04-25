SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL';

DROP SCHEMA IF EXISTS `cloudstore` ;
CREATE SCHEMA IF NOT EXISTS `cloudstore` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci ;
USE `cloudstore` ;

-- -----------------------------------------------------
-- Table `cloudstore`.`Group`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `cloudstore`.`Group` ;

CREATE  TABLE IF NOT EXISTS `cloudstore`.`Group` (
  `groupid` INT UNSIGNED NOT NULL AUTO_INCREMENT ,
  `goupname` VARCHAR(20) NOT NULL ,
  PRIMARY KEY (`groupid`) ,
  UNIQUE INDEX `groupid_UNIQUE` (`groupid` ASC) )
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `cloudstore`.`User`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `cloudstore`.`User` ;

CREATE  TABLE IF NOT EXISTS `cloudstore`.`User` (
  `userid` INT UNSIGNED NOT NULL AUTO_INCREMENT ,
  `username` VARCHAR(20) NOT NULL ,
  `password` VARCHAR(32) NOT NULL ,
  `groupid` INT UNSIGNED NOT NULL ,
  `identity` VARCHAR(1) NOT NULL DEFAULT 0 ,
  PRIMARY KEY (`userid`) ,
  UNIQUE INDEX `userid_UNIQUE` (`userid` ASC) ,
  INDEX `groupid` (`groupid` ASC) ,
  CONSTRAINT `groupid`
    FOREIGN KEY (`groupid` )
    REFERENCES `cloudstore`.`Group` (`groupid` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `cloudstore`.`Directory`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `cloudstore`.`Directory` ;

CREATE  TABLE IF NOT EXISTS `cloudstore`.`Directory` (
  `directoryid` INT UNSIGNED NOT NULL AUTO_INCREMENT ,
  `directoryname` VARCHAR(20) NOT NULL ,
  PRIMARY KEY (`directoryid`) ,
  UNIQUE INDEX `directoryid_UNIQUE` (`directoryid` ASC) )
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `cloudstore`.`File`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `cloudstore`.`File` ;

CREATE  TABLE IF NOT EXISTS `cloudstore`.`File` (
  `fileid` INT UNSIGNED NOT NULL AUTO_INCREMENT ,
  `filename` VARCHAR(20) NOT NULL ,
  `userid` INT UNSIGNED NOT NULL ,
  `fileident` VARCHAR(1) NOT NULL DEFAULT 1 ,
  `update` TIMESTAMP NULL ,
  `modify` TIMESTAMP NULL ,
  `count` INT UNSIGNED NOT NULL ,
  `location` VARCHAR(100) NOT NULL ,
  `type` VARCHAR(20) NOT NULL ,
  `directoryid` INT UNSIGNED NOT NULL ,
  PRIMARY KEY (`fileid`) ,
  UNIQUE INDEX `fileid_UNIQUE` (`fileid` ASC) ,
  INDEX `userid` (`userid` ASC) ,
  INDEX `directoryid` (`directoryid` ASC) ,
  CONSTRAINT `userid`
    FOREIGN KEY (`userid` )
    REFERENCES `cloudstore`.`User` (`userid` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `directoryid`
    FOREIGN KEY (`directoryid` )
    REFERENCES `cloudstore`.`Directory` (`directoryid` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;



SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
