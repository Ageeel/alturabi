# main.py
import sqlite3
import flet as ft
# استيراد دالة شاشة الترحيب من الملف المنفصل
from splash import show_splash_screen 

def init_db():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'SDG',
            days_passed INTEGER DEFAULT 0,
            days_left INTEGER DEFAULT 0,
            type TEXT NOT NULL
        )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM debts")
    if cursor.fetchone()[0] == 0:
        sample_data = [
            ('سكر وزيت ودقيق', 8000, 'SDG', 2, 15, 'madin'),
            ('ست العطور', 600, 'SDG', 2, 4, 'madin'),
            ('بتاع الطعمية', 9000, 'SDG', 2, 8, 'madin'),
            ('حق الموية والغاز', 45000, 'SDG', 2, 7, 'madin'),
            ('هنادي محمد', 1000, 'SDG', 2, 13, 'madin'),
        ]
        cursor.executemany("""
            INSERT INTO debts (name, amount, currency, days_passed, days_left, type)
            VALUES (?, ?, ?, ?, ?, ?)
        """, sample_data)
        conn.commit()
    conn.close()

def get_debts(debt_type):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, amount, currency, days_passed, days_left FROM debts WHERE type=?", (debt_type,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def main(page: ft.Page):
    init_db()
    
    # إعدادات الخطوط والصفحة (تبدأ بخلفية بيضاء لتلائم شاشة الترحيب)
    page.fonts = {
        "font": "font/ar.ttf",
        "num_font": "font/num_font.ttf"
    }
    page.theme = ft.Theme(font_family="font")
    page.theme_mode = ft.ThemeMode.LIGHT
    page.rtl = True
    page.padding = 0
    page.bgcolor = "#ffffff"

    # --- إدارة نافذة التأكيد ---
    def close_dlg(e):
        confirm_dialog.open = False
        page.update()

    def delete_confirmed(name):
        print(f"تم تأكيد حذف: {name}")
        confirm_dialog.open = False
        page.update()

    confirm_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("تأكيد الحذف"),
        content=ft.Text("هل أنت متأكد أنك تريد حذف السجل؟"),
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def show_confirm_dialog(name):
        confirm_dialog.actions = [
            ft.TextButton("حذف", on_click=lambda _: delete_confirmed(name)),
            ft.TextButton("إلغاء", on_click=close_dlg),
        ]
        page.dialog = confirm_dialog
        confirm_dialog.open = True
        page.update()
    # ---------------------------

    # --- نافذة إضافة دين جديد ---
    def close_add_dlg(e):
        add_dialog.open = False
        page.update()

    def save_new_debt(e):
        print(f"النوع: {selected_type}, الاسم: {name_input.value}, المبلغ: {amount_input.value}")
        add_dialog.open = False
        page.update()

    selected_type = "madin"

    def change_type(e):
        nonlocal selected_type
        if e.control.text == "دائنون":
            selected_type = "adin"
            btn_adin.style = ft.ButtonStyle(
                color="#ec407a",
                bgcolor="#fce4ec",
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(color="#ec407a", width=1.5)
            )
            btn_madin.style = ft.ButtonStyle(
                color="#ec407a",
                bgcolor=ft.colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(color="#e0e0e0", width=1)
            )
        else:
            selected_type = "madin"
            btn_madin.style = ft.ButtonStyle(
                color="#ec407a",
                bgcolor="#fce4ec",
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(color="#ec407a", width=1.5)
            )
            btn_adin.style = ft.ButtonStyle(
                color="#ec407a",
                bgcolor=ft.colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(color="#e0e0e0", width=1)
            )
        page.update()

    btn_adin = ft.OutlinedButton(
        text="دائنون",
        style=ft.ButtonStyle(
            color="#ec407a",
            bgcolor=ft.colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=8),
            side=ft.BorderSide(color="#e0e0e0", width=1)
        ),
        width=110,
        on_click=change_type
    )

    btn_madin = ft.OutlinedButton(
        text="مدينون",
        style=ft.ButtonStyle(
            color="#ec407a",
            bgcolor="#fce4ec",
            shape=ft.RoundedRectangleBorder(radius=8),
            side=ft.BorderSide(color="#ec407a", width=1.5)
        ),
        width=110,
        on_click=change_type
    )

    name_input = ft.TextField(
        label="الإسم", 
        border_color="#e0e0e0", 
        text_align=ft.TextAlign.RIGHT, 
        width=240, height=50
    )
    
    amount_input = ft.TextField(
        label="10000", 
        border_color="#e0e0e0", 
        text_align=ft.TextAlign.RIGHT, 
        keyboard_type=ft.KeyboardType.NUMBER, 
        width=240, height=50
    )

    add_dialog = ft.AlertDialog(
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[btn_adin, btn_madin], 
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                        width=240
                    ),
                    ft.Container(height=8),
                    name_input,
                    amount_input,
                    ft.OutlinedButton(
                        text="تاريخ السداد", 
                        style=ft.ButtonStyle(
                            color="#ec407a",
                            bgcolor=ft.colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=8),
                            side=ft.BorderSide(color="#ec407a", width=1)
                        ),
                        width=240
                    ),
                    ft.Container(height=12),
                    ft.ElevatedButton(
                        text="حفظ",
                        bgcolor="#ec407a",
                        color=ft.colors.WHITE,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                        width=240,
                        on_click=save_new_debt
                    )
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

    def show_add_dialog(e):
        page.dialog = add_dialog
        add_dialog.open = True
        page.update()
    # ---------------------------

    def build_debt_card(name, amount, currency, days_passed, days_left):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text(name, size=16, color="#b06a7b", weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT),
                            ft.Text(f"{int(amount)} {currency}", size=15, color="#d4af37", weight=ft.FontWeight.W_600, text_align=ft.TextAlign.RIGHT),
                            ft.Text(f"مضى {days_passed} يوم ومتبقي {days_left} يوم للسداد", size=12, color="#757575", text_align=ft.TextAlign.RIGHT),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.START,
                        spacing=4,
                        expand=True
                    ),
                    ft.IconButton(
                        icon=ft.icons.DELETE_ROUNDED,
                        icon_color=ft.colors.RED_400,
                        on_click=lambda e: show_confirm_dialog(name)
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            bgcolor=ft.colors.WHITE,
            padding=15,
            border_radius=10,
            margin=ft.margin.only(bottom=10, left=15, right=15)
        )

    # بناء قوائم العناصر الأساسية
    madin_list = ft.ListView(expand=True, spacing=0, padding=ft.padding.only(top=10))
    adin_list = ft.ListView(expand=True, spacing=0, padding=ft.padding.only(top=10))

    for debt in get_debts('madin'):
        madin_list.controls.append(build_debt_card(*debt))
        
    for debt in get_debts('adin'):
        adin_list.controls.append(build_debt_card(*debt))

    tabs_content = [
        ft.Column(controls=[madin_list], expand=True),
        ft.Column(controls=[madin_list], expand=True),
        ft.Column(controls=[adin_list], expand=True)
    ]

    content_container = ft.Container(
        content=tabs_content[0],
        expand=True
    )

    def on_nav_change(e):
        clicked_index = e.control.selected_index
        content_container.content = tabs_content[clicked_index]
        page.update()

    # تحضير عناصر الواجهة ليتم استدعاؤها لاحقاً
    navigation_bar = ft.NavigationBar(
        selected_index=0, 
        on_change=on_nav_change,
        bgcolor="#f8f9fa",
        destinations=[
            ft.NavigationDestination(icon=ft.icons.ACCOUNT_BALANCE_ROUNDED, label="مدين منهم"),
            ft.NavigationDestination(icon=ft.icons.ACCOUNT_BALANCE_OUTLINED, label="المكتملة"),
            ft.NavigationDestination(icon=ft.icons.ACCOUNT_BALANCE_OUTLINED, label="أدين لهم"),
        ]
    )

    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.Column([ft.Text("63,600", size=28, color=ft.colors.WHITE, weight=ft.FontWeight.BOLD, font_family="num_font")], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                ft.Column([ft.Text("198,000", size=28, color=ft.colors.WHITE, weight=ft.FontWeight.BOLD, font_family="num_font")], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND
        ),
        bgcolor="#ec407a",
        padding=ft.padding.only(top=40, bottom=20, left=10, right=10),
    )

    fab = ft.FloatingActionButton(
        icon=ft.icons.ADD,
        bgcolor="#ec407a",
        shape=ft.RoundedRectangleBorder(radius=15),
        on_click=show_add_dialog
    )

    # دالة لبناء واجهة تطبيق "الترابي لإدارة الديون" بعد إغلاق شاشة الترحيب
    def build_main_ui():
        page.navigation_bar = navigation_bar
        page.floating_action_button = fab
        page.add(header, content_container)
        page.update()

    # تشغيل شاشة الترحيب المستوردة وتمرير الواجهة الرئيسية لها لتعمل بعد انتهاء الـ 3 ثواني
    show_splash_screen(page, on_timeout_callback=build_main_ui)

ft.app(target=main, view=ft.AppView.WEB_BROWSER, assets_dir="assets")
