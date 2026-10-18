# VK Music Patcher

Пайплайн для сборки модифицированной VK Музыки (Android) из установленной оригинальной версии. Патч разблокирует подписку и оффлайн-треки.

## Как это работает

1. `pull_apks.ps1` - вытягивает base.apk и сплиты установленной оригинальной версии через adb, собирает в `pulled.apks`.
2. `build_patch.ps1 -Build` - распаковывает apks, декомпилирует base через apktool, патчит:
   - `vk_package.py` - переименование пакета в `.patched` (side-by-side с оригиналом), правка authorities и метки.
   - `vk_patch.py` - целевые правки smali (подписка, оффлайн, ограничения).
   - `patch_native.py` - правка нативного `libvkcore.so`.
3. `build_patch.ps1 -Build` собирает base через apktool, сплиты перепаковывает через `axml_rename.py` (правка бинарного манифеста без apktool), всё подписывает.
4. `build_patch.ps1 -Install` - `adb install-multiple -r` поверх установленного патча. Данные и логин сохраняются.

## Ключевая идея: резолв по `.source`

Обфусцированные имена классов и методов меняются от версии к версии (gdm, uhm, fo9...). Пайплайн не хардкодит их. Вместо этого цели ищутся по оригинальным именам Kotlin-файлов, которые сохраняются в директиве `.source` smali-класса (`MusicSubscriptionProviderImpl.kt`, `CurrentAccountInformation.kt` и т.д.). Поиск через ripgrep. Это переживает реобфускацию: при обновлении VK цели находятся автоматически.

## Возможности

- Side-by-side установка: патч `com.uma.musicvk.patched` ставится рядом с оригиналом `com.uma.musicvk`.
- Сохранение данных и логина при переустановке поверх патча.
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

# только пересобрать из уже вытянутого pulled.apks
.\build_patch.ps1 -Build -Install

# без запуска приложения после установки
.\build_patch.ps1 -Build -Install -NoLaunch
```

Пакет патча: `com.uma.musicvk.patched` (ставится рядом с оригиналом `com.uma.musicvk`).

## Файлы

Основной пайплайн:

- `build_patch.ps1` - оркестратор
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

Вариант 8.45:

- `build_845.ps1` - отдельный оркестратор
- `patch_package_845.py`, `patch_subscription_845.py`, `patch_migration_845.py`, `patch_native_845.py`
- `find_pkg_845.py`

## Обновление при выходе новой версии VK

1. Обновить оригинал в RuStore.
2. `.\build_patch.ps1 -Pull -Build -Install`
3. Если обфускация сдвинула сигнатуры методов - поправить `vk_targets.py` (цели ищутся по `.source`, но сигнатуры тел могут измениться).

## CI

`.forgejo/workflows/ci.yml` проверяет синтаксис Python (`compileall`) и парсинг PowerShell-скриптов на каждый push в `dev` и `prod`.

## Лицензия

MIT, см. `LICENSE`.

## Дисклеймер

Только для личного использования. Модифицированный apk не распространять, подпись и keystore держать приватно.