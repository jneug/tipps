# Installation

**Tipps** ist auf dem Python-Framework [Flask](https://flask.palletsprojects.com) entwickelt worden und kann als WSGI-App auf kompatiblen Servern ausgeführt werden. In der [Flask Dokumentation](https://flask.palletsprojects.com/en/2.2.x/deploying/) finden sich weitere Informationen.

Im Folgenden findet sich eine detaillierte Anleitung, wie **Tipps** auf einem [Uberspace](https://uberspace.de) mit der Server-Software [gunicorn](https://gunicorn.org) ausgeführt werden kann.

## Tipps von GitHub klonen

```shell
git clone https://github.com/jneug/tipps.git
cd tipps
```

## Abhängigkeiten installieren

```shell
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Einen Admin-Nutzer einrichten

```shell
flask --app tipps user new username --admin
```

## Konfigurationsdatei anlegen

```shell
mkdir instance
vim instance/config.py
```

```python
SERVER_NAME = "127.0.0.1:5000"
BASE_URL = "http://127.0.0.1:5000"
SECRET_KEY = "bauen genutzt anders porsche"
```

## Tipps das erste Mal ausführen


