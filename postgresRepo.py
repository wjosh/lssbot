import psycopg2 
import os
from psycopg2 import errors

from CustomException import CustomException

class PostgresRepo:
    def __init__(self):
        dbUrl = os.environ.get('DATABASE_URL', None)
        self.conn = psycopg2.connect(dbUrl)
    
    def getGuidesJson(self):
        cur = self.conn.cursor()
        selectQuery = 'SELECT * FROM guides'
        try:
            cur.execute(selectQuery,)
            records = cur.fetchall()
            cur.close()
        except Exception as e:
            cur.execute("ROLLBACK")
            self.conn.commit()

        return records

    def insertGuidesRecord(self, section, title, url):
        cur = self.conn.cursor()
        selectQuery = 'Insert into guides(section, title, url) VALUES (%s, %s, %s)'
        try:
            cur.execute(selectQuery, (section, title, url))
            self.conn.commit()
            cur.close()
        except Exception as e:
            cur.execute("ROLLBACK")
            self.conn.commit()

    def deleteGuideRecord(self, section, title):
        cur = self.conn.cursor()
        selectQuery = 'delete from guides where section ILIKE %s AND title ILIKE %s'
        try:
            cur.execute(selectQuery, (section, title))
            self.conn.commit()
            cur.close()
        except Exception as e:
            cur.execute("ROLLBACK")
            self.conn.commit()

    def getUserCount(self, userId):
        cur = self.conn.cursor()
        selectQuery = 'SELECT COUNT(*) FROM reminder where userkey = %s'
        try:
            cur.execute(selectQuery, (userId,))
            record = cur.fetchone()
            cur.close()
        except Exception as e:
            cur.execute("ROLLBACK")
            self.conn.commit()

        return record[0]

    def getGroupCount(self, groupId):
        cur = self.conn.cursor()
        selectQuery = 'SELECT COUNT(*) FROM reminder where groupkey = %s'
        try:
            cur.execute(selectQuery, (groupId,))
            record = cur.fetchone()
            cur.close()
        except Exception as e:
            cur.execute("ROLLBACK")
            self.conn.commit()
        return record[0]
    
    def insertReminderRecord(self, userId, groupId, msg, timeToRemindAt):
        cur = self.conn.cursor()
        selectQuery = 'Insert into reminder(userkey, groupkey, message, timetoremindat) VALUES (%s, %s, %s, %s)'
        try:
            cur.execute(selectQuery, (userId, groupId, msg, timeToRemindAt))
            self.conn.commit()
            cur.close()
        except errors.lookup("23505"):
            raise CustomException('Another reminder already exists for the time, please pick a different time')
        except Exception as e:
            cur.execute("ROLLBACK")
            self.conn.commit()

    def getReminders(self, userId, groupId):
        cur = self.conn.cursor()
        selectQuery = 'SELECT * FROM reminder where groupkey = %s AND userkey = %s'
        try:
            cur.execute(selectQuery, (groupId,userId))
            records = cur.fetchall()
            cur.close()
        except Exception as e:
            cur.execute("ROLLBACK")
            self.conn.commit()
        return records

    def getRemindersForTodayInGroup(self, groupId, gameTime):
        cur = self.conn.cursor()
        gameDay = str(gameTime.strftime("%d %B %Y"))
        selectQuery = 'SELECT * FROM reminder where groupkey = %s AND timetoremindat::date = %s ORDER BY timetoremindat ASC'
        try:
            cur.execute(selectQuery, (groupId, gameDay))
            records = cur.fetchall()
            cur.close()
        except Exception as e:
            cur.execute("ROLLBACK")
            self.conn.commit()
        return records
    
    def deleteReminder(self, reminderId):
        cur = self.conn.cursor()
        deleteQuery = 'delete from reminder where id = %s'
        try:
            cur.execute(deleteQuery, (reminderId,))
            self.conn.commit()
            deletedCount = cur.rowcount
            cur.close()
        except Exception as e:
            cur.execute("ROLLBACK")
            self.conn.commit()
        return deletedCount

    def getReminderByReminderId(self, reminderId):
        cur = self.conn.cursor()
        selectQuery = 'SELECT * FROM reminder where id = %s'
        try:
            cur.execute(selectQuery, (reminderId,))
            records = cur.fetchall()
            cur.close()
        except Exception as e:
            cur.execute("ROLLBACK")
            self.conn.commit()
        return records

    def getReminderByTime(self, time):
        try:
            cur = self.conn.cursor()
            selectQuery = 'SELECT * FROM reminder where timetoremindat <= %s'
            cur.execute(selectQuery, (time,))
            records = cur.fetchall()
            cur.close()
        except Exception as e:
            cur.execute("ROLLBACK")
            self.conn.commit()
        return records
    