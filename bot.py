import sqlite3
from bs4 import BeautifulSoup
import urllib.request
import random
import telebot
import time
import asyncio

bot_token = "" # Example: 1163936920:AAHp4_m9Rfl3ocKdWkRfSuhvRHSPmfBE4

bot = telebot.TeleBot(bot_token)

yest_otvet = 0
answer = 0
started = 0
stoper = 0 
conn = sqlite3.connect('game.db', check_same_thread=False)
c = conn.cursor()

def round():
	rand = random.choice([(1,178289),(186640,374199)])
	url = "https://wordparts.ru/crossword/{}/".format(random.randint(*rand))
	page = urllib.request.urlopen(url)
	soup = BeautifulSoup(page, 'html.parser')
	question = soup.title.string
	answer = soup.find("div", style="text-align:right;font-size:32px;font-weight:600;width: 100%;").string
	if answer == None:
		print("Detected wrong game: {}".format(url))
		return round()
	else:
		return question, answer


def start(message):
	global score, question, answer, stoper, yest_otvet
	yest_otvet = 0
	game = round()
	score = 0
	question = game[0]
	answer = game[1].lower()
	print(answer)
	stoper = 0
	start2(message)
	
	
def start2(message):
	global answer_list
	answer_list = []
	for x in range(len(answer)):
		answer_list.extend("•")
	bot.send_message(message.chat.id, question)
	while '•' in answer_list:
		if '•' in answer_list:
			randletter = random.randint(0, len(answer) -1)
			if answer_list[randletter] == "•":
				answer_list[randletter] = answer[randletter]
				time.sleep(8)
				try:
					bot.send_message(message.chat.id, "Подсказка: " + "".join(map(str, answer_list)))
				except NameError:
					return
	else:
		global stoper
		stoper = 1
		bot.send_message(message.chat.id, "Никто не отгадал! Правильный ответ был «{}». Следующий вопрос через пятнадцать секунд.".format(answer))
		for abcde in range(15):
			if started == 1:
				time.sleep(1)
			else:
				return
		return start(message)

@bot.message_handler(regexp=r'^начать викторину(i?)$')
def first_start(message):
	global started
	if started == 0:
		started = 1 

		bot.send_message(message.chat.id, "Викторина запущена!")
		sql = 'create table if not exists ' + str(message.chat.id).replace("-", "f") + ' (id INT, tgid TEXT, name TEXT)'
		c.execute(sql)
		conn.commit()
		start(message)

@bot.message_handler(regexp=r'^топ$|^Топ$|^ТОп$|^ТОП$|^тоП$|^ТоП$|^тОП$|^тОп$')
def top(message):
	sqltop = 'SELECT * FROM ' + str(message.chat.id).replace("-", "f") + ' ORDER BY id DESC' #+ ' LIMIT 0, 10'
	c.execute(sqltop)
	topsy = c.fetchmany(10)
	i=0
	text = "Топ игроков:\n"
	while i < len(list(topsy)):
		top = list(topsy[i])
		text = text + str(i+1) +'. ' + "[{}](tg://user?id={})".format(str(top[2]), str(top[1])) + " — " + str(top[0]) + " очков\n"
		i = i + 1
	
	bot.send_message(message.chat.id, text, parse_mode='Markdown')
	#print(top)

@bot.message_handler(regexp=r'^стоп(i?)$')
def stop(message):
	try:
		del globals()['answer_list']
		global answer_list, started
		#сообщение о том что бот остановлен и вывод правильного ответа
		bot.send_message(message.chat.id, "​Игра остановлена. Правильный ответ был «{}». Для запуска викторины напишите команду «начать викторину». В следующий раз остановить игру можно будет только через одну минуту.".format(answer))
		started = 0
	except KeyError:
		return

def otvetinit(message):
	score = 1
	global answer_list
	for a in range(len(answer_list)):
		if answer_list[a] == '•':
			score = score + 1
	del globals()['answer_list']

	gamer_name = message.from_user.first_name
	gamer_id = message.from_user.id
	gamer = '<a href="tg://user?id={}">{}</a>'.format(gamer_id, gamer_name)

	sql = 'SELECT 1 FROM {} WHERE tgid={};'.format(str(message.chat.id).replace("-", "f"), gamer_id)
	c.execute(sql)
	records = c.fetchall()

	if str(records) == '[]':
		sqlite_insert_query = """INSERT INTO {}
			(id, tgid, name)
			VALUES
			({},'{}','{}')""".format(str(message.chat.id).replace("-", "f"), score, gamer_id, gamer_name)

		c.execute(sqlite_insert_query)
		conn.commit()
		full_score = score
	else:
		sql2 = 'SELECT id FROM {} WHERE tgid={};'.format(str(message.chat.id).replace("-", "f"), gamer_id)
		score2 = c.execute(sql2)
		records2 = c.fetchone()
		full_score = score + int(records2[0])

		sql_update_query = """Update {} set id = {} where tgid = {}""".format(str(message.chat.id).replace("-", "f"), full_score, gamer_id)
		c.execute(sql_update_query)
		conn.commit()

	sql3 = """
SELECT tgid,
       id,
       (SELECT COUNT(*)
        FROM {} AS t2
        WHERE (t2.id >= t1.id)) AS row_Num
FROM {} AS t1
WHERE tgid = {};
		""".format(str(message.chat.id).replace("-", "f"), str(message.chat.id).replace("-", "f"), gamer_id)

	placelol = c.execute(sql3)
	records3 = c.fetchone()
	place = records3[2]

	bot.send_message(message.chat.id, "​Правильно ответил {} — «{}» и получает за это {} очков!\n{} с {} очками занимает {}-е место в рейтинге!\nСледующий вопрос через пятнадцать секунд.".format(gamer, answer, score, gamer_name, full_score, place), parse_mode="HTML")
	time.sleep(15)
	return start(message)

@bot.message_handler(content_types=["text"])
def otvet(message):
	global yest_otvet
	if message.text.lower() == answer and started == 1 and stoper == 0 and yest_otvet == 0:
		yest_otvet = 1
		return otvetinit(message)
	else:
		return


if __name__ == '__main__':
	bot.polling()
