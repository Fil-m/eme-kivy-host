[app]
title = EME Dynamic Host
package.name = eme_os
package.domain = org.eme
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0.0

# Requirements
requirements = python3,kivy,django,djangorestframework,requests,pillow,openssl,pyjnius

orientation = portrait
osx.python_version = 3
osx.kivy_version = 1.9.1
fullscreen = 0

# Android specific
android.permissions = INTERNET,ACCESS_NETWORK_STATE,FOREGROUND_SERVICE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 24
android.sdk = 33
android.ndk = 25b
android.archs = arm64-v8a, x86_64

# Services
# services = EmeMesh:service.py

[buildozer]
log_level = 2
warn_on_root = 1
