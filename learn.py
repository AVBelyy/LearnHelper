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

repeat_time = db.execute("SELECT repeat_time FROM dictionaries WHERE id=?", (lang_id,)).fetchone()[0]
rows = db.execute("SELECT * FROM words WHERE lang_id=?", (lang_id,))
for row in rows:
	if row[4] + repeat_time < int(time()):
		repeat.append(row)

while True:
	try:
		if correct:
			try:
				word = choice(repeat)
			except IndexError: # repeat is empty
				print "All done!"
				break
			del repeat[repeat.index(word)]
		print word[2] + "?",
		translation = raw_input().decode(sys.stdout.encoding).lower()
	except EOFError:
		break
	correct = translation in word[3].split("|")
	if correct: # update last_repeat in words table
		db.execute("UPDATE words SET last_repeat=? WHERE id=?", (int(time()), word[0]))

print
connection.commit() # save changes
db.close()
