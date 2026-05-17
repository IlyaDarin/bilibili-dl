# bilibili-dl — Bilibili Video Downloader GUI

GUI-приложение для Windows с минимальным интерфейсом. Вставить ссылку → выбрать качество → скачать.

![screenshot](screenshot.png)

## Requirements

- Python 3.10+
- tkinter (идёт в комплекте с Python)
- curl (для Windows — скачать и положить в ту же папку или добавить в PATH)

## Установка

```bash
# клонировать
git clone https://github.com/IlyaDarin/bilibili-dl.git
cd bilibili-dl

# (опционально) скачать curl.exe для Windows
# https://curl.se/windows/
```

## Использование

```bash
python bilibili_gui.py
```

Или открыть двойным кликом.

## Интерфейс

1. Вставить ссылку (b23.tv или BV...)
2. Выбрать качество (360p / 480p / 720p / 1080p)
3. Нажать "Скачать"
4. Выбрать папку сохранения
5. Ждать завершения

## Структура

| Файл | Описание |
|------|----------|
| `bilibili_dl.py` | Python-ядро (API вызовы, скачивание) |
| `bilibili_gui.py` | tkinter GUI обёртка |
| `bilibili_dl.sh` | (Linux) оригинальный bash-скрипт |
