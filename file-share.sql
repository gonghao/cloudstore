SELECT File.*
FROM User, File, `Group`
WHERE `Group`.groupid=User.groupid AND User.userid=File.userid AND File.fileident=0 AND User.groupid IN
(SELECT groupid
 FROM User 
 WHERE userid=7)
