import os
import sqlite3
from datetime import datetime, date, timedelta
import flet as ft
from splash import show_splash_screen 

def init_db():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'ج.س',
            days_passed INTEGER DEFAULT 0,
            days_left INTEGER DEFAULT 0,
            type TEXT NOT NULL,
            record_date TEXT,
            due_date TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_debts(debt_type):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, amount, currency, days_passed, days_left, type, record_date, due_date FROM debts WHERE type=?", (debt_type,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_debts_count(debt_type):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM debts WHERE type=?", (debt_type,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_total_amount(debt_type):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(amount) FROM debts WHERE type=?", (debt_type,))
    total = cursor.fetchone()[0]
    conn.close()
    if total:
        formatted_total = f"{total:,.2f}".rstrip('0').rstrip('.') if total % 1 != 0 else f"{int(total):,}"
        return f"{formatted_total} جنيه"
    return "0 جنيه"

def main(page: ft.Page):
    init_db()
    page.fonts = {"font": "font/ar.ttf", "num_font": "font/num_font.ttf"}
    page.theme = ft.Theme(font_family="font", color_scheme=ft.ColorScheme(primary="#ec407a", secondary="#ec407a"))
    page.theme_mode = ft.ThemeMode.LIGHT
    page.rtl = True
    page.padding = 0
    page.bgcolor = "#f5f5f5"
    page.locale = "ar"

    active_debt_id = None
    selected_date_str = None  
    stored_amount = 0.0
    operation_mode = None  
    selected_type = "madin"
    current_completed_view = "madin_done"
    current_nav_index = 0

    # --- وظائف الإغلاق الصارمة ---
    def close_all_dialogs(e=None):
        add_dialog.open = False
        confirm_dialog.open = False
        page.dialog = None # إفراغ المرجع تماماً
        page.update()

    def delete_confirmed(debt_id):
        # إغلاق فوري للنافذة قبل المعالجة
        confirm_dialog.open = False
        page.dialog = None
        page.update()
        
        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM debts WHERE id=?", (debt_id,))
        conn.commit()
        conn.close()
        refresh_ui_data()

    # --- نافذة تأكيد الحذف ---
    confirm_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("تأكيد الحذف", text_align=ft.TextAlign.CENTER),
        content=ft.Text("هل أنت متأكد أنك تريد حذف السجل؟", text_align=ft.TextAlign.CENTER),
        actions_alignment=ft.MainAxisAlignment.CENTER,
    )

    def show_confirm_dialog(debt_id):
        confirm_dialog.actions = [
            ft.TextButton("حذف", on_click=lambda _: delete_confirmed(debt_id)),
            ft.TextButton("إلغاء", on_click=close_all_dialogs),
        ]
        page.dialog = confirm_dialog
        confirm_dialog.open = True
        page.update()

    # --- دالة الحفظ الصارمة ---
    def save_new_debt(e):
        nonlocal selected_date_str, active_debt_id, selected_type, stored_amount, operation_mode
        if not name_input.value or not amount_input.value: return
            
        try: input_amount = float(amount_input.value)
        except ValueError: return  
            
        # 1. إغلاق النافذة أولاً لضمان عدم التعليق في أندرويد
        add_dialog.open = False
        page.dialog = None
        page.update()

        # 2. معالجة البيانات في الخلفية
        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()
        today_str = datetime.now().strftime('%Y-%m-%d')
        week_from_now_str = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        final_due_date = selected_date_str if selected_date_str else week_from_now_str

        target_type = selected_type
        if active_debt_id:
            if operation_mode == "add": final_amount = stored_amount + input_amount
            elif operation_mode == "subtract":
                final_amount = stored_amount - input_amount
                if final_amount < 0: final_amount = 0.0
            else: final_amount = input_amount
        else: final_amount = input_amount

        if final_amount == 0:
            if target_type in ["madin", "madin_done"]: target_type = "madin_done"
            elif target_type in ["adin", "adin_done"]: target_type = "adin_done"
        else:
            if target_type == "madin_done": target_type = "madin"
            elif target_type == "adin_done": target_type = "adin"

        if active_debt_id:
            cursor.execute("UPDATE debts SET name=?, amount=?, type=?, due_date=? WHERE id=?", (name_input.value, final_amount, target_type, final_due_date, active_debt_id))
        else:         
            cursor.execute("INSERT INTO debts (name, amount, currency, type, record_date, due_date) VALUES (?, ?, ?, ?, ?, ?)", (name_input.value, final_amount, "ج.س", target_type, today_str, final_due_date))
            
        conn.commit()
        conn.close()
        
        # 3. تصفير المتغيرات
        name_input.value = ""
        amount_input.value = ""
        selected_date_str = None
        date_picker.value = None 
        active_debt_id = None
        stored_amount = 0.0
        operation_mode = None
        btn_date_picker.text = "تاريخ السداد"
        btn_save.text = "حفظ"
        
        refresh_ui_data()

    def handle_date_change(e):
        nonlocal selected_date_str
        if date_picker.value:
            selected_date_str = date_picker.value.strftime('%Y-%m-%d')
            btn_date_picker.text = f"تاريخ السداد: {selected_date_str}"
            page.update()

    date_picker = ft.DatePicker(on_change=handle_date_change)
    
    def update_type_buttons(type_text):
        nonlocal selected_type
        if type_text in ["دائن", "adin", "adin_done"]:
            selected_type = "adin"
            btn_adin.style = ft.ButtonStyle(color="#ec407a", bgcolor="#fce4ec", shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(color="#ec407a", width=1.5))
            btn_madin.style = ft.ButtonStyle(color="#ec407a", bgcolor=ft.colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(color="#e0e0e0", width=1))
        else:
            selected_type = "madin"
            btn_madin.style = ft.ButtonStyle(color="#ec407a", bgcolor="#fce4ec", shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(color="#ec407a", width=1.5))
            btn_adin.style = ft.ButtonStyle(color="#ec407a", bgcolor=ft.colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(color="#e0e0e0", width=1))

    # --- عناصر واجهة الإدخال ---
    btn_adin = ft.OutlinedButton(text="دائن", width=110, on_click=lambda e: update_type_buttons("adin"))
    btn_madin = ft.OutlinedButton(text="مدين", width=110, on_click=lambda e: update_type_buttons("madin"))
    name_input = ft.TextField(hint_text="الإسم", text_align=ft.TextAlign.RIGHT, width=240)
    amount_input = ft.TextField(hint_text="المبلغ", text_align=ft.TextAlign.RIGHT, keyboard_type=ft.KeyboardType.NUMBER, width=240)
    btn_quick_add = ft.OutlinedButton(text="إضافة ", visible=False, width=110, on_click=lambda _: start_op("add"))
    btn_quick_sub = ft.OutlinedButton(text="طرح ", visible=False, width=110, on_click=lambda _: start_op("subtract"))
    btn_date_picker = ft.OutlinedButton(text="تاريخ السداد", width=240, on_click=lambda _: date_picker.pick_date())
    btn_save = ft.ElevatedButton(text="حفظ", bgcolor="#ec407a", color=ft.colors.WHITE, width=240, on_click=save_new_debt)

    def start_op(mode):
        nonlocal operation_mode, stored_amount
        operation_mode = mode
        stored_amount = float(amount_input.value) if amount_input.value else 0.0
        amount_input.value = ""
        amount_input.hint_text = f"المبلغ لـ {'الإضافة' if mode=='add' else 'الطرح'}"
        btn_save.text = "تأكيد العملية"
        page.update()

    add_dialog = ft.AlertDialog(
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row([btn_adin, btn_madin], alignment=ft.MainAxisAlignment.CENTER),
                    name_input, amount_input,
                    ft.Row([btn_quick_sub, btn_quick_add], alignment=ft.MainAxisAlignment.CENTER),
                    btn_date_picker, btn_save,
                    ft.TextButton("إلغاء", on_click=close_all_dialogs)
                ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ), width=260
        )
    )

    def open_add_dialog_fast(edit_id=None, name="", amount=0, dtype="madin", due_date=None):
        nonlocal active_debt_id, selected_type, selected_date_str, operation_mode
        operation_mode = None
        if edit_id:
            active_debt_id, name_input.value, amount_input.value = edit_id, name, f"{amount:g}"
            btn_quick_add.visible = btn_quick_sub.visible = True
            update_type_buttons(dtype)
        else:
            active_debt_id = None
            name_input.value = amount_input.value = ""
            btn_quick_add.visible = btn_quick_sub.visible = False
            update_type_buttons("madin")
        
        page.dialog = add_dialog
        add_dialog.open = True
        page.update()

    # --- بناء البطاقات والقوائم ---
    def build_debt_card(debt_id, name, amount, currency, db_days_passed, db_days_left, debt_type, record_date, due_date):
        is_completed = debt_type in ["madin_done", "adin_done"]
        formatted_amount = f"{amount:,.2f}".rstrip('0').rstrip('.') if amount % 1 != 0 else f"{int(amount):,}"
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(name, size=16, weight=ft.FontWeight.BOLD),
                    ft.Text(f"{formatted_amount} {currency}", size=15, color="#d4af37"),
                ], expand=True),
                ft.IconButton(icon=ft.icons.DELETE_ROUNDED, on_click=lambda e: show_confirm_dialog(debt_id)),
            ]), bgcolor=ft.colors.WHITE, padding=15, border_radius=10, margin=5,
            on_click=lambda e: open_add_dialog_fast(debt_id, name, amount, debt_type, due_date)
        )

    # القوائم
    madin_list = ft.ListView(expand=True)
    adin_list = ft.ListView(expand=True)
    completed_list = ft.ListView(expand=True)
    
    total_madin_text = ft.Text("0", size=28, color=ft.colors.WHITE, font_family="num_font")
    total_adin_text = ft.Text("0", size=28, color=ft.colors.WHITE, font_family="num_font")

    def refresh_ui_data():
        # تحديث المبالغ
        total_madin_text.value = get_total_amount('madin')
        total_adin_text.value = get_total_amount('adin')
        
        # تحديث القوائم
        madin_list.controls = [build_debt_card(*d) for d in get_debts('madin')]
        adin_list.controls = [build_debt_card(*d) for d in get_debts('adin')]
        
        done_data = get_debts('madin_done') + get_debts('adin_done')
        completed_list.controls = [build_debt_card(*d) for d in done_data]
        
        # تحديث شريط التنقل
        update_nav_bar()
        page.update()

    def update_nav_bar():
        c_madin = get_debts_count('madin')
        c_adin = get_debts_count('adin')
        c_done = get_debts_count('madin_done') + get_debts_count('adin_done')
        
        page.navigation_bar = ft.NavigationBar(
            selected_index=current_nav_index,
            on_change=lambda e: on_nav_change(e.control.selected_index),
            destinations=[
                ft.NavigationDestination(icon=ft.icons.PERSON, label=f"مدين ({c_madin})"),
                ft.NavigationDestination(icon=ft.icons.CHECK_CIRCLE, label=f"مكتمل ({c_done})"),
                ft.NavigationDestination(icon=ft.icons.PEOPLE, label=f"دائن ({c_adin})"),
            ]
        )

    def on_nav_change(index):
        nonlocal current_nav_index
        current_nav_index = index
        content_container.content = [madin_list, completed_list, adin_list][index]
        page.update()

    # الهيكل الرئيسي
    header = ft.Container(
        content=ft.Row([
            ft.Column([ft.Text("رصيد المدينين", color=ft.colors.WHITE70), total_madin_text], expand=True, horizontal_alignment="center"),
            ft.Column([ft.Text("رصيد الدائنين", color=ft.colors.WHITE70), total_adin_text], expand=True, horizontal_alignment="center"),
        ]), bgcolor="#ec407a", padding=20
    )

    content_container = ft.Container(content=madin_list, expand=True)
    fab = ft.FloatingActionButton(icon=ft.icons.ADD, on_click=lambda _: open_add_dialog_fast())

    # إعداد الـ Overlays لضمان بقائها في الذاكرة
    page.overlay.extend([date_picker, add_dialog, confirm_dialog])

    def build_main_ui():
        page.floating_action_button = fab
        page.add(header, content_container)
        refresh_ui_data()

    show_splash_screen(page, on_timeout_callback=build_main_ui)

ft.app(target=main, assets_dir="assets")
