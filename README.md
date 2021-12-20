# Secret Santa

## Setup
1. Создать файл `.env` из `.env.Exmaple`
2. `pip install -r requirements.txt`

## .env
1. `TELEGRAM_TOKEN` - токен от бота. Создать бота у [BotFather](https://t.me/botfather)
2. `SECRET_KEY` - Django SECRET_KEY
3. `DEBUG` - Django mode
4. `ALLOWED_HOSTS` - Настройка доверенных хостов. По дефолту: `['.localhost', '127.0.0.1', '[::1]', '.herokuapp.com']`
5. `DATABASE_URL` - настройка доступа к БД. Согласно [примеру](https://github.com/jacobian/dj-database-url#url-schema)
## Run
```
python manage.py migrate
python manage.py bot
```
Проект также подготовлен для деплоя на [Heroku](https://id.heroku.com/login)