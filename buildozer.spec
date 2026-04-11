[app]
# (str) Title of your application
title = MyKivyMDApp

# (str) Package name
package.name = mykivymdapp

# (str) Package domain (needed for android packaging)
package.domain = org.test

# (str) Source code where the main.py is located
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json

# (list) Application requirements
# تأكد من وضع الإصدارات لضمان الاستقرار
requirements = python3, kivy==2.3.0, kivymd==1.2.0, pillow, requests, charset-normalizer, idna, urllib3

# (str) Custom source folders for requirements
# (list) Garden requirements
# (str) Presplash of the application
# (str) Icon of the application
# (str) Supported orientation (landscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

# (int) Target Android API, should be as high as possible.
# حالياً 33 أو 34 هو المطلوب لمتجر جوجل بلاي
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (str) Android SDK directory (if empty, it will be automatically downloaded)
# android.sdk_path = 

# (str) Android NDK directory (if empty, it will be automatically downloaded)
# android.ndk_path = 

# (list) Android architectures to build for
# ضروري جداً لدعم الهواتف الحديثة 64-bit
android.archs = arm64-v8a, armeabi-v7a

# (bool) enables Android auto backup
android.allow_backup = True

# (str) The format used to package the app for release mode (aab or apk)
# استخدم aab للرفع على المتجر و apk للتجربة الشخصية
android.release_artifact = apk

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = off, 1 = on)
warn_on_root = 1
