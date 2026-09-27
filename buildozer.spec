[app]
title = Pendu Royal
package.name = penduroyal
package.domain = org.penduroyal
source.dir = .
source.include_exts = py,kv,png,json,ttf,wav
# ni les originaux haute résolution, ni les outils, ni les tests dans l'APK
source.exclude_dirs = assets_src,tools,tests,bin,.buildozer,venv,.venv,__pycache__
version = 2.0.0
# charset_normalizer épinglé : la 3.5 a des paquets Android que python-for-android 2026.05 installe mal
requirements = python3,kivy==2.3.1,charset_normalizer==3.3.2
orientation = portrait
fullscreen = 0
icon.filename = %(source.dir)s/assets/images/png/icon.png
presplash.filename = %(source.dir)s/assets/images/png/pendu_hero.png
android.presplash_color = #120B07
android.permissions = VIBRATE
android.api = 34
android.minapi = 24
# 64 bits ET 32 bits : beaucoup de téléphones d'entrée de gamme tournent sous Android 32 bits
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
