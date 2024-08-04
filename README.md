# passworttool
Mailpasswörter auf uberspace setzen. In Python. Mit OIDC-Login. yay.

## Installation

Im Wesentlichen nur zwei Stück: Flask und Waitress (als WSGI-Server). Am besten kommt das in einem venv daher. Etwa so:

```bash
$ git clone https://github.com/Queer-Lexikon/passworttool.git
$ cd passworttool
$ python3.11 -m venv venv
$ source venv/bin/activate/
$ pip install -r requirements.txt
```
Das ganze brauch entsprechend OIDC-Konfiguration, die mit ein paar Informationen zum Uberspace in eine Datei mit Namen `config.json` darf. 

```json
{
    "DOMAIN": "XXX",
    
    "OIDC_CLIENT_SECRETS": {
        "web": {
            "issuer": "",
            "auth_uri": "",
            "client_id": "",
            "client_secret": "",
            "redirect_uris": [
                "http://localhost:8008/*"
            ]
          
        }
    }
}
```
Die Redirect-Uri ist fine für lokales Testen, in Prod ist das wahrscheinlich eher ungefähr das, was in domain steht oder ein subdomain davon.
Alle Angaben innerhalb von Web kommen aus dem IDP. Alles davon, außer dem Client-Secret kann im Prinzip auch in Version-Control drin sein.

In `~/etc/services.d/` einen entsprechenden Service anlegen:

```
[program:passworttool]
command=%(ENV_HOME)s/passworttool/venv/bin/python3 %(ENV_HOME)s/passworttool/app.py

autostart=no
autorestart=no
```

Dann läuft das, wenn über supervisord gestartet auf Port 8008 und kann für Zugriff von außen als [Web-Backend](https://manual.uberspace.de/web-backends/) eingerichtet werden. Smooth.

## Verwendung

Das ist ziemlich entspannt: Im Browser den entsprechenden Link zum eingerichteten Web-Backend aufrufen, mit OIDC-Zugangsdaten einloggen, Mailadresse und gewünschtes neues Passwort eingeben und bestätigen und dann wird das gesetzt. 


### Warum Waitress?
Weil keine Abhängigkeiten außerhalb der Standardbibliothek und weil der Werkzeug-WSGI nicht für das große weite Internet gemacht ist. Im Prinzip sollte sich aber jeglicher WSGI-fähige Server dahinklemmen lassen. aus `create_app()` in der `app.py` fällt das passend Objekt raus, das zum Beispiel an gunicorn wie folgt anknoten lässt: `gunicorn -w 4 app:create_app`. Die Schreibweise mit dem Doppelpunkt ist auch für andere WSGI-Server üblich. Mit `python -m flask run` kommt das ganze auch im flask-developmentserver hoch. 

## Und sonst so?

Das hier läuft in der Infrastruktur vom Queer Lexikon, der Login gegen das Keycloak hier klappt, Python3.11 ist sowohl auf dem Dev-System als auch auf dem Uberspace-Host fine, andere Systeme oder Kombinationen sind nicht getestet, diesdas.
