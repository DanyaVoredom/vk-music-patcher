# VK Music Patcher

Пайплайн для сборки модифицированной VK Музыки (Android) из APK или установленной оригинальной версии. Патч разблокирует подписку и оффлайн-треки.

## Как это работает

1. `pull_apks.ps1` - вытягивает base.apk и сплиты установленной оригинальной версии через adb, собирает в `pulled.apks`.
2. `build_patch.ps1 -Build` - принимает APK или `pulled.apks`, декомпилирует base через apktool и патчит:
   - `vk_package.py` - переименование пакета в `.patched` (side-by-side с оригиналом), правка authorities и метки.
   - `vk_patch.py` - целевые правки smali (подписка, оффлайн, ограничения и восстановление сессии после холодного запуска).
   - `patch_native.py` - правка нативного `libvkcore.so`.
3. Для универсального APK собирает и подписывает один APK; для `pulled.apks` собирает base и перепаковывает сплиты через `axml_rename.py`.
4. `build_patch.ps1 -Install` устанавливает APK или набор сплитов поверх патча. Данные и логин сохраняются.

## Автопатч

Обфусцированные имена классов меняются от версии к версии (gdm, uhm, fo9...). `vk_auto.py` не хардкодит их: цели ищутся по `.source` исходного Kotlin-файла, форме метода, маскам флагов, строковым константам, доступам к полям и вызовам. Если R8 переименовал метод, но сохранил смысловые якоря, патч находится автоматически. Если структура не совпала, сборка падает с диагностикой, а не патчит похожий метод наугад.

`native_auto.py` определяет функции `libvkcore.so` по unwind-таблицам (`.eh_frame_hdr` для arm64, `.ARM.exidx` для armv7) и строковым якорям `signatures` и `error! verify new libraries`. Точные офсеты 8.53 остаются резервным вариантом, если capstone или pyelftools недоступны.

Результат резолва записывается в `build/patch_manifest.json`: классы, методы, ожидаемые инструкции, константы, строки и native offsets. `verify_patch.py` проверяет собранный APK по этому манифесту, поэтому проверка не привязана к именам классов конкретной версии.

## Возможности

- Side-by-side установка: патч `com.uma.musicvk.patched` ставится рядом с оригиналом `com.uma.musicvk`.
- Сохранение данных и логина при переустановке поверх патча.
- Восстановление входа после холодного запуска через резервное хранилище сессии и ключа шифрования.
- Автопатч smali по `.source`, форме методов и смысловым якорям.
- Автоподбор native offsets `libvkcore.so` (arm64-v8a и armeabi-v7a) по unwind-таблицам и строкам.
- Манифест патча и динамическая верификация собранного APK.
- Встроенная проверка обновлений мода через GitHub Releases.
- CI собирает патч на GitHub Actions и публикует APK с манифестом обновления.
- Верификация результата: `verify_patch.py` проверяет манифест, регистры и апдейтер; `verify_package.py` - пакет, authorities, компоненты и разрешение на установку.

## Требования

- Windows, PowerShell 7+
- JDK 21+
- Python 3.10+
- apktool 3.0.3+ (`C:\Windows\apktool.jar` или `-ApkToolJar`)
- Android build-tools 36.x (zipalign, apksigner) - `-BuildTools`
- adb
- ripgrep (`rg`) в PATH
- keystore - свой, положить как `patch.keystore` (в .gitignore)

Если apktool падает на `private resources` в `values-v34`, удалите старый `%LOCALAPPDATA%\apktool\framework\1.apk` и повторите сборку: apktool 3.0.3 создаст встроенный framework.

Python-пакеты нужны для verify-скриптов и автоподбора native offsets:

```powershell
pip install -r requirements.txt
```

## Использование

```powershell
# один раз: указать пароль keystore через переменную окружения
$env:VKM_KS_PASS = "yourpass"

# полный цикл: вытянуть оригу, собрать, поставить
.\build_patch.ps1 -Pull -Build -Install

# собрать универсальный APK из скачанного RuStore
.\build_patch.ps1 -Apk "VK_Music_<версия>.apk" -Build -Install

# только пересобрать из уже вытянутого pulled.apks
.\build_patch.ps1 -Build -Install

# без запуска приложения после установки
.\build_patch.ps1 -Build -Install -NoLaunch
```

Пакет патча: `com.uma.musicvk.patched` (ставится рядом с оригиналом `com.uma.musicvk`).

## Автообновление

### Внутри APK

`UpdateChecker` встроен в `MainActivity`. При запуске приложение проверяет релизы в `DanyaVoredom/DanyExternal-Releases` (не чаще раза в 5 минут), выбирает последний релиз с тегом `vk-`, сравнивает `versionCode` и `modRevision`, скачивает APK, проверяет SHA-256 и открывает системный установщик. Для установки используется существующий `<package>.fileprovider`, разрешение `REQUEST_INSTALL_PACKAGES` добавляется при сборке.

Репозиторий и API задаются при сборке через `VKM_UPDATE_REPO` и `VKM_UPDATE_API`. По умолчанию это GitHub `DanyaVoredom/DanyExternal-Releases` и список релизов с `per_page=100`. Если релиза нет или сеть недоступна, приложение работает как обычно.

Установленная версия 8.49 не содержит встроенного апдейтера, поэтому первый переход на 8.53 выполняется установкой APK поверх неё (подпись и пакет совпадают, данные сохраняются). Дальнейшие обновления приложение устанавливает само через системный установщик.

### Сборка и релизы

Основной контур: GitHub Actions собирает APK и публикует его в GitHub Releases. Codeberg используется только как git-зеркало.

- `.github/workflows/build-release.yml` запускается ежедневно в 00:00 МСК, по push в `main` и вручную.
- Проверяет версию на `norobot.ru` и сравнивает с последним тегом `vk-` в `DanyVoredom/DanyExternal-Releases`.
- Сборка выполняется на `windows-latest` с build-tools 36.1.0 (если доступны) или самыми новыми.
- `update_mod.ps1 -NoInstall` собирает APK и пишет `build/update.json`.
- Workflow публикует `VK_Music_<версия>_patched.apk` и `update.json` в GitHub Releases через `gh` и токен `RELEASES_TOKEN`.

Для workflow нужны secrets в GitHub `DanyaVoredom/vk-music-patcher`:

- `RELEASES_TOKEN` - GitHub-токен с доступом к `DanyVoredom/DanyExternal-Releases`.
- `VKM_KS_BASE64` - `patch.keystore` в base64.
- `VKM_KS_PASS` - пароль keystore.
- `VKM_KS_ALIAS` - опционально, по умолчанию `vkmpatch`.

Codeberg Releases не используются для APK: при загрузке 85 МБ APK и update.json срабатывает quota exceeded. `.forgejo/workflows/build-release.yml` и self-hosted runner отключены; не включать их на этой машине.

### Обновление с ПК

`update_mod.ps1` проверяет свежую версию VK Музыки, скачивает APK, проверяет package, versionCode и официальную подпись VK, затем собирает и устанавливает патч.

```powershell
# только проверить и проверить APK
.\update_mod.ps1 -CheckOnly

# проверить, собрать и установить патч
.\update_mod.ps1

# сохранить пароль keystore (DPAPI, файл patch.kspass)
.\update_mod.ps1 -SetPassword

# ежедневная задача в 10:00
.\update_mod.ps1 -RegisterTask -TaskTime 10:00
```

Источник по умолчанию - `https://norobot.ru/vk-music/`. Другой APK можно указать через `-ApkUrl` и `-ExpectedVersion`. Подпись проверяется по закреплённому SHA-256 сертификата VK; без совпадения обновление не выполняется.

Для задачи пароль берётся из `patch.kspass` или `VKM_KS_PASS`. Файл `patch.kspass` зашифрован DPAPI и добавлен в `.gitignore`. Задача выполняется от текущего пользователя, поэтому должна быть доступна его сессия и `adb`. Журнал: `logs/update.log`.

Флаги: `-NoInstall` собирает без установки, `-NoBuild` устанавливает уже собранный `build/VK_Music_patched.apk`, `-Force` игнорирует совпадение versionCode. Локальная сборка с `-ModRevision N` создаёт APK с этой ревизией апдейтера.

## Файлы

Основной пайплайн:

- `build_patch.ps1` - оркестратор
- `update_mod.ps1` - автообновление: проверка версии, загрузка, сборка, установка
- `pull_apks.ps1` - извлечение apk с устройства
- `vk_auto.py` - автопатч: резолв целей по `.source`, форме методов, маскам и якорям
- `vk_targets.py` - тела замен, far-future константа и паттерн миграции
- `vk_resolve.py` - вспомогательный резолв по `.source` через rg
- `vk_patch.py` - применение правок smali и запись `build/patch_manifest.json`
- `vk_updater.py` - встраивание апдейтера, ревизии и разрешения на установку
- `updater/` - исходник апдейтера и готовый smali
- `vk_package.py` - переименование пакета
- `native_auto.py` - автоподбор функций libvkcore.so по unwind-таблицам и строкам
- `patch_native.py` - правка libvkcore.so с fallback на точные офсеты
- `axml_rename.py` - правка имени пакета в бинарном AndroidManifest.xml (для сплитов)
- `repack_split.py` - замена lib внутри сплита

Верификация:

- `verify_patch.py` - проверка собранного apk по манифесту патча
- `verify_package.py` - проверка пакета, authorities и компонентов

Отладка и диагностика:

- `deploy_debug.ps1` - сборка, установка и запуск варианта (side / samepkg) со снятием logcat, скриншота и exit-info
- `patch_subscription.py`, `patch_migration.py`, `patch_trace.py`, `patch_package.py` - точечные патчи и трейсинг
- `find_sources.py`, `resolve_targets.py`, `index_scan.py`, `check_remaining.py` - разовые инструменты анализа smali

Устаревшие скрипты 8.45:

- `build_845.ps1` - отдельный оркестратор
- `patch_package_845.py`, `patch_subscription_845.py`, `patch_migration_845.py`, `patch_native_845.py`
- `find_pkg_845.py`

## Обновление при выходе новой версии VK

1. Получить APK конкретной версии и проверить package/version metadata.
2. Запустить сборку. `vk_auto.py` резолвит цели и пишет `build/patch_manifest.json`; `native_auto.py` находит функции `libvkcore.so`.
3. Если автопатч не нашел цель или нашел несколько, сборка падает с диагностикой. Обновить правило или якорь в `vk_auto.py`; тела замен остаются в `vk_targets.py`.
4. Если native-якоря изменились, обновить fallback-офсеты в `patch_native.py`; автоподбор по unwind-таблицам и строкам должен найти функции сам.
5. Собрать и выполнить `verify_patch.py` до установки. Манифест проверяется динамически, hardcoded-проверки 8.53 остаются только запасным вариантом.
6. Использовать `.\build_patch.ps1 -Apk "VK_Music_<версия>.apk" -Build -Install` или `.\build_patch.ps1 -Pull -Build -Install`.

## CI

`.github/workflows/ci.yml` проверяет синтаксис Python (`compileall`) и парсинг PowerShell-скриптов на каждый push и pull request в `main`. `.github/workflows/build-release.yml` собирает и публикует релизы.

## Лицензия

MIT, см. `LICENSE`.

## Дисклеймер

Только для личного использования. Модифицированный apk не распространять, подпись и keystore держать приватно.
