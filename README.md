# 🌐 🇬🇧 English Version

> 🇪🇸 *Desplázate hacia abajo para ver la versión en Español.*

---
# 🛒 Mercadona Price Tracker

Python script that tracks price changes in [Mercadona’s online store](https://tienda.mercadona.es) using its **public API**, storing data in a local **SQLite** database and logging every price variation with timestamp and `unit_size`.

> ⚠️ **For educational purposes only** — respect Mercadona’s Terms of Service and API rate limits.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey)
![Status](https://img.shields.io/badge/status-Active-brightgreen)

---

## ✨ Features

- Crawls all product categories and subcategories.  
- Detects and logs every price change automatically.  
- Saves `unit_size` when available.  
- Stores data in two tables:
  - **products** → current state  
  - **price_history** → all changes over time  

---

## 🧱 Database structure

| Table | Columns |
|--------|----------|
| **products** | id (PK), name, last_price, unit_size, last_update |
| **price_history** | id (PK), product_id (FK), name, old_price, new_price, change_date |

---

## ⚙️ Requirements

- **Python 3.10+**
- Dependencies:

```bash
pip install -r requirements.txt
or simply:

pip install requests

```

## ▶️ How to use
```bash
python src/mercadona_price_tracker.py
```
### Example output

🚀 Iniciando proceso de actualización de precios...
📦 Inicializando base de datos...
📌 Obteniendo lista de categorías...
🔄 Agua mineral: 0.45€ → 0.49€
✅ No hubo cambios de precios en esta ejecución.)

---

## 🧮 Useful SQLite queries

**Get latest 50 price changes**
SELECT * FROM price_history
ORDER BY change_date DESC
LIMIT 50;

**Find most frequently changing products**
SELECT name, COUNT(*) AS changes
FROM price_history
GROUP BY product_id
ORDER BY changes DESC
LIMIT 20;

---

## ⏱️ Automation (GitHub Actions)

This project runs on a scheduled **GitHub Actions** workflow:

- **Schedule (UTC):** `0 6 * * *` and `0 18 * * *`  
  > Note: GitHub schedules use **UTC**. In Madrid, that’s ~08:00 and ~20:00 during summer (CEST), and ~07:00 and ~19:00 in winter (CET).
- **What it does:** runs the tracker, exports data to CSV (`data_public/`), commits changes, and uploads an artifact with the CSV files.
- **Manual runs:** go to the **Actions** tab → *Scheduled run (Mercadona Price Tracker)* → **Run workflow**.
- **Artifacts:** each run uploads a ZIP with `products.csv` and `price_history.csv`.

**Workflow file:** `.github/workflows/scheduled-run.yml`  
**Public CSVs (versioned):** `data_public/products.csv`, `data_public/price_history.csv`


## 📝 License
MIT License © 2025 [Sergi Salas Andres]
See the LICENSE file for details.

---

# 🌐 🇪🇸 Versión en Español

> 🇬🇧 *Scroll up for the English version.*

---

## 🛒 Rastreador de Precios de Mercadona

Script en **Python** que rastrea los cambios de precios en la [tienda online de Mercadona](https://tienda.mercadona.es) utilizando su **API pública**, guardando los datos en una base de datos **SQLite** y registrando cada variación con su fecha y `unit_size`.

> ⚠️ **Solo con fines educativos** — respeta los Términos de Servicio de Mercadona y los límites de la API.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![SQLite](https://img.shields.io/badge/Base_de_datos-SQLite-lightgrey)
![Estado](https://img.shields.io/badge/estado-Activo-brightgreen)

---
## ✨ Características

- Recorre todas las categorías y subcategorías de la tienda.  
- Detecta y guarda automáticamente cada cambio de precio.  
- Registra el `unit_size` si está disponible.  
- Utiliza dos tablas:
  - **products** → estado actual  
  - **price_history** → histórico de cambios  

---

## 🧱 Estructura de la base de datos

| Tabla | Columnas |
|--------|----------|
| **products** | id (PK), name, last_price, unit_size, last_update |
| **price_history** | id (PK), product_id (FK), name, old_price, new_price, change_date |

---

## ⚙️ Requisitos

- **Python 3.10+**
- Dependencias:
- 
```bash
pip install -r requirements.txt
o simplemente:

pip install requests
```
## ▶️ Uso
```bash
python src/mercadona_price_tracker.py
```
### Ejemplo de salida

🚀 Iniciando proceso de actualización de precios...
📦 Inicializando base de datos...
📌 Obteniendo lista de categorías...
🔄 Agua mineral: 0.45€ → 0.49€
✅ No hubo cambios de precios en esta ejecución.)

---

## 🧮 Consultas útiles en SQLite

**Últimos 50 cambios de precio**
SELECT * FROM price_history
ORDER BY change_date DESC
LIMIT 50;

**Productos con más variaciones**
SELECT name, COUNT(*) AS cambios
FROM price_history
GROUP BY product_id
ORDER BY cambios DESC
LIMIT 20;

---

## ⏱️ Automatización (GitHub Actions)

Este proyecto se ejecuta con un workflow programado de **GitHub Actions**:

- **Horario (UTC):** `0 6 * * *` y `0 18 * * *`  
  > Nota: GitHub programa en **UTC**. En Madrid esto equivale aprox. a **08:00** y **20:00** en verano (CEST) y **07:00** y **19:00** en invierno (CET).
- **Qué hace:** ejecuta el tracker, exporta datos a CSV (`data_public/`), hace commit con los cambios y sube un artifact con los CSV.
- **Ejecución manual:** pestaña **Actions** → *Scheduled run (Mercadona Price Tracker)* → **Run workflow**.
- **Artifacts:** cada ejecución sube un ZIP con `products.csv` y `price_history.csv`.

**Workflow:** `.github/workflows/scheduled-run.yml`  
**CSVs públicos (versionados):** `data_public/products.csv`, `data_public/price_history.csv`

## 📝 Licencia
Licencia MIT © 2025 [Sergi Salas Andres]
Consulta el archivo LICENSE para más información.
