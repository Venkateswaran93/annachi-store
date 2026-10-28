# Annachi Store - Website (Flask + SQLite, HTML & CSS only, no JavaScript)

## Run it
    python -m venv venv
    venv\Scripts\activate          (Windows)   |   source venv/bin/activate  (Mac/Linux)
    pip install -r requirements.txt
    python app.py
Open http://127.0.0.1:5000

## Owner panel
URL: /admin/login   Default password: annachi123
Change it before going live:
    set ADMIN_PASSWORD=YourPassword  (Windows)  |  export ADMIN_PASSWORD=YourPassword (Mac/Linux)
    set SECRET_KEY=any-long-random-text
From the panel you can add/delete products, mark stock/featured and read customer messages.

## Customise
- Shop name, phone, WhatsApp number, address, hours: top of app.py (STORE dictionary)
- Sample products and prices are only examples: edit them in app.py (SEED_PRODUCTS) or from the owner panel.
  To reset, delete instance/annachi.db and restart.
- Colours: variables at the top of static/css/style.css

## Going live
Use a production server (e.g. gunicorn app:app) and set ADMIN_PASSWORD and SECRET_KEY.
