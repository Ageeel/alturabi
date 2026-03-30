[app]

title = الترابي بزنس

package.name = alturabibusiness
package.domain = com.alamin

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,db

version = 0.1
requirements = python3,hostpython3,kivy,kivymd,pillow,arabic-reshaper,python-bidi
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
 

#presplash.filename = %(source.dir)s/data/alturabi.png
#icon.filename = %(source.dir)s/data/icon.png

orientation = portrait
fullscreen = 0


# --------------------------------
# Android
# --------------------------------


android.api = 29
android.sdk = 29
android.ndk = 25b


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
