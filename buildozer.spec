[app]

title = الترابي بزنس

package.name = alturabibusiness
package.domain = com.alamin

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,db

version = 0.1
requirements = python3,kivy,kivymd,arabic-reshaper,python-bidi
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
 

#presplash.filename = %(source.dir)s/data/alturabi.png
#icon.filename = %(source.dir)s/data/icon.png

orientation = portrait
fullscreen = 0


# --------------------------------
# Android
# --------------------------------

android.api = 33
android.minapi = 21
android.ndk_api = 21
android.archs = arm64-v8a, armeabi-v7a


# --------------------------------
# Python / Kivy
# --------------------------------

osx.python_version = 3
osx.kivy_version = 2.3.1


# --------------------------------
# Buildozer
# --------------------------------

log_level = 2
warn_on_root = 1