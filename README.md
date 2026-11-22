# Nightwell Dev · Nightwell Studio

Закрытый портал разработки игры для команды Nightwell Studio. Адрес будущего сайта: **https://dev.nightwell.fun**.

Дневник разработки, технические заметки и документация, доска задач, приватное хранилище файлов, поиск, команда и роли. Интерфейс адаптирован для компьютера и телефона. **Без Docker.**

## Что уже работает

- **Закрытая авторизация.** Публичной регистрации и публичных страниц с рабочими материалами нет.
- **Права доступа.** Администратор создаёт пользователей и проекты; разработчик добавляет записи, задачи и файлы; наблюдатель читает опубликованные записи, смотрит задачи и скачивает разрешённые всем участникам файлы.
- **Публикации.** Дневники разработки, заметки, итоги встреч, решения и документы. Поддерживается Markdown, черновики и закрепление.
- **Задачи.** Доска с четырьмя статусами, исполнителями, приоритетами и сроками.
- **Файлы.** Загружаются в непубличное хранилище, скачиваются только через проверяющий авторизацию обработчик Django. До 100 МБ на файл.
- **Поиск.** По тексту записей, задачам и материалам.
- **Админка.** Управление аккаунтами, ролями, проектами, задачами и публикациями через `/control/`.

Все данные пока сохраняются в SQLite. На сервере можно использовать PostgreSQL через `DATABASE_URL`. GitHub хранит код, а **GitHub Pages публикует отдельный интерфейс приложения** по адресу https://opoaal080-eng.github.io/Game-Dev/. Сам Python/Django и база данных на GitHub Pages не запускаются: авторизация и приватные данные поступают из защищённого API Railway. Если Railway недоступен из сети пользователя, интерфейс на GitHub Pages откроется, но вход и синхронизация не сработают, пока API не переедет на доступный хостинг.

## Размещение настоящего сайта без компьютера (Railway)

GitHub хранит только код. Чтобы Django работал круглосуточно как сайт, потребуется облачный хостинг. Для временного размещения подготовлен `railway.json`. Dockerfile и Docker Compose не используются.

1. Зарегистрируйтесь на [Railway](https://railway.com/) с телефона, подключите GitHub и выберите репозиторий `opoaal080-eng/Game-Dev`, ветку `main` (Create Project / Deploy from GitHub repo).
2. Добавьте в проект сервис **PostgreSQL**, затем в Variables сайта задайте `DATABASE_URL=${{Postgres.DATABASE_URL}}`. Название `Postgres` должно совпадать с именем сервиса базы в Railway.
3. Прикрепите к сервису сайта **Volume**, mount path `/data`. Файлы будут храниться в `/data/private_uploads`, а не исчезать при новом деплое.
4. Добавьте следующие переменные среды веб-сервиса. Реальные секреты вводите только в Railway, не в GitHub:

   | Переменная | Значение |
   | --- | --- |
   | `DJANGO_SECRET_KEY` | длинный случайный секрет (не меньше 50 символов) |
   | `DJANGO_DEBUG` | `false` |
   | `DJANGO_ALLOWED_HOSTS` | `dev.nightwell.fun` |
   | `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://dev.nightwell.fun` |
   | `DJANGO_SECURE_SSL_REDIRECT` | `true` |
   | `DJANGO_TRUST_PROXY_SSL_HEADER` | `true` |
   | `PRIVATE_UPLOAD_ROOT` | `/data/private_uploads` |
   | `BOOTSTRAP_ADMIN_USERNAME` | имя первого администратора |
   | `BOOTSTRAP_ADMIN_PASSWORD` | уникальный пароль администратора минимум 16 символов |
   | `BOOTSTRAP_ADMIN_EMAIL` | почта администратора, необязательно |

5. При первом успешном запуске автоматически выполнятся миграции, сбор статики и создание администратора. После входа удалите переменные `BOOTSTRAP_ADMIN_PASSWORD`, `BOOTSTRAP_ADMIN_USERNAME`, `BOOTSTRAP_ADMIN_EMAIL` из Railway и перезапустите сервис. Сама учётная запись останется.
6. Для начала включите `Generate Domain` в Public Networking и откройте адрес вида `https://....up.railway.app/login/`. В `settings.py` имя выдаваемого Railway домена добавляется автоматически из `RAILWAY_PUBLIC_DOMAIN`.
7. После проверки сайта в Settings → Networking → Custom Domain добавьте `dev.nightwell.fun`. Railway выдаст **CNAME и TXT**. Создайте обе DNS-записи у своего DNS-провайдера. Не придумывайте CNAME вручную. После подтверждения домена откроется `https://dev.nightwell.fun/login/`.

**Доступ ограничен:** без авторизации страницы и файлы закрыты. Дополнительно ограничьте сайт через Cloudflare Access, если хотите скрыть даже форму входа. Администратору необходимо включить 2FA на аккаунте Railway и GitHub.

**Важные нюансы:** Railway требует отдельного подключения вашего аккаунта и может взимать плату за используемые ресурсы; следите за лимитами. Для защиты данных регулярно выгружайте резервные копии PostgreSQL и каталога `/data/private_uploads`. В случае переноса на собственный сервер сохраните оба источника данных и `DJANGO_SECRET_KEY`, иначе входы и файлы могут перестать работать. Содержимое рабочего портала нельзя хранить в публичном репозитории.

## 1. Первый запуск (Windows / Linux / macOS)

Нужен **Python 3.11+**. Рекомендуется Python 3.12 или 3.13.

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

В файле `.env` замените `REPLACE_WITH_A_LONG_RANDOM_SECRET` на сгенерированное значение. Затем:

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

Откройте **http://127.0.0.1:8000/login/**. Первый пользователь-суперадминистратор создаётся командой `createsuperuser`, самостоятельно зарегистрироваться на сайте нельзя. В `/control/` добавьте участников и выдайте каждому роль в блоке «Доступ к порталу». Пользователи должны быть **активны**.

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -c 'import secrets; print(secrets.token_urlsafe(64))'
# Впишите выведенный секрет в .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

**Никогда не загружайте `.env`, `var/` и пользовательские файлы в GitHub**: они исключены в `.gitignore`.

## 2. Публикация исходников в GitHub

Создайте **private** репозиторий. Из папки проекта:

```bash
git init
git branch -M main
git add .
git commit -m "Initial Nightwell Dev portal"
git remote add origin https://github.com/USERNAME/REPOSITORY.git
git push -u origin main
```

Рабочий процесс GitHub Actions (`.github/workflows/ci.yml`) запускает проверку Django и тесты на каждом push/PR. Он **не публикует сайт в интернет**.

## 3. Позже: dev.nightwell.fun на собственном сервере

1. Склонируйте этот репозиторий на сервер, установите Python и зависимости. При переносе сохраните рабочую базу данных, `var/private_uploads/` и `.env` безопасным способом, не через GitHub.
2. Для боевого запуска создайте в `.env` уникальный секрет, `DJANGO_DEBUG=false`, `DJANGO_ALLOWED_HOSTS=dev.nightwell.fun`, `DJANGO_CSRF_TRUSTED_ORIGINS=https://dev.nightwell.fun`, `DJANGO_SECURE_SSL_REDIRECT=true`.
3. Выполните `python manage.py migrate` и `python manage.py collectstatic --noinput`.
4. На Linux запустите Gunicorn (`pip install -r requirements-prod.txt`; `gunicorn nightwell_dev.wsgi:application --bind 127.0.0.1:8000 --workers 3`). На Windows используйте Waitress (`pip install -r requirements-prod-windows.txt`; `waitress-serve --listen=127.0.0.1:8000 nightwell_dev.wsgi:application`).
5. Настройте Caddy, Nginx или иной доверенный HTTPS reverse proxy. Пример Caddy есть в `deploy/Caddyfile.example`. DNS-запись домена должна указывать на публичный адрес сервера или туннель. Не выставляйте Python-порт напрямую в интернет.
6. Если используете HTTPS reverse proxy с заголовком `X-Forwarded-Proto`, который **сам его задаёт и очищает входящий от клиента заголовок**, можно поставить `DJANGO_TRUST_PROXY_SSL_HEADER=true`. Если нет, оставьте `false` и настройте HTTPS корректно для Django на уровне прокси.
7. Для дополнительного ограничения доступа на уровне домена подключите Cloudflare Access. Обязательно оставьте внутреннюю авторизацию сайта: Access не заменяет права внутри портала.

На рабочем сервере лучше PostgreSQL и регулярные резервные копии БД и закрытых файлов. Для PostgreSQL задайте `DATABASE_URL=postgresql://user:pass@127.0.0.1:5432/nightwell_dev`.

> Важно: настройка HTTPS, доступов, резервных копий и проверка сетевого прокси остаются задачами при развёртывании. Наличие исходников не означает, что `dev.nightwell.fun` уже работает.

## Библиотеки

| Название | Для чего |
| --- | --- |
| Django 5.2 LTS | маршруты, сервер, формы, база данных, учётные записи, роли, админ-панель |
| WhiteNoise | отдача публичных статических файлов приложения, **не** закрытых загрузок |
| markdown-it-py | безопасный Markdown, сырой HTML отключён |
| python-dotenv | настройки из `.env` |
| psycopg | подключение к PostgreSQL позже |
| Gunicorn или Waitress | запуск WSGI в зависимости от ОС |
| Caddy / Nginx | HTTPS и обратное проксирование |
| Cloudflare Access (опционально) | допуск к домену только разрешённых пользователей |

Не требуется: Docker, Node.js, платный CDN, внешнее файловое хранилище.

## Безопасность и ограничения начальной версии

- Для тестов `DJANGO_DEBUG=true` и простой SQLite. **Нельзя так выставлять сайт в интернет**.
- HTTPS обязателен в продакшне. Пароли хэшируются встроенной системой Django.
- Загруженные файлы не имеют открытых URL, но участники портала, включая наблюдателей, могут скачивать все файлы всех проектов. Если нужны секретные материалы с доступом по отдельным командам, нужно добавить ACL на каждый проект/файл.
- Расширение загружаемого файла проверяется, содержимое пока не сканируется антивирусом. Не принимайте файлы из недоверенных источников. Не запускайте загруженные скрипты/сборки автоматически.
- Для боевого использования желательно добавить 2FA/SSO, журнал аудита, политику резервного копирования и защиту от перебора паролей на уровне обратного прокси или Auth-провайдера.
- Не предусмотрены синхронное совместное редактирование, уведомления, комментарии и загрузка файлов больше 100 МБ. Это возможные следующие этапы.

## Проверки

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```
