# passworttool
Mailpasswörter auf uberspace setzen. In Python. yay.

## Installation

Im Wesentlichen nur zwei Stück: Flask und Waitress (als WSGI-Server). Am besten kommt das in einem venv daher. Etwa so:

```bash
$ git clone https://github.com/Queer-Lexikon/passworttool.git
$ cd passworttool
$ python3.9 -m venv venv
$ source venv/bin/activate/
$ pip install -r requirements.txt
```

Dann noch in `app.py` den uberspace-host vermerken. (Also den Teil vor .uber.space) und in `~/etc/services.d/` einen entsprechenden Service anlegen. 

```
[program:passworttool]
command=%(ENV_HOME)s/passworttool/venv/bin/python3 %(ENV_HOME)s/passworttool/app.py

autostart=no
autorestart=no
```

Dann läuft das, wenn über supervisord gestartet auf Port 8008 und kann für Zugriff von außen als [Web-Backend](https://manual.uberspace.de/web-backends/) eingerichtet werden. Smooth.

## Verwendung

Das ist ziemlich entspannt: Im Browser den entsprechenden Link zum eingerichteten Web-Backend aufrufen, Mailadresse und gewünschtes neues Passwort eingeben und bestätigen und dann wird das gesetzt.

Vorsicht: in dieser Fassung verifiziert nichts, ob die eingebende Person berechtigt ist, dieses Mailpasswort zu ändern. Deswegen am besten den Service für das Passworttool nur nach Bedarf starten und später wieder stoppen oder zum Beispiel über [flask-login](https://flask-login.readthedocs.io/en/latest/) oder so Authentifizierung verlangen. 

Das ist auch auf der Agenda hier, eine Unterstützung für einen Login über ldap einzuführen.

### Warum Waitress?
Weil keine Abhängigkeiten außerhalb der Standardbibliothek und weil der Werkzeug-WSGI nicht für das große weite Internet gemacht ist.
