#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
	CREATE  TABLE "main"."dictionaries" ("id" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE , "lang" VARCHAR , "repeat_time" INTEGER)
	CREATE  TABLE "main"."words" ("id" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE , "lang_id" INTEGER, "word" VARCHAR,
	"translation" VARCHAR, "last_repeat" INTEGER)
	INSERT INTO dictionaries (lang, repeat_time) VALUES ('Lingua Latina', 259200)
"""

import sys
import sqlite3
from random import choice
from time import time

connection = sqlite3.connect("words.db")
db = connection.cursor()
lang_id = 1
repeat = []
correct = True
start = time()

if "--reset" in sys.argv[1:]:
	db.execute("UPDATE words SET last_repeat=0 WHERE lang_id=?", (lang_id,))
	db.close()
	connection.commit()
	exit(0)

repeat_time = db.execute("SELECT repeat_time FROM dictionaries WHERE id=?", (lang_id,)).fetchone()[0]
rows = db.execute("SELECT * FROM words WHERE lang_id=?", (lang_id,))
all, repeated = 0, 0
for row in rows:
	all += 1
	if row[4] + repeat_time < int(time()):
		repeat.append(row)
	else:
		repeated += 1

while True:
	try:
		if correct:
			try:
				word = choice(repeat)
			except IndexError: # repeat is empty
				cur = time()
				delta = int(cur-start)
				if cur - start < 1.0:
					print u"Приходите позже!"
				else:
					print u"Повторено за %s" % delta,
					if   (delta % 100) not in (11, 12, 13, 14) and \
					     (delta % 1000) not in (11, 12, 13, 14):
						if (delta % 10) in (2, 3, 4): print u"секунды"
						elif (delta % 10) == 1:       print u"секунду"
						else: print u"секунд"
					else:
						print u"секунд"
				break
			repeated += 1
			del repeat[repeat.index(word)]
		print ("[%s/%s] " % (repeated, all)) + word[2] + "?",
		translation = raw_input().decode(sys.stdout.encoding)
	except EOFError:
		break
	correct = translation in word[3].split("|") or translation.lower() in word[3].split("|")
	if correct: # update last_repeat in words table
		db.execute("UPDATE words SET last_repeat=? WHERE id=?", (int(time()), word[0]))

print
db.close()
connection.commit() # save changes
