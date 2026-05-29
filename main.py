import os
import shutil
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
    
    page.fonts = {
        "font": "font/ar.ttf",
        "num_font": "font/num_font.ttf"
    }
    
    page.theme = ft.Theme(
        font_family="font",
        color_scheme=ft.ColorScheme(
            primary="#ec407a",       
            secondary="#ec407a",     
        )
    )
    
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

    # --- ميزة النسخ الاحتياطي ---
    def save_backup_result(e: ft.FilePickerResultEvent):
        if e.path:
            try:
                shutil.copy("data.db", e.path)
                page.snack_bar = ft.SnackBar(ft.Text("تم تصدير النسخة الاحتياطية بنجاح! 💾"), bgcolor=ft.colors.GREEN_400)
                page.snack_bar.open = True
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"فشل التصدير: {str(ex)}"), bgcolor=ft.colors.RED_400)
                page.snack_bar.open = True
            page.update()

    def restore_backup_result(e: ft.FilePickerResultEvent):
        if e.files:
            selected_file_path = e.files[0].path
            try:
                shutil.copy(selected_file_path, "data.db")
                page.snack_bar = ft.SnackBar(ft.Text("تم استيراد البيانات بنجاح! 🔄"), bgcolor=ft.colors.GREEN_400)
                page.snack_bar.open = True
                refresh_ui_data()
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"فشل الاستيراد: {str(ex)}"), bgcolor=ft.colors.RED_400)
                page.snack_bar.open = True
            page.update()

    file_picker_save = ft.FilePicker(on_result=save_backup_result)
    file_picker_open = ft.FilePicker(on_result=restore_backup_result)
    page.overlay.extend([file_picker_save, file_picker_open])

    def on_header_pan_update(e: ft.DragUpdateEvent):
        if e.delta_x > 15:  
            file_picker_open.pick_files(allowed_extensions=["db"])
        elif e.delta_x < -15:  
            file_picker_save.save_file(file_name=f"backup_{datetime.now().strftime('%Y%m%d')}.db")

    # --- إدارة نافذة تأكيد الحذف ---
    def close_confirm_dlg(e):
        confirm_dialog.open = False
        page.update()

    def delete_confirmed(debt_id):
        nonlocal active_debt_id
        # إغلاق النافذة فوراً لتحسين استجابة الواجهة في APK
        confirm_dialog.open = False
        page.update()
        
        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM debts WHERE id=?", (debt_id,))
        conn.commit()
        conn.close()
        
        active_debt_id = None
        refresh_ui_data()

    confirm_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("تأكيد الحذف", text_align=ft.TextAlign.CENTER),
        content=ft.Text("هل أنت متأكد أنك تريد حذف السجل؟", text_align=ft.TextAlign.CENTER),
        actions_alignment=ft.MainAxisAlignment.CENTER,
    )
    page.overlay.append(confirm_dialog)

    def show_confirm_dialog(debt_id):
        confirm_dialog.actions = [
            ft.TextButton("حذف", on_click=lambda _: delete_confirmed(debt_id)),
            ft.TextButton("إلغاء", on_click=close_confirm_dlg),
        ]
        confirm_dialog.open = True
        page.update()

    # --- دالة الحفظ والتحديث ---
    def save_new_debt(e):
        nonlocal selected_date_str, active_debt_id, selected_type, stored_amount, operation_mode
        if not name_input.value or not amount_input.value: return
            
        try: input_amount = float(amount_input.value)
        except ValueError: return  

        # إغلاق النافذة أولاً لضمان عدم تعليقها في الأندرويد
        add_dialog.open = False
        page.update()
            
        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()
        today_str = datetime.now().strftime('%Y-%m-%d')
        week_from_now_str = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        final_due_date = selected_date_str if selected_date_str else week_from_now_str

        target_type = selected_type
        if active_debt_id:
            if operation_mode == "add": final_amount = stored_amount + input_amount
            elif operation_mode == "subtract":
                final_amount = max(0.0, stored_amount - input_amount)
            else: final_amount = input_amount
        else: final_amount = input_amount

        # منطق تحويل الحالة للمكتمل تلقائياً
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
        
        # تصفير القيم
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

    date_picker = ft.DatePicker(on_change=handle_date_change, confirm_text="موافق", cancel_text="إلغاء")
    page.overlay.append(date_picker)

    def change_type(e):
        update_type_buttons(e.control.text)
        page.update()

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

    def start_add_operation(e):
        nonlocal stored_amount, operation_mode
        try: stored_amount = float(amount_input.value) if amount_input.value else 0.0
        except: stored_amount = 0.0
        operation_mode = "add"
        amount_input.value = ""
        amount_input.hint_text = f"إضافة إلى {stored_amount:g}"
        btn_save.text = "تأكيد الإضافة"
        btn_quick_add.style = ft.ButtonStyle(color="#ec407a", bgcolor="#fce4ec", side=ft.BorderSide(color="#ec407a", width=1.5))
        btn_quick_sub.style = ft.ButtonStyle(color="#607d8b", bgcolor=ft.colors.WHITE)
        page.update()

    def start_subtract_operation(e):
        nonlocal stored_amount, operation_mode
        try: stored_amount = float(amount_input.value) if amount_input.value else 0.0
        except: stored_amount = 0.0
        operation_mode = "subtract"
        amount_input.value = ""
        amount_input.hint_text = f"خصم من {stored_amount:g}"
        btn_save.text = "تأكيد الطرح"
        btn_quick_sub.style = ft.ButtonStyle(color="#607d8b", bgcolor="#eceff1", side=ft.BorderSide(color="#607d8b", width=1.5))
        btn_quick_add.style = ft.ButtonStyle(color="#ec407a", bgcolor=ft.colors.WHITE)
        page.update()

    # --- واجهة نافذة الإدخال ---
    btn_adin = ft.OutlinedButton(text="دائن", width=110, on_click=change_type)
    btn_madin = ft.OutlinedButton(text="مدين", width=110, on_click=change_type)
    name_input = ft.TextField(hint_text="الإسم", width=240)
    amount_input = ft.TextField(hint_text="المبلغ", keyboard_type=ft.KeyboardType.NUMBER, width=240)
    btn_quick_add = ft.OutlinedButton(text="إضافة", width=110, on_click=start_add_operation, visible=False)
    btn_quick_sub = ft.OutlinedButton(text="طرح", width=110, on_click=start_subtract_operation, visible=False)
    btn_date_picker = ft.OutlinedButton(text="تاريخ السداد", width=240, on_click=lambda _: date_picker.pick_date())
    btn_save = ft.ElevatedButton(text="حفظ", bgcolor="#ec407a", color=ft.colors.WHITE, width=240, on_click=save_new_debt)

    add_dialog = ft.AlertDialog(
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(controls=[btn_adin, btn_madin], alignment=ft.MainAxisAlignment.CENTER),
                    name_input, amount_input,
                    ft.Row(controls=[btn_quick_sub, btn_quick_add], alignment=ft.MainAxisAlignment.CENTER),
                    btn_date_picker, btn_save
                ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ), width=260, padding=5
        )
    )
    page.overlay.append(add_dialog)

    def open_add_dialog_fast(edit_id=None, name="", amount=0, dtype="madin", due_date=None):
        nonlocal active_debt_id, selected_type, selected_date_str, operation_mode, stored_amount
        operation_mode = None
        stored_amount = 0.0
        amount_input.hint_text = "المبلغ"

        if edit_id:
            active_debt_id = edit_id
            name_input.value = name
            amount_input.value = f"{amount:g}"
            btn_save.text = "تحديث"
            update_type_buttons(dtype)
            btn_quick_add.visible = True
            btn_quick_sub.visible = True
            selected_date_str = due_date
            btn_date_picker.text = f"تاريخ السداد: {due_date}" if due_date else "تاريخ السداد"
        else:
            active_debt_id = None
            name_input.value = ""
            amount_input.value = ""
            btn_save.text = "حفظ"
            btn_date_picker.text = "تاريخ السداد"
            selected_date_str = None
            update_type_buttons("madin")
            btn_quick_add.visible = False
            btn_quick_sub.visible = False
            
        add_dialog.open = True
        page.update()

    def build_debt_card(debt_id, name, amount, currency, db_p, db_l, debt_type, r_date, d_date):
        is_completed = debt_type in ["madin_done", "adin_done"]
        formatted_amount = f"{amount:,.2f}".rstrip('0').rstrip('.') if amount % 1 != 0 else f"{int(amount):,}"

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text(name, size=16, weight=ft.FontWeight.BOLD, color="#b06a7b" if not is_completed else "#9e9e9e"),
                            ft.Text(f"{formatted_amount} {currency}", size=15, color="#d4af37" if not is_completed else "#9e9e9e"),
                        ], expand=True
                    ),
                    ft.IconButton(icon=ft.icons.DELETE_ROUNDED, icon_color=ft.colors.PINK_200, on_click=lambda e: show_confirm_dialog(debt_id)),
                ]
            ), bgcolor=ft.colors.WHITE, padding=15, border_radius=10, margin=ft.margin.only(bottom=10, left=15, right=15),
            on_click=lambda e: open_add_dialog_fast(debt_id, name, amount, debt_type, d_date)
        )

    # --- هياكل عرض البيانات ---
    madin_container = ft.Container(expand=True)
    adin_container = ft.Container(expand=True)
    completed_items_container = ft.Container(expand=True)
    total_madin_text = ft.Text("0", size=28, color=ft.colors.WHITE, font_family="num_font")
    total_adin_text = ft.Text("0", size=28, color=ft.colors.WHITE, font_family="num_font")

    def refresh_ui_data():
        madin_data = get_debts('madin')
        madin_container.content = ft.ListView(controls=[build_debt_card(*d) for d in madin_data]) if madin_data else ft.Text("لا يوجد بيانات")
        
        adin_data = get_debts('adin')
        adin_container.content = ft.ListView(controls=[build_debt_card(*d) for d in adin_data]) if adin_data else ft.Text("لا يوجد بيانات")
        
        # تحديث المبالغ
        total_madin_text.value = get_total_amount('madin')
        total_adin_text.value = get_total_amount('adin')
        
        # تحديث عدادات الأيقونات في النافبار
        update_navigation_bar()
        page.update()

    def update_navigation_bar():
        m_count = get_debts_count('madin')
        a_count = get_debts_count('adin')
        d_count = get_debts_count('madin_done') + get_debts_count('adin_done')
        
        page.navigation_bar = ft.NavigationBar(
            selected_index=current_nav_index,
            on_change=lambda e: on_nav_change(e),
            destinations=[
                ft.NavigationDestination(icon=ft.icons.ASSIGNMENT_IND, label=f"مدين ({m_count})"),
                ft.NavigationDestination(icon=ft.icons.CHECK_CIRCLE, label=f"مكتمل ({d_count})"),
                ft.NavigationDestination(icon=ft.icons.SUPERVISOR_ACCOUNT, label=f"دائن ({a_count})"),
            ]
        )

    def on_nav_change(e):
        nonlocal current_nav_index
        current_nav_index = e.control.selected_index
        if current_nav_index == 0: content_container.content = madin_container
        elif current_nav_index == 1: content_container.content = completed_page_layout
        else: content_container.content = adin_container
        page.update()

    # أزرار التبديل في صفحة المكتمل
    btn_comp_madin = ft.TextButton("المدينين", expand=True, on_click=lambda _: switch_done_view("madin_done"))
    btn_comp_adin = ft.TextButton("الدائنين", expand=True, on_click=lambda _: switch_done_view("adin_done"))

    def switch_done_view(view_type):
        data = get_debts(view_type)
        completed_items_container.content = ft.ListView(controls=[build_debt_card(*d) for d in data])
        page.update()

    completed_page_layout = ft.Column([ft.Row([btn_comp_madin, btn_comp_adin]), completed_items_container], expand=True)
    content_container = ft.Container(content=madin_container, expand=True)

    header = ft.GestureDetector(
        on_pan_update=on_header_pan_update,
        content=ft.Container(
            content=ft.Row([
                ft.Column([ft.Text("مدين منهم", color="white70"), total_madin_text], expand=True, horizontal_alignment="center"),
                ft.Column([ft.Text("أدين لهم", color="white70"), total_adin_text], expand=True, horizontal_alignment="center"),
            ]), bgcolor="#ec407a", padding=30
        )
    )

    def build_main_ui():
        page.floating_action_button = ft.FloatingActionButton(icon=ft.icons.ADD, on_click=lambda _: open_add_dialog_fast())
        page.add(header, content_container)
        refresh_ui_data()

    show_splash_screen(page, on_timeout_callback=build_main_ui)

ft.app(target=main, assets_dir="assets")
