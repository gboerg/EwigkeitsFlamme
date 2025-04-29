from email.policy import default
import json
import logging
from enum import member

from easy_pil import Editor, Font
from interactions import Extension, SlashContext, listen, slash_command
from interactions.api.events import MemberAdd
from numpy import size

from extensions.bot import event
from database import conn, cursor

class Event(Extension):
    def __init__(self, bot):
        self.bot = bot




    

            
