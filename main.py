import os
import sqlite3
from datetime import datetime, date, timedelta
import flet as ft
from splash import show_splash_screen 

# --- 1. إصلاح قاعدة البيانات (إضافة try-except لضمان عدم التوقف) ---
def init_db():
    try:
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
    except Exception as e:
        print(f"Database Error: {e}")

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
    page.rtl = True
    page.padding = 0
    page.bgcolor = "#f5f5f5"

    # متغيرات الحالة
    active_debt_id = None
    selected_date_str = None  
    stored_amount = 0.0
    operation_mode = None  
    selected_type = "madin"
    current_nav_index = 0
    current_completed_view = "madin_done"

    # --- 2. الحل الصارم لإغلاق النوافذ (إزالة الشبح الأبيض) ---
    def close_all_dialogs(e=None):
        add_dialog.open = False
        confirm_dialog.open = False
        page.dialog = None # حاسم جداً: مسح المرجع من الصفحة
        page.update()

    def delete_confirmed(debt_id):
        # إغلاق فوري قبل العملية الثقيلة
        confirm_dialog.open = False
        page.dialog = None
        page.update()
        
        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM debts WHERE id=?", (debt_id,))
        conn.commit()
        conn.close()
        refresh_ui_data()

    # --- 3. تعريف النوافذ (بدون إضافتها للـ overlay يدوياً لتجنب التعارض) ---
    confirm_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("تأكيد الحذف", text_align=ft.TextAlign.CENTER),
        content=ft.Text("هل أنت متأكد؟", text_align=ft.TextAlign.CENTER),
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

    def save_new_debt(e):
        nonlocal selected_date_str, active_debt_id, selected_type, stored_amount, operation_mode
        if not name_input.value or not amount_input.value: return
        
        try: input_amount = float(amount_input.value)
        except: return

        # --- إغلاق النافذة قبل معالجة البيانات ---
        add_dialog.open = False
        page.dialog = None 
        page.update() 

        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()
        today_str = datetime.now().strftime('%Y-%m-%d')
        final_due_date = selected_date_str if selected_date_str else today_str

        # منطق الحساب
        final_amount = input_amount
        if active_debt_id:
            if operation_mode == "add": final_amount = stored_amount + input_amount
            elif operation_mode == "subtract": final_amount = max(0, stored_amount - input_amount)

        target_type = selected_type
        if final_amount == 0:
            target_type = "madin_done" if "madin" in selected_type else "adin_done"

        if active_debt_id:
            cursor.execute("UPDATE debts SET name=?, amount=?, type=?, due_date=? WHERE id=?", 
                         (name_input.value, final_amount, target_type, final_due_date, active_debt_id))
        else:
            cursor.execute("INSERT INTO debts (name, amount, currency, type, record_date, due_date) VALUES (?, ?, ?, ?, ?, ?)", 
                         (name_input.value, final_amount, "ج.س", target_type, today_str, final_due_date))
        
        conn.commit()
        conn.close()
        refresh_ui_data()

    # --- 4. عناصر واجهة الإدخال ---
    name_input = ft.TextField(hint_text="الإسم", text_align=ft.TextAlign.RIGHT, width=240)
    amount_input = ft.TextField(hint_text="المبلغ", keyboard_type=ft.KeyboardType.NUMBER, width=240)
    btn_save = ft.ElevatedButton(text="حفظ", bgcolor="#ec407a", color="white", width=240, on_click=save_new_debt)
    date_picker = ft.DatePicker(on_change=lambda e: page.update())

    add_dialog = ft.AlertDialog(
        content=ft.Column([
            name_input, amount_input, btn_save,
            ft.TextButton("إلغاء", on_click=close_all_dialogs)
        ], tight=True),
    )

    def open_add_dialog_fast(edit_id=None, name="", amount=0, dtype="madin"):
        nonlocal active_debt_id
        active_debt_id = edit_id
        name_input.value = name
        amount_input.value = str(amount) if amount else ""
        
        page.dialog = add_dialog # إعادة التعيين عند الفتح
        add_dialog.open = True
        page.update()

    # --- 5. بناء القائمة والـ UI ---
    def refresh_ui_data():
        total_madin_text.value = get_total_amount('madin')
        total_adin_text.value = get_total_amount('adin')
        
        # تحديث القوائم (مثال للمدين)
        madin_data = get_debts('madin')
        madin_list.controls = [
            ft.ListTile(title=ft.Text(d[1]), subtitle=ft.Text(f"{d[2]} ج"), 
                        trailing=ft.IconButton(ft.icons.DELETE, on_click=lambda e, id=d[0]: show_confirm_dialog(id)),
                        on_click=lambda e, id=d[0], n=d[1], a=d[2]: open_add_dialog_fast(id, n, a))
            for d in madin_data
        ]
        page.update()

    total_madin_text = ft.Text("0", size=28, color="white")
    total_adin_text = ft.Text("0", size=28, color="white")
    madin_list = ft.ListView(expand=True)

    header = ft.Container(
        content=ft.Row([
            ft.Column([ft.Text("مدينين"), total_madin_text], expand=True),
            ft.Column([ft.Text("دائنين"), total_adin_text], expand=True),
        ]), bgcolor="#ec407a", padding=20
    )

    page.overlay.append(date_picker)
    page.floating_action_button = ft.FloatingActionButton(icon=ft.icons.ADD, on_click=lambda _: open_add_dialog_fast())
    
    def start_app():
        page.add(header, madin_list)
        refresh_ui_data()

    show_splash_screen(page, on_timeout_callback=start_app)

ft.app(target=main, assets_dir="assets")
