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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('onboarding_showed', '0')")
    conn.commit()
    conn.close()

def check_onboarding_status():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key='onboarding_showed'")
    row = cursor.fetchone()
    conn.close()
    return row[0] == '1' if row else False

def set_onboarding_completed():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET value='1' WHERE key='onboarding_showed'")
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

    # دالة إغلاق تأكيد الحذف عبر الـ overlay المباشر
    def close_dlg(e):
        confirm_dialog.open = False
        page.update()

    def delete_confirmed(debt_id):
        nonlocal active_debt_id
        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM debts WHERE id=?", (debt_id,))
        conn.commit()
        conn.close()
        
        confirm_dialog.open = False
        page.update()
        
        active_debt_id = None
        refresh_ui_data()

    confirm_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("تأكيد الحذف", text_align=ft.TextAlign.CENTER),
        content=ft.Text("هل أنت متأكد أنك تريد حذف السجل؟", text_align=ft.TextAlign.CENTER),
        actions_alignment=ft.MainAxisAlignment.CENTER,
    )
    # إدراج الـ dialog في الـ overlay مباشرة بدلاً من استدعاء page.dialog
    page.overlay.append(confirm_dialog)

    def show_confirm_dialog(debt_id):
        confirm_dialog.actions = [
            ft.TextButton("حذف", on_click=lambda _: delete_confirmed(debt_id)),
            ft.TextButton("إلغاء", on_click=close_dlg),
        ]
        confirm_dialog.open = True
        page.update()

    def save_new_debt(e):
        nonlocal selected_date_str, active_debt_id, selected_type, stored_amount, operation_mode
        if not name_input.value or not amount_input.value: return
        try: input_amount = float(amount_input.value)
        except ValueError: return  
            
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
        
        # حل مشكلة الأندرويد: إغلاق وتحديث فوري قبل تفريغ النصوص لكي يستوعب الـ Engine الاختفاء
        add_dialog.open = False
        page.update()

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

    date_picker = ft.DatePicker(on_change=handle_date_change, help_text="اختر تاريخ السداد", confirm_text="موافق", cancel_text="إلغاء")
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
        except ValueError: stored_amount = 0.0
        operation_mode = "add"
        amount_input.value = ""
        formatted_stored = f"{stored_amount:,.2f}".rstrip('0').rstrip('.') if stored_amount % 1 != 0 else f"{int(stored_amount):,}"
        amount_input.hint_text = f"المبلغ المراد إضافته لـ {formatted_stored}"
        btn_save.text = "تأكيد الإضافة "
        btn_quick_add.style = ft.ButtonStyle(color="#ec407a", bgcolor="#fce4ec", shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(color="#ec407a", width=1.5))
        btn_quick_sub.style = ft.ButtonStyle(color="#607d8b", bgcolor=ft.colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(color="#e0e0e0", width=1))
        page.update()

    def start_subtract_operation(e):
        nonlocal stored_amount, operation_mode
        try: stored_amount = float(amount_input.value) if amount_input.value else 0.0
        except ValueError: stored_amount = 0.0
        operation_mode = "subtract"
        amount_input.value = ""
        formatted_stored = f"{stored_amount:,.2f}".rstrip('0').rstrip('.') if stored_amount % 1 != 0 else f"{int(stored_amount):,}"
        amount_input.hint_text = f"المبلغ المراد طرحه من {formatted_stored}"
        btn_save.text = "تأكيد الطرح "  
        btn_quick_sub.style = ft.ButtonStyle(color="#607d8b", bgcolor="#eceff1", shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(color="#607d8b", width=1.5))
        btn_quick_add.style = ft.ButtonStyle(color="#ec407a", bgcolor=ft.colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(color="#e0e0e0", width=1))
        page.update()

    btn_adin = ft.OutlinedButton(text="دائن", style=ft.ButtonStyle(color="#ec407a", bgcolor=ft.colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(color="#e0e0e0", width=1)), width=110, on_click=change_type)
    btn_madin = ft.OutlinedButton(text="مدين", style=ft.ButtonStyle(color="#ec407a", bgcolor="#fce4ec", shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(color="#ec407a", width=1.5)), width=110, on_click=change_type)
    name_input = ft.TextField(hint_text="الإسم", border_color="#e0e0e0", text_align=ft.TextAlign.RIGHT, width=240, height=50)
    amount_input = ft.TextField(hint_text="المبلغ", border_color="#e0e0e0", text_align=ft.TextAlign.RIGHT, keyboard_type=ft.KeyboardType.NUMBER, width=240, height=50)
    btn_quick_add = ft.OutlinedButton(text="إضافة ", style=ft.ButtonStyle(color="#ec407a", bgcolor=ft.colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(color="#e0e0e0", width=1)), width=110, on_click=start_add_operation, visible=False)
    btn_quick_sub = ft.OutlinedButton(text="طرح ", style=ft.ButtonStyle(color="#607d8b", bgcolor=ft.colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(color="#e0e0e0", width=1)), width=110, on_click=start_subtract_operation, visible=False)
    btn_date_picker = ft.OutlinedButton(text="تاريخ السداد", style=ft.ButtonStyle(color="#ec407a", bgcolor=ft.colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(color="#ec407a", width=1)), width=240, on_click=lambda _: date_picker.pick_date())
    btn_save = ft.ElevatedButton(text="حفظ", bgcolor="#ec407a", color=ft.colors.WHITE, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)), width=240, on_click=save_new_debt)

    add_dialog = ft.AlertDialog(
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(controls=[btn_adin, btn_madin], alignment=ft.MainAxisAlignment.CENTER, spacing=10, width=240),
                    ft.Container(height=8), name_input, amount_input,
                    ft.Row(controls=[btn_quick_sub, btn_quick_add], alignment=ft.MainAxisAlignment.CENTER, spacing=10, width=240),
                    btn_date_picker, ft.Container(height=12), btn_save
                ], tight=True, spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ), width=260, padding=ft.padding.all(5)
        ), shape=ft.RoundedRectangleBorder(radius=15)
    )
    # إضافة الـ dialog كجزء مستقر وثابت من الـ Overlay
    page.overlay.append(add_dialog)

    def open_add_dialog_fast(edit_id=None, name="", amount=0, dtype="madin", due_date=None):
        nonlocal active_debt_id, selected_type, selected_date_str, operation_mode, stored_amount
        operation_mode = None
        stored_amount = 0.0
        amount_input.hint_text = "المبلغ"
        btn_quick_add.style = ft.ButtonStyle(color="#ec407a", bgcolor=ft.colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(color="#e0e0e0", width=1))
        btn_quick_sub.style = ft.ButtonStyle(color="#607d8b", bgcolor=ft.colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(color="#e0e0e0", width=1))

        if edit_id:
            active_debt_id = edit_id
            name_input.value = name
            amount_input.value = f"{amount:g}"
            btn_save.text = "تحديث"
            update_type_buttons(dtype)
            btn_quick_add.visible = True
            btn_quick_sub.visible = True
            if due_date:
                selected_date_str = due_date
                btn_date_picker.text = f"تاريخ السداد: {selected_date_str}"
                try: date_picker.value = datetime.strptime(selected_date_str, '%Y-%m-%d')
                except: pass
            else:
                selected_date_str = None
                btn_date_picker.text = "تاريخ السداد"
                date_picker.value = None
        else:
            active_debt_id = None
            name_input.value = ""
            amount_input.value = ""
            btn_save.text = "حفظ"
            btn_date_picker.text = "تاريخ السداد"
            selected_date_str = None
            date_picker.value = None
            update_type_buttons("madin")
            btn_quick_add.visible = False
            btn_quick_sub.visible = False
            
        # نفتح الكيان مباشرة دون استدعاء صفحة الـ dialog الافتراضية للويب
        add_dialog.open = True
        page.update()

    def build_debt_card(debt_id, name, amount, currency, db_days_passed, db_days_left, debt_type, record_date, due_date):
        today_now = datetime.now()
        today_pure = date(today_now.year, today_now.month, today_now.day)
        if record_date:
            try:
                r_parts = [int(x) for x in record_date.split(' ')[0].split('-')]
                r_pure = date(r_parts[0], r_parts[1], r_parts[2])
            except: r_pure = today_pure
        else: r_pure = today_pure
            
        if due_date:
            try:
                d_parts = [int(x) for x in due_date.split(' ')[0].split('-')]
                d_pure = date(d_parts[0], d_parts[1], d_parts[2])
            except: d_pure = today_pure
        else: d_pure = today_pure
        
        calc_passed = (today_pure - r_pure).days
        calc_left = (d_pure - today_pure).days
        days_passed = calc_passed if calc_passed >= 0 else 0
        days_left = calc_left if calc_left >= 0 else 0
        is_completed = debt_type in ["madin_done", "adin_done"]

        if is_completed:
            sub_info_control = ft.Row(controls=[ft.Icon(name=ft.icons.CHECK_CIRCLE_ROUNDED, color="#4caf50", size=15), ft.Text("تم السداد بالكامل", size=12, color="#4caf50", text_align=ft.TextAlign.RIGHT)], spacing=4, alignment=ft.MainAxisAlignment.START)
        else:
            sub_info_control = ft.Text(f"مضى {days_passed} يوم ومتبقي {days_left} يوم للسداد", size=12, color="#757575", text_align=ft.TextAlign.RIGHT)

        formatted_amount = f"{amount:,.2f}".rstrip('0').rstrip('.') if amount % 1 != 0 else f"{int(amount):,}"

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(controls=[ft.Text(name, size=16, color="#b06a7b" if not is_completed else "#9e9e9e", weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT), ft.Text(f"{formatted_amount} {currency}", size=15, color="#d4af37" if not is_completed else "#9e9e9e", weight=ft.FontWeight.W_600, text_align=ft.TextAlign.RIGHT), sub_info_control], horizontal_alignment=ft.CrossAxisAlignment.START, spacing=4, expand=True),
                    ft.IconButton(icon=ft.icons.DELETE_ROUNDED, icon_color=ft.colors.PINK_200, on_click=lambda e: show_confirm_dialog(debt_id)),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ), bgcolor=ft.colors.WHITE, padding=15, border_radius=10, margin=ft.margin.only(bottom=10, left=15, right=15), on_click=lambda e: open_add_dialog_fast(debt_id, name, amount, debt_type, due_date)
        )

    madin_container = ft.Container(expand=True)
    adin_container = ft.Container(expand=True)
    madin_list = ft.ListView(expand=True, spacing=0, padding=ft.padding.only(top=10))
    adin_list = ft.ListView(expand=True, spacing=0, padding=ft.padding.only(top=10))
    madin_completed_list = ft.ListView(expand=True, spacing=0, padding=ft.padding.only(top=10))
    adin_completed_list = ft.ListView(expand=True, spacing=0, padding=ft.padding.only(top=10))
    completed_items_container = ft.Container(expand=True)

    empty_view = ft.Container(content=ft.Column(controls=[ft.Container(content=ft.Icon(name=ft.icons.CHECK, color=ft.colors.WHITE, size=20), alignment=ft.alignment.center, width=30, height=30, bgcolor="#bdbdbd", shape=ft.BoxShape.CIRCLE), ft.Container(height=1), ft.Text("قائمتك فارغة", color="#bdbdbd", size=13, weight=ft.FontWeight.W_200)], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER), expand=True)

    total_madin_text = ft.Text("0", size=28, color=ft.colors.WHITE, weight=ft.FontWeight.BOLD, font_family="num_font")
    total_adin_text = ft.Text("0", size=28, color=ft.colors.WHITE, weight=ft.FontWeight.BOLD, font_family="num_font")

    def on_nav_change(e):
        nonlocal current_nav_index
        current_nav_index = e.control.selected_index
        content_container.content = tabs_content[current_nav_index]
        page.update()

    def refresh_ui_data():
        nonlocal current_completed_view, current_nav_index
        madin_data = get_debts('madin')
        count_madin = len(madin_data) if madin_data else 0
        if not madin_data: madin_container.content = empty_view
        else:
            madin_list.controls = [build_debt_card(*debt) for debt in madin_data]
            madin_container.content = madin_list

        adin_data = get_debts('adin')
        count_adin = len(adin_data) if adin_data else 0
        if not adin_data: adin_container.content = empty_view
        else:
            adin_list.controls = [build_debt_card(*debt) for debt in adin_data]
            adin_container.content = adin_list
        
        count_madin_done = get_debts_count('madin_done')
        count_adin_done = get_debts_count('adin_done')
        count_total_done = count_madin_done + count_adin_done
        btn_comp_madin.text = f"المدينين ( {count_madin_done} )"
        btn_comp_adin.text = f"الدائنين ( {count_adin_done} )"
        
        if current_completed_view == "madin_done":
            completed_madin_data = get_debts('madin_done')
            if not completed_madin_data: completed_items_container.content = empty_view
            else:
                madin_completed_list.controls = [build_debt_card(*d) for d in completed_madin_data]
                completed_items_container.content = madin_completed_list
        else:
            completed_adin_data = get_debts('adin_done')
            if not completed_adin_data: completed_items_container.content = empty_view
            else:
                adin_completed_list.controls = [build_debt_card(*d) for d in completed_adin_data]
                completed_items_container.content = adin_completed_list
            
        total_madin_text.value = get_total_amount('madin')
        total_adin_text.value = get_total_amount('adin')

        badge_alignment = ft.alignment.top_right
        badge_offset = ft.Offset(15, -6)
        icon_madin = ft.Badge(content=ft.Icon(ft.icons.ASSIGNMENT_IND_ROUNDED), text=str(count_madin), bgcolor="#ec407a", text_color=ft.colors.WHITE, alignment=badge_alignment, offset=badge_offset) if count_madin > 0 else ft.Icon(ft.icons.ASSIGNMENT_IND_ROUNDED)
        icon_done = ft.Badge(content=ft.Icon(ft.icons.CHECK_CIRCLE_ROUNDED), text=str(count_total_done), bgcolor="#4caf50", text_color=ft.colors.WHITE, alignment=badge_alignment, offset=badge_offset) if count_total_done > 0 else ft.Icon(ft.icons.CHECK_CIRCLE_ROUNDED)
        icon_adin = ft.Badge(content=ft.Icon(ft.icons.SUPERVISOR_ACCOUNT_ROUNDED), text=str(count_adin), bgcolor="#ec407a", text_color=ft.colors.WHITE, alignment=badge_alignment, offset=badge_offset) if count_adin > 0 else ft.Icon(ft.icons.SUPERVISOR_ACCOUNT_ROUNDED)

        page.navigation_bar = ft.NavigationBar(
            selected_index=current_nav_index, on_change=on_nav_change, bgcolor="#f8f9fa",
            destinations=[
                ft.NavigationDestination(icon_content=icon_madin, label="مدين منهم"),
                ft.NavigationDestination(icon_content=icon_done, label="مكتمل"),
                ft.NavigationDestination(icon_content=icon_adin, label="أدين لهم"),
            ]
        )
        page.update()

    def switch_completed_tab(e):
        nonlocal current_completed_view
        if "الدائنين" in e.control.text:
            current_completed_view = "adin_done"
            btn_comp_adin.style = ft.ButtonStyle(bgcolor="#ec407c", color=ft.colors.WHITE, shape=ft.RoundedRectangleBorder(radius=10))
            btn_comp_madin.style = ft.ButtonStyle(bgcolor=ft.colors.WHITE, color="#ec407c", shape=ft.RoundedRectangleBorder(radius=10))
            completed_adin_data = get_debts('adin_done')
            if not completed_adin_data: completed_items_container.content = empty_view
            else:
                adin_completed_list.controls = [build_debt_card(*d) for d in completed_adin_data]
                completed_items_container.content = adin_completed_list
        else:
            current_completed_view = "madin_done"
            btn_comp_madin.style = ft.ButtonStyle(bgcolor="#ec407c", color=ft.colors.WHITE, shape=ft.RoundedRectangleBorder(radius=10))
            btn_comp_adin.style = ft.ButtonStyle(bgcolor=ft.colors.WHITE, color="#ec407c", shape=ft.RoundedRectangleBorder(radius=10))
            completed_madin_data = get_debts('madin_done')
            if not completed_madin_data: completed_items_container.content = empty_view
            else:
                madin_completed_list.controls = [build_debt_card(*d) for d in completed_madin_data]
                completed_items_container.content = madin_completed_list
        page.update()

    btn_comp_madin = ft.TextButton(text="المدينين ( 0 )", style=ft.ButtonStyle(bgcolor="#ec407c", color=ft.colors.WHITE, shape=ft.RoundedRectangleBorder(radius=10)), expand=True, on_click=switch_completed_tab)
    btn_comp_adin = ft.TextButton(text="الدائنين ( 0 )", style=ft.ButtonStyle(bgcolor=ft.colors.WHITE, color="#ec407c", shape=ft.RoundedRectangleBorder(radius=10)), expand=True, on_click=switch_completed_tab)

    completed_page_layout = ft.Column(controls=[ft.Container(content=ft.Row(controls=[btn_comp_madin, btn_comp_adin], spacing=12, alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=ft.padding.only(left=15, right=15, top=12, bottom=12), bgcolor=ft.colors.WHITE), completed_items_container], expand=True, spacing=0)

    tabs_content = [ft.Column(controls=[madin_container], expand=True), completed_page_layout, ft.Column(controls=[adin_container], expand=True)]
    content_container = ft.Container(content=tabs_content[0], expand=True)

    header = ft.Container(content=ft.Column(controls=[ft.Row(controls=[ft.Column([ft.Text("رصيد المدينين", color=ft.colors.WHITE70, size=12), total_madin_text], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True), ft.Column([ft.Text("رصيد الدائنين", color=ft.colors.WHITE70, size=12), total_adin_text], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)], alignment=ft.MainAxisAlignment.SPACE_AROUND)], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5), bgcolor="#ec407a", padding=ft.padding.only(top=30, bottom=20, left=10, right=10))

    fab = ft.FloatingActionButton(content=ft.Icon(name=ft.icons.ADD, color="#ec407a"), bgcolor=ft.colors.WHITE, shape=ft.RoundedRectangleBorder(radius=15), on_click=lambda e: open_add_dialog_fast())

    current_step = 0
    steps_data = [
        {"icon": ft.icons.ACCOUNT_BALANCE_WALLET_ROUNDED, "title": "إدارة ديونك بسهولة", "desc": "الترابي بزنس هو تطبيق مثالي لتسجيل الديون ومتابعة المبالغ المستحقة لك أو عليك بدقة وبأمان."},
        {"icon": ft.icons.ALARM_ROUNDED, "title": "تنبيه بمواعيد السداد", "desc": "تابع كم يوماً مضى وكم يوماً متبقياً على موعد سداد كل دين لضمان الالتزام الزمني."},
        {"icon": ft.icons.SECURITY_ROUNDED, "title": "بياناتك آمنة محلياً", "desc": "يتم حفظ كافة السجلات بشكل آمن تماماً داخل جهازك لتصل إليها في أي وقت بدون إنترنت."}
    ]

    icon_display = ft.Icon(name=steps_data[0]["icon"], size=100, color="#ec407a")
    title_display = ft.Text(steps_data[0]["title"], size=24, weight=ft.FontWeight.BOLD, color="#b06a7b")
    desc_display = ft.Text(steps_data[0]["desc"], size=14, color="#757575", text_align=ft.TextAlign.CENTER)
    dots_row = ft.Row([ft.Container(width=10, height=10, bgcolor="#ec407a", border_radius=5), ft.Container(width=10, height=10, bgcolor="#e0e0e0", border_radius=5), ft.Container(width=10, height=10, bgcolor="#e0e0e0", border_radius=5)], alignment=ft.MainAxisAlignment.CENTER, spacing=8)

    def next_step(e):
        nonlocal current_step
        if current_step < 2:
            current_step += 1
            icon_display.name = steps_data[current_step]["icon"]
            title_display.value = steps_data[current_step]["title"]
            desc_display.value = steps_data[current_step]["desc"]
            for idx, dot in enumerate(dots_row.controls):
                dot.bgcolor = "#ec407a" if idx == current_step else "#e0e0e0"
            if current_step == 2: btn_next.text = "ابدأ الآن"
            page.update()
        else: start_app_after_onboarding(None)

    def start_app_after_onboarding(e):
        set_onboarding_completed()
        page.controls.clear()
        build_main_ui()

    btn_next = ft.ElevatedButton("التالي", bgcolor="#ec407a", color=ft.colors.WHITE, width=150, height=45, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)), on_click=next_step)
    btn_skip = ft.TextButton("تخطى", style=ft.ButtonStyle(color="#757575"), on_click=start_app_after_onboarding)

    def build_onboarding_ui():
        page.clean()
        page.bgcolor = ft.colors.WHITE
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Container(content=btn_skip, alignment=ft.alignment.top_left, padding=ft.padding.only(left=10, top=10)),
                    ft.Container(content=ft.Column([icon_display, ft.Container(height=10), title_display, ft.Container(height=5), desc_display], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER), expand=True, padding=40),
                    ft.Container(content=ft.Column([dots_row, ft.Container(height=15), ft.Row([btn_next], alignment=ft.MainAxisAlignment.CENTER)], horizontal_alignment=ft.CrossAxisAlignment.CENTER), padding=ft.padding.only(bottom=40))
                ]), expand=True
            )
        )
        page.update()

    def build_main_ui():
        page.bgcolor = "#f5f5f5"
        page.floating_action_button = fab
        page.add(header, content_container)
        refresh_ui_data()

    def check_routing_after_splash():
        if check_onboarding_status(): build_main_ui()
        else: build_onboarding_ui()

    show_splash_screen(page, on_timeout_callback=check_routing_after_splash)

ft.app(target=main, assets_dir="assets")
