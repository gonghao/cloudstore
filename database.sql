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
  `groupname` VARCHAR(20) NOT NULL ,
  `grouppassword` VARCHAR(32) NOT NULL ,
  PRIMARY KEY (`groupid`) ,
  UNIQUE INDEX `groupid_UNIQUE` (`groupid` ASC) ,
  UNIQUE INDEX `goupname_UNIQUE` (`groupname` ASC) )
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `cloudstore`.`User`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `cloudstore`.`User` ;

CREATE  TABLE IF NOT EXISTS `cloudstore`.`User` (
  `userid` INT UNSIGNED NOT NULL AUTO_INCREMENT ,
  `username` VARCHAR(20) NOT NULL ,
  `password` VARCHAR(32) NOT NULL ,
  `groupid` INT UNSIGNED NULL ,
  `identity` VARCHAR(1) NOT NULL DEFAULT 0 ,
  PRIMARY KEY (`userid`) ,
  UNIQUE INDEX `userid_UNIQUE` (`userid` ASC) ,
  UNIQUE INDEX `username_UNIQUE` (`username` ASC) ,
  INDEX `groupid` (`groupid` ASC) ,
  CONSTRAINT `groupid`
    FOREIGN KEY (`groupid` )
    REFERENCES `cloudstore`.`Group` (`groupid` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `cloudstore`.`Folder`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `cloudstore`.`Folder` ;

CREATE  TABLE IF NOT EXISTS `cloudstore`.`Folder` (
  `folderid` INT UNSIGNED NOT NULL AUTO_INCREMENT ,
  `foldername` VARCHAR(20) NOT NULL ,
  `userid` INT UNSIGNED NOT NULL ,
  PRIMARY KEY (`folderid`) ,
  UNIQUE INDEX `directoryid_UNIQUE` (`folderid` ASC) ,
  INDEX `userid_folder` (`userid` ASC) ,
  CONSTRAINT `userid_folder`
    FOREIGN KEY (`userid` )
    REFERENCES `cloudstore`.`User` (`userid` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `cloudstore`.`File`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `cloudstore`.`File` ;

CREATE  TABLE IF NOT EXISTS `cloudstore`.`File` (
  `fileid` INT UNSIGNED NOT NULL AUTO_INCREMENT ,
  `filename` VARCHAR(200) NOT NULL ,
  `userid` INT UNSIGNED NOT NULL ,
  `fileident` VARCHAR(1) NOT NULL DEFAULT 1 ,
  `upload` INT NOT NULL DEFAULT 0 ,
  `modify` INT NOT NULL DEFAULT 0 ,
  `count` INT UNSIGNED NOT NULL DEFAULT 0 ,
  `location` VARCHAR(200) NULL ,
  `type` VARCHAR(40) NOT NULL ,
  `folderid` INT UNSIGNED NULL ,
  PRIMARY KEY (`fileid`) ,
  UNIQUE INDEX `fileid_UNIQUE` (`fileid` ASC) ,
  INDEX `userid` (`userid` ASC) ,
  INDEX `folderid` (`folderid` ASC) ,
  UNIQUE INDEX `location_UNIQUE` (`location` ASC) ,
  CONSTRAINT `userid`
    FOREIGN KEY (`userid` )
    REFERENCES `cloudstore`.`User` (`userid` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `folderid`
    FOREIGN KEY (`folderid` )
    REFERENCES `cloudstore`.`Folder` (`folderid` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;



SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
