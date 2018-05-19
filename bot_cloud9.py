#!/usr/bin/env python
#-*- coding: utf-8 -*-
from telegram.ext import Updater, MessageHandler, CommandHandler, RegexHandler, ConversationHandler, Filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
import sqlite3
from datetime import datetime
from emoji import emojize
import re

step = {}
ordername = {}
BOOK_DATE, BOOK_RES, BOOK_CHOICE, MENU_VEG, MENU_SHOW, ORDER, ORDER_INSERT, CHANGE_END = range(8)

def start(bot, update):
    id = update.message.chat_id
    em = emojize(':star:', use_aliases=True)
    bot.sendMessage(chat_id=id, text=em + em + em + '<b>Добро пожаловать в наш ресторан!</b> ' + em + em + em + '''
              Чтобы оформить заказ, наберите /order
          Чтобы забронировать столик, наберите /book
             Чтобы изменить бронь, наберите /change
             Чтобы отменить бронь, наберите /cancel
        Если хотите посмотреть наше меню, наберите /menu
    Чтобы прервать незавершенное действие, наберите /back
        Чтобы завершить работу с ботом, наберите /end
             
             ''', parse_mode='HTML')
# Бронирование
def book(bot, update):
    id = update.message.chat_id
    reply_keyboard = [['VIP', 'У окна'], ['В зале', 'Все равно']]
    update.message.reply_text('Какой столик вы хотите?', reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return BOOK_DATE
    
def book_date(bot, update, user_data):
    user_data['table'] = update.message.text
    update.message.reply_text('На какую дату вы хотите забронировать столик?\n Введите дату в формате YYYY-MM-DD', reply_markup=ReplyKeyboardRemove())
    return BOOK_RES

def book_res(bot, update, user_data):
    user_data['date'] = update.message.text
    if user_data['table'] == 'Все равно':
        try:
            conn = sqlite3.connect('Restaurant.db')
            c = conn.cursor()
            c.execute('PRAGMA foreign_keys = ON;')
            conn.commit()
            c.execute('''SELECT * FROM Столики NATURAL JOIN
            (SELECT Столик FROM Столики 
            EXCEPT SELECT Столик FROM Бронирования 
                WHERE Дата = '%s') ORDER BY Цена ASC ''' % (user_data['date']))
            result = c.fetchall()
            c.close()
            conn.close()
            update.message.reply_text('Вот все свободные столики на ' + user_data['date'] + ':')
            user_data['biggest'] = result[0][0]
            max = result[0][2]
            for row in result:
                if row[2] > max:
                    user_data['biggest'] = row[0]
                    max = row[2]
                update.message.reply_text(emojize(":large_blue_circle:", use_aliases=True) + 
                'Столик №' + str(row[0]) + ' | ' + str(row[1]) + ' | Мест: ' + str(row[2]) + ' | Цена: ' + str(row[3]) + ' руб.')
            reply_keyboard = [['Самый дешевый', 'Самый вместительный']]
            user_data['cheapest'] = result[0][0]
            update.message.reply_text('Введите номер столика, либо выберите из предложенных вариантов.', reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        except:
            update.message.reply_text('Кажется, вы ввели дату неправильно. Попробуйте еще раз')
    else:
        try:
            conn = sqlite3.connect('Restaurant.db')
            c = conn.cursor()
            c.execute('PRAGMA foreign_keys = ON;')
            conn.commit()
            c.execute('''SELECT * FROM Столики NATURAL JOIN
            (SELECT Столик FROM Столики 
            EXCEPT SELECT Столик FROM Бронирования 
                WHERE Дата = '%s') WHERE Тип = '%s' ORDER BY Цена ASC ''' % (user_data['date'], str(user_data['table'])))
            result = c.fetchall()
            c.close()
            conn.close()
            update.message.reply_text('Вот все свободные столики ' + str(user_data['table']).lower() + ' на ' + user_data['date'] + ':')
            user_data['biggest'] = result[0][0]
            max = result[0][2]
            for row in result:
                if row[2] > max:
                    user_data['biggest'] = row[0]
                    max = row[2]
                update.message.reply_text(emojize(":large_blue_circle:", use_aliases=True) + 
                'Столик №' + str(row[0]) + ' | Мест: ' + str(row[2]) + ' | Цена: ' + str(row[3]) + ' руб.')
            reply_keyboard = [['Самый дешевый', 'Самый вместительный']]
            user_data['cheapest'] = result[0][0]
            update.message.reply_text('Введите номер столика, либо выберите из предложенных вариантов.', reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        except:
            update.message.reply_text('Кажется, вы ввели дату неправильно. Попробуйте еще раз')
    return BOOK_CHOICE
    
def book_choice(bot, update, user_data):
    try:
        conn = sqlite3.connect('Restaurant.db')
        c = conn.cursor()
        c.execute('PRAGMA foreign_keys = ON;')
        conn.commit()
        c.execute("INSERT INTO Бронирования (Столик, Дата) VALUES ('%s','%s')" % (update.message.text, user_data['date']))
        conn.commit()
        c.execute("SELECT Цена FROM Столики WHERE Столик = '%s' " % (update.message.text))
        price = c.fetchone()
        d = datetime.now()
        c.execute("SELECT Состояние_счета FROM Доходы ORDER BY Дата DESC LIMIT 1")
        summary = c.fetchone()
        c.execute("INSERT INTO Доходы VALUES ('%s', '%s', '%s')" % (d, price[0], summary[0] + price[0]))
        conn.commit()
        update.message.reply_text('Поздравляем! Вы забронировали столик №' + update.message.text + ' на ' + user_data['date'] + '!'
        + '\nЕсли хотите отменить бронирование, нажмите /cancel.' + '\nЧтобы изменить бронь, нажмите /change.', reply_markup=ReplyKeyboardRemove())
        user_data['book'] = update.message.text
    except:
        update.message.reply_text('К сожалению, забронировать не удалось. Попробуйте еще раз.', reply_markup=ReplyKeyboardRemove())
    c.close()
    conn.close()
    return ConversationHandler.END

def book_button(bot, update, user_data):
    if update.message.text == 'Самый дешевый':
        try:
            conn = sqlite3.connect('Restaurant.db')
            c = conn.cursor()
            c.execute('PRAGMA foreign_keys = ON;')
            conn.commit()
            c.execute("INSERT INTO Бронирования (Столик, Дата) VALUES ('%s','%s')" % (user_data['cheapest'], user_data['date']))
            conn.commit()
            c.execute("SELECT Цена FROM Столики WHERE Столик = '%s' " % (user_data['cheapest']))
            price = c.fetchone()
            d = datetime.now()
            c.execute("SELECT Состояние_счета FROM Доходы ORDER BY Дата DESC LIMIT 1")
            summary = c.fetchone()
            c.execute("INSERT INTO Доходы VALUES ('%s', '%s', '%s')" % (d, price[0], summary[0] + price[0]))
            conn.commit()
            c.close()
            conn.close()
            update.message.reply_text('Поздравляем! Вы забронировали самый дешевый столик №' + str(user_data['cheapest']) + ' на ' + user_data['date'] + '!'
            + '\nЕсли хотите отменить бронирование, нажмите /cancel.' + '\nЧтобы изменить бронь, нажмите /change.', reply_markup=ReplyKeyboardRemove())
            user_data['book'] = user_data['cheapest']
        except:
            update.message.reply_text('К сожалению, забронировать не удалось. Попробуйте еще раз.', reply_markup=ReplyKeyboardRemove())
    else:
        try:
            conn = sqlite3.connect('Restaurant.db')
            c = conn.cursor()
            c.execute('PRAGMA foreign_keys = ON;')
            conn.commit()
            c.execute("INSERT INTO Бронирования (Столик, Дата) VALUES ('%s','%s')" % (user_data['biggest'], user_data['date']))
            conn.commit()
            c.execute("SELECT Цена FROM Столики WHERE Столик = '%s' " % (user_data['biggest']))
            price = c.fetchone()
            d = datetime.now()
            c.execute("SELECT Состояние_счета FROM Доходы ORDER BY Дата DESC LIMIT 1")
            summary = c.fetchone()
            c.execute("INSERT INTO Доходы VALUES ('%s', '%s', '%s')" % (d, price[0], summary[0] + price[0]))
            conn.commit()
            c.close()
            conn.close()
            update.message.reply_text('Поздравляем! Вы забронировали самый вместительный столик №' + str(user_data['biggest']) + ' на ' + user_data['date'] + '!'
            + '\nЕсли хотите отменить бронирование, нажмите /cancel.' + '\nЧтобы изменить бронь, нажмите /change.', reply_markup=ReplyKeyboardRemove())
            user_data['book'] = user_data['biggest']
        except:
            update.message.reply_text('К сожалению, забронировать не удалось. Попробуйте еще раз.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END
# Бронирование - конец
# Меню
def menu(bot, update):
    id = update.message.chat_id
    reply_keyboard = [['Горячие закуски', 'Холодные закуски'], ['Супы', 'Основные блюда'], ['Десерты', 'Все блюда']]
    update.message.reply_text('Выберите категорию блюд', reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return MENU_VEG
    
def menu_veg(bot, update, user_data):
    user_data['type'] = update.message.text
    reply_keyboard = [['Да', 'Нет']]
    update.message.reply_text('Вы вегетарианец?', reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return MENU_SHOW
    
def menu_show(bot, update, user_data):
    conn = sqlite3.connect('Restaurant.db')
    c = conn.cursor()
    c.execute('PRAGMA foreign_keys = ON;')
    conn.commit()
    if user_data['type'] == 'Все блюда':
        if update.message.text == 'Да':
            c.execute('''SELECT * FROM Блюда WHERE Вегетарианское = 1 AND Наличие = 1 ''')
        else:
            c.execute('''SELECT * FROM Блюда WHERE Наличие = 1 ''')
        result = c.fetchall()
        for row in result:
            update.message.reply_text(emojize(":fork_and_knife:", use_aliases=True) + 
            'Блюдо: ' + str(row[1]) + ' | Тип: ' + str(row[2]) + '\nИнгредиенты: ' + str(row[3]) + '\nЦена: ' + str(row[4]) + ' руб.')
    else:
        if update.message.text == 'Да':
            c.execute('''SELECT * FROM Блюда WHERE Вегетарианское = 1 AND Наличие = 1 AND Тип = '%s' ''' % (str(user_data['type'])))
        else:
            c.execute('''SELECT * FROM Блюда WHERE Наличие = 1 AND Тип = '%s' ''' % (str(user_data['type'])))
        result = c.fetchall()
        if result is None:
            update.message.reply_text('Увы, ничего не нашлось. Вы можете поискать еще с помощью /menu', reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END
        if user_data['type'] == 'Горячие закуски':
            s = ':stew:'
        elif user_data['type'] == 'Холодные закуски':
            s = ':oden:'
        elif user_data['type'] == 'Супы':
            s = ':ramen:'
        elif user_data['type'] == 'Десерты':
            s = ':shaved_ice:'
        else:
            s = ':spaghetti:'
        for row in result:
            update.message.reply_text(emojize(s, use_aliases=True) + 
            'Блюдо: ' + str(row[1]) + '\nИнгредиенты: ' + str(row[3]) + '\nЦена: ' + str(row[4]) + ' руб.')
    reply_keyboard = [[str(row[1])] for row in result]
    update.message.reply_text('''Выберите блюдо из предложенных, если хотите что-то заказать.\nВы также можете набрать его название.
    ''', reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    c.close()
    conn.close()
    if 'order_table' in user_data:
        return ORDER_INSERT
    return ORDER
# Меню - конец   
# Заказ
def order(bot, update, user_data):
    if update.message.text != '/order':
        user_data['dish'] = update.message.text
    if 'order_table' not in user_data:
        update.message.reply_text('Введите номер своего столика', reply_markup=ReplyKeyboardRemove())
    else:
        update.message.reply_text('Введите блюдо для заказа')
    return ORDER_INSERT
    
def order_insert(bot, update, user_data):
    if 'order_table' not in user_data:
        try:
            user_data['order_table'] = update.message.text
            conn = sqlite3.connect('Restaurant.db')
            c = conn.cursor()
            c.execute('PRAGMA foreign_keys = ON;')
            conn.commit()
            date = str(datetime.now())
            c.execute("INSERT INTO Заказы (Столик, Дата) VALUES ('%s','%s')" % (user_data['order_table'], date))
            conn.commit()
            c.execute("SELECT Заказ FROM Заказы WHERE Столик = '%s' AND Дата = '%s'" % (user_data['order_table'], date))
            row = c.fetchone()
            user_data['ord'] = row[0]
            c.close()
            conn.close()
        except:
            update.message.reply_text('Ошибка. Введите, пожалуйста, существующий столик.')
            return ORDER_INSERT
    else:
        user_data['dish'] = update.message.text
    if 'dish' not in user_data:
        update.message.reply_text('Введите блюдо для заказа')
        return ORDER_INSERT
    conn = sqlite3.connect('Restaurant.db')
    c = conn.cursor()
    c.execute('PRAGMA foreign_keys = ON;')
    conn.commit()
    c.execute("SELECT Блюдо, Цена FROM Блюда WHERE Название ='%s' " % (str(user_data['dish'])))
    row = c.fetchone()
    if row is None:
        c.close()
        conn.close()
        update.message.reply_text('Такого блюда не существует. Напишите, пожалуйста, еще раз. Вы можете уточнить наше меню с помощью /menu')
        return ORDER_INSERT
    else:
        c.execute("INSERT INTO Заказы_Блюда (Заказ, Блюдо) VALUES ('%s','%s')" % (user_data['ord'], row[0]))
        conn.commit()
        d = datetime.now()
        c.execute("SELECT Состояние_счета FROM Доходы ORDER BY Дата DESC LIMIT 1")
        summary = c.fetchone()
        c.execute("INSERT INTO Доходы VALUES ('%s', '%s', '%s')" % (d, row[1], summary[0] + row[1]))
        conn.commit()
        update.message.reply_text('Блюдо добавлено в Ваш заказ!\n' + 
        'Вы можете написать еще блюдо, либо посмотреть наше меню с помощью /menu.\n' + 
        'Наберите /back, если вы больше не хотите заказывать.\n' + 
        'Чтобы завершить сеанс, наберите /end')
    c.close()
    conn.close()
    return ORDER_INSERT
#Заказ - конец
#Удаление брони
def cancel(bot, update, user_data):
    if 'book' not in user_data:
        update.message.reply_text('Вы не бронировали столик в этом сеансе.')
        return ConversationHandler.END
    conn = sqlite3.connect('Restaurant.db')
    c = conn.cursor()
    c.execute('PRAGMA foreign_keys = ON;')
    conn.commit()
    c.execute("DELETE FROM Бронирования WHERE Столик='%s' AND Дата='%s' " % (user_data['book'], user_data['date']))
    conn.commit()
    c.close()
    conn.close()
    update.message.reply_text('Столик №' + str(user_data['book']) + ' снова свободен для бронирования на ' + str(user_data['date']) + '!')
    return ConversationHandler.END
#Удаление брони - конец
#Изменение брони
def change(bot, update, user_data):
    if 'book' not in user_data:
        update.message.reply_text('Вы не бронировали столик в этом сеансе.')
        return ConversationHandler.END
    update.message.reply_text('Введите номер столика, на который вы бы хотели поменять вашу бронь.')
    return CHANGE_END
    
def change_end(bot, update, user_data):
    conn = sqlite3.connect('Restaurant.db')
    c = conn.cursor()
    try:
        c.execute('PRAGMA foreign_keys = ON;')
        conn.commit()
        c.execute("UPDATE Бронирования SET Столик='%s' WHERE Столик='%s' AND Дата='%s' " % (update.message.text, user_data['book'], user_data['date']))
        conn.commit()
    except:
        update.message.reply_text('Ошибка! Столика не существует либо он уже был забронирован. Чтобы отменить прошлую бронь, введите /cancel')
    c.close()
    conn.close()
    update.message.reply_text('Столик №' + str(user_data['book']) + ' изменен на столик №' + str(update.message.text) + ', на ' + str(user_data['date']) + '!')
    user_data['book']=update.message.text
    return ConversationHandler.END
#Изменение брони - конец
def end(bot, update, user_data):
    update.message.reply_text('До скорой встречи и приятного аппетита!\nЧтобы получить справку, наберите /start',
                              reply_markup=ReplyKeyboardRemove())
    user_data.clear()
    return ConversationHandler.END

def back(bot, update, user_data):
    update.message.reply_text('Вы прервали последнее действие.\nЧтобы получить справку, наберите /start',
                              reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def texter(bot, update):
    update.message.reply_text('Извините, я не понимаю :)')
    return ConversationHandler.END

def main():
    updater = Updater(token='332092160:AAF-tcH2XOou15eNSNFTmyX3ONLeNyaV5Gg')
    dispatcher = updater.dispatcher
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), 
        CommandHandler("order", order, pass_user_data=True), 
        CommandHandler("end", end, pass_user_data=True), 
        CommandHandler("book", book),
        CommandHandler("menu", menu),
        CommandHandler("cancel", cancel, pass_user_data=True),
        CommandHandler("change", change, pass_user_data=True)],

        states={
            BOOK_DATE: [RegexHandler('^(VIP|У окна|В зале|Все равно)$', book_date, pass_user_data=True)],
            BOOK_RES: [RegexHandler('^(\d\d\d\d-\d\d-\d\d)$', book_res, pass_user_data=True)],
            BOOK_CHOICE: [RegexHandler('^(Самый дешевый|Самый вместительный)$', book_button, pass_user_data=True),
                RegexHandler('^(\d+)$', book_choice, pass_user_data=True)],
            MENU_VEG: [RegexHandler('^(Горячие закуски|Холодные закуски|Супы|Основные блюда|Десерты|Все блюда)$', menu_veg, pass_user_data=True)],
            MENU_SHOW: [RegexHandler('^(Да|Нет)$', menu_show, pass_user_data=True)],
            ORDER: [MessageHandler(Filters.text, order, pass_user_data=True)],
            ORDER_INSERT: [MessageHandler(Filters.text, order_insert, pass_user_data=True)],
            CHANGE_END: [RegexHandler('^(\d+)$', change_end, pass_user_data=True)]
        },

        fallbacks=[CommandHandler('end', end, pass_user_data=True), CommandHandler('back', back, pass_user_data=True), CommandHandler("menu", menu), MessageHandler(Filters.text, texter, pass_user_data=True)]
    )
    
    dispatcher.add_handler(conv_handler)
    
    updater.start_polling()
    updater.idle()
    
if __name__ == '__main__':
    main()