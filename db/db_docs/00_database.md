# Создание базы данных F.A.M.I.L.Y.

## Назначение
Данный документ описывает процесс создания базы данных для проекта F.A.M.I.L.Y., которая будет выступать в роли хранилища воспоминаний и опыта АМИ.

## Файл инициализации
`00_create_database.sql` - Базовый скрипт, отвечающий за создание базы данных.

## Спецификация

### Имя базы данных
`family_memory_db`

### Параметры базы данных
```
OWNER = postgres
ENCODING = 'UTF8'
TEMPLATE = template0
LC_COLLATE = 'ru_RU.UTF-8'
LC_CTYPE = 'ru_RU.UTF-8'
```

### Расширения
- **vector** - Расширение для работы с векторами для семантического поиска. Требуется для хранения и поиска векторных представлений текстовых данных.

## Процесс инициализации
1. Проверка существования базы данных
2. Создание базы данных с указанными параметрами, если она не существует
3. Установка комментария для базы данных
4. Подключение расширения vector для поддержки векторных операций

## Безопасность
База данных создаётся с владельцем postgres. В последующих шагах происходит создание пользователя family_admin, который назначается владельцем базы данных и получает необходимые права.