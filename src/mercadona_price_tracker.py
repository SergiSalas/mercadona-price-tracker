import os
import csv
import sqlite3
import time
import requests
from datetime import datetime

# ── CONFIG ───────────────────────────────────────────────────────────────────────────────

BASE_URL = "https://tienda.mercadona.es/api"
DB_PATH  = "data/mercadona_prices.db"
SLEEP_REQ = 0.1   # segundos entre requests
RETRIES   = 3

DEFAULT_HEADERS = {
    "User-Agent":      "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Accept":          "application/json",
    "Accept-Language": "es-ES,es;q=0.9",
}

price_changes: list[tuple] = []


# ── TAXONOMÍA CANÓNICA ─────────────────────────────────────────────────────────────────
# Mercadona ya tiene categorías en español y bien estructuradas.
# El mapeo se aplica sobre el nombre de la subcategoría (nivel hoja).
# Se evalúan en orden: el primer match gana.

_CANONICAL_RULES: list[tuple[str, str]] = [
    # Lácteos
    ("lácteo",            "Lacteos"),
    ("leche",              "Lacteos"),
    ("yogur",              "Lacteos"),
    ("queso",              "Lacteos"),
    ("mantequilla",        "Lacteos"),
    ("nata ",              "Lacteos"),
    ("huevo",              "Lacteos"),
    ("mantecado",          "Lacteos"),
    # Carnes
    ("carne",              "Carnes"),
    (" ave ",              "Carnes"),
    ("aves ",              "Carnes"),
    ("embutido",           "Carnes"),
    ("charcutería",       "Carnes"),
    ("jamón",              "Carnes"),
    ("pollo",              "Carnes"),
    ("pavo",               "Carnes"),
    ("cerdo",              "Carnes"),
    ("ternera",            "Carnes"),
    ("vacuno",             "Carnes"),
    ("cordero",            "Carnes"),
    ("hamburguesa",        "Carnes"),
    ("salchicha",          "Carnes"),
    ("fuet",               "Carnes"),
    ("chorizo",            "Carnes"),
    ("bacon",              "Carnes"),
    ("longaniza",          "Carnes"),
    # Pescados y Mariscos
    ("pescado",            "Pescados y Mariscos"),
    ("marisco",            "Pescados y Mariscos"),
    ("atún",              "Pescados y Mariscos"),
    ("sardina",            "Pescados y Mariscos"),
    ("salmón",             "Pescados y Mariscos"),
    ("gamba",              "Pescados y Mariscos"),
    ("calamar",            "Pescados y Mariscos"),
    ("mejillón",           "Pescados y Mariscos"),
    ("bacalao",            "Pescados y Mariscos"),
    ("merluza",            "Pescados y Mariscos"),
    ("surimi",             "Pescados y Mariscos"),
    ("ahumado",            "Pescados y Mariscos"),
    # Frutas y Verduras
    ("fruta",              "Frutas y Verduras"),
    ("verdura",            "Frutas y Verduras"),
    ("hortaliza",          "Frutas y Verduras"),
    ("ensalada",           "Frutas y Verduras"),
    ("seta",               "Frutas y Verduras"),
    ("champiñón",          "Frutas y Verduras"),
    ("naranja",            "Frutas y Verduras"),
    ("melocotón",          "Frutas y Verduras"),
    ("piña",               "Frutas y Verduras"),
    ("plátano",            "Frutas y Verduras"),
    ("manzana",            "Frutas y Verduras"),
    ("tomate",             "Frutas y Verduras"),
    # Panadería
    ("pan ",               "Panaderia y Bolleria"),
    ("bollería",           "Panaderia y Bolleria"),
    ("pastelería",         "Panaderia y Bolleria"),
    ("galleta",            "Panaderia y Bolleria"),
    ("bizcocho",           "Panaderia y Bolleria"),
    ("croissant",          "Panaderia y Bolleria"),
    ("magdalena",          "Panaderia y Bolleria"),
    ("tostada",            "Panaderia y Bolleria"),
    # Congelados
    ("congelad",           "Congelados"),
    ("pizza",              "Congelados"),
    ("plato preparado",    "Congelados"),
    ("platos preparado",   "Congelados"),
    # Bebidas
    ("agua",               "Bebidas"),
    ("refresco",           "Bebidas"),
    ("cerveza",            "Bebidas"),
    ("vino",               "Bebidas"),
    ("cava",               "Bebidas"),
    ("zumo",               "Bebidas"),
    ("café",              "Bebidas"),
    ("cafe ",              "Bebidas"),
    ("infusión",           "Bebidas"),
    ("isótonic",           "Bebidas"),
    ("energétic",          "Bebidas"),
    ("tónica",             "Bebidas"),
    ("licor",              "Bebidas"),
    ("ginebra",            "Bebidas"),
    ("whisky",             "Bebidas"),
    (" ron ",              "Bebidas"),
    ("vodka",              "Bebidas"),
    ("vermut",             "Bebidas"),
    ("sangría",            "Bebidas"),
    ("bodega",             "Bebidas"),
    # Conservas
    ("conserva",           "Conservas"),
    ("enlatado",           "Conservas"),
    ("caldo",              "Conservas"),
    ("sopa",               "Conservas"),
    ("crema de",           "Conservas"),
    # Pasta, Arroz y Legumbres
    ("pasta",              "Pasta, Arroz y Legumbres"),
    ("arroz",              "Pasta, Arroz y Legumbres"),
    ("legumbre",           "Pasta, Arroz y Legumbres"),
    # Cereales y Desayunos
    ("cereal",             "Cereales y Desayunos"),
    ("desayuno",           "Cereales y Desayunos"),
    ("muesli",             "Cereales y Desayunos"),
    # Aceites y Condimentos
    ("aceite",             "Aceites y Condimentos"),
    ("vinagre",            "Aceites y Condimentos"),
    ("especia",            "Aceites y Condimentos"),
    ("salsa",              "Aceites y Condimentos"),
    ("mayonesa",           "Aceites y Condimentos"),
    ("ketchup",            "Aceites y Condimentos"),
    ("mostaza",            "Aceites y Condimentos"),
    ("sal ",               "Aceites y Condimentos"),
    # Snacks y Aperitivos
    ("aperitivo",          "Snacks y Aperitivos"),
    ("snack",              "Snacks y Aperitivos"),
    ("patatas fritas",     "Snacks y Aperitivos"),
    ("fruto seco",         "Snacks y Aperitivos"),
    ("aceituna",           "Snacks y Aperitivos"),
    ("encurtido",          "Snacks y Aperitivos"),
    # Dulces y Postres
    ("chocolate",          "Dulces y Postres"),
    ("dulce",              "Dulces y Postres"),
    ("postre",             "Dulces y Postres"),
    ("mermelada",          "Dulces y Postres"),
    (" miel ",             "Dulces y Postres"),
    ("cacao",              "Dulces y Postres"),
    ("chicle",             "Dulces y Postres"),
    ("gominola",           "Dulces y Postres"),
    ("golosina",           "Dulces y Postres"),
    ("caramelo",           "Dulces y Postres"),
    ("turrón",             "Dulces y Postres"),
    # Higiene Personal
    ("higiene",            "Higiene Personal"),
    ("cuidado personal",   "Higiene Personal"),
    ("cosmética",          "Higiene Personal"),
    ("perfumería",         "Higiene Personal"),
    ("farmacia",           "Higiene Personal"),
    ("dental",             "Higiene Personal"),
    ("maquillaje",         "Higiene Personal"),
    ("champú",             "Higiene Personal"),
    ("capilar",            "Higiene Personal"),
    ("cuidado del cabello","Higiene Personal"),
    ("gel ",               "Higiene Personal"),
    ("jabón",              "Higiene Personal"),
    ("desodorante",        "Higiene Personal"),
    ("crema ",             "Higiene Personal"),
    ("protector solar",    "Higiene Personal"),
    ("afeitado",           "Higiene Personal"),
    ("depilación",         "Higiene Personal"),
    ("compresa",           "Higiene Personal"),
    ("tampón",             "Higiene Personal"),
    # Limpieza del Hogar
    ("limpieza",           "Limpieza del Hogar"),
    ("detergente",         "Limpieza del Hogar"),
    ("hogar",              "Limpieza del Hogar"),
    ("fregasuelo",         "Limpieza del Hogar"),
    ("suavizante",         "Limpieza del Hogar"),
    ("lejía",              "Limpieza del Hogar"),
    ("lavavajilla",        "Limpieza del Hogar"),
    ("ambientador",        "Limpieza del Hogar"),
    ("insecticida",        "Limpieza del Hogar"),
    ("papel higiénico",    "Limpieza del Hogar"),
    ("papel de cocina",    "Limpieza del Hogar"),
    ("celulosa",           "Limpieza del Hogar"),
    # Bebés y Niños
    ("bebé",               "Bebes y Ninos"),
    ("infantil",           "Bebes y Ninos"),
    ("pañal",              "Bebes y Ninos"),
    # Mascotas
    ("mascota",            "Mascotas"),
    ("perro",              "Mascotas"),
    ("gato",               "Mascotas"),
    ("pienso",             "Mascotas"),
]


def get_canonical_category(subcategory_name: str) -> str:
    """
    Mapea el nombre de la subcategoría de Mercadona (en español) a la
    categoría canónica unificada compartida con BonPreu y Consum.

    Ejemplos:
        "Aceite, vinagre y sal"    → "Aceites y Condimentos"
        "Patatas fritas y snacks"  → "Snacks y Aperitivos"
        "Agua"                     → "Bebidas"
    """
    if not subcategory_name:
        return "Otros"
    name_lower = f" {subcategory_name.lower()} "
    for keyword, canonical in _CANONICAL_RULES:
        if keyword in name_lower:
            return canonical
    return "Otros"


# ── HTTP ───────────────────────────────────────────────────────────────────────────────

def safe_get(url: str) -> requests.Response | None:
    for attempt in range(1, RETRIES + 1):
        try:
            r = requests.get(url, headers=DEFAULT_HEADERS, timeout=15)
            if r.status_code == 200:
                return r
            print(f"  ⚠️  HTTP {r.status_code} — {url} (intento {attempt}/{RETRIES})")
        except requests.RequestException as e:
            print(f"  ❌ Error de red: {e} (intento {attempt}/{RETRIES})")
        time.sleep(2)
    return None


# ── DB ────────────────────────────────────────────────────────────────────────────────

def init_db() -> None:
    print("📦 Inicializando base de datos...")
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id                 TEXT PRIMARY KEY,
            name               TEXT,
            last_price         REAL,
            unit_size          REAL,
            image_url          TEXT,
            canonical_category TEXT,
            last_update        TIMESTAMP
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id  TEXT,
            name        TEXT,
            old_price   REAL,
            new_price   REAL,
            change_date TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')

    # Migración segura: añade columnas nuevas en DBs existentes
    _add_column_if_missing(cur, "products", "image_url",          "TEXT")
    _add_column_if_missing(cur, "products", "canonical_category", "TEXT")

    conn.commit()
    conn.close()
    print("✅ Base de datos lista.")


def _add_column_if_missing(cur: sqlite3.Cursor, table: str, column: str, col_type: str) -> None:
    cur.execute(f"PRAGMA table_info({table})")
    existing = {row[1] for row in cur.fetchall()}
    if column not in existing:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        print(f"  🔧 Columna '{column}' añadida a '{table}'")


# ── PROCESADO DE PRODUCTO ─────────────────────────────────────────────────────────────

def process_product(p: dict, subcategory_name: str) -> None:
    """
    Procesa un producto del listado de categoría de Mercadona.

    Todos los campos necesarios están disponibles en el dict del producto
    (display_name, price_instructions, thumbnail) — no hace falta llamar
    a /api/products/{id} individualmente.

    Mercadona no tiene precios de oferta tradicionales (offer_price siempre
    null). Las bajadas de precio se rastrean mediante price_history.
    """
    product_id = str(p.get("id", "")).strip()
    if not product_id:
        return

    name      = p.get("display_name", "Sin nombre").strip()
    thumbnail = p.get("thumbnail", "") or ""
    # El thumbnail viene como URL directa o puede ser None
    image_url = thumbnail.strip() if isinstance(thumbnail, str) else ""

    price_info = p.get("price_instructions", {})
    new_price  = float(price_info.get("unit_price") or 0)
    unit_size  = price_info.get("unit_size")   # REAL, puede ser None

    canonical_category = get_canonical_category(subcategory_name)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    cur.execute("SELECT last_price FROM products WHERE id = ?", (product_id,))
    row = cur.fetchone()

    if row:
        old_price = row[0]
        if old_price != new_price:
            arrow = "📈" if new_price > old_price else "📉"
            print(f"  {arrow} {name}: {old_price}€ → {new_price}€")
            price_changes.append((product_id, name, old_price, new_price, now))
            cur.execute('''
                INSERT INTO price_history (product_id, name, old_price, new_price, change_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (product_id, name, old_price, new_price, now))
        cur.execute('''
            UPDATE products
            SET name=?, last_price=?, unit_size=?, image_url=?,
                canonical_category=?, last_update=?
            WHERE id=?
        ''', (name, new_price, unit_size, image_url, canonical_category, now, product_id))
    else:
        cur.execute('''
            INSERT INTO products
                (id, name, last_price, unit_size, image_url, canonical_category, last_update)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (product_id, name, new_price, unit_size, image_url, canonical_category, now))

    conn.commit()
    conn.close()


# ── FETCH ─────────────────────────────────────────────────────────────────────────────

def get_products_for_subcategory(subcat_id: int, subcat_name: str) -> int:
    """
    Llama a /api/categories/{id} y procesa todos los productos del resultado.
    El endpoint devuelve productos con name, price y thumbnail sin necesidad
    de llamadas adicionales por producto.
    """
    response = safe_get(f"{BASE_URL}/categories/{subcat_id}")
    if response is None:
        print(f"  ❌ Saltando subcategoría '{subcat_name}' tras {RETRIES} intentos")
        return 0

    data  = response.json()
    count = 0

    # Los productos pueden estar directamente o dentro de sub-subcategorías
    for product in data.get("products", []):
        process_product(product, subcat_name)
        count += 1

    for sub in data.get("categories", []):
        sub_name = sub.get("name", subcat_name)
        for product in sub.get("products", []):
            process_product(product, sub_name)
            count += 1

    return count


def get_all_categories() -> None:
    print("📌 Obteniendo árbol de categorías...")
    response = safe_get(f"{BASE_URL}/categories/")
    if response is None:
        print("❌ Error de red al obtener categorías.")
        return

    data       = response.json()
    categories = data.get("results", [])
    grand_total = 0

    for category in categories:
        cat_name = category["name"]
        subcats  = category.get("categories", [])
        print(f"\n📂 {cat_name} ({len(subcats)} subcategorías)")

        for subcat in subcats:
            subcat_id   = subcat["id"]
            subcat_name = subcat["name"]
            print(f"  └─ {subcat_name}")
            n = get_products_for_subcategory(subcat_id, subcat_name)
            grand_total += n
            print(f"     ✔️ {n} productos")
            time.sleep(SLEEP_REQ)

    print(f"\n📊 Total productos procesados: {grand_total}")


# ── EXPORT CSV ──────────────────────────────────────────────────────────────────────────

def export_to_csv() -> None:
    os.makedirs("data_public", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    with open("data_public/products.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "name", "last_price", "unit_size",
                    "image_url", "canonical_category", "last_update"])
        for row in cur.execute("""
            SELECT id, name, last_price, unit_size,
                   image_url, canonical_category, last_update
            FROM products ORDER BY name COLLATE NOCASE
        """):
            w.writerow(row)

    with open("data_public/price_history.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "product_id", "name", "old_price", "new_price", "change_date"])
        for row in cur.execute("""
            SELECT id, product_id, name, old_price, new_price, change_date
            FROM price_history ORDER BY change_date DESC, id DESC
        """):
            w.writerow(row)

    conn.close()
    print("📤 CSV exportados en data_public/")


# ── MAIN ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    start = time.time()
    print("🚀 Iniciando actualización de precios Mercadona...\n")

    try:
        init_db()
        get_all_categories()
    finally:
        try:
            export_to_csv()
        except Exception as e:
            print(f"⚠️  No se pudo exportar CSV: {e}")

    elapsed = time.time() - start

    print("\n" + "═" * 50)
    print("📌 RESUMEN DE CAMBIOS DE PRECIO")
    print("═" * 50)
    if price_changes:
        for pid, name, old, new, ts in price_changes:
            d    = "📈" if new > old else "📉"
            diff = round(new - old, 2)
            sign = "+" if diff > 0 else ""
            print(f"  {d} {name}: {old}€ → {new}€  ({sign}{diff}€)")
        print(f"\n  Total cambios: {len(price_changes)}")
    else:
        print("  ✅ Sin cambios de precio en esta ejecución.")

    print(f"\n⏱️  Tiempo total: {elapsed:.1f}s")
    print("🏁 Proceso finalizado.")
