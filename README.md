# passworttool
Mailpasswörter auf uberspace setzen. In Python. Mit LDAP-Login. yay.

## Installation

Im Wesentlichen nur zwei Stück: Flask und Waitress (als WSGI-Server). Am besten kommt das in einem venv daher. Etwa so:

```bash
$ git clone https://github.com/Queer-Lexikon/passworttool.git
$ cd passworttool
$ python3.9 -m venv venv
$ source venv/bin/activate/
$ pip install -r requirements.txt
```
Das ganze brauch entsprechend LDAP-Konfiguration, die mit ein paar Informationen zum Uberspace in eine Datei mit Namen `config.json` darf. Für das Directory vom Queer Lexikon haben wir folgende Keys gebruacht, YMMV:

```json
{
    "UBERSPACE_HOST": "XXX.uberspace.de",
    "DOMAIN": "XXX",

    "SECRET_KEY": "XXX",
    "LDAP_PORT": 0,
    "LDAP_HOST": "XXX",
    "LDAP_USE_SSL": true,
    "LDAP_BIND_USER_DN": "XXX",
    "LDAP_BIND_USER_PASSWORD": "XXX",
    "LDAP_BASE_DN": "XXX",
    "LDAP_USER_DN": "XXX",
    "LDAP_GROUP_DN": "XXX",
    "LDAP_USER_RDN_ATTR": "XX",
    "LDAP_USER_LOGIN_ATTR": "XX",
    "LDAP_USER_OBJECT_FILTER": "(objectClass=people)",
    "LDAP_GROUP_OBJECT_FILTER": "(objectClass=groupOfNames)"
}
```
Die letzten beiden überschreiben defaults der Python-LDAP-Implementierung, die von Active Directories ausgehen.

In `~/etc/services.d/` einen entsprechenden Service anlegen:

```
[program:passworttool]
command=%(ENV_HOME)s/passworttool/venv/bin/python3 %(ENV_HOME)s/passworttool/app.py

autostart=no
autorestart=no
```

Dann läuft das, wenn über supervisord gestartet auf Port 8008 und kann für Zugriff von außen als [Web-Backend](https://manual.uberspace.de/web-backends/) eingerichtet werden. Smooth.

## Verwendung

Das ist ziemlich entspannt: Im Browser den entsprechenden Link zum eingerichteten Web-Backend aufrufen, mit LDAP-Zugangsdaten einloggen, Mailadresse und gewünschtes neues Passwort eingeben und bestätigen und dann wird das gesetzt. 


### Warum Waitress?
Weil keine Abhängigkeiten außerhalb der Standardbibliothek und weil der Werkzeug-WSGI nicht für das große weite Internet gemacht ist. Im Prinzip sollte sich aber jeglicher WSGI-fähige Server dahinklemmen lassen. aus `create_app()` in der `app.py` fällt das passend Objekt raus, das zum Beispiel an gunicorn wie folgt anknoten lässt: `gunicorn -w 4 app:create_app`. Die Schreibweise mit dem Doppelpunkt ist auch für andere WSGI-Server üblich. Mit `python -m flask run` kommt das ganze auch im flask-developmentserver hoch. 
