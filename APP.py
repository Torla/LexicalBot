import datetime
import math
import os
from threading import Thread
from time import sleep
from typing import List

import psycopg2
from telegram.ext import Updater, MessageHandler, Filters

updater = Updater(token=os.environ.get('BOT_TOKEN'), use_context=True)
dispatcher = updater.dispatcher
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


def get_db_connection():
    return psycopg2.connect(host=os.environ.get('DB_HOST'),
                            port=os.environ.get('DB_PORT'),
                            user=os.environ.get('DB_USER'),
                            password=os.environ.get('DB_PSW'),
                            database=os.environ.get('DB_NAME'))


def add_word(update, context):
    user = update.message.chat_id
    word = str(update.message.text)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(''' INSERT INTO words(users,word) VALUES (%(id)s,%(text)s);
        ''', {'id': user, 'text': word})
        conn.commit()
        cursor.execute('''SELECT count(*) FROM words WHERE users = %(id)s''', {'id': user})
        num = cursor.fetchone()[0]
        updater.dispatcher.bot.send_message(135249522, f"Added {word}({num})")
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

    def send(self):
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            conn.commit()
            cursor.execute('''SELECT DISTINCT ON (users) * FROM words ORDER BY users, random()''')
            for row in cursor.fetchall():
                try:
                    updater.dispatcher.bot.send_message(row[2], str(row[1]))
                except Exception as e:
                    pass
        finally:
            if cursor is not None:
                cursor.close()
            if conn is not None:
                conn.close()


Sender().start()
updater.start_polling()
