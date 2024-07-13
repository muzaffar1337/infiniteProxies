from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler, CallbackQueryHandler
)
import json
import requests
import os
from typing import Final
# Global Variables
TOKEN = 'xxxxxxxxxxxxxxxxxxxxxxxx'
API_Key = 'xxxxxxxxxxxxxxx'
adminId: Final = 1608290518
adminId2: Final = 6899196939
authorizedUsers = []
Users = {}

def fetch_user_info(API_Key):
    print('Fetching user info...')
    headers = {'X-API-KEY': API_Key}
    url = "https://api.infiniteproxies.com/v2/reseller/sub_users/view_all"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("data", [])
    return []

async def save_user_credentials():
    user_data = fetch_user_info(API_Key)
    user_credentials = {user["username"]: user["products"]["residential"]["proxy_key"] for user in user_data}
    return user_credentials
async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_credentials = await save_user_credentials()
    parts = update.message.text.split(' ')
    if update.message.text == "/login":
        await context.bot.send_message(chat_id=update.message.chat_id,text=f'invalid format please use /login <username> <password>')
        return
    elif len(parts) == 3 and parts[0] == "/login":
        username = parts[1]
        print(f'Username: {username}')
        proxy_key = parts[2]
        print(f'Proxy Key: {proxy_key}')
        if username in user_credentials and user_credentials[username] == proxy_key:
            await update.message.reply_text(f"Welcome {username}! You are now logged in.")
            authorizedUsers.append(update.message.from_user.id)
            Users[update.message.from_user.id] = username
            print("Authorized Users", authorizedUsers)
            print("Username", Users[update.message.from_user.id])
        else:
            await update.message.reply_text("Invalid username or residential proxy key. Please try again.")
    else:
        await context.bot.send_message(chat_id=update.message.chat_id,text=f'invalid format please use /login <username> <password>')

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Just a help message')


async def check_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.callback_query.from_user.id
    print(f'user_id: {user_id}')
    if user_id not in authorizedUsers:
        await update.callback_query.from_user.send_message("You are not logged in.")
        return

    username = Users.get(user_id)
    if not username:
        await update.callback_query.from_user.send_message("Error: Username not found. Please login again.")
        return

    headers = {'X-Api-Key': API_Key}
    url = "https://api.infiniteproxies.com/v1/reseller/sub_users/view_all"
    try:
        response = requests.get(url, headers=headers)
        data = response.json()["data"]
        user_info = next((item for item in data if item["username"].lower() == username.lower()), None)
        if user_info:
            balance = user_info["balance"]
            await update.callback_query.from_user.send_message(f"Your balance: {balance} MB")
        else:
            await update.callback_query.from_user.send_message("No balance information found.")
    except Exception as e:
        print(e)
        await update.callback_query.from_user.send_message("Failed to fetch balance. Please try again later.")


async def change_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.callback_query.from_user.id
    print("change_password")
    if user_id not in authorizedUsers:
        await update.callback_query.message.reply_text("You are not logged in.")
        return

    # Get the username associated with the user ID
    username = Users.get(user_id)
    if not username:
        await update.callback_query.message.reply_text("Username not found. Please login again.")
        return


    url = "https://api.infiniteproxies.com/v2/reseller/sub_users/reset_rp_auth_key"
    headers = {
        'Content-Type': 'application/json',
        'X-Api-Key': API_Key
    }
    data = json.dumps({"username": username})

    # Execute the POST request
    try:
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'products' in data['data'] and 'residential' in data['data']['products']:
                new_key = data['data']['products']['residential']['proxy_key']
                if new_key:
                    proxy_host = "rp.infiniteproxies.com"
                    proxy_port = "1111"
                    format1 = f"{username}:{new_key}@{proxy_host}:{proxy_port}"
                    format2 = f"{proxy_host}:{proxy_port}:{username}:{new_key}"
                    format3 = f"{username}:{new_key}:{proxy_host}:{proxy_port}"

                await update.callback_query.from_user.send_message(f"Your new residential proxy key: {new_key}")
                await update.callback_query.from_user.send_message(f"Here are your new proxy credentials in different formats, {username}:\n\n")
                await update.callback_query.from_user.send_message(f"{format2}")
                await update.callback_query.from_user.send_message(f"{format1}")
                await update.callback_query.from_user.send_message(f"{format3}")
            else:
                await update.callback_query.message.reply_text("Failed to retrieve new proxy key.")
        else:
            await update.callback_query.message.reply_text("Failed to reset proxy key. Please try again later.")
    except Exception as e:
        print(e)
        await update.callback_query.message.reply_text("An error occurred while processing your request.")


async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.callback_query.from_user.id if update.callback_query else update.message.from_user.id
    if user_id in authorizedUsers:
        authorizedUsers.remove(user_id)
        print("been logout")
        if update.callback_query:
            await update.callback_query.message.reply_text("You have been logged out successfully!")
        else:
            await update.message.reply_text("You have been logged out successfully!")
    else:
        if update.callback_query:
            await update.callback_query.message.reply_text("You are not logged in.")
        else:
            await update.message.reply_text("You are not logged in.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in authorizedUsers:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Welcome to infiniteproxies!\nPlease login to Start Use bot\n'
                                                                              '/login <username> <password>.')
        await context.bot.send_message(chat_id=update.effective_chat.id,text='This Bot is Only for Users who have Subscribed from @srrrs.')
    elif update.message.from_user.id in authorizedUsers:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Welcome to infiniteproxies!\nYou are login in\n')
        keyboard = [[InlineKeyboardButton("Check Balance", callback_data='check_balance')],[InlineKeyboardButton("Change Proxy Password", callback_data='change_password')],
                    [InlineKeyboardButton("Logout", callback_data='logout')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Please choose an option:',
                                       reply_markup=reply_markup)

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id == adminId2:
        await update.message.reply_text('Welcome Huc!')
        await context.bot.send_message(chat_id=adminId2, text='infiniteproxies is Online ..!')
        headers = {
            'X-API-KEY': API_Key
        }
        r = requests.get("https://api.infiniteproxies.com/v2/reseller/my_info", headers=headers)
        data = r.json()
        username = data['data']['username']
        residential_balance = data['data']['products']['residential']['balance']
        created_at = data['data']['created_at']
        updated_at = data['data']['updated_at']
        await context.bot.send_message(chat_id=adminId2,text=f'<b>Username:</b> {username}\n<b>Residential Balance:</b> {residential_balance} GB\n<b>Created At:</b> {created_at}\n<b>Updated At:</b> {updated_at}',parse_mode="HTML")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='<b>Not Authorized</b> Sorry This is just for Admin @srrrs', parse_mode="HTML")

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('Update "%s" caused error "%s"' % (update, context.error))

async def button2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'logout':
        await logout(update, context)
    elif query.data == 'check_balance':
        await check_balance(update, context)
    elif query.data == 'change_password':
        await change_password(update, context)


if __name__ == '__main__':
    print('infiniteproxies v1.0')
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler('start', start))
    bot.add_handler(CommandHandler('info', info))
    bot.add_handler(CommandHandler('error', error))
    bot.add_handler(CommandHandler('help', help))
    bot.add_handler(CommandHandler('login', login))
    bot.add_handler(CallbackQueryHandler(button))
    bot.add_handler(CallbackQueryHandler(button2))
    print('infiniteproxies Polling')
    bot.run_polling()