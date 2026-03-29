import arabic_reshaper
import bidi.algorithm
from datetime import datetime

def ar(text):
	ar = arabic_reshaper.reshape(text)
	result = bidi.algorithm.get_display(ar)
	return result

# show sub number such 12,345
def sub_number(number):
	number = str(number)
	if len(number) == 4:
		return number[0:1] + "," + number[1:]
	elif len(number) == 5:
		return number[0:2] + "," + number[2:]
	elif len(number) == 6:
		return number[0:3] + "," + number[3:]
	else:
		return number

def date_calc(db_date, option):
	if db_date != "null":
		generate = datetime.strptime(db_date, "%Y-%m-%d")
		now = datetime.now()
		if option == "past":
			diff = now - generate
		elif option == "remains":
			diff = generate - now
		d = diff.days	
		s = diff.seconds
		h = s // 3600
		if h > 0: d = d + 1
		else: d = d + 0
	
		if d == 0 and h <  1:
			d = ar("دقائق")
		elif d == 1 and h >= 1:
			d = ar("ساعات")
		elif d ==  7 and h >= 1:
			d = ar("أسبوع")
		elif d == 30 and h >= 1:
			d = ar("شهر")
		elif d > 30 and h >= 1:
			d = ar("أكثر من شهر")
		else: d = ar( str(d) + " يوم")
	else : d = ar("وقت طويل")
	return d