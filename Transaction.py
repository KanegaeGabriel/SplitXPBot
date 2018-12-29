from time import time

from utils import *

class Transaction:
    def __init__(self, userFrom, userTo, value, description=None, unixtime=None):
        self.unixtime = unixtime if unixtime else int(time())
        self.userFrom = userFrom
        self.userTo = userTo
        self.value = int(value*100)
        self.description = description

    def toString(self, timestamp=True, GMToffset=0, currency="$"):
        descriptionIfExists = " ({})".format(self.description) if self.description else ""

        s = ""
        if timestamp:
            s += "\\[{}] ".format(unixToString(self.unixtime, GMToffset))
        s += "{} gave {} ".format(self.userFrom, self.userTo)
        s += "{}{:.2f}{}".format(currency, self.value/100, descriptionIfExists)
        return s