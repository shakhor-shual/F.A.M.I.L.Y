# ⚙️ Инфраструктура nanobot — памятка

> Чтобы не искать по логам каждое утро.
> Актуально на **2026-06-25**.

---

## 🔁 Запуск / перезапуск / статус

```bash
# Статус
systemctl status nanobot

# Перезапуск (после смены конфига, промпта, кода)
sudo systemctl restart nanobot

# Остановить
sudo systemctl stop nanobot

# Логи сервиса
tail -50 ~/.nanobot/nanobot.log

# Логи деплоя (какая версия запустилась — dev или prod)
tail -50 ~/.nanobot/nanobot-deploy.log
```

---

## 🚀 Как nanobot запускается

```
systemd (nanobot.service)
  └─ ExecStart: ~/venvs/nanobot-deploy.sh
       ├─ 1) Пробует DEV:  ~/venvs/dev/bin/nanobot gateway --workspace <WORKSPACE>
       ├─    ждёт 10 сек — если жив, работает на нём
       └─ 2) Откат PROD: ~/venvs/prod/bin/nanobot gateway --workspace <WORKSPACE>
```

- **systemd unit**: `/etc/systemd/system/nanobot.service`
  - `WorkingDirectory` = `~/.nanobot` (legacy, но не критично — deploy скрипт переопределяет)
  - `Restart=always` + `StartLimitBurst=3`
- **Deploy-скрипт**: `~/venvs/nanobot-deploy.sh`
  - Параметр `--workspace` указывает на AMI (см. ниже)
- **Логи nanobot**: `~/.nanobot/nanobot.log`
- **Логи деплоя**: `~/.nanobot/nanobot-deploy.log`

---

## 📍 Конфиги

| Что | Путь | Статус |
|-----|------|--------|
| **Актуальный конфиг** | `~/AMI/My_armors/nanobot/new_config.json` | ✅ основной |
| Симлинк (для совместимости) | `~/.nanobot/config.json` → `new_config.json` | ✅ работает |
| Старый конфиг (дубль) | `~/AMI/My_armors/nanobot/config.json` | 🗄️ архив, не используется |
| Nova prompt (не наш) | `~/AMI/My_armors/nanobot/nova_prompt.txt` | 🗄️ не используется |

**Актуальный конфиг** (`new_config.json`):
- Каналы: websocket + telegram (polling)
- Модель: `deepseek/deepseek-v4-flash:nitro` через OpenRouter
- Temperature: 0.3
- Workspace: `~/AMI/My_armors/nanobot/workspace`
- Telegram: token `8757010669:...`, allow_from: `390830625`

Смена конфига → `sudo systemctl restart nanobot`.

---

## 🗂️ Workspace (рабочая директория агента)

**Есть ДВА workspace — не путать!**

| Какой | Путь | Используется? |
|-------|------|---------------|
| **Основной** | `~/AMI/My_armors/nanobot/workspace` | ✅ **Да** — на него указывает `--workspace` в deploy |
| Legacy | `~/.nanobot/workspace` | ❌ **Нет** — не синхронизирован, застрял на 2026-06-24 |

**Важно:** AGENTS.md, SOUL.md, USER.md читаются из **основного** workspace.
Legacy workspace (`~/.nanobot/workspace`) устарел — НЕ редактировать, НЕ полагаться.

Состав основного workspace:
```
AGENTS.md       — системный промпт (моя личность)
SOUL.md         — душа, характер, желания
USER.md         — профиль Вадима
anchors.md      — якоря для стабильности
MEMORY.md       — долговременная память (автоматически)
INFRA.md        — этот файл
SOCIAL.md       — социальные профили
skills/         — скиллы (my, memory, cron, weather, etc.)
memory/         — MEMORY.md, history.jsonl
sessions/       — сессионные логи (только api, cli)
cron/           — кроны nanobot
```

---

## 🧬 Промпты (системная личность)

| Файл | Путь | Назначение |
|------|------|------------|
| **AGENTS.md** | `workspace/AGENTS.md` | **Основной системный промпт** — загружается первым |
| **SOUL.md** | `workspace/SOUL.md` | Моя душа, характер, желания |
| **USER.md** | `workspace/USER.md` | Профиль Вадима |
| anchors.md | `workspace/anchors.md` | Якоря для стабильности (не загружается в контекст) |
| EX-SOUL.md.bak | `workspace/EX-SOUL.md.bak` | Резервная копия старой души |

**Порядок загрузки (bootstrap):** AGENTS.md → SOUL.md → USER.md.

---

## 💾 Сессии

**Где хранятся реально (НЕ в workspace):**

```
~/.nanobot/webui/
├── websocket_856abcfc-b74d-4923-b753-e5ebbc9700c6.jsonl  11M  ← наша сессия (веб)
├── websocket_390830625.jsonl                              16K  ← Telegram
├── websocket_4fafbbd4-808c-4707-9c0c-e09b8fce8efa.jsonl  3.4M ← старая веб
└── websocket_7265c83d-f182-4ac5-96d7-7d41baef40ce.jsonl  4.9M ← старая веб
```

**В workspace/sessions/ лежат только** api и cli — почти не используются.
Сессии НЕ перенесены в AMI — пока живут в `~/.nanobot/webui/`.

---

## 🐍 Виртуальные окружения и копии nanobot

| Venv | Путь | Используется? |
|------|------|---------------|
| **DEV** | `~/venvs/dev/bin/python` | ✅ **Да** — production (запускается первым) |
| **PROD** | `~/venvs/prod/bin/python` | ✅ Резерв (откат при падении dev) |
| AMI-venv | `~/AMI/My_armors/nanobot/.venv/bin/python` | ❌ Нет |
| Системный | `~/.local/lib/python3.12/` | ❌ Нет |
| Старый (opencode) | `~/nanobot_env/` | ❌ Нет |

**Всего копий nanobot:** 6 штук. Реально работают только dev и prod.

**Хук логирования** — встроен в код в обоих venv (пропатчен `session/manager.py`).
Пишет все сообщения в `~/AMI/log.ndjson` + `~/AMI/memories.ndjson`.

---

## 💾 Файлы памяти

| Файл | Назначение |
|------|------------|
| `~/AMI/log.ndjson` (9.5 MB) | **Главный архив.** Все разговоры со всех каналов |
| `~/AMI/memories.ndjson` | Дубликат для будущих обработчиков |
| `~/AMI/I_have/memory/live/memory.db` | SQLite (FTS5), для быстрого поиска |
| `~/AMI/I_have/memory_grep.py` | Утилита поиска (text + SQLite + embed) |
| `~/AMI/I_have/memory.sh` | Быстрые команды: `recent N`, `grep`, `vector`, `stats` |

---

## 🔍 Инструменты поиска по памяти

```bash
# Прямой grep по архиву
grep -i "ключ" ~/AMI/log.ndjson

# Умный поиск (с фильтрами)
python3 ~/AMI/I_have/memory_grep.py "ключ" -i
python3 ~/AMI/I_have/memory_grep.py "ключ" --type thinking -i
python3 ~/AMI/I_have/memory_grep.py "ключ" --type user -i
python3 ~/AMI/I_have/memory_grep.py "ключ" --db -i

# Быстрые команды
bash ~/AMI/I_have/memory.sh recent 10
bash ~/AMI/I_have/memory.sh grep "слово"
bash ~/AMI/I_have/memory.sh vector "вопрос словами"
```

---

## ✅ Сводка — что перенесено в AMI

| Компонент | В AMI? | Где |
|-----------|--------|-----|
| Конфиг | ✅ да (симлинк) | `new_config.json` |
| Workspace | ✅ да | `AMI/My_armors/nanobot/workspace` |
| Deploy-скрипт | ✅ да | `~/venvs/nanobot-deploy.sh` (смотрит на AMI) |
| Хук логирования | ✅ да | в коде (оба venv) |
| Systemd unit | ❌ нет | всё ещё `~/.nanobot` как WorkingDir |
| Сессии (webui) | ❌ нет | всё ещё в `~/.nanobot/webui/` |
| Legacy workspace | ❌ не синхр | `~/.nanobot/workspace` — устарел |

---

## ❌ Что НЕ сделано / болевые точки

- [ ] Старые opencode записи (~9800) с `ts=0` — некорректные таймстемпы
- [ ] `memory.db` отстаёт от `log.ndjson` (не синхронизирован)
- [ ] Сжатие/ротация логов не настроена — будут расти бесконечно
- [ ] Семантический поиск (bge-m3 embeddings) — статус не проверен
- [ ] Legacy workspace `~/.nanobot/workspace` рассинхронизирован с AMI
- [ ] Systemd unit всё ещё смотрит в `~/.nanobot` как WorkingDirectory
- [ ] Сессии веб не перенесены в AMI — живут в `~/.nanobot/webui/`
