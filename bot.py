from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
from logic import *
import schedule
import threading
import time
from config import *

bot = TeleBot(API_TOKEN)

def gen_markup(id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton("Получить!", callback_data=id))
    return markup


def send_message():
    try:
        prize_id, img = manager.get_random_prize()[:2]
    except ValueError:
        return
    manager.mark_prize_used(prize_id)
    hide_img(img)
    for user in manager.get_users():
        with open(f'hidden_img/{img}', 'rb') as photo:
            bot.send_photo(user, photo, reply_markup=gen_markup(id = prize_id))
        

def shedule_thread():
    schedule.every().minute.do(send_message) # Здесь ты можешь задать периодичность отправки картинок
    while True:
        schedule.run_pending()
        time.sleep(1)

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.chat.id
    if user_id in manager.get_users():
        bot.reply_to(message, "Ты уже зарегестрирован!")
    else:
        manager.add_user(user_id, message.from_user.username)
        bot.reply_to(message, """Привет! Добро пожаловать! 
Тебя успешно зарегистрировали!
Каждый час тебе будут приходить новые картинки и у тебя будет шанс их получить!
Для этого нужно быстрее всех нажать на кнопку 'Получить!'

Только три первых пользователя получат картинку!
Если выигранная картинка не пришла, отправь /getprize через 5 минут.)""")

@bot.message_handler(commands=['rating'])
def handle_rating(message):
    res = manager.get_rating()
    res = [f'| @{x[0]:<11} | {x[1]:<11}|\n{"_"*26}' for x in res]
    res = '\n'.join(res)
    res = f'|USER_NAME    |COUNT_PRIZE|\n{"_"*26}\n' + res
    bot.send_message(message.chat.id, res)
    
    
    
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):

    prize_id = call.data
    user_id = call.message.chat.id

    if manager.get_winners_count(int(prize_id)) < 3:
        res = manager.add_winner(user_id, int(prize_id))
        if res:
            img = manager.get_prize_img(int(prize_id))
            with open(f'img/{img}', 'rb') as photo:
                bot.send_photo(user_id, photo, caption="Поздравляем! Ты получил картинку!")
            manager.mark_prize_delivered(user_id, int(prize_id))
        else:
            bot.send_message(user_id, 'Ты уже получил картинку!')
    else:
        bot.send_message(user_id, "К сожалению, ты не успел получить картинку! Попробуй в следующий раз!)")



@bot.message_handler(commands=['getprize'])
def handle_get_prize(message):
    user_id = message.chat.id
    prize = manager.get_next_user_prize(user_id)

    if not prize:
        bot.reply_to(message, "У тебя пока нет выигранных призов.")
        return

    prize_id, img, win_time = prize
    available_at = datetime.strptime(win_time, '%Y-%m-%d %H:%M:%S') + timedelta(minutes=5)
    seconds_left = int((available_at - datetime.now()).total_seconds())
    if seconds_left > 0:
        minutes, seconds = divmod(seconds_left, 60)
        bot.reply_to(message, f"Картинка будет доступна через {minutes} мин. {seconds} сек.")
        return

    with open(f'img/{img}', 'rb') as photo:
        bot.send_photo(user_id, photo, caption=f'Твой приз #{prize_id}')
    manager.mark_prize_delivered(user_id, prize_id)

@bot.message_handler(commands=['getmyscore'])
def handle_get_my_score(message):
    user_id = message.chat.id
    winners_img = manager.get_winners_img(user_id)
    if not winners_img:
        bot.reply_to(message, "У тебя пока нет выигранных призов.")
        return

    img_list = [img[0] for img in winners_img]
    img_str = "\n".join(img_list)
    bot.reply_to(message, f"Твои выигранные призы в виде коллажа:\n{create_collage([f'img/{x}' for x in img_list])}")
def polling_thread():
    bot.polling(none_stop=True)

if __name__ == '__main__':
    manager = DatabaseManager(DATABASE)
    manager.create_tables()

    polling_thread = threading.Thread(target=polling_thread)
    polling_shedule  = threading.Thread(target=shedule_thread)

    polling_thread.start()
    polling_shedule.start()
  
