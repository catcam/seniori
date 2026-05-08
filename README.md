# seniori.org

Web aplikacija za slušanje HRT Radija — dvije tipke, **VIJESTI** i **DNEVNIK**. Radi na svim uređajima u browseru, bez instalacije. Na iPhoneu se može dodati na početni ekran i ponaša se kao native app.

Dostupno na: **https://seniori.org**

## Kako radi

Flask backend na serveru fetcha HRT stranicu i izvlači MP3 link — browser to ne može sam zbog CORS-a. Frontend je čisti HTML/JS koji poziva `/api/vijesti` ili `/api/dnevnik` i dobiva JSON s MP3 URL-om i vremenom emitiranja.

```
Browser → nginx → Flask (gunicorn) → radio.hrt.hr
```

Isti scraper kao u Android verziji ([senior-radio](https://github.com/catcam/senior-radio)) — čita `__NEXT_DATA__` JSON koji Next.js ubacuje u stranicu, odatle `lastAvailableEpisode.audio.metadata[0].path`.

Cache je 15 minuta u memoriji — vijesti se mijenjaju svakih sat, nema potrebe fetchati na svaki klik.

## API

```
GET /api/vijesti  →  { url, broadcastStart, caption }
GET /api/dnevnik  →  { url, broadcastStart, caption }
```

Primjer odgovora:
```json
{
  "url": "https://api.hrt.hr/media/.../vijesti.mp3",
  "broadcastStart": "2026-05-09T12:00:00Z",
  "caption": "Vijesti 09.05."
}
```

## Pokretanje lokalno

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flask run
```

Aplikacija se pokreće na `http://localhost:5000`.

## Deploy (produkcija)

Gunicorn + nginx + Let's Encrypt. Systemd service drži proces živ:

```bash
# Start/restart
systemctl restart seniori

# Logovi
journalctl -u seniori -f
```

## Ako HRT promijeni strukturu stranice

Scraper čita `props.pageProps.cycle.data.radioCycle[0].lastAvailableEpisode` iz `__NEXT_DATA__` JSON-a. Ako HRT restrukturira Next.js podatke, popravi `fetch_episode()` u `app.py` — dovoljno je promijeniti putanju u JSON stablu.

## Struktura

```
app.py                  — Flask app, scraper, API endpointi
templates/index.html    — cijeli frontend (HTML + CSS + JS)
static/manifest.json    — PWA manifest (ikona, standalone mode)
requirements.txt        — flask, gunicorn
```

---

**Autori:** Nikša Barlović i Claude (Anthropic)
