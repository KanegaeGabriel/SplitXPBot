from psycopg2 import connect
from time import time

from Transaction import Transaction
from utils import *

class DBM:
    def __init__(self, DATABASE_URL):
        self.conn = connect(DATABASE_URL, sslmode='require')
        self.c = self.conn.cursor()
        self.c.execute("""CREATE TABLE IF NOT EXISTS configs (
                                                    chatID INTEGER PRIMARY KEY,
                                                    GMToffset INTEGER NOT NULL,
                                                    currency TEXT NOT NULL
                                                    )""")
        self.conn.commit()

    def getTableList(self):
        self.c.execute("""SELECT table_name FROM information_schema.tables
                          WHERE table_schema='public'""")

        result = self.c.fetchall()
    
        l = set()
        for r in result:
            l.add(r[0])

        return l

    def close(self):
        self.conn.close()

    def newChat(self, chatID):
        self.c.execute("""CREATE TABLE IF NOT EXISTS \"chat{}\" (
                                                    unixtime INTEGER NOT NULL,
                                                    userFrom TEXT NOT NULL,
                                                    userTo TEXT NOT NULL,
                                                    value INTEGER NOT NULL,
                                                    description TEXT
                                                    )""".format(chatID))

        self.c.execute("""DELETE FROM configs WHERE chatID = %s""", (chatID,))
        self.conn.commit()

        self.c.execute("""INSERT INTO configs (chatID, GMToffset, currency)
                          VALUES(%s, %s, %s)""", (chatID, 0, "$"))
        self.conn.commit()

        return "Table for chatID={} created.".format(chatID)

    def resetChat(self, chatID, currency):
        s = "Database reset.\n"
        s += "The group total was:\n\n"
        s += self.printAllTotals(chatID, currency)

        self.c.execute("""DROP TABLE IF EXISTS \"chat{}\"""".format(chatID))
        self.newChat(chatID)

        return s

    def killAllTables(self):
        for t in self.getTableList():
            self.c.execute("""DROP TABLE IF EXISTS \"{}\"""".format(t))
        self.c.execute("""CREATE TABLE IF NOT EXISTS configs (
                                                    chatID INTEGER PRIMARY KEY,
                                                    GMToffset INTEGER NOT NULL,
                                                    currency TEXT NOT NULL
                                                    )""")
        self.conn.commit()

        return "Wiped all data."

    def getConfig(self, chatID):
        self.c.execute("""SELECT * FROM configs WHERE chatID = %s""", (chatID,))
        r = self.c.fetchone()
        
        if r:
            GMToffset, currency = r[1], r[2]
            return (GMToffset, currency)
        else:
            return (None, None)

    def setConfig(self, chatID, GMToffset, currency):
        self.c.execute("""UPDATE configs SET GMToffset = %s, currency = %s
                          WHERE chatID = %s""", (GMToffset, currency, chatID))
        self.conn.commit()
        return "GMToffset is now {}.\nCurrency is now '{}'.".format(GMToffset, currency)

    def saveTransaction(self, chatID, t, GMToffset, currency):
        if t.value > 999999999: # $10M
            return "Couldn't save that transaction. The amount is too large."
        else:
            self.c.execute("""INSERT INTO \"chat{}\" (unixtime, userFrom, userTo, value, description)
                              VALUES(%s, %s, %s, %s, %s)""".format(chatID),
                              (t.unixtime, t.userFrom, t.userTo, t.value, t.description))
            self.conn.commit()
            return t.toString(False, GMToffset, currency)

    def printTotal(self, chatID, user, currency):
        self.c.execute("""SELECT * FROM \"chat{}\"
                          WHERE userFrom = %s OR userTo = %s""".format(chatID), (user,user))

        result = self.c.fetchall()
        txs = []
        for r in result:
            txs.append(Transaction(r[1], r[2], r[3]/100, r[4], r[0]))

        d = {}
        for t in txs:
            if user == t.userFrom:
                if t.userTo in d:
                    d[t.userTo] += -t.value
                else:
                    d[t.userTo] = -t.value
            elif user == t.userTo:
                if t.userFrom in d:
                    d[t.userFrom] += t.value
                else:
                    d[t.userFrom] = t.value
        
        s = []
        for person in d:
            if d[person] > 0:
                s += "{} owes {} {}{:.2f}".format(user, person, currency, d[person]/100) + "\n"
            elif d[person] < 0:
                s += "{} owes {} {}{:.2f}".format(person, user, currency, -d[person]/100) + "\n"

        if len(s) == 0:
            return "Nothing to show."
        else:
            return "".join(s[:-1])

    def printAllTotals(self, chatID, currency):
        self.c.execute("""SELECT * FROM \"chat{}\"""".format(chatID))

        result = self.c.fetchall()
        txs = []
        for r in result:
            txs.append(Transaction(r[1], r[2], r[3]/100, r[4], r[0]))

        totals = []
        for t in txs:
            updated = False
            for total in totals:
                if t.userFrom == total[0] and t.userTo == total[1]:
                    total[2] += -t.value
                    updated = True
                    break
                elif t.userTo == total[0] and t.userFrom == total[1]:
                    total[2] += t.value
                    updated = True
                    break

            if not updated:
                totals.append([t.userFrom, t.userTo, -t.value])

        s = []
        for total in totals:
            if total[2] > 0:
                s += "{} owes {} {}{:.2f}".format(total[0], total[1], currency, total[2]/100) + "\n"
            elif total[2] < 0:
                s += "{} owes {} {}{:.2f}".format(total[1], total[0], currency, -total[2]/100) + "\n"

        if len(s) == 0:
            return "Nothing to show."
        else:
            return "".join(s[:-1])

    def printRecent(self, chatID, user, n, GMToffset, currency):
        if user == "all":
            self.c.execute("""SELECT * FROM \"chat{}\"
                              ORDER BY unixtime DESC LIMIT %s""".format(chatID), (n,))
        else:
            self.c.execute("""SELECT * FROM \"chat{}\"
                              WHERE (userFrom = %s OR userTo = %s)
                              ORDER BY unixtime DESC LIMIT %s""".format(chatID), (user,user,n))

        result = self.c.fetchall()

        if len(result) == 0:
            return "Nothing to show."
        else:
            s = ""
            for r in result:
                tx = Transaction(r[1], r[2], r[3]/100, r[4], r[0])
                s += tx.toString(True, GMToffset, currency)
                s += "\n"

            if user != "all":
                title = "Showing the {} most recent transactions regarding {}...\n\n".format(n, user)
            else:              
                title = "Showing the {} most recent transactions...\n\n".format(n)

            return title + s