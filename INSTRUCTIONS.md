## Käivitamise eeldused

Selle skripti edukaks käivitamiseks on vajalikud järgmised komponendid ja seadistused:

1.  **Python 3**:
    *   Skript on kirjutatud Python 3-s. Veendu, et sul on paigaldatud Python 3.6 või uuem versioon. Saad selle alla laadida [python.org](https://www.python.org/) lehelt.

2.  **Vajalikud Pythoni teegid**:
    *   Enne skripti käivitamist tuleb paigaldada järgmised Pythoni teegid. Seda saab teha `pip` käsuga:
        ```bash
        pip install pandas selenium beautifulsoup4 matplotlib
        ```

3.  **Mozilla Firefox veebilehitseja**:
    *   Skript kasutab Seleniumit koos Firefoxiga. Veendu, et Firefox on sinu süsteemi paigaldatud.

4.  **GeckoDriver**:
    *   `GeckoDriver` on vajalik Seleniumi ja Firefoxi vaheliseks suhtluseks.
    *   Lae alla oma operatsioonisüsteemile sobiv `geckodriver` versioon [Mozilla geckodriver releases](https://github.com/mozilla/geckodriver/releases) lehelt.
    *   **Oluline**: Pärast allalaadimist ja lahtipakkimist peab `geckodriver` käivitatav fail olema süsteemi `PATH` keskkonnamuutujas määratud kataloogis (nt `/usr/local/bin` Linuxis/macOS-is või lisades kausta tee Windowsi Environment Variables alla).