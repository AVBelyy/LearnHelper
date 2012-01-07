#!/usr/bin/env python3
# -*- coding: utf-8 -*-

db_initcode = \
"""
    CREATE  TABLE "main"."dictionaries" ("id" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE , "lang" VARCHAR , "repeat_time" INTEGER)
    CREATE  TABLE "main"."words" ("id" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE , "lang_id" INTEGER, "word" VARCHAR, "translation" VARCHAR, "last_repeat" INTEGER)
"""

import sys
import sqlite3
from random import choice
from time import time
from optparse import OptionParser

connection = sqlite3.connect("words.db")
db = connection.cursor()

empty_msg = "База слов пуста. Добавьте слова в редакторе и приходите снова"

def db_create():
    for cmd in db_initcode.split("\n"):
        db.execute(cmd)

def select_lang():
    langs = db.execute("SELECT id, lang FROM dictionaries").fetchall()
    print("Какой язык изволите повторить?\n")
    for x, (id, name) in enumerate(langs):
        print("%d) %s" % (x+1, name))
    print()
    while True:
        try:
            user = input("#")
            if user.isdigit() and int(user) in range(1, len(langs)+1):
                break
        except(EOFError, KeyboardInterrupt):
            print()
            exit(0)
    return langs[int(user)-1][0]

repeat = []
correct = True

lang_count, count = db.execute("SELECT (SELECT COUNT(*) FROM dictionaries), (SELECT COUNT(*) FROM words)").fetchone()

parser = OptionParser(description="Database: %d words in %d languages" % (count, lang_count))
parser.add_option("-r", "--reset",
                  action="store_true", dest="reset", default=False,
                  help="repeat all words again")
parser.add_option("-c", "--clear",
                  action="store_true", dest="clear", default=False,
                  help="recreate database file, removing all words. be careful!")
(options, args) = parser.parse_args()

if options.clear:
    if input("Are you sure? ").lower() in ["y", "yes", "yeah", "yep", "ja", "jes"]:
        try:
            db.execute("DROP TABLE dictionaries")
            db.execute("DROP TABLE words")
        except sqlite3.OperationalError:
            pass # this may occur if db file was already broken
        db_create()
    connection.commit()
    db.close()
    exit(0)

if lang_count == 1:
    (lang_id, count) = db.execute("SELECT (SELECT id FROM dictionaries), (SELECT COUNT(*) FROM words)").fetchone()
elif lang_count != 0:
    lang_id = select_lang()
    (count,) = db.execute("SELECT COUNT(*) FROM words WHERE lang_id = ?", (lang_id,)).fetchone()

if count == 0:
    print(empty_msg)
    exit(0)

if options.reset:
    db.execute("UPDATE words SET last_repeat=0 WHERE lang_id=?", (lang_id,))

import readline

(lang, repeat_time) = db.execute("SELECT lang, repeat_time FROM dictionaries WHERE id=?", (lang_id,)).fetchone()
rows = db.execute("SELECT * FROM words WHERE lang_id=?", (lang_id,))
all, repeated = 0, 0
for row in rows:
    all += 1
    if row[4] + repeat_time < int(time()):
        repeat.append(row)
    else:
        repeated += 1

if not repeat:
    print("Приходите позже!")
else:
    print("Проверяется знание слов языка %s. Количество слов: %d\n" % (lang, all-repeated))
come_later_flag = not repeat

start = time()
while True:
    try:
        if correct:
            try:
                word = choice(repeat)
            except IndexError: # repeat is empty
                cur = time()
                delta = int(cur-start)
                if not come_later_flag:
                    print("\nПовторено за %s" % delta, end=' ')
                    if   (delta % 100) not in (11, 12, 13, 14) and \
                         (delta % 1000) not in (11, 12, 13, 14):
                        if (delta % 10) in (2, 3, 4): print("секунды")
                        elif (delta % 10) == 1:       print("секунду")
                        else: print("секунд")
                    else:
                        print("секунд")
                break
            repeated += 1
            del repeat[repeat.index(word)]
        try:
            translation = input("[%d/%d] %s? " % (repeated, all, word[2]))
        except KeyboardInterrupt:
            print()
            break
    except EOFError:
        print()
        break
    correct = translation.lower() in word[3].split("|")
    if correct: # update last_repeat in words table
        db.execute("UPDATE words SET last_repeat=? WHERE id=?", (int(time()), word[0]))

connection.commit() # save changes
db.close()
