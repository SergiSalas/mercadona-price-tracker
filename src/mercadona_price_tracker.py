import requests
import sqlite3
import time
from datetime import datetime

BASE_URL = "https://tienda.mercadona.es/api"
DB_PATH = "mercadona_prices.db"

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
        response = requests.get(url)

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
    response = requests.get(url)

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
    response = requests.get(url)

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

if __name__ == "__main__":
    start_time = time.time()  # Tiempo de inicio

    print("🚀 Iniciando proceso de actualización de precios...\n")
    init_db()  # Inicializar la base de datos
    get_categories()  # Obtener y procesar datos
    save_price_changes()  # Guardar cambios de precio al final

    end_time = time.time()  # Tiempo de finalización
    elapsed_time = end_time - start_time  # Tiempo total
    print("\n📌 Resumen de cambios de precios:")
    if price_changes:
        for change in price_changes:
            product_id, product_name, old_price, new_price, now = change
            print(f"🔄 {product_name}: {old_price}€ → {new_price}€")
    else:
        print("✅ No hubo cambios de precios en esta ejecución.")

    print(f"\n⏱️ Tiempo total de ejecución: {elapsed_time:.2f} segundos")
    print("🚀 Proceso finalizado con éxito.")


