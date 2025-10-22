import requests
import sqlite3
import time
from datetime import datetime

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "es-ES,es;q=0.9"
}
REQUEST_TIMEOUT = 15

def safe_get(url):
    """GET con headers/timeout y manejo de excepciones."""
    try:
        return requests.get(url, headers=DEFAULT_HEADERS, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as e:
        print(f"❌ Error de red al llamar {url}: {e}")
        return None

BASE_URL = "https://tienda.mercadona.es/api"
DB_PATH = "data/mercadona_prices.db"

# Lista para almacenar los cambios de precio detectados
price_changes = []

def init_db():
    """Inicializa la base de datos, incluyendo el unit_size en la tabla de productos."""
    print("📦 Inicializando base de datos...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Se añade la columna unit_size (tipo REAL) a la tabla products
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            name TEXT,
            last_price REAL,
            unit_size REAL,
            last_update TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT,
            name TEXT,
            old_price REAL,
            new_price REAL,
            change_date TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ Base de datos lista.")

def get_product_details(product_id):
    """Obtiene los detalles del producto y, si hay variación en el precio, lo almacena en price_changes.
       Además, extrae y guarda el unit_size."""
    retries = 3  # Número de intentos permitidos antes de abandonar
    attempt = 0

    while attempt < retries:
        print(f"🔍 Obteniendo detalles del producto ID {product_id} (Intento {attempt + 1}/{retries})...")
        url = f"{BASE_URL}/products/{product_id}"
        response = safe_get(url)
        if response is None:
            attempt += 1
            time.sleep(2)
            continue

        if response.status_code == 200:
            product_data = response.json()
            product_name = product_data.get("display_name", "Sin nombre")
            price_info = product_data.get("price_instructions", {})
            new_price = float(price_info.get("unit_price", 0))
            # Extraemos unit_size; si no existe se guarda como None
            unit_size = price_info.get("unit_size")
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            print(f"ℹ️ Procesando {product_name} ({new_price}€) - Unit size: {unit_size}")

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Verificar si el producto ya existe en la BD (ahora se recupera last_price y unit_size)
            cursor.execute("SELECT last_price, unit_size FROM products WHERE id = ?", (product_id,))
            result = cursor.fetchone()

            if result:
                old_price, old_unit_size = result
                if old_price != new_price:
                    change_msg = f"{product_name}: {old_price}€ → {new_price}€"
                    price_changes.append((product_id, product_name, old_price, new_price, now))
                    print(f"🔄 Cambio detectado en {product_name}: {old_price}€ → {new_price}€")
                    # Se insertan los cambios en el historial
                    cursor.execute('''
                        INSERT INTO price_history (product_id, name, old_price, new_price, change_date)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (product_id, product_name, old_price, new_price, now))
                # Actualizamos el producto con el nuevo precio, unit_size y la fecha
                cursor.execute("UPDATE products SET last_price = ?, unit_size = ?, last_update = ? WHERE id = ?",
                               (new_price, unit_size, now, product_id))
            else:
                print(f"✅ Nuevo producto detectado: {product_name} ({new_price}€) - Unit size: {unit_size}")
                cursor.execute("INSERT INTO products (id, name, last_price, unit_size, last_update) VALUES (?, ?, ?, ?, ?)",
                               (product_id, product_name, new_price, unit_size, now))
            conn.commit()
            conn.close()

            print(f"✔️ Información de {product_name} consultada.\n")
            time.sleep(0.1)  # Evita sobrecargar la API
            return
        else:
            print(f"❌ Error al obtener detalles del producto {product_id} (Código: {response.status_code})")
            attempt += 1
            time.sleep(2)  # Esperar 2 segundos antes de reintentar

    print(f"❌ No se pudo obtener los detalles del producto {product_id} tras {retries} intentos.")

def get_products(subcategory_id):
    """Obtiene los productos de una subcategoría y consulta sus precios."""
    print(f"📂 Consultando productos en la subcategoría ID {subcategory_id}...")
    url = f"{BASE_URL}/categories/{subcategory_id}"
    response = safe_get(url)
    if response is None:
        print(f"❌ Error de red al obtener productos de la subcategoría {subcategory_id}")
        return

    if response.status_code == 200:
        subcategory_data = response.json()
        if "products" in subcategory_data and isinstance(subcategory_data["products"], list):
            print(f"🔎 Se encontraron {len(subcategory_data['products'])} productos en esta subcategoría.")
            for product in subcategory_data["products"]:
                get_product_details(product["id"])
        if "categories" in subcategory_data and isinstance(subcategory_data["categories"], list):
            for subcat in subcategory_data["categories"]:
                if "products" in subcat and isinstance(subcat["products"], list):
                    print(f"📂 Subcategoría secundaria encontrada: ID {subcat['id']}...")
                    for product in subcat["products"]:
                        get_product_details(product["id"])
    else:
        print(f"❌ Error al obtener productos de la subcategoría {subcategory_id}")

def get_categories():
    """Recorre todas las categorías y obtiene los productos."""
    print("📌 Obteniendo lista de categorías...")
    url = f"{BASE_URL}/categories/"
    response = safe_get(url)
    if response is None:
        print("❌ Error de red al obtener categorías.")
        return

    if response.status_code == 200:
        categorias = response.json()
        if "results" in categorias:
            for category in categorias["results"]:
                print(f"📂 Procesando categoría: {category['name']}...")
                if "categories" in category:
                    for subcategory in category["categories"]:
                        print(f"📂 Procesando subcategoría: {subcategory['name']}...")
                        get_products(subcategory["id"])
    print("🔍 Proceso completado.")

def save_price_changes():
    """Guarda todos los cambios de precio (almacenados en price_changes) en la base de datos."""
    if not price_changes:
        print("✅ No hubo cambios de precios en esta ejecución.")
        return

    print("\n📥 Guardando cambios de precio en la base de datos...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for change in price_changes:
        product_id, product_name, old_price, new_price, now = change
        cursor.execute('''
            INSERT INTO price_history (product_id, name, old_price, new_price, change_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (product_id, product_name, old_price, new_price, now))
        # Actualizar el producto en la tabla principal (ya se hace en get_product_details, pero se refuerza aquí)
        cursor.execute("UPDATE products SET last_price = ?, last_update = ? WHERE id = ?",
                       (new_price, now, product_id))
    conn.commit()
    conn.close()
    print("✅ Cambios de precios guardados correctamente.")
    
def export_to_csv():
    """Exporta las tablas 'products' y 'price_history' a CSV en data_public/."""
    import os, csv

    os.makedirs("data_public", exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Export: products
    with open("data_public/products.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "name", "last_price", "unit_size", "last_update"])  # cabeceras
        for row in cursor.execute("""
            SELECT id, name, last_price, unit_size, last_update
            FROM products
            ORDER BY name COLLATE NOCASE
        """):
            w.writerow(row)

    # Export: price_history
    with open("data_public/price_history.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "product_id", "name", "old_price", "new_price", "change_date"])  # cabeceras
        for row in cursor.execute("""
            SELECT id, product_id, name, old_price, new_price, change_date
            FROM price_history
            ORDER BY change_date DESC, id DESC
        """):
            w.writerow(row)

    conn.close()
    print("📤 Exportación a CSV completada en data_public/")


if __name__ == "__main__":
    start_time = time.time()
    print("🚀 Iniciando proceso de actualización de precios...\n")

    try:
        init_db()
        get_categories()
        save_price_changes()
    finally:
        # Exporta CSV ocurra lo que ocurra
        try:
            export_to_csv()
        except Exception as e:
            print(f"⚠️ No se pudo exportar CSV: {e}")

    end_time = time.time()
    elapsed_time = end_time - start_time
    print("\n📌 Resumen de cambios de precios:")
    if price_changes:
        for change in price_changes:
            product_id, product_name, old_price, new_price, now = change
            print(f"🔄 {product_name}: {old_price}€ → {new_price}€")
    else:
        print("✅ No hubo cambios de precios en esta ejecución.")

    print(f"\n⏱️ Tiempo total de ejecución: {elapsed_time:.2f} segundos")
    print("🚀 Proceso finalizado con éxito.")


