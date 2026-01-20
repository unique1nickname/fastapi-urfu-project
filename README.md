# Как запустить

Запустить nats-server (заранее установить)
```sh
nats-server
```

Создать виртуальное окружение, скачать зависимости и запусить uvicorn сервер
<br>(пример с использованием пакетного менеджера UV)
```sh
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
cd app/
uvicorn main:app --reload
```
