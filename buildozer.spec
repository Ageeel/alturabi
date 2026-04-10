[app]

# (str) Title of your application
title = My Arabic App

# (str) Package name
package.name = myarabicapp

# (str) Package domain (needed for android packaging)
package.domain = org.test

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,ttf

# (list) Application requirements
# تم إضافة المكتبات المطلوبة هنا مع التأكد من تسمية python-bidi بشكل صحيح
requirements = python3,kivy,kivymd,arabic_reshaper,python-bidi

# (str) Custom source folders for requirements
# source.nodes =

# (str) Presplash of the application
# تم تعطيل شاشة التوقف بناءً على طلبك
# presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
# icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientations (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (list) Permissions
# أذونات اختيارية إذا كنت تريد حفظ قاعدة البيانات في ذاكرة الهاتف
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, INTERNET

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (int) Android SDK version to use
# android.sdk = 33

# (str) Android NDK version to use
# android.ndk = 25b

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (str) Android entry point, default is to use start.py
# android.entrypoint = default

# (list) List of Java .jar files to add to the libs so that pyjnius can access
# their classes. Don't add jar files that you anticipate joining via 
# gradle dependencies.
# android.add_jars = foo.jar,bar.jar,path/to/more/*.jar

# (list) Gradle dependencies
# android.gradle_dependencies =
