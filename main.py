from kivy.uix.widget import Widget
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout

from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.text import LabelBase
from kivy.resources import resource_add_path
from kivy.metrics import dp
import os
from kivy.utils import platform
import sqlite3
from kivy.properties import NumericProperty
from tools import ar, sub_number, date_calc
from form import Form

# Fonts Customization
resource_add_path(os.getcwd())
LabelBase.register(name="ar", fn_regular="ar.ttf")
LabelBase.register(name="num", fn_regular="num.ttf")

class Card(MDCard):
	post_id = NumericProperty(0)

class EmptyLender(Widget):
    text = ar("ليس لديك مدينون")

class EmptyDebtor(Widget):
    text = ar("ليس لديك دائنون")

class EmptyFinished(Widget):
    text = ar("قائمتك فارغة")

class DeleteConfirm(MDBoxLayout):
	pass

class Demo(MDApp):
    current_list = 'lenders'
    lender_text = ar("مدين منهم")
    debtor_text = ar("أدين لهم")
    lender_btn_text = ar("مدين منه")
    debtor_btn_text = ar("أدين له")
    save_btn_text = ar("حفظ")
    card_to_delete = None

    def on_start(self):
    	self.load_data("lenders")

    def finished_list(self, table):
    	if table == "lenders":
    		self.load_data(table, True)
    		self.current_list = "lenders"
    		self.root.ids.finished_debts.md_bg_color = "white"
    		self.root.ids.finished_lends.md_bg_color = "#F4D995"

    	elif table == "debtors":
    		self.load_data(table, True)
    		self.root.ids.finished_lends.md_bg_color = "white"
    		self.root.ids.finished_debts.md_bg_color = "#F4D995"
    		self.current_list = "debtors"

    def build(self):
        self.theme_cls.primary_palette = "Pink"
        self.theme_cls.primary_hue = "300"
        return Builder.load_file("main.kv")

    def set_badge(self, index, number, table):
        nav = self.root.ids.bottom_nav
        if table == "lenders":
        	badge = self.root.ids.badge_0
        	badge_label = self.root.ids.badge_label_0
        elif table == "debtors":
        	badge = self.root.ids.badge_1
        	badge_label = self.root.ids.badge_label_1
        items = len(nav.children)

        # حساب موقع العنصر 636
        pos = (index + 0.520) / items

        badge.pos_hint = {"center_x": pos, "center_y": 0.0995}

        if number == 0:
            badge.opacity = 0
        else:
            badge.opacity = 1

        if number > 99:
            badge_label.text = "99+"
        else:
            badge_label.text = str(number)
    # -------------------------
    # Database Safe Connection
    # -------------------------
    def get_connection(self):
        if platform == "android":
        	from android.storage import app_storage_path
        	db_path = os.path.join(app_storage_path(), "data.db")
        else:
        	db_path = "data.db"
        conn = sqlite3.connect(db_path, timeout=10)
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS lenders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person TEXT,
            amount TEXT,
            date TEXT,
            payat TEXT
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS debtors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person TEXT,
            amount TEXT,
            date TEXT,
            payat TEXT
        )
        """)

        conn.commit()
        return conn, c
    # -------------------------
    # Load Data
    # -------------------------
    def load_data(self, table, finished = False):
        if table == "lenders" and finished == False:
        	widget = self.root.ids.lends
        	widget.clear_widgets( )
        	self.current_list = "lenders"
        elif table == "debtors" and finished == False:
        	widget = self.root.ids.debtors
        	self.current_list = "debtors"
        	widget.clear_widgets( )
        elif finished == True:
        	widget = self.root.ids.finished
        	widget.clear_widgets()
        	self.show_sum("debtors", True)
        	self.show_sum("lenders", True)

        # show sum or total
        self.show_sum("lenders")
        self.show_sum("debtors")
        try:       
            conn, c = self.get_connection()
            if finished == True:
            	c.execute(f"SELECT * FROM {table} WHERE amount IN(0) ORDER BY id DESC")
            else:
            	c.execute(f"SELECT * FROM {table} WHERE amount NOT IN(0) ORDER BY id DESC")
            	
            rows = c.fetchall()

            if rows:
                for row in rows:
                    card = Card()
                    card.post_id = row[0]
                    card.ids.person.text = ar(row[1])
                    card.ids.amount.text= ar(row[2] + " SDG")
                    card.ids.date.text = ar(" للسداد") + date_calc(row[4], "remains") + ar(" ومتبقي ") + date_calc(row[3], "past") + ar("مضى ")
                    widget.add_widget(card)
            else:
                if self.current_list == "lenders":
                	widget.spacing=0
                	widget.padding=0
                	if finished == False:
                		widget.add_widget(EmptyLender())
                	else:
                		widget.add_widget(EmptyFinished())
                elif self.current_list == "debtors":
                	widget.spacing=0
                	widget.padding=0
                	if finished == False:
                		widget.add_widget(EmptyDebtor())
                	else:
                		widget.add_widget(EmptyFinished())

            conn.close()

        except Exception as e:
            print("LOAD ERROR:", e)

    def lenders_list(self):
    	self.current_list = "lenders"
 
    # Count Records
    # -------------------------
    def numeric(self, table):
        try:
            conn, c = self.get_connection()
            c.execute(f"SELECT id FROM {table} WHERE amount NOT IN(0)")
            rows = c.fetchall()
            conn.close()

            count = len(rows)
            return count

        except:
            return 0
    # -------------------------
    # Show Sum
    # -------------------------
    def show_sum(self, table, finished = False):
        try:
            total = 0
            conn, c = self.get_connection()
            if finished == True:
            	c.execute(f"SELECT amount FROM {table} WHERE amount IN(0)")
            elif finished == False:
            	c.execute(f"SELECT amount FROM {table} WHERE amount NOT IN(0)")
            else: pass

            rows = c.fetchall()

            for row in rows:
                try:
                    total += int(row[0])
                except:
                    pass
            conn.close()
            if table == "lenders" and finished == False:
            	self.root.ids.left_sum.text = sub_number(total)
            	self.set_badge(0, self.numeric("lenders"), "lenders")
	
            elif table == "debtors" and finished == False:
            	self.root.ids.right_sum.text = sub_number(total)
            	self.set_badge(1, self.numeric("debtors"), "debtors")
            elif table == "lenders" and finished == True:
            	self.root.ids.finished_lends.text = ar("المدينين" + f" ( {len(rows)} )")
            elif table == "debtors" and finished == True:
            	self.root.ids.finished_debts.text = ar("الدائنين" + f" ( {len(rows)} )")
        except:
            return "0"
    # -------------------------
    # Delete Item
    # -------------------------
    def confirm_delete(self, card):
    	self.card_to_delete = card
    	self.dialog = MDDialog(auto_dismiss = False, content_cls = DeleteConfirm(), type ="custom")
    	self.dialog.open()
 
    def close_delete_confirmation(self):
    	self.dialog.dismiss()
  
    def delete_item(self, card):
    	self.dialog.dismiss()
    	try:
    		conn, c = self.get_connection()
    		c.execute(f"DELETE FROM {self.current_list} WHERE id=?", (int(card.post_id), ))
    		conn.commit()
    		conn.close()
    		if card.parent:
    			card.parent.remove_widget(card)
	    	self.show_sum("lenders")
	    	self.show_sum("debtors")

	    	# check if the widget has children
	    	if self.current_list == "lenders":
	    		if not self.root.ids.lends.children:
	    			self.load_data(self.current_list)

	    	elif self.current_list == "debtors":
	    		if not self.root.ids.debtors.children:
	    			self.load_data(self.current_list)

    	except Exception as e:
    		print("Delete Error", e)

    # -------------------------
    # Add New
    # -------------------------
    def add_new(self):
        Form().open_form()

# Run the application
if __name__ == "__main__":
    Demo().run()