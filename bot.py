from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from gsheets import Sheets
import pandas as pd
import gspread
import datetime
from tabulate import tabulate
import pickle
import os

class BotMono:
    def __init__(self):
        self.data = None
        self.users_datapath = "./users.pkl"
    
    def restore_users_data(self):
        if os.path.getsize(self.users_datapath) > 0:      
            with open(self.users_datapath, "rb") as f:
                self.mapping = pickle.load(f)
        else:
            self.mapping = {}
    
    def flush_user_data(self):
        with open(self.users_datapath, "wb+") as f:
            pickle.dump(self.mapping, f)

    def load_data_from_gdock(self) -> None:
        gc = gspread.service_account("./service_creds.json")
        sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1DWS0S5CmU5on6qZaILc2CmeLJP3LwcbVqTzL_7gXwDQ/edit#gid=1421840034Q")
        pandas_worksheet = sh.get_worksheet_by_id(478666602)
        dataframe = pd.DataFrame(pandas_worksheet.get_all_values())
        location = dataframe[0].loc[(dataframe.index * (dataframe[1] == 'Пн')).cummax()]
        location = location.reset_index()
        location.rename({0: 'location'}, axis=1, inplace=True)
        dataframe = pd.concat([dataframe, location], axis=1)
        dataframe.rename({0: 'task'}, axis=1, inplace=True)
        dataframe.to_csv("./week_schedule.csv")
        self.data = dataframe


    def get_tasks_by_id_and_day(self, id: int, day: int):
        tasknames = self.data[['task', 'location']]
        current_day = self.data[day]
        mask = current_day == str(id)
        return tasknames[mask]

    async def upgrade_table(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.load_data_from_gdock()
        await  update.message.reply_text(f'TABLE UPDATED')
    
    async def register_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        name = update.effective_user.full_name
        new_id = update.message.text.split()[-1]
        self.mapping[name] = str(new_id)
        self.flush_user_data()
        await update.message.reply_text(f'User {name} now has id {new_id}')
    
    async def get_tasks_by_weekday(self, update: Update, context: ContextTypes.DEFAULT_TYPE, weekday) -> None:
        # weekday = datetime.datetime.today().weekday() + 1
        username = update.effective_user.full_name
        tasks = self.get_tasks_by_id_and_day(self.mapping[username], weekday)
        tasks_with_levels = tasks['location'].str.pad(width=12, side="right") + ":               " + tasks["task"]
        strval = '\n'.join(tasks_with_levels.values)
        await update.message.reply_text(f'User {username}  has following tasks:\n{strval}')
 
    async def get_today_tasks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        weekday = datetime.datetime.today().weekday() + 1
        await self.get_tasks_by_weekday(update, context, weekday)
    
    async def get_yesterday_tasks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        weekday = (datetime.datetime.today() -  datetime.timedelta(days=1)).weekday() + 1
        await self.get_tasks_by_weekday(update, context, weekday)

    async def huynu_zakazal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        username = update.effective_user.full_name
        await update.message.reply_text(f'{username} считает, что хуйню заказал!')

    async def CUM(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        username = update.effective_user.full_name
        await update.message.reply_text(f'{username} делает троекратный CUM!')

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Display a help message"""
        await update.message.reply_text("""
                                        You can use the following commands:
    /register_user num : Set your number from the violence table
    /update_table : Load new version of violence table
    /get_today_tasks : Get a list of your today tasks
    /get_yesterday_tasks : Get a list of your yesterday tasks
    /CUM : Tell everyone that you are fucking cumming
    /huynu_zakazal: Tell everyone, that you huynu zakazal
                                        """)
    def main(self):
        self.load_data_from_gdock()
        self.restore_users_data()
        with open("zovuni_token", "r") as f:
            token = f.read()

        self.app = ApplicationBuilder().token(token).build()

        self.app.add_handler(CommandHandler("help", self.help))
        self.app.add_handler(CommandHandler("update_table", self.upgrade_table))
        self.app.add_handler(CommandHandler("register_user", self.register_user))
        self.app.add_handler(CommandHandler("get_today_tasks", self.get_today_tasks))
        self.app.add_handler(CommandHandler("get_yesterday_tasks", self.get_yesterday_tasks))
        self.app.add_handler(CommandHandler("huynu_zakazal", self.huynu_zakazal))
        self.app.add_handler(CommandHandler("CUM", self.CUM))
        self.app.run_polling()

if __name__ == "__main__":
    bot = BotMono()
    bot.main()