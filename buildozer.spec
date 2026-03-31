[app]

title = الترابي بزنس
package.name = alturabibusiness
package.domain = com.alamin

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,db

version = 0.1

requirements = python3,kivy==2.3.0,kivymd,pillow,arabic-reshaper,python-bidi,sqlite3

android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

orientation = portrait
fullscreen = 0

# --------------------------------
# Android
# --------------------------------

android.api = 30
android.minapi = 21
android.sdk = 30
android.ndk = 25b
android.ndk_api = 21

# مهم جداً
android.build_tools_version = 30.0.3

# --------------------------------
# Python / Kivy
# --------------------------------

osx.python_version = 3

# --------------------------------
# تحسينات
# --------------------------------

android.enable_androidx = True
android.add_libs_armeabi_v7a = libs/*.so

# --------------------------------
# Buildozer
# --------------------------------

log_level = 2
warn_on_root = 1
