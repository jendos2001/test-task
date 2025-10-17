## Тестовое задание
### Запуск проекта
1. Скопировать содержимое файла `.env.example` в `.env`.
2. В корне проекта выполнить команду `docker compose up --build`. Будут запущены 3 контейнера:
- На 8000 - Gateway
- На 8001 - ASR
- На 8082 - TTS

### Запуск клиента
1. Из корня проекта установить зависимости командой `pip install -r requirements.txt`
2. Перейти в папку с проектом командой `cd client`
3. Запустить один из клиентов командой:
- Скрипт `echo_bytes.py` запускается командой `python3 echo_bytes.py`
- Скрипт `stream_tts.py` запускается командой `python3 stream_tts.py`

### Запуск тестов
- Для сервиса TTS: `docker exec -it tts pytest -v tests/test_tts_service.py`

