import sqlite3
from datetime import datetime, date, timedelta
import flet as ft
import os  # تم إضافة مكتبة os لإدارة المسارات بشكل آمن على أندرويد
from splash import show_splash_screen 

# دالة لتحديد المسار الصحيح لقاعدة البيانات لتجنب مشاكل الصلاحيات في أندرويد
def get_db_connection():
    # سيتم إنشاء قاعدة البيانات في نفس مجلد تشغيل التطبيق بشكل آمن
    db_path = os.path.join(os.path.dirname(__file__), "data.db")
    return sqlite3.connect(db_path)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'SDG',
            days_passed INTEGER DEFAULT 0,
            days_left INTEGER DEFAULT 0,
            type TEXT NOT NULL,
            record_date TEXT,
            due_date TEXT
        )
    """)
    
    try:
        cursor.execute("SELECT record_date FROM debts LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE debts ADD COLUMN record_date TEXT")
        
    try:
        cursor.execute("SELECT due_date FROM debts LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE debts ADD COLUMN due_date TEXT")

    conn.commit()
    conn.close()

def get_debts(debt_type):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, amount, currency, days_passed, days_left, type, record_date, due_date FROM debts WHERE type=?", (debt_type,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_debts_count(debt_type):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM debts WHERE type=?", (debt_type,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_total_amount(debt_type):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(amount) FROM debts WHERE type=?", (debt_type,))
    total = cursor.fetchone()[0]
    conn.close()
    return f"{int(total):,}" if total else "0"

def main(page: ft.Page):
    init_db()
    
    page.fonts = {
        "font": "font/ar.ttf",
        "num_font": "font/num_font.ttf"
    }
    
    page.theme = ft.Theme(
        font_family="font",
        color_scheme=ft.ColorScheme(
            primary="#f48fb1",       
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

    def close_dlg(e):
        confirm_dialog.open = False
        page.update()

    def delete_confirmed(debt_id):
        nonlocal active_debt_id
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM debts WHERE id=?", (debt_id,))
        conn.commit()
        conn.close()
        
        confirm_dialog.open = False
        active_debt_id = None
        refresh_ui_data()

    confirm_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("تأكيد الحذف", text_align=ft.TextAlign.CENTER),
        content=ft.Text("هل أنت متأكد أنك تريد حذف السجل؟", text_align=ft.TextAlign.CENTER),
        actions_alignment=ft.MainAxisAlignment.CENTER,
    )

    def show_confirm_dialog(debt_id):
        confirm_dialog.actions = [
            ft.TextButton("حذف", on_click=lambda _: delete_confirmed(debt_id)),
            ft.TextButton("إلغاء", on_click=close_dlg),
        ]
        page.dialog = confirm_dialog
        confirm_dialog.open = True
        page.update()

    def save_new_debt(e):
        nonlocal selected_date_str, active_debt_id, selected_type, stored_amount, operation_mode
        
        if not name_input.value or not amount_input.value:
            return
            
        try:
            input_amount = float(amount_input.value)
        except ValueError:
            return  
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        today_str = datetime.now().strftime('%Y-%m-%d')
        week_from_now_str = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        final_due_date = selected_date_str if selected_date_str else week_from_now_str

        target_type = selected_type
        if active_debt_id:
            if operation_mode == "add":
                final_amount = stored_amount + input_amount
            elif operation_mode == "subtract":
                final_amount = stored_amount - input_amount
                if final_amount < 0: final_amount = 0.0
            else:
                final_amount = input_amount
        else:
            final_amount = input_amount

        if final_amount == 0:
            if target_type in ["madin", "madin_done"]:
                target_type = "madin_done"
            elif target_type in ["adin", "adin_done"]:
                target_type = "adin_done"
        else:
            if target_type == "madin_done":
                target_type = "madin"
            elif target_type == "adin_done":
                target_type = "adin"

        if active_debt_id:
            cursor.execute("""
                UPDATE debts 
                SET name=?, amount=?, type=?, due_date=?
                WHERE id=?
            """, (name_input.value, final_amount, target_type, final_due_date, active_debt_id))
        else:         
            cursor.execute("""
                INSERT INTO debts (name, amount, currency, type, record_date, due_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name_input.value, final_amount, "SDG", target_type, today_str, final_due_date))
            
        conn.commit()
        conn.close()
        
        add_dialog.open = False
        
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

    date_picker = ft.DatePicker(
        on_change=handle_date_change,
        help_text="اختر تاريخ السداد",
        confirm_text="موافق",
        cancel_text="إلغاء"
    )
    page.overlay.append(date_picker)

    def change_type(e):
        update_type_buttons(e.control.text)
        page.update()

    def update_type_buttons(type_text):
        nonlocal selected_type
        if type_text in ["دائنون", "adin", "adin_done"]:
            selected_type = "adin"
            btn_adin.style = ft.ButtonStyle(color="#ec407a", bgcolor="#fce4ec", shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(color="#ec407a", width=1.5))
            btn_madin.style = ft.ButtonStyle(color="#ec407a", bgcolor=ft.colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(color="#e0e0e0", width=1))
        else:
            selected_type = "madin"
            btn_madin.style = ft.ButtonStyle(color="#ec407a", bgcolor="#fce4ec", shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(color="#ec407a", width=1.5))
            btn_adin.style = ft.ButtonStyle(color="#ec407a", bgcolor=ft.colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(color="#e0e0e0", width=1))

    def start_add_operation(e):
        nonlocal stored_amount, operation_mode
        try:
            stored_amount = float(amount_input.value) if amount_input.value else 0.0
        except ValueError:
            stored_amount = 0.0
        operation_mode = "add"
        amount_input.value = ""
        amount_input.label = f"المبلغ المراد إضافته لـ {int(stored_amount)}"
        btn_save.text = "تأكيد الإضافة +"
        
        btn_quick_add.style = ft.ButtonStyle(color="#ec407a", bgcolor="#fce4ec", shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(color="#ec407a", width=1.5))
        btn_quick_sub.style = ft.ButtonStyle(color="#607d8b", bgcolor=ft.colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(color="#e0e0e0", width=1))
        page.update()

    def start_subtract_operation(e):
        nonlocal stored_amount, operation_mode
        try:
            stored_amount = float(amount_input.value) if amount_input.value else 0.0
        except ValueError:
            stored_amount = 0.0
        operation_mode = "subtract"
        amount_input.value = ""
        amount_input.label = f"المبلغ المراد طرحه من {int(stored_amount)}"
        btn_save.text = "تأكيد الطرح -"
        
        btn_quick_sub.style = ft.ButtonStyle(color="#607d8b", bgcolor="#eceff1", shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(color="#607d8b", width=1.5))
        btn_quick_add.style = ft.ButtonStyle(color="#ec407a", bgcolor=ft.colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(color="#e0e0e0", width=1))
        page.update()

    btn_adin = ft.OutlinedButton(text="دائنون", style=ft.ButtonStyle(color="#ec407a", bgcolor=ft.colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(color="#e0e0e0", width=1)), width=110, on_click=change_type)
    btn_madin = ft.OutlinedButton(text="مدينون", style=ft.ButtonStyle(color="#ec407a", bgcolor="#fce4ec", shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(color="#ec407a", width=1.5)), width=110, on_click=change_type)

    name_input = ft.TextField(label="الإسم", border_color="#e0e0e0", text_align=ft.TextAlign.RIGHT, width=240, height=50)
    amount_input = ft.TextField(label="المبلغ", border_color="#e0e0e0", text_align=ft.TextAlign.RIGHT, keyboard_type=ft.KeyboardType.NUMBER, width=240, height=50)

    btn_quick_add = ft.OutlinedButton(text="إضافة +", style=ft.ButtonStyle(color="#ec407a", bgcolor=ft.colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(color="#e0e0e0", width=1)), width=110, on_click=start_add_operation, visible=False)
    btn_quick_sub = ft.OutlinedButton(text="طرح -", style=ft.ButtonStyle(color="#607d8b", bgcolor=ft.colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(color="#e0e0e0", width=1)), width=110, on_click=start_subtract_operation, visible=False)

    btn_date_picker = ft.OutlinedButton(
        text="تاريخ السداد", 
        style=ft.ButtonStyle(color="#ec407a", bgcolor=ft.colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(color="#ec407a", width=1)), 
        width=240,
        on_click=lambda _: date_picker.pick_date()
    )

    btn_save = ft.ElevatedButton(text="حفظ", bgcolor="#ec407a", color=ft.colors.WHITE, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)), width=240, on_click=save_new_debt)

    add_dialog = ft.AlertDialog(
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(controls=[btn_adin, btn_madin], alignment=ft.MainAxisAlignment.CENTER, spacing=10, width=240),
                    ft.Container(height=8),
                    name_input,
                    amount_input,
                    ft.Row(controls=[btn_quick_sub, btn_quick_add], alignment=ft.MainAxisAlignment.CENTER, spacing=10, width=240),
                    btn_date_picker,
                    ft.Container(height=12),
                    btn_save
                ],
                tight=True,
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            width=260,
            padding=ft.padding.all(5)
        ),
        shape=ft.RoundedRectangleBorder(radius=15)
    )
    
    page.overlay.append(add_dialog)

    def open_add_dialog_fast(edit_id=None, name="", amount=0, dtype="madin", due_date=None):
        nonlocal active_debt_id, selected_type, selected_date_str, operation_mode, stored_amount
        
        operation_mode = None
        stored_amount = 0.0
        amount_input.label = "المبلغ"
        
        btn_quick_add.style = ft.ButtonStyle(color="#ec407a", bgcolor=ft.colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(color="#e0e0e0", width=1))
        btn_quick_sub.style = ft.ButtonStyle(color="#607d8b", bgcolor=ft.colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(color="#e0e0e0", width=1))

        if edit_id:
            active_debt_id = edit_id
            name_input.value = name
            amount_input.value = str(int(amount))
            btn_save.text = "تحديث"
            update_type_buttons(dtype)
            
            btn_quick_add.visible = True
            btn_quick_sub.visible = True
            
            if due_date:
                selected_date_str = due_date
                btn_date_picker.text = f"تاريخ السداد: {selected_date_str}"
                try:
                    date_picker.value = datetime.strptime(selected_date_str, '%Y-%m-%d')
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
        sub_text = "تم السداد بالكامل ✓" if is_completed else f"مضى {days_passed} يوم ومتبقي {days_left} يوم للسداد"

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text(name, size=16, color="#b06a7b" if not is_completed else "#9e9e9e", weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT),
                            ft.Text(f"{int(amount)} {currency}", size=15, color="#d4af37" if not is_completed else "#9e9e9e", weight=ft.FontWeight.W_600, text_align=ft.TextAlign.RIGHT),
                            ft.Text(sub_text, size=12, color="#757575" if not is_completed else "#4caf50", text_align=ft.TextAlign.RIGHT),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.START,
                        spacing=4,
                        expand=True
                    ),
                    ft.IconButton(icon=ft.icons.DELETE_ROUNDED, icon_color=ft.colors.RED_400, on_click=lambda e: show_confirm_dialog(debt_id)),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            bgcolor=ft.colors.WHITE,
            padding=15,
            border_radius=10,
            margin=ft.margin.only(bottom=10, left=15, right=15),
            on_click=lambda e: open_add_dialog_fast(debt_id, name, amount, debt_type, due_date)
        )

    madin_container = ft.Container(expand=True)
    adin_container = ft.Container(expand=True)

    madin_list = ft.ListView(expand=True, spacing=0, padding=ft.padding.only(top=10))
    adin_list = ft.ListView(expand=True, spacing=0, padding=ft.padding.only(top=10))

    madin_completed_list = ft.ListView(expand=True, spacing=0, padding=ft.padding.only(top=10))
    adin_completed_list = ft.ListView(expand=True, spacing=0, padding=ft.padding.only(top=10))
    completed_items_container = ft.Container(expand=True)

    empty_view = ft.Container(
        content=ft.Column(
            controls=[
                ft.Container(
                    content=ft.Icon(name=ft.icons.CHECK, color=ft.colors.WHITE, size=20),
                    alignment=ft.alignment.center, width=30, height=30, bgcolor="#bdbdbd", shape=ft.BoxShape.CIRCLE,
                ),
                ft.Container(height=1),
                ft.Text("قائمتك فارغة", color="#bdbdbd", size=13, weight=ft.FontWeight.W_200)
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER
        ),
        expand=True
    )

    total_madin_text = ft.Text("0", size=28, color=ft.colors.WHITE, weight=ft.FontWeight.BOLD, font_family="num_font")
    total_adin_text = ft.Text("0", size=28, color=ft.colors.WHITE, weight=ft.FontWeight.BOLD, font_family="num_font")

    def refresh_ui_data():
        nonlocal current_completed_view
        
        madin_data = get_debts('madin')
        if not madin_data: madin_container.content = empty_view
        else:
            madin_list.controls = [build_debt_card(*debt) for debt in madin_data]
            madin_container.content = madin_list

        adin_data = get_debts('adin')
        if not adin_data: adin_container.content = empty_view
        else:
            adin_list.controls = [build_debt_card(*debt) for debt in adin_data]
            adin_container.content = adin_list
        
        count_madin_done = get_debts_count('madin_done')
        count_adin_done = get_debts_count('adin_done')
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

    completed_page_layout = ft.Column(
        controls=[
            ft.Container(content=ft.Row(controls=[btn_comp_madin, btn_comp_adin], spacing=12, alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=ft.padding.only(left=15, right=15, top=12, bottom=12), bgcolor=ft.colors.WHITE),
            completed_items_container
        ], expand=True, spacing=0
    )

    tabs_content = [
        ft.Column(controls=[madin_container], expand=True),
        completed_page_layout, 
        ft.Column(controls=[adin_container], expand=True)
    ]

    content_container = ft.Container(content=tabs_content[0], expand=True)

    def on_nav_change(e):
        content_container.content = tabs_content[e.control.selected_index]
        page.update()

    navigation_bar = ft.NavigationBar(
        selected_index=0, on_change=on_nav_change, bgcolor="#f8f9fa",
        destinations=[
            ft.NavigationDestination(icon=ft.icons.ACCOUNT_BALANCE_ROUNDED, label="مدين منهم"),
            ft.NavigationDestination(icon=ft.icons.CHECK_CIRCLE_ROUNDED, label="مكتمل"),
            ft.NavigationDestination(icon=ft.icons.ACCOUNT_BALANCE_OUTLINED, label="أدين لهم"),
        ]
    )

    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.Column([total_madin_text], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                ft.Column([total_adin_text], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
            ], alignment=ft.MainAxisAlignment.SPACE_AROUND
        ), bgcolor="#ec407a", padding=ft.padding.only(top=40, bottom=20, left=10, right=10),
    )

    fab = ft.FloatingActionButton(
        content=ft.Icon(name=ft.icons.ADD, color="#ec407a"), 
        bgcolor=ft.colors.WHITE, 
        shape=ft.RoundedRectangleBorder(radius=15), 
        on_click=lambda e: open_add_dialog_fast()
    )

    def build_main_ui():
        page.navigation_bar = navigation_bar
        page.floating_action_button = fab
        page.add(header, content_container)
        refresh_ui_data()

    show_splash_screen(page, on_timeout_callback=build_main_ui)

# التعديل هنا: إزالة فئة العرض المتصفح لتعمل بشكل طبيعي على أندرويد
ft.app(target=main, assets_dir="assets")
