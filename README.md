# Обеды — учёт обеденных перерывов

Сотрудник нажимает **«Ушёл на обед»** и **«Вернулся»**, сайт следит за лимитом, HR видит табло и статистику.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white)
![Vue](https://img.shields.io/badge/Vue-3.5-4FC08D?logo=vuedotjs&logoColor=white)
![SQL Server](https://img.shields.io/badge/SQL%20Server-CC2927?logo=microsoftsqlserver&logoColor=white)
![Docker](https://img.shields.io/badge/Docker_Compose-2496ED?logo=docker&logoColor=white)
![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04-E95420?logo=ubuntu&logoColor=white)

## Оглавление

1. [Возможности](#возможности)
2. [Как устроено](#как-устроено)
3. [Требования](#требования)
4. [Установка](#установка)
5. [Обновление](#обновление)
6. [Свой центр сертификации](#свой-центр-сертификации)
7. [Команды на сервере](#команды-на-сервере)
8. [Разработка и тесты](#разработка-и-тесты)

## Возможности

| Роль | Разделы |
|---|---|
| 🙋 **Сотрудник** | Обед: кнопка, обратный отсчёт, своя история по месяцам |
| 🧑‍💼 **HR** | Обед, Табло, Статистика и Excel, Отсутствия, Правила |
| 👑 **Администратор** | Табло, Статистика, Сотрудники, Отсутствия, Правила, Доступ, Домен, База, Log |

- **Правила:** лимит обеда, рабочие дни, конец дня, окно обеда, праздники и переносы, учёт дней без обеда.
- **Табло:** кто на обеде, нарушения, кто ещё не обедал; исправление, добавление и удаление обеда с причиной.
- **Вход через Active Directory** (LDAPS), синхронизация с группой доступа каждый час.
- **Доступ по IP:** сайт открывается только с разрешённых адресов.
- **Журнал действий** с IP-адресом и «было → стало», хранится 3 года.

Пояснения к каждому разделу — на самом сайте, в кнопке «i».

## Как устроено

```
Браузер ──► nginx (контейнер web, :80/:443) ──► Django + Gunicorn (контейнер app, 127.0.0.1:8000) ──► SQL Server
                                                         └──► Active Directory (LDAPS)
```

| Путь на сервере | Что |
|---|---|
| `/opt/obedy` | код |
| `/opt/obedy/.env` | секретный ключ и настройки, только root (создаёт `install.sh`) |
| `/var/lib/obedy` | зашифрованное подключение к базе |
| `/etc/obedy/tls` | сертификат HTTPS |
| `/etc/obedy/ca` | свой центр сертификации |

Данные хранятся на вашем **Microsoft SQL Server**: сервер сайта можно переставить с нуля и подключить ту же базу.

## Требования

- Ubuntu Server 24.04 LTS, 2 ядра, 2 ГБ памяти, 20 ГБ диска, **постоянный IP**.
- Интернет при установке и обновлении: репозитории Ubuntu, Docker Hub, PyPI, npm.
- Порты: `22` — администраторам, `80` и `443` — пользователям. `8000` наружу не открывать.
- SQL Server: пустая база и SQL-логин с ролью `db_owner`, смешанная проверка подлинности, TCP/IP включён.

```sql
CREATE DATABASE obedy;
GO
CREATE LOGIN obedy WITH PASSWORD = '<пароль>';
GO
USE obedy;
CREATE USER obedy FOR LOGIN obedy;
ALTER ROLE db_owner ADD MEMBER obedy;
GO
```

## Установка

```bash
sudo git clone <адрес репозитория> /opt/obedy
cd /opt/obedy
sudo ./scripts/ca.sh init company.local                 # только если нужен свой центр сертификации
sudo ./scripts/install.sh --https obedy.company.local   # или просто: sudo ./scripts/install.sh
```

`install.sh` ставит Docker, создаёт `.env`, собирает и запускает контейнеры, включает таймеры, HTTPS и печатает
**код настройки**. Дальше — на сайте:

1. Открыть адрес сайта → «Подключение базы»: код настройки, адрес и порт SQL Server, база, логин, пароль →
   «Проверить» → «Подключить».
2. «Создать администратора» — сайт один раз покажет логин `admin` и временный пароль.
3. Войти, задать свой пароль, настроить разделы **«Домен»** и **«Доступ»**.

## Обновление

```bash
cd /opt/obedy
sudo ./scripts/deploy.sh <ветка>
```

Получает ветку, собирает контейнеры, применяет миграции, запускает и проверяет `/api/health`. При ошибке сам
возвращает прошлую версию кода. Перед крупным обновлением сделайте копию базы на SQL Server.

## Свой центр сертификации

Нужен, если в домене нет службы сертификатов: сайт открывается по имени без предупреждений, контроллеры домена
принимают LDAPS. Центр выпускает сертификаты только для имён внутри своего домена и частных IP-адресов.

1. **DNS:** на контроллере
   `Add-DnsServerResourceRecordA -ZoneName "company.local" -Name "obedy" -IPv4Address "<IP сервера>"`.
2. **Центр и сайт:** `sudo ./scripts/ca.sh init company.local`, затем `sudo ./scripts/setup-https.sh obedy.company.local`.
3. **Доверие:** текст из `sudo ./scripts/ca.sh root` сохранить в `obedy-root.cer` и импортировать через GPO, связанную
   с доменом: *Конфигурация компьютера → Политики → Конфигурация Windows → Параметры безопасности → Политики открытого
   ключа → Доверенные корневые центры сертификации*.
4. **LDAPS на каждом контроллере:** `sudo ./scripts/ca.sh dc srv-ad16.company.local`, перенести
   `/etc/obedy/ca/issued/srv-ad16.company.local.pfx` на контроллер и выполнить там от администратора:

   ```powershell
   Import-PfxCertificate -FilePath C:\srv-ad16.company.local.pfx -CertStoreLocation Cert:\LocalMachine\My -Password (Read-Host -AsSecureString)
   ```

   Применить без перезагрузки — файл `ldaps-renew.txt`:

   ```text
   dn:
   changetype: modify
   add: renewServerCert
   renewServerCert: 1
   -
   ```

   и `ldifde -i -f ldaps-renew.txt`. Затем удалить `.pfx` с контроллера.
5. **Проверка с сервера сайта:**
   `openssl s_client -connect srv-ad16.company.local:636 -CAfile /etc/obedy/ca/ca.pem </dev/null 2>/dev/null | grep "Verify return code"`
   → `0 (ok)`.
6. **Раздел «Домен»:** контроллеры полными именами, LDAPS, в «Корневой сертификат» — текст из `ca.sh root`.

Сертификаты сайта и контроллеров действуют 825 дней: продлить — повторить шаги 2 (только `setup-https.sh`) и 4.
Ключ центра `/etc/obedy/ca/ca.key` храните как пароль; копию `/etc/obedy` и `.env` держите на защищённом носителе.

## Команды на сервере

Все команды — из `/opt/obedy`, через `sudo`.

| Команда | Что делает |
|---|---|
| `./scripts/install.sh [--https [имя ...] \| --http]` | Первая установка |
| `./scripts/deploy.sh <ветка>` | Обновление с откатом при ошибке (`update.sh` — то же) |
| `./scripts/setup-https.sh [имя ...]` | Выпустить или продлить сертификат HTTPS |
| `./scripts/ca.sh init <домен> \| root \| dc <контроллер>` | Свой центр сертификации |
| `./scripts/setup-code.sh` | Новый код для подключения базы |
| `./scripts/reset-database.sh` | Забыть подключение к базе (данные в SQL Server остаются) |
| `./scripts/change-password.sh [логин]` | Временный пароль локальной учётной записи (по умолчанию `admin`) |
| `./scripts/access.sh show \| add <IP> [пометка] \| remove <IP> \| lan on\|off` | Доступ по IP, если закрыли себе вход |
| `./scripts/directory-sync-timer.sh status\|run\|install\|remove` | Синхронизация с AD (каждый час) |
| `./scripts/journal-clean-timer.sh status\|run\|install\|remove` | Очистка журнала и сессий (00:30 по Москве) |
| `./scripts/reset-stats.sh` | Удалить все обеды перед запуском (спросит слово `СБРОС`) |

Состояние и логи:

```bash
sudo docker compose ps
curl -sk https://127.0.0.1/api/health
sudo docker compose logs --tail=100 app
```

## Разработка и тесты

```
backend/    Django: accounts, access, directory, staff, lunches, journal, config; тесты в backend/tests
frontend/   Vue 3 + TypeScript: src/pages, src/components, src/api; тесты в frontend/tests
deploy/     Dockerfile-ы и настройки nginx
scripts/    установка, обновление, сертификаты, обслуживание
```

```bash
# сервер: нужен SQL Server с логином, которому можно создать тестовую базу
docker run -d --name mssql-test -e ACCEPT_EULA=Y -e MSSQL_PID=Express -e MSSQL_SA_PASSWORD=<пароль> -p 1433:1433 mcr.microsoft.com/mssql/server:2019-latest
cd backend && DJANGO_SECRET_KEY=dev DB_USER=sa DB_PASSWORD=<пароль> python -m pytest

# интерфейс
cd frontend && npm ci && npm run typecheck && npm test && npm run build

# скрипты
bash scripts/tests/sqlserver-switch.test.sh
sudo bash scripts/tests/deploy-handoff.test.sh
```

Точные версии зависимостей — в `requirements.txt`, `frontend/package.json` и `deploy/*.Dockerfile`.
