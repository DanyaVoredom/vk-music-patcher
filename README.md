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

## Ключевая идея: резолв по `.source`

Обфусцированные имена классов меняются от версии к версии (gdm, uhm, fo9...). Классы не хардкодятся: цели ищутся по оригинальным именам Kotlin-файлов, которые сохраняются в директиве `.source` smali-класса (`MusicSubscriptionProviderImpl.kt`, `CurrentAccountInformation.kt` и т.д.). Поиск через ripgrep. Сигнатуры методов при обновлении версии всё равно нужно сверять: R8 может изменить их вместе с телами.

Текущие цели и native offsets проверены на VK Музыке 8.53 (versionCode 15193). Для другой версии их нужно сверить заново; `verify_patch.py` для этого хранит точные обфусцированные классы и методы проверяемой версии.

## Возможности

- Side-by-side установка: патч `com.uma.musicvk.patched` ставится рядом с оригиналом `com.uma.musicvk`.
- Сохранение данных и логина при переустановке поверх патча.
- Восстановление входа после холодного запуска через резервное хранилище сессии и ключа шифрования.
- Резолв целей по `.source`, устойчивый к реобфускации.
- Нативные правки `libvkcore.so` (arm64-v8a и armeabi-v7a).
- Верификация результата: `verify_patch.py` проверяет инструкции и регистры, `verify_package.py` - пакет, authorities, компоненты.

## Требования

- Windows, PowerShell 7+
- JDK 21+
- Python 3.10+
- apktool 3.0.3+ (`C:\Windows\apktool.jar` или правь `$ApkToolJar`)
- Android build-tools 36.x (zipalign, apksigner) - правь `$BuildTools`
- adb
- ripgrep (`rg`) в PATH
- keystore - свой, положить как `patch.keystore` (в .gitignore)

Python-пакеты нужны только для verify-скриптов:

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

Флаги: `-NoInstall` собирает без установки, `-NoBuild` устанавливает уже собранный `build/VK_Music_patched.apk`, `-Force` игнорирует совпадение versionCode.

## Файлы

Основной пайплайн:

- `build_patch.ps1` - оркестратор
- `update_mod.ps1` - автообновление: проверка версии, загрузка, сборка, установка
- `pull_apks.ps1` - извлечение apk с устройства
- `vk_targets.py` - список целей патча (source + сигнатура метода)
- `vk_resolve.py` - резолв цели по `.source` через rg
- `vk_patch.py` - применение правок smali
- `vk_package.py` - переименование пакета
- `patch_native.py` - правка libvkcore.so
- `axml_rename.py` - правка имени пакета в бинарном AndroidManifest.xml (для сплитов)
- `repack_split.py` - замена lib внутри сплита

Верификация:

- `verify_patch.py` - проверка правок smali в собранном apk
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
2. Проверить цели в `vk_targets.py` по `.source` и сигнатурам методов в smali.
3. Проверить native offsets и ожидаемые байты в `patch_native.py` на `libvkcore.so` из того же APK.
4. Обновить проверки в `verify_patch.py`, собрать и запустить верификацию до установки.
5. Использовать `.\build_patch.ps1 -Apk "VK_Music_<версия>.apk" -Build -Install` или `.\build_patch.ps1 -Pull -Build -Install`.

## CI

`.github/workflows/ci.yml` проверяет синтаксис Python (`compileall`) и парсинг PowerShell-скриптов на каждый push и pull request в `main`.

## Лицензия

MIT, см. `LICENSE`.

## Дисклеймер

Только для личного использования. Модифицированный apk не распространять, подпись и keystore держать приватно.
