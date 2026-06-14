# Схема базы данных

## Таблица users_table

| Колонка | Тип | Описание |
| :--- | :--- | :--- |
| id | INTEGER | Первичный ключ, автоинкремент |
| email | STRING | Уникальный, не null |
| password | STRING | Хэш пароля |
| user_name | STRING | Имя пользователя, уникальное |

## Планируемые таблицы

### processes_table
Хранит историю судебных процессов.

| Колонка | Тип | Описание |
| :--- | :--- | :--- |
| id | INTEGER | Первичный ключ |
| user_id | INTEGER | Внешний ключ к users_table |
| mode | STRING | Режим игры |
| prosecutor_model | STRING | Какая ИИ-модель была прокурором |
| judge_model | STRING | Какая ИИ-модель была судьей |
| verdict | STRING | Результат |
| created_at | DATETIME | Дата создания |