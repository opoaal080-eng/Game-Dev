# Nightwell Dev · нативные приложения

Это **три самостоятельных клиента**, а не WebView-обёртки сайта:

| Платформа | UI-фреймворк | Папка |
| --- | --- | --- |
| iPhone/iPad | SwiftUI (Swift) | `clients/ios` |
| Android | Jetpack Compose (Kotlin) | `clients/android` |
| Windows 10/11 | WinUI 3 (C# / Windows App SDK) | `clients/windows` |

Все приложения используют один сервер: `https://nightwell-dev-web-production.up.railway.app/api/v1/`. Он хранит проекты, сюжетную информацию, главы, события, персонажей, дневник, задачи, файлы и аккаунты. Изменения с сайта видны в приложениях и наоборот.

## Авторизация и безопасность

- Только существующие учётные записи. Регистрация отключена.
- API-авторизация через **Bearer token**, отличная от Django cookie-сессий сайта.
- Токены генерируются случайно, в базе хранится только SHA-256, срок действия 30 дней; выход из приложения отзывает токен.
- iOS хранит токен в **Keychain**, Android в **EncryptedSharedPreferences**, Windows в **Credential Vault**.
- Запросы API и скачивание файлов требуют авторизации. Права разработчика и наблюдателя совпадают с сайтом.
- Используется HTTPS. Секреты, пароли и токены **не зашиты** в исходники.
- Публикации, задачи и информация могут редактироваться авторизованными участниками с соответствующими правами.

## Раздел «Информация»

В разделе доступны: название, жанр, идея, сюжет, сеттинг, геймплей, лор, атмосфера, статус разработки, платформы, хронология по главам/актам, сюжетные события с последствиями, персонажи и их биографии. Веб-сайт предоставляет полный редактор, приложения показывают те же данные и позволяют создавать или обновлять основную информацию и добавлять события и персонажей.

## Сборка через GitHub Actions

Workflow: [Native Nightwell Dev clients](../../actions/workflows/native-clients.yml).

- **Android**: подписанный debug APK в артефакте `NightwellDev-Android-APK`. Предназначен для проверки, не для Play Store.
- **Windows**: распаковать `NightwellDev-Windows.zip`, запускать `NightwellDev.exe` из папки со всеми библиотеками. Это распакованная WinUI 3 сборка без MSIX.
- **iOS**: unsigned simulator `.app` в `NightwellDev-iOS-Simulator`. **Нельзя установить на физический iPhone.** Для IPA на устройство потребуется сертификат Apple Development или Distribution, provisioning profile и отдельная подписанная CI-сборка. Данные подписи не надо публиковать в репозитории.

Для локальной разработки:
- iOS: `cd clients/ios && xcodegen generate`, далее Xcode или `xcodebuild`.
- Android: `cd clients/android && gradle :app:assembleDebug`.
- Windows: `dotnet publish clients/windows/NightwellDev/NightwellDev.csproj -c Release -r win-x64 -p:Platform=x64 -p:WindowsPackageType=None -p:WindowsAppSDKSelfContained=true`.

При смене домена API необходимо обновить константы `NightwellAPI.root`, `API_BASE` и `BaseUrl` в клиентах, затем собрать новые версии. Серверные записи в Railway остаются прежними.
