from time import strftime, gmtime, mktime

def getMsgAttributes(bot, update):
    myself = str(update.message.from_user.username)
    myselfID = str(update.message.from_user.id)
    text = str(update.message.text)
    
    isGroup = str(update.message.chat.type) == "group"
    chatID = str(update.message.chat_id)
    chatName = str(update.message.chat.title if isGroup else update.message.chat.username)

    cm = bot.getChatMember(chatID, int(myselfID))
    isAdmin = cm.status == "creator" or cm.status == "administrator"
    canRunAdmin = not isGroup or update.message.chat.all_members_are_administrators or isAdmin

    return (myself, text, isGroup, chatID, chatName, canRunAdmin)

def printCommandExecution(bot, update):
    myself, text, isGroup, chatID, chatName, canRunAdmin = getMsgAttributes(bot, update)

    print("{{{}}}@{} in {}[{}]: \"{}\"".format("A" if canRunAdmin else "U", myself, chatName, chatID, text))

def unixToString(unix, offset, verbose=False):
    if verbose:
        return strftime('%d/%m/%y %H:%M:%S', gmtime(unix+3600*offset)) + " (GMT{:+})".format(offset)
    else:
        return strftime('%d/%m %H:%M', gmtime(unix+3600*offset))

def isFloat(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def isInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False