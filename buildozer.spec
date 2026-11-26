# buildozer.spec
[app]
title = Field Commander AI
package.name = fieldcommander
package.domain = org.commander
source.include_exts = py,png,jpg,kv,atlas
source.dir = .
version = 1.0
requirements = python3,kivy,openssl,urllib3,certifi,idna,charset-normalizer,requests
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 33
android.minapi = 21
android.sdk = 31
android.ndk = 25b
android.accept_sdk_license =지요
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/presplash.png

[buildozer]
log_level = 2
warn_on_root = 1
