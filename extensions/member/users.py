import json
import logging
import os
from enum import member
from shutil import ExecError

import self
from interactions import Extension, listen, Message, Guild, SlashCommand, SlashContext
import aiofiles
from interactions.api.events import MessageCreate
from interactions.api.events.processors import GuildEvents
from database import conn, cursor 


class Users(Extension):
    def __init__(self, bot):
        self.bot = bot
        




