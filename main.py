import telebot
from telebot import types
from datetime import datetime, timedelta
from random import shuffle

bot = telebot.TeleBot("5287049971:AAGrFEFSUi1BdvZAR45NiJAa8Cb9UNbxRz8")

# словарь со всеми чатами и игроками в этих чатах
chat_list = {}
# Пример словаря одного чата
# {-684942573:
#   {'game_running': True,
#   'players':
#       {1680333060: {'name': 'Михаил', 'role': 'мафия'},
#       704323030: {'name': 'Olesya', 'role': 'мирный житель'}},
#       532324189: {'name': 'Danil', 'role': 'мирный житель'}},
#    'dead': (1081561235, {'name': 'Ярослав', 'role': 'шериф'}),
#    'шериф': True,
#    'dList_id': 2418,
#    'шList_id': 2419,
#    'time_event': datetime.datetime(2022, 1, 26, 20, 25, 47, 280965)}}
time_now = datetime.now()

def PlayerInGame(player_id):
    # Проверка на наличие игрока в словаре
    global chat_list
    for el in chat_list:
        if player_id in chat_list[el]['players']:
            return False
        else:
            return True
def ChangeRole(player_id, player_dict, new_role, text):
    # Функция для смены роли
    player_dict[player_id].update({'role': new_role})
    bot.send_message(player_id, text)
def ListBtn(player_dict, game_id, player_role, text):
    # Функция для отправки колонки кнопок из имён игроков, кроме игрока с выбраной ролью (player_role)
    chat_id = ''
    players_btn = types.InlineKeyboardMarkup()
    for key, val in player_dict.items():
        if val['role'] != player_role:
            # В callback_data передаётся 2 значения ID игрока(key) и ID игры(game_id),между ними первая буква роли игрока
            players_btn.add(types.InlineKeyboardButton(val['name'], callback_data=f'{key}{player_role[0]}{game_id}'))
        elif val['role'] == player_role:
            chat_id = key
    message_id = bot.send_message(chat_id, text, reply_markup=players_btn)
    return message_id.message_id
def ChoiceChecker(chat_id, chat, player_role):
    if not chat[player_role]:
        bot.edit_message_text(chat_id=chat_id, message_id=chat[f'{player_role[0]}List_id'],
                              text='Время выбора истекло...', reply_markup=None)
        chat.update({player_role: True})
def Timer(chat_id, sec):
    # таймер который будет работать пока время не превысит time_event
    global chat_list, time_now
    chat_list[chat_id].update({'time_event': datetime.now() + timedelta(seconds=sec)})
    while chat_list[chat_id]['time_event'] > time_now:
        time_now = datetime.now()
def PlayersAlive(player_dict):
    # Функция для создания строки с живыми игроками
    mes = "*Живые игроки:*"
    player_keys = list(player_dict.keys())
    for i in range(len(player_keys)):
        mes += f'\n{i+1}.{player_dict[player_keys[i]]["name"]}'
    return mes
def PlayersRole(player_dict):
    # Функция для создания строки с ролями живых игроков
    mes = "*Кто-то из них:*\n"
    player_keys = list(player_dict.keys())
    shuffle(player_keys)
    for i in range(len(player_keys)):
        mes += f'{player_dict[player_keys[i]]["role"]}'
        if i < len(player_keys) - 1:
            mes += ', '
    return mes
def VoiceHandler(game_id):
    # Функция для подсчёта голосов
    global chat_list
    players = chat_list[game_id]['players']
    voice_dict = []
    for key,val in players.items():
        if 'voice' in val:
            voice_dict.append(val['voice'])
            players[key].pop('voice')
    if len(voice_dict) > 0:
        dead = players[[max(set(voice_dict), key=voice_dict.count)][0]]
        players.pop([max(set(voice_dict), key=voice_dict.count)][0])
        return dead

@bot.message_handler(commands=['create_game', 'start_game'])
def get_command(mes):
    global game_running, chat_list, time_now
    # При получении команды, в chat_list добавляется чат, если его там ещё нет
    if mes.chat.id not in chat_list:
        # game_running - определяет идёт ли в чате сейчас игра
        chat_list.update({mes.chat.id: {'game_running': False, 'players': {}}})
    # Словарь, который хранит id чата, game_running,словарь игроков и button_id
    chat = chat_list[mes.chat.id]
    players = chat['players']

    # в одном чате можно создать только одну игру (пока в переменной players нет ни одного игрока)
    if mes.text == '/create_game' and len(players) < 1:
        # инлайн кнопка для добавления в словарь игроков
        join_btn = types.InlineKeyboardMarkup()
        item1 = types.InlineKeyboardButton('Присоединиться к игре', callback_data='join')
        join_btn.add(item1)
        bot.send_message(mes.chat.id, """Нажмите на кнопку чтобы вступить в игру
Напишите команду /start_game  для начала игры""", reply_markup=join_btn)

    elif mes.text == '/start_game':
        if len(players) >= 4 and not chat['game_running']:
            # при начале игры значение game_running меняется на True чтобы нельзя было играть несколько игр одновременно
            chat_list[mes.chat.id].update({'game_running': True})
            # удаляем сообщение с join_btn и удаляем ключ и значение 'button_id' т.к. оно больше не будет использоваться
            bot.edit_message_text(chat_id=mes.chat.id, message_id=chat['button_id'],
                                  text="присоединиться к игре", reply_markup=None)
            del chat['button_id']
            # переменная 'a' это СПИСОК с информацией о игроках, как в словаре players, который мы перемешиваем
            a = list(players.items())
            shuffle(a)

            # Берём id первого игрока из перемешаного списка и меняем его роль в players
            ChangeRole(a[0][0], players, 'мафия', 'Ты - 🤵🏻мафия!\nТебе решать кто не проснётся этой ночью...')
            ChangeRole(a[1][0], players, 'шериф', 'Ты - 🕵🏼️‍♂️шериф!\nГлавный городской защитник и гроза мафии...')
            for i in range(2, len(a)):
                ChangeRole(a[i][0], players, 'мирный житель',
                           'Ты - 👨🏼 Мирный житель\nТвоя задача вычислить мафию и на городском собрании казнить засранца!')

            while True:

                if a[1][0] in players:
                    # Checker, который будет меняется при нажатии на кнопку
                    chat.update({'dead': False, 'шериф': False})
                else:
                    chat.update({'dead': False, 'шериф': True})
                bot.send_video(mes.chat.id, open("video/sunset.mp4", "rb").read(), caption='''🌃 Наступает ночь
На улицы города выходят лишь самые отважные и бесстрашные. Утром попробуем сосчитать их головы...''')
                bot.send_message(mes.chat.id, PlayersAlive(players) + '\n\nСпать осталось *1 мин.*', parse_mode="Markdown")

                # Отправляем сообщение с кнопками из игроков в игре и в chat записываем id этих сообщений

                chat.update({'dList_id': ListBtn(players, mes.chat.id, 'мафия', 'Кого будем убивать?')})
                if a[1][0] in players:
                    chat.update({'шList_id' : ListBtn(players, mes.chat.id, 'шериф', 'Кого будем проверять?')})

                chat.update({'time_event': datetime.now() + timedelta(seconds=60)})

                while chat_list[mes.chat.id]['time_event'] > time_now:
                    time_now = datetime.now()
                    if chat['dead'] and chat['шериф']:
                        break

                # Проверка нажатия на кнопку мафии и шерифа
                ChoiceChecker(a[0][0], chat, 'dead')
                if a[1][0] in players:
                    ChoiceChecker(a[1][0], chat, 'шериф')

                bot.send_video(mes.chat.id, open("video/sunrise.mp4", "rb").read(), caption='''🏙 Наступает день
Солнце всходит, подсушивая на тротуарах пролитую ночью кровь...''')
                # dead был изменён на True если мафия никого не выбрала
                if type(chat['dead']) != bool:
                    players.pop(chat['dead'][0])
                    bot.send_message(mes.chat.id,
                                     f'Сегодня был жестоко убит {chat["dead"][1]["role"]} {chat["dead"][1]["name"]}...')
                else:
                    bot.send_message(mes.chat.id,
                                     f'Мафия не проснулась этой ночью...')
                    bot.send_message(mes.chat.id, f'*Игра окончена!*\nПобедили мирные жители', parse_mode="Markdown")
                    del chat_list[mes.chat.id]
                    break

                if len(players) < 3:
                    bot.send_message(mes.chat.id, f'*Игра окончена!*\nПобедила мафия', parse_mode="Markdown")
                    del chat_list[mes.chat.id]
                    break

                bot.send_message(mes.chat.id,
                                 f'''{PlayersAlive(players)}\n\n{PlayersRole(players)}\n
Сейчас самое время обсудить результаты ночи, разобраться в причинах и следствиях...''', parse_mode="Markdown")
                Timer(mes.chat.id, 180)

                players_btn = types.InlineKeyboardMarkup()
                for key, val in players.items():
                    players_btn.add(types.InlineKeyboardButton(val['name'], callback_data=key))
                chat.update({'dList_id': bot.send_message(mes.chat.id, '''Пришло время определить и наказать виноватых.
Голосование продлится 45 секунд''', reply_markup=players_btn).message_id})


                Timer(mes.chat.id, 45)
                # Подсчёт голосов
                chat.update({'dead': VoiceHandler(mes.chat.id)})
                if chat["dead"] != None:
                    bot.edit_message_text(chat_id=mes.chat.id, message_id=chat['dList_id'],
                                          text=f'Вы решили казнить {chat["dead"]["name"]}. Он оказался {chat["dead"]["role"]}',
                                          reply_markup=None)
                else:
                    bot.edit_message_text(chat_id=mes.chat.id, message_id=chat['dList_id'],
                                          text='Мнения жителей разошлись...\nРазошлись и сами жители, так никого и не повесив...',
                                          reply_markup=None)

                if a[0][0] not in players:
                    bot.send_message(mes.chat.id, f'*Игра окончена!*\nПобедили мирные жители', parse_mode="Markdown")
                    del chat_list[mes.chat.id]
                    break
                elif len(players) < 2:
                    bot.send_message(mes.chat.id, f'*Игра окончена!*\nПобедила мафия', parse_mode="Markdown")
                    del chat_list[mes.chat.id]
                    break

        else:
            if 'button_id' in chat:
                bot.edit_message_text(chat_id=mes.chat.id, message_id=chat['button_id'],
                                      text="присоединиться к игре", reply_markup=None)

            bot.send_message(mes.chat.id, 'Слишком мало людей😢')
            del chat_list[mes.chat.id]


@bot.message_handler(content_types=
                     ['text', 'audio', 'document', 'photo', 'sticker', 'video',
                      'video_note', 'voice', 'location', 'contact', 'pinned_message'])
def get_text(mes):
    if mes.chat.id in chat_list:
        chat = chat_list[mes.chat.id]
        if chat['game_running']:
            # Удаление сообщений не играющих пользователей во время игры
            if mes.from_user.id not in chat['players']:
                bot.delete_message(mes.chat.id, mes.message_id)
            # Удаление сообщений во время ночи
            elif not chat['dead'] or not chat['шериф']:
                bot.delete_message(mes.chat.id, mes.message_id)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    global chat_list
    if call.data == 'join':
        chat_id = chat_list[call.message.chat.id]
        players = chat_id['players']
        # если игрок не запустил бота, выдаст ошибку и переёдёт к блоку except
        try:
            bot.send_message(call.from_user.id, 'Вы присоединились к игре')
            if len(players) < 1:
                chat_id.update({'button_id': call.message.message_id})
            if PlayerInGame(call.from_user.id):
                chat_id['players'].update(
                    {call.from_user.id: {'name': call.from_user.first_name}})

            elif not PlayerInGame(call.from_user.id):
                bot.send_message(call.from_user.id, 'Вы не можете присоединиться, пока находитесь в другой игре')
        except:
            bot.send_message(call.message.chat.id, f'{call.from_user.first_name}, чтобы присоединиться, нужно запустить бота (зайти в чат с ботом и нажать кнопку start)')

    # Обработка нажатия мафии на кнопку у неё в чате
    elif len(call.data.split('м')) > 1:
        # В callback_data передаётся 2 значения ID игрока и ID игры,между ними первая буква роли игрока который нажал на кнопку
        data = call.data.split('м')
        dead = chat_list[int(data[1])]["players"][int(data[0])]
        bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id,
                              text=f'Вы выбрали {dead["name"]}', reply_markup=None)
        chat_list[int(data[1])].update({'dead': (int(data[0]), dead)})
        bot.send_message(int(data[1]), '🤵🏻 Мафия выбрала жертву...')

    # Обработка нажатия шерифа на кнопку у него в чате
    elif len(call.data.split('ш')) > 1:
        data = call.data.split('ш')
        checked = chat_list[int(data[1])]["players"][int(data[0])]
        bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id,
                              text=f'{checked["name"]} оказался {checked["role"]}', reply_markup=None)
        bot.send_message(int(data[1]), '🕵🏼️‍♂️ Шериф ушёл искать злодеев...')
        chat_list[int(data[1])].update({'шериф': True})

    # Обработка голосов в общей группе
    elif call.data.isdigit:
        if call.from_user.id in chat_list[call.message.chat.id]['players']:
            chat_list[call.message.chat.id]['players'][call.from_user.id].update({'voice': int(call.data)})
bot.polling()
