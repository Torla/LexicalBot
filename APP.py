import datetime
import math
import os
from threading import Thread
from time import sleep
from typing import List

import sqlite3
from telegram.ext import Updater, MessageHandler, Filters

updater = Updater(token=os.environ.get('BOT_TOKEN'), use_context=True)
dispatcher = updater.dispatcher
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


def get_db_connection():
    if not os.path.exists(os.path.join("data", "db")):
        with sqlite3.connect(os.path.join("data", "db")) as conn:
            conn.execute(open("schema.sql").read())
    return sqlite3.connect(os.path.join("data", "db"))


def add_word(update, context):
    user = update.message.chat_id
    word = str(update.message.text)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(''' INSERT INTO words(users,word) VALUES (?,?);
        ''', (str(user), str(word)))
        conn.commit()
        cursor.execute('''SELECT count(*) FROM words WHERE users = ?''', (str(user),))
        num = cursor.fetchone()[0]
        updater.dispatcher.bot.send_message(user, f"Added {word}({num})")
    except Exception as e:
        conn.rollback()
        updater.dispatcher.bot.send_message(user, f"ERRORE {str(e)}")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


dispatcher.add_handler(MessageHandler(Filters.text, add_word))


class Sender(Thread):

    def run(self) -> None:
        while (True):
            sleep(1)
            if datetime.datetime.now().hour == 9:
                self.send()
            sleep(3700)

    def send(self):
        conn = None
        cursor = None
        cursor2 = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor2 = conn.cursor()
            conn.commit()
            if datetime.datetime.now().weekday() != 6:
                cursor.execute('''SELECT * FROM words ORDER BY random() limit 1''')
                for row in cursor.fetchall():
                    try:
                        updater.dispatcher.bot.send_message(int(row[1]),row[2])
                    except Exception as e:
                        print(e)
            # else:
            #     cursor.execute('''SELECT DISTINCT users FROM words''')
            #     cursor2.execute(f'''SELECT word FROM words ORDER BY random() LIMIT {cursor.rowcount}''')
            #     words = cursor2.fetchall()
            #     for user in cursor.fetchall():
            #         try:
            #             updater.dispatcher.bot.send_message(user[0], str(words.pop()[0]))
            #         except Exception as e:
            #             pass
        finally:
            if cursor is not None:
                cursor.close()
            if cursor2 is not None:
                cursor2.close()
            if conn is not None:
                conn.close()


Sender().start()
updater.start_polling()
