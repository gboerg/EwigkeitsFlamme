import json
import sqlite3

from interactions import Extension, IntervalTrigger, Task, listen



conn = sqlite3.connect('database/bot.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()






class Database(Extension):
    def __init__(self, bot):
        self.bot = bot


