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

## 🗓️ Automate with Cron

Run every day at 8 AM:
```bash
0 8 * * * /ruta/a/python /ruta/al/repo/src/mercadona_price_tracker.py >> /ruta/al/repo/logs/cron.log 2>&1
```

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

## 🗓️ Automatización con Cron

Ejecutar cada día a las 8 AM:
```bash
0 8 * * * /ruta/a/python /ruta/al/repo/src/mercadona_price_tracker.py >> /ruta/al/repo/logs/cron.log 2>&1
```
## 📝 Licencia
Licencia MIT © 2025 [Sergi Salas Andres]
Consulta el archivo LICENSE para más información.
