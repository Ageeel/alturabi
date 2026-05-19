# splash.py
import asyncio
import flet as ft

def show_splash_screen(page: ft.Page, on_timeout_callback):
    """
    دالة تقوم بعرض شاشة الترحيب ثم الانتقال للواجهة الرئيسية بعد انتهاء الوقت
    """
    # تصميم مكونات شاشة الترحيب
    splash_content = ft.Container(
        content=ft.Column(
            controls=[
                ft.Image(
                    src="icon.png",  # يجب أن يكون داخل مجلد assets
                    width=260,
                    height=260,
                    fit=ft.ImageFit.CONTAIN
                ),
                ft.Container(height=15),
                ft.ProgressRing(color="#ec407a", width=35, height=35, stroke_width=3.5),
                ft.Container(height=5),
                ft.Text("جاري التحميل...", color="#b06a7b", size=15, weight=ft.FontWeight.W_500)
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        expand=True,
        alignment=ft.alignment.center,
        bgcolor=ft.colors.WHITE
    )

    async def load_and_transition():
        # 1. عرض شاشة الترحيب
        page.add(splash_content)
        
        # 2. الانتظار لمدة 3 ثواني
        await asyncio.sleep(3)
        
        # 3. تنظيف الشاشة وتغيير الخلفية للوضع الأصلي للتطبيق
        page.controls.clear()
        page.bgcolor = "#f5f5f5" 
        
        # 4. تشغيل الدالة (Callback) المسؤولة عن بناء الواجهة الرئيسية في ملف main.py
        on_timeout_callback()

    # تشغيل الانتقال
    asyncio.run(load_and_transition())
