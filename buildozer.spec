[app]

title = الترابي بزنس
package.name = alturabibusiness
package.domain = com.alamin

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,db

version = 0.1

# ❗ تم حذف hostpython3 لأنه يسبب مشاكل
requirements = python3,kivy==2.3.0,kivymd,pillow,arabic-reshaper,python-bidi,sqlite3

# صلاحيات
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# ملفات الأيقونة (اختياري)
# icon.filename = %(source.dir)s/data/icon.png
# presplash.filename = %(source.dir)s/data/alturabi.png

orientation = portrait
fullscreen = 0


# --------------------------------
# Android
# --------------------------------

# ✅ أفضل توافق
android.api = 30
android.minapi = 21
android.sdk = 30
android.ndk = 25b

# مهم لتفادي مشاكل
android.ndk_api = 21


# --------------------------------
# Python / Kivy
# --------------------------------

osx.python_version = 3

# --------------------------------
# تحسينات مهمة
# --------------------------------

# يمنع crash في بعض الأجهزة
android.enable_androidx = True

# دعم SQLite بشكل أفضل
android.add_libs_armeabi_v7a = libs/*.so

# تسجيل الأخطاء

warn_on_root = 1osx.python_version = 3

# --------------------------------
# Buildozer
# --------------------------------

log_level = 2
warn_on_root = 1
