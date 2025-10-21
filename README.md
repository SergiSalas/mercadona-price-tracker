

Python script that tracks price changes in [Mercadona’s online store](https://tienda.mercadona.es) using its public API, storing data in a local **SQLite** database and logging every price variation with timestamp and `unit_size`.

> ⚠️ For **educational purposes only** — respect Mercadona’s Terms of Service and API rate limits.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey)
![Status](https://img.shields.io/badge/status-Active-brightgreen)

---

## ✨ Features
- Crawls all product categories and subcategories.
- Detects and logs every price change.
- Saves `unit_size` when available.
- Stores data in two tables:  
  - **products:** current state  
  - **price_history:** all changes over time

---

## 🧱 Database structure

| Table | Columns |
|--------|----------|
| **products** | id (PK), name, last_price, unit_size, last_update |
| **price_history** | id (PK), product_id (FK), name, old_price, new_price, change_date |

---

## ⚙️ Requirements
- Python 3.10+
- Dependencies:  
  ```bash
  pip install requests
  bash```
  
▶️ How to use
python src/mercadona_price_tracker.py

Example output:

🚀 Iniciando proceso de actualización de precios...
📦 Inicializando base de datos...
📌 Obteniendo lista de categorías...
🔄 Agua mineral: 0.45€ → 0.49€
✅ No hubo cambios de precios en esta ejecución.
🧮 Useful SQLite queries

-- Latest 50 price changes
SELECT * FROM price_history ORDER BY change_date DESC LIMIT 50;

-- Most frequently changing products
SELECT name, COUNT(*) AS changes
FROM price_history
GROUP BY product_id
ORDER BY changes DESC
LIMIT 20;


🗓️ Automate with Cron
Run every day at 8 AM:

0 8 * * * /ruta/a/python /ruta/al/repo/src/mercadona_price_tracker.py >> /ruta/al/repo/logs/cron.log 2>&1


📝 License
MIT License © 2025 [Sergi Salas Andres]
