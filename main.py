from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from os import environ
import logging

import auth # Telegram Bot Token
from DBM import DBM
from Transaction import Transaction
from utils import *

def kill(bot, update):
    printCommandExecution(bot, update)
    myself, text, isGroup, chatID, chatName, canRunAdmin = getMsgAttributes(bot, update)
    
    s = dbm.killAllTables()
    
    bot.send_message(chat_id=chatID, text=s, parse_mode="Markdown")

def help(bot, update): # /help
    printCommandExecution(bot, update)
    myself, text, isGroup, chatID, chatName, canRunAdmin = getMsgAttributes(bot, update)

    h = [
        "*{U}* commands can be used by anyone. *{A}* can be used only by group admins. ",
        "If used in a private chat, all commands can be used.\n",
        "\n",
        "*{U}* `/start`\n",
        "> Starts the bot and initializes the database.\n",
        "\n",
        "*{U}* `/help`\n",
        "> Shows this message.\n",
        "\n",
        "*{A}* `/reset`\n",
        "> Resets the database.\n",
        "\n",
        "*{U}* `/gaveTo (@user) (amount) [description]`\n",
        "> Records that you gave `amount` to `@user`.\n",
        "\n",
        "*{U}* `/gaveMe (@user) (amount) [description]`\n",
        "> Records that `@user` gave `amount` to you.\n",
        "\n",
        "*{A}* `/whoGaveWho (@userA) (@userB) (amount) [description]`\n",
        "> Records that `@userA` gave `amount` to `@userB`.\n",
        "\n",
        "*{U}* `/total [@user]`\n",
        "> Shows how much `@user` owes and is owed. Defaults to you.\n",
        "\n",
        "*{U}* `/recent [@user|all] [n]`\n",
        "> Lists the `n` most recent transactions involving `@user|all`.\n",
        "\n",
        "*{A}* `/config (GMToffset) (currency)`\n",
        "> Configures the bot to your liking:\n"
        "  `GMToffset`: Hours to add/sub from the GMT timezone. e.g. `3`, `-2`.\n"
        "  `currency`: Currency symbol to use. e.g. `$`, `US$`.\n"
        ]

    s = "".join(h)
    bot.send_message(chat_id=chatID, text=s, parse_mode="Markdown")

def start(bot, update): # /start
    printCommandExecution(bot, update)
    myself, text, isGroup, chatID, chatName, canRunAdmin = getMsgAttributes(bot, update)

    h = [
        "Hi! I am SplitXPBot! I'm here to manage your shared expenses! ",
        "I can be used in a group chat or in a private one. :)\n",
        "\n",
        "Type `/help` to see the available commands.\n"
        "\n",
        "Also, be sure to configure me to your liking with `/config`!\n",
        ]

    dbm.newChat(chatID)

    s = "".join(h)
    bot.send_message(chat_id=chatID, text=s, parse_mode="Markdown")

def reset(bot, update): # /reset
    printCommandExecution(bot, update)
    myself, text, isGroup, chatID, chatName, canRunAdmin = getMsgAttributes(bot, update)
    GMToffset, currency = dbm.getConfig(chatID)
    
    if not canRunAdmin:
        s = "You are not allowed to use that command. Please ask a group admin."
        bot.send_message(chat_id=chatID, text=s, parse_mode="Markdown")
        return

    if GMToffset == None and currency == None:
        s = "I couldn't find some important data. Are you sure you have already run `/start`?"
        bot.send_message(chat_id=chatID, text=s, parse_mode="Markdown")
        return

    s = dbm.resetChat(chatID, currency)

    bot.send_message(chat_id=chatID, text=s, parse_mode="Markdown")

def config(bot, update, args): # /config (GMToffset) (currency)
    printCommandExecution(bot, update)
    myself, text, isGroup, chatID, chatName, canRunAdmin = getMsgAttributes(bot, update)

    if len(args) != 2:
        s = "Command usage: `/config (GMT offset) (currency)`\n"
        s += "  `GMT offset`: Hours to add/sub from the GMT timezone. e.g. `3`, `-2`.\n"
        s += "  `currency`: Currency symbol to use. e.g. `$`, `US$`.\n"
    elif not isInt(args[0]):
        s = "Invalid GMT offset. Please give me an integer value."
    elif abs(int(args[0])) > 12:
        s = "Invalid GMT offset. Please give me a value between -12 and 12."
    elif len(args[1]) > 5:
        s = "Your currency symbol is too long. Please don't go over 5 characters."
    else:
        GMToffset = int(args[0])
        currency = args[1]

        s = dbm.setConfig(chatID, GMToffset, currency)

    bot.send_message(chat_id=chatID, text=s, parse_mode="Markdown")

def gaveTo(bot, update, args): # /gaveTo (@user) (amount) [description]
    printCommandExecution(bot, update)
    myself, text, isGroup, chatID, chatName, canRunAdmin = getMsgAttributes(bot, update)
    GMToffset, currency = dbm.getConfig(chatID)

    if GMToffset == None and currency == None:
        s = "I couldn't find some important data. Are you sure you have already run `/start`?"
        bot.send_message(chat_id=chatID, text=s, parse_mode="Markdown")
        return

    if len(args) > 1: args[1] = args[1].replace(",", ".")

    if myself == "None":
        s = "How come you don't have a Telegram username? Please create one."
    elif len(args) < 2:
        s = "Command usage: `/gaveTo (@user) (amount) [description]`"
    elif args[0][0] != "@":
        s = "Please call a user by their Telegram username, starting with @."
    elif not isFloat(args[1]):
        s = "The amount has to be a number."
    elif float(args[1]) < 0.01:
        s = "Only positive amounts, please!"
    elif args[0].replace("@", "") == myself:
        s = "You can't make a transaction with yourself!"
    else:
        user = args[0].replace("@", "")
        amount = float(args[1])
        description = " ".join(args[2:])

        if len(description) > 50:
            description = description[:(50-3)] + "..."

        s = dbm.saveTransaction(chatID, Transaction(myself, user, amount, description), GMToffset, currency)

    bot.send_message(chat_id=chatID, text=s, parse_mode="Markdown")

def gaveMe(bot, update, args): # /gaveMe (@user) (amount) [description]
    printCommandExecution(bot, update)
    myself, text, isGroup, chatID, chatName, canRunAdmin = getMsgAttributes(bot, update)
    GMToffset, currency = dbm.getConfig(chatID)

    if GMToffset == None and currency == None:
        s = "I couldn't find some important data. Are you sure you have already run `/start`?"
        bot.send_message(chat_id=chatID, text=s, parse_mode="Markdown")
        return

    if len(args) > 1: args[1] = args[1].replace(",", ".")

    if myself == "None":
        s = "How come you don't have a Telegram username? Please create one."
    elif len(args) < 2:
        s = "Command usage: `/gaveMe (@user) (amount) [description]`"
    elif args[0][0] != "@":
        s = "Please call a user by their Telegram username, starting with @."
    elif not isFloat(args[1]):
        s = "The amount has to be a number."
    elif float(args[1]) < 0.01:
        s = "Only positive amounts, please!"
    elif args[0].replace("@", "") == myself:
        s = "You can't make a transaction with yourself!"
    else:
        user = args[0].replace("@", "")
        amount = float(args[1])
        description = " ".join(args[2:])

        if len(description) > 50:
            description = description[:(50-3)] + "..."

        s = dbm.saveTransaction(chatID, Transaction(user, myself, amount, description), GMToffset, currency)

    bot.send_message(chat_id=chatID, text=s, parse_mode="Markdown")

def whoGaveWho(bot, update, args): # /whoGaveWho (@userA) (@userB) (amount) [description]
    printCommandExecution(bot, update)
    myself, text, isGroup, chatID, chatName, canRunAdmin = getMsgAttributes(bot, update)
    GMToffset, currency = dbm.getConfig(chatID)
    
    if not canRunAdmin:
        s = "You are not allowed to use that command. Please ask a group admin."
        bot.send_message(chat_id=chatID, text=s, parse_mode="Markdown")
        return

    if GMToffset == None and currency == None:
        s = "I couldn't find some important data. Are you sure you have already run `/start`?"
        bot.send_message(chat_id=chatID, text=s, parse_mode="Markdown")
        return

    if len(args) > 2: args[2] = args[2].replace(",", ".")

    if myself == "None":
        s = "How come you don't have a Telegram username? Please create one."
    elif len(args) < 3:
        s = "Command usage: `/whoGaveWho (@userA) (@userB) (amount) [description]`"
    elif args[0][0] != "@" or args[1][0] != "@":
        s = "Please call a user by their Telegram username, starting with @."
    elif not isFloat(args[2]):
        s = "The amount has to be a number."
    elif float(args[2]) < 0.01:
        s = "Only positive amounts, please!"
    else:
        userA = args[0].replace("@", "")
        userB = args[1].replace("@", "")
        amount = float(args[2])
        description = " ".join(args[3:])

        if len(description) > 50:
            description = description[:(50-3)] + "..."

        s = dbm.saveTransaction(chatID, Transaction(userA, userB, amount, description), GMToffset, currency)

    bot.send_message(chat_id=chatID, text=s, parse_mode="Markdown")

def total(bot, update, args): # /total [@user]
    printCommandExecution(bot, update)
    myself, text, isGroup, chatID, chatName, canRunAdmin = getMsgAttributes(bot, update)
    GMToffset, currency = dbm.getConfig(chatID)

    if GMToffset == None and currency == None:
        s = "I couldn't find some important data. Are you sure you have already run `/start`?"
        bot.send_message(chat_id=chatID, text=s, parse_mode="Markdown")
        return

    if len(args) > 0 and args[0] != "all" and args[0][0] != "@":
        s = "Please call a user by their Telegram username, starting with @."
    else:
        if len(args) > 0 and args[0] == "all":
            s = dbm.printAllTotals(chatID, currency)
        elif len(args) > 0:
            user = args[0].replace("@", "")
            s = dbm.printTotal(chatID, user, currency)
        else:
            s = dbm.printTotal(chatID, myself, currency)

    bot.send_message(chat_id=chatID, text=s, parse_mode="Markdown")

def recent(bot, update, args): # /recent [@user|all] [n]
    printCommandExecution(bot, update)
    myself, text, isGroup, chatID, chatName, canRunAdmin = getMsgAttributes(bot, update)
    GMToffset, currency = dbm.getConfig(chatID)

    if GMToffset == None and currency == None:
        s = "I couldn't find some important data. Are you sure you have already run `/start`?"
        bot.send_message(chat_id=chatID, text=s, parse_mode="Markdown")
        return

    if myself == "None":
        s = "How come you don't have a Telegram username? Please create one."
    elif len(args) > 0 and (args[0] != "all" and args[0][0] != "@"):
        s = "Please call a user by their Telegram username, starting with @."
    elif len(args) > 1 and not isInt(args[1]):
        s = "The amount has to be a number."
    else:
        if len(args) == 0:
            s = dbm.printRecent(chatID, myself, 5, GMToffset, currency)
        elif len(args) == 1:
            user = args[0].replace("@", "")
            s = dbm.printRecent(chatID, user, 5, GMToffset, currency)
        else:
            user = args[0].replace("@", "") 
            n = int(args[1])

            if n < 1: n = 1
            if n > 50: n = 50
            
            s = dbm.printRecent(chatID, user, n, GMToffset, currency)

    bot.send_message(chat_id=chatID, text=s, parse_mode="Markdown")

def unknown(bot, update):
    printCommandExecution(bot, update)
    myself, text, isGroup, chatID, chatName, canRunAdmin = getMsgAttributes(bot, update)

    s = "Sorry, I didn't understand that command. Try `/help` to see all commands."
    bot.send_message(chat_id=chatID, text=s, parse_mode="Markdown")

def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger(__name__)
    updater = Updater(token=auth.TOKEN)
    dp = updater.dispatcher

    # Commands
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('reset', reset))
    dp.add_handler(CommandHandler('gaveTo', gaveTo, pass_args=True))
    dp.add_handler(CommandHandler('gaveMe', gaveMe, pass_args=True))
    dp.add_handler(CommandHandler('whoGaveWho', whoGaveWho, pass_args=True))
    dp.add_handler(CommandHandler('total', total, pass_args=True))
    dp.add_handler(CommandHandler('recent', recent, pass_args=True))
    dp.add_handler(CommandHandler('config', config, pass_args=True))

    dp.add_handler(CommandHandler('kill', kill, filters=Filters.user(315421140)))

    # Aliases
    dp.add_handler(CommandHandler('giveTo', gaveTo, pass_args=True))
    dp.add_handler(CommandHandler('givesTo', gaveTo, pass_args=True))
    dp.add_handler(CommandHandler('giveMe', gaveMe, pass_args=True))
    dp.add_handler(CommandHandler('givesMe', gaveMe, pass_args=True))
    dp.add_handler(CommandHandler('wgw', whoGaveWho, pass_args=True))
    dp.add_handler(CommandHandler('whoGiveWho', whoGaveWho, pass_args=True))
    dp.add_handler(CommandHandler('whoGivesWho', whoGaveWho, pass_args=True))
    dp.add_handler(CommandHandler('hist', recent, pass_args=True))
    dp.add_handler(CommandHandler('history', recent, pass_args=True))

    # Unknown command
    dp.add_handler(MessageHandler(Filters.command, unknown))

    updater.start_polling()
    print("Bot running...")

    updater.idle()
    dbm.close()

if __name__ == "__main__":
    # Connect to PostgreSQL database
    dbm = DBM(environ['DATABASE_URL'])

    main()