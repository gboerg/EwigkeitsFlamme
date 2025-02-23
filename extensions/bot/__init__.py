import logging
from interactions import Extension, IntervalTrigger, Task, Status, Activity, ActivityType, listen


class Bot(Extension):
    def __init__(self, bot):
        logging.info("Extension loaded: Bot1")
        bot.load_extension("extensions.bot.event")
        logging.info("Extension loaded: Bot2")


    #@Task.create(IntervalTrigger(minutes=10))
    async def update_activity(self):
        await self.bot.change_presence(status=Status.ONLINE, activity=Activity.create(
            name="Die Geschichte von der Ewigen Flamme | Cobania und die 7 Sterne",
            type=ActivityType.STREAMING,
            url="https://twitch.tv/bycoba",
            state="YA BOY EWI"
        ))



    @listen()
    async def on_startup(self):
        await self.update_activity()
        Task(self.update_activity, IntervalTrigger(minutes=10)).start()
        #task.start()
