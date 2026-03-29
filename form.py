from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.label import MDLabel
from kivy.uix.widget import Widget
from kivymd.uix.pickers import MDDatePicker

from kivy.base import Builder
from kivy.properties import ObjectProperty
from kivy.factory import Factory
from datetime import datetime
import  os
from kivy.utils import platform
import sqlite3
from tools import ar, date_calc

# load the form.kv file
Builder.load_file('form.kv')

class Update(MDBoxLayout):
	save_edit = ar("تحديث")
	minus_text = ar("نقص")
	plus_text = ar("إضافة")
	update_cls = None
	old_value = 0
	current_sign = "?"
	operation_btn_pressed = False

	def open_update_form(self, card, list_name):
		self.update_cls = Update()
		self.update_cls.card = card
		global current_list
		current_list = list_name
		global update_dialog
		global id
		id = card.post_id
		self.update_cls.ids.update_debtor.text = card.ids.person.text
		self.update_cls.ids.update_amount.text = card.ids.amount.text.replace(" SDG", "")
		update_dialog = MDDialog(type ='custom', content_cls = self.update_cls)
		update_dialog.open()

	def update_operation(self, btn, operation):
		# get the old value
		if self.operation_btn_pressed == False:
			amount = self.ids.update_amount
			self.old_value = amount.text.replace(" SDG", "")
			self.operation_btn_pressed = True
		amount = self.ids.update_amount
		if operation == "+":
			self.ids.minus.md_bg_color = 'white'
			self.ids.minus.text_color = (1, 0.35, 0.31, 1)
			btn.md_bg_color = (1, 0.35, 0.31, 1)
			btn.text_color = "white"
			amount.text = ''
			self.current_sign = "+"

		elif operation == "-":
			self.ids.plus.md_bg_color = 'white'
			self.ids.plus.text_color = (1, 0.35, 0.31, 1)
			btn.md_bg_color = (1, 0.35, 0.31, 1)
			btn.text_color = "white"
			amount.text = ''
			self.current_sign  = "-"
		else:
			self.current_sign = "?"

	def update(self, debtor, amount):
		if debtor.text != '' and amount.text != '':
			new_value = 0
			if self.current_sign == "+":
				debtor.real_text = ar(debtor.text)
				new_value = int(self.old_value) + int(amount.text)
			elif self.current_sign == "-":
				debtor.real_text = ar(debtor.text)
				new_value = int(self.old_value) - int(amount.text)
			if self.current_sign == "?":
				debtor.real_text = ar(debtor.text)				
				new_value = amount.text

			if platform == "android":
			 	from android.storage import app_storage_path
			 	db_path = os.path.join(app_storage_path(), "data.db")
			else:
			 	db_path = "data.db"
			conn = sqlite3.connect(db_path)
			c = conn.cursor()
			c.execute(f"UPDATE {current_list} SET person=?, amount=? WHERE id=?", (debtor.real_text, new_value, id, ))
			conn.commit()
			conn.close()

			from kivymd.app import MDApp
			MDApp.get_running_app().show_sum(current_list)

			self.card.ids.person.text = ar(debtor.real_text)
			self.card.ids.amount.text = f"{new_value} SDG" 
			#then close the update's dialog box
			update_dialog.dismiss()
				
class Content(MDBoxLayout):
	table = 'lenders'
	payment_at = ""

	def select_table(self, btn, id):
			if id == "lender_btn":
				self.ids.debtor_btn.md_bg_color = 'white'
				self.ids.debtor_btn.text_color = (1, 0.35, 0.31, 1)
				btn.md_bg_color = (1, 0.35, 0.31, 1)
				btn.text_color = "white"
				self.table = "lenders"

			elif id == "debtor_btn":
				self.ids.lender_btn.md_bg_color = 'white'
				self.ids.lender_btn.text_color = (1, 0.35, 0.31, 1)
				btn.md_bg_color = (1, 0.35, 0.31, 1)
				btn.text_color = "white"
				self.table = "debtors"

	def open_payment(self):
		datetime.strptime("2026-3-1", "%Y-%m-%d").date()
		date = MDDatePicker(min_date = min, mode = "picker")
		date.bind(on_save = self.payment_date)
		date.open()

	def payment_date(self, ins, val, range):
		self.payment_at = val
		self.ids.payment_btn.text = f"{val}"

	def save(self, debtor, amount):
		if self.payment_at != "":
			self.payment_at = self.payment_at
		else : self.payment_at = "null"

		if debtor.text != '' and amount.text != '' and amount.text != "0":
			from datetime import date
			today = date.today()
			# connect
			if platform == "android":
				from android.storage import app_storage_path
				db_path = os.path.join(app_storage_path(), "data.db")
			else:
				db_path = "data.db"
			 			
			conn = sqlite3.connect(db_path)
			c = conn.cursor()
			# create table
			c.execute(f"CREATE TABLE if not exists {self.table} (id integer PRIMARY KEY AUTOINCREMENT, person string, amount integer, date string, payat string)")
			# put the cursor
			c = conn.cursor()
			#insert the data
			c.execute(f"INSERT INTO {self.table} (person, amount, date, payat) VALUES (?, ?, ?, ?)", (debtor.real_text, amount.text, today, self.payment_at))
			#commit and close
			conn.commit()
			new_id = c.lastrowid
			conn.close()
			form.dismiss()
			from main import Card
			from kivymd.app import MDApp
			new_card = Card(post_id=new_id)
			# update sum's label'
			MDApp.get_running_app().show_sum(self.table)
			new_card.ids.person.text = ar(debtor.real_text)
			new_card.ids.amount.text = f"{amount.text} SDG"
			new_card.ids.date.text = ar(" للسداد") + date_calc(f"{self.payment_at}", "remains") + ar(" ومتبقي ") + date_calc(f"{today}", "past") + ar("مضى ")

			# add the result to th widget
			app = MDApp.get_running_app()
			if self.table == "lenders":
				self.remove_alert(app.root.ids.lends)
				app.root.ids.lends.add_widget(new_card)
			elif self.table == "debtors":
				self.remove_alert(app.root.ids.debtors)
				app.root.ids.debtors.add_widget(new_card)

	def remove_alert(self, item):
		for widget in item.children:
			if widget.__class__.__name__ == "EmptyLender" or widget.__class__.__name__ == "EmptyDebtor" :
				item.remove_widget(widget) 
class Form:
	def open_form(self):
		global form
		form = None
		if not form:
			form = MDDialog(type='custom', content_cls = Content())
		form.open()