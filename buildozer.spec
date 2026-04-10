[app]

# (str) Title of your application
title = My Arabic App

# (str) Package name
package.name = myarabicapp

# (str) Package domain (needed for android packaging)
package.domain = org.test

# (str) Source code where the main.py lives
source.dir = .

# (str) Version of your application (تمت إضافته لحل المشكلة الأخيرة)
version = 0.1

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,ttf

# (list) Application requirements
# تشمل المكتبات العربية وقاعدة البيانات المطلوبة
requirements = python3, kivy, kivymd, arabic_reshaper, python-bidi, sqlite3

# (str) Supported orientations (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (list) Permissions
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, INTERNET

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (bool) Enable AndroidX support. Required when using KivyMD.
android.enable_androidx = True

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a, armeabi-v7a

# (bool) copy library instead of making a libpython.so
android.copy_libs = 1

# --- تم إلغاء شاشة التوقف بناءً على طلبك ---
# presplash.filename = %(source.dir)s/data/presplash.png

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = off, 1 = on)
warn_on_root = 1
