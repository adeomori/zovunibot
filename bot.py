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
    
    async def get_tasks(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        weekday = datetime.datetime.today().weekday() + 1
        username = update.effective_user.full_name
        tasks = self.get_tasks_by_id_and_day(self.mapping[username], weekday)
        
        await update.message.reply_text(f'User {username}  has following tasks:\n {tabulate(tasks)}')


    async def hello(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(f'Hello {update.effective_user.first_name}')


    def main(self):
        self.load_data_from_gdock()
        self.restore_users_data()
        with open("zovuni_token", "r") as f:
            token = f.read()

        self.app = ApplicationBuilder().token(token).build()

        self.app.add_handler(CommandHandler("hello", self.hello))
        self.app.add_handler(CommandHandler("update_table", self.upgrade_table))
        self.app.add_handler(CommandHandler("register_user", self.register_user))
        self.app.add_handler(CommandHandler("get_tasks", self.get_tasks))
        self.app.run_polling()

if __name__ == "__main__":
    bot = BotMono()
    bot.main()