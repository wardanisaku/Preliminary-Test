#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import uuid
import random
import hashlib
from datetime import datetime, timedelta, date
from io import StringIO
from typing import Iterable, List, Tuple, Dict, Any

import psycopg2
from psycopg2.extras import execute_values
from faker import Faker

# -----------------------
# CONFIG
# -----------------------
DB_CONF = {
    "host": "localhost",
    "port": 5432,
    "dbname": "preliminary_test",
    "user": "postgres",
    "password": "postgres",
}

ORDERS_CSV = "orders.csv"
ORDER_DETAILS_CSV = "order_details.csv"
CHUNK_SIZE = 5000
SEED = 42

fake = Faker("id_ID")
random.seed(SEED)


# -----------------------
# HELPERS
# -----------------------
def short(s: str, n: int = 255) -> str:
    return s[:n] if isinstance(s, str) else s


def hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((password + salt).encode()).hexdigest()


def rand_dt(start: datetime, end: datetime) -> datetime:
    if start > end:
        start, end = end, start
    days = max(0, (end - start).days)
    return start + timedelta(days=random.randint(0, days))


def gen_phone() -> str:
    prefix = "08"
    total_len = random.randint(10, 14)
    rest_len = max(0, total_len - len(prefix))
    return prefix + "".join(random.choices("0123456789", k=rest_len))


def parse_date_str(s: Any) -> datetime:
    if isinstance(s, datetime):
        return s
    if isinstance(s, date):
        return datetime.combine(s, datetime.min.time())
    s = str(s).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    raise ValueError(f"Unknown date format: {s!r}")


# -----------------------
# CSV LOADERS (robust)
# -----------------------
def load_csv_dicts(path: str) -> List[Dict[str, Any]]:
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        return [dict(row) for row in r]


def load_orders(path: str) -> List[Dict[str, Any]]:
    rows = load_csv_dicts(path)
    required = {"id", "order_date", "user_id"}
    if not required.issubset(rows[0].keys()):
        raise ValueError(f"orders CSV must contain columns: {required}; found {list(rows[0].keys())}")
    out = []
    for r in rows:
        out.append({
            "id": int(r["id"]),
            "date": parse_date_str(r["order_date"]),
            "user_id": int(r["user_id"]),
        })
    return out


def load_order_details(path: str) -> List[Dict[str, Any]]:
    rows = load_csv_dicts(path)
    # auto-fix possible typo 'quality' -> 'quantity'
    if rows and "quality" in rows[0] and "quantity" not in rows[0]:
        for r in rows:
            r["quantity"] = r.get("quality")
    required = {"id", "order_date", "user_id", "product_id", "quantity"}
    if not rows:
        return []
    if not required.issubset(rows[0].keys()):
        raise ValueError(f"order_details CSV must contain columns: {required}; found {list(rows[0].keys())}")
    out = []
    for r in rows:
        out.append({
            "id": int(r["id"]),
            "order_date": parse_date_str(r["order_date"]),
            "user_id": int(r["user_id"]),
            "product_id": int(r["product_id"]),
            "quantity": float(r["quantity"]),
        })
    return out


# -----------------------
# GENERATORS (yield-chunks)
# -----------------------
def generate_users(sample_orders: List[Dict], sample_details: List[Dict],
                   num_users: int = 28000) -> Dict[int, Dict]:
    users = {}
    for i in range(1, num_users + 1):
        salt = uuid.uuid4().hex
        users[i] = {
            "id": i,
            "name": short(fake.name()),
            "email": short(fake.unique.email()),
            "phone": gen_phone(),
            "password_hash": hash_password("password123", salt),
            "salt": salt,
            "photo": fake.image_url(),
            "status": random.randint(1, 3),
        }
    # ensure CSV users exist
    for s in sample_orders + sample_details:
        uid = int(s["user_id"])
        if uid not in users:
            salt = uuid.uuid4().hex
            users[uid] = {
                "id": uid,
                "name": short(fake.name()),
                "email": f"dummy_{uid}@mail.com",
                "phone": gen_phone(),
                "password_hash": hash_password("password123", salt),
                "salt": salt,
                "photo": fake.image_url(),
                "status": 1,
            }
    return users


def generate_user_locations(users: Dict[int, Dict], num_locations: int = 28000) -> Dict[int, Dict]:
    CITY_POOL = [fake.city() for _ in range(500)]
    ADDR_POOL = [fake.address().replace("\n", ", ") for _ in range(500)]
    user_locations = {}
    user_keys = list(users.keys())
    for i in range(1, num_locations + 1):
        uid = random.choice(user_keys)
        user_locations[i] = {
            "id": i,
            "type": random.randint(1, 3),
            "status": random.randint(1, 3),
            "user_id": uid,
            "location": random.choice(CITY_POOL),
            "address": random.choice(ADDR_POOL),
        }
    return user_locations


def ensure_user_location(uid: int, user_locations: Dict[int, Dict]) -> int:
    # cheap lookup: try to find existing (first hit)
    for lid, loc in user_locations.items():
        if loc["user_id"] == uid:
            return lid
    new_id = max(user_locations.keys()) + 1 if user_locations else 1
    user_locations[new_id] = {
        "id": new_id,
        "type": 1,
        "status": 1,
        "user_id": uid,
        "location": fake.city(),
        "address": fake.address().replace("\n", ", "),
    }
    return new_id


def generate_orders(sample_orders: List[Dict], users: Dict[int, Dict],
                    n_random: int = 10000) -> Dict[int, Dict]:
    orders = {}
    start = datetime(2020, 1, 1)
    end = datetime(2024, 1, 1)
    next_oid = 1
    user_keys = list(users.keys())

    for _ in range(n_random):
        dt = rand_dt(start, end)
        uid = random.choice(user_keys)
        orders[next_oid] = {
            "id": next_oid,
            "user_id": uid,
            "status": random.randint(1, 4),
            "created_at": dt,
            "updated_at": dt + timedelta(days=random.randint(0, 10))
        }
        next_oid += 1

    # insert sample_orders preserving their IDs
    for s in sample_orders:
        orders[s["id"]] = {
            "id": s["id"],
            "user_id": s["user_id"],
            "status": 1,
            "created_at": s["date"],
            "updated_at": s["date"],
        }
    return orders


def generate_products(sample_details: List[Dict], n_products: int = 50,
                      n_categories: int = 12, n_rel: int = 80):
    categories = [(i, fake.word().capitalize()) for i in range(1, n_categories + 1)]
    products = {}
    for i in range(1, n_products + 1):
        eff = date(2021, 1, 1)
        products[i] = {
            "id": i,
            "name": f"{fake.word().capitalize()} {fake.word().capitalize()}",
            "effective_date": eff,
            "effective_until": eff + timedelta(days=random.randint(100, 800)),
            "photo": fake.image_url(),
            "price": round(random.uniform(10, 2000), 2),
            "status": random.randint(1, 3),
        }
    for d in sample_details:
        pid = d["product_id"]
        if pid not in products:
            products[pid] = {
                "id": pid,
                "name": f"Dummy Product {pid}",
                "effective_date": date(2021, 1, 1),
                "effective_until": date(2022, 1, 1),
                "photo": fake.image_url(),
                "price": 999.0,
                "status": 1,
            }
    p_ids = list(products.keys())
    c_ids = [c[0] for c in categories]
    product_cat = [(i, random.choice(p_ids), random.choice(c_ids)) for i in range(1, n_rel + 1)]
    return categories, products, product_cat


# -----------------------
# FAST order_details builder using O(1) index
# -----------------------
def build_order_index(orders: Dict[int, Dict]) -> Dict[Tuple[int, date], int]:
    idx = {}
    for oid, o in orders.items():
        key = (o["user_id"], o["created_at"].date())
        # first come wins; if multiple orders for same (user,date) prefer existing
        if key not in idx:
            idx[key] = oid
    return idx


def generate_order_details(sample_details: List[Dict],
                           orders: Dict[int, Dict],
                           user_locations: Dict[int, Dict],
                           n_random: int = 20000) -> List[Tuple]:
    # we build a list small enough to insert in chunks, but we avoid O(N^2) matching
    order_details = []
    next_od = 1
    order_index = build_order_index(orders)

    # random generated details
    order_ids = list(orders.keys())
    for _ in range(n_random):
        oid = random.choice(order_ids)
        uid = orders[oid]["user_id"]
        loc = ensure_user_location(uid, user_locations)
        qty = round(random.uniform(1, 5), 2)
        delivery = rand_dt(orders[oid]["created_at"], orders[oid]["created_at"] + timedelta(days=5)).date()
        status = random.randint(1, 6)
        order_details.append((next_od, loc, oid, random.choice(list(range(1, 51))), qty, delivery, status))
        next_od += 1

    # add sample details: match by (user_id, order_date)
    for s in sample_details:
        s_user = s["user_id"]
        s_date = s["order_date"].date()
        key = (s_user, s_date)
        oid_match = order_index.get(key)
        if oid_match is None:
            # create new order for this user & date
            oid_match = max(orders.keys()) + 1 if orders else 1
            orders[oid_match] = {
                "id": oid_match,
                "user_id": s_user,
                "status": 1,
                "created_at": s["order_date"],
                "updated_at": s["order_date"],
            }
            order_index[key] = oid_match
            order_ids.append(oid_match)
        loc = ensure_user_location(s_user, user_locations)
        order_details.append((next_od, loc, oid_match, s["product_id"], round(s["quantity"], 2), s_date, 1))
        next_od += 1

    return order_details


# -----------------------
# DB helpers (chunked inserts)
# -----------------------
def insert_chunked(cur, table: str, cols: List[str], rows_iter: Iterable[Tuple], chunk_size: int = CHUNK_SIZE):
    """Insert rows from an iterable in chunks using execute_values."""
    buf = []
    col_str = ",".join(cols)
    for r in rows_iter:
        buf.append(tuple(r))
        if len(buf) >= chunk_size:
            execute_values(cur, f"INSERT INTO {table} ({col_str}) VALUES %s", buf, page_size=chunk_size)
            buf.clear()
    if buf:
        execute_values(cur, f"INSERT INTO {table} ({col_str}) VALUES %s", buf, page_size=chunk_size)


# -----------------------
# MAIN
# -----------------------
def main():
    print("Loading CSV…")
    sample_orders = load_orders(ORDERS_CSV)
    sample_details = load_order_details(ORDER_DETAILS_CSV)
    print(f"Loaded {len(sample_orders)} sample orders, {len(sample_details)} sample order_details")

    # generate data
    print("Generating synthetic data…")
    users = generate_users(sample_orders, sample_details)
    user_locations = generate_user_locations(users)
    orders = generate_orders(sample_orders, users)
    categories, products, product_rel = generate_products(sample_details)
    order_details = generate_order_details(sample_details, orders, user_locations)

    print("Connecting to DB…")
    conn = psycopg2.connect(**DB_CONF)
    try:
        with conn:
            with conn.cursor() as cur:
                steps = [
                    ("ku_user_status", ["id", "name"], [(1, "active"), (2, "inactive"), (3, "banned")]),
                    ("ku_user", ["id", "name", "email", "phone", "password_hash", "salt", "photo", "status"],
                     ((v["id"], v["name"], v["email"], v["phone"], v["password_hash"], v["salt"], v["photo"], v["status"]) for v in users.values())),
                    ("ku_user_location_type", ["id", "name"], [(1, "home"), (2, "office"), (3, "warehouse")]),
                    ("ku_user_location_status", ["id", "name"], [(1, "active"), (2, "inactive"), (3, "deleted")]),
                    ("ku_user_location", ["id", "type", "status", "user_id", "location", "address"],
                     ((v["id"], v["type"], v["status"], v["user_id"], v["location"], v["address"]) for v in user_locations.values())),
                    ("ku_order_status", ["id", "name"], [(1,"pending"), (2,"success"), (3,"waiting_payment"),
                                                         (4,"error"), (5,"void"), (6,"user_cancel"),
                                                         (7,"payment_timeout"), (8,"refund_requested"),
                                                         (9,"refund_approved"), (10,"refund_declined")]),
                    ("ku_order", ["id", "user_id", "status", "created_at", "updated_at"],
                     ((v["id"], v["user_id"], v["status"], v["created_at"], v["updated_at"]) for v in orders.values())),
                    ("ku_product_status", ["id", "name"], [(1,"active"), (2,"inactive"), (3,"draft")]),
                    ("ku_category", ["id", "name"], categories),
                    ("ku_product", ["id", "name", "effective_date", "effective_until", "photo", "price", "status"],
                     ((v["id"], v["name"], v["effective_date"], v["effective_until"], v["photo"], v["price"], v["status"]) for v in products.values())),
                    ("ku_product_category", ["id", "product_id", "category_id"], product_rel),
                    ("ku_order_detail_status", ["id", "name"], [(1,"processing"),(2,"ready"),(3,"packed"),
                                                                (4,"shipped"),(5,"delivered"),(6,"canceled")]),
                    ("ku_order_detail", ["id", "user_location_id", "order_id", "product_id", "quantity", "delivery_date", "status"], order_details),
                ]

                print("Starting bulk insert (chunked)...")
                for idx, (table, cols, rows) in enumerate(steps, start=1):
                    print(f"  [{idx}/{len(steps)}] {table} ...", end="", flush=True)
                    # rows may be iterable/generator or list; ensure iterator
                    insert_chunked(cur, table, cols, iter(rows))
                    print(" done")

                # sync sequences for serials
                seqs = [
                    ("ku_user", "id"),
                    ("ku_user_location", "id"),
                    ("ku_order", "id"),
                    ("ku_product", "id"),
                    ("ku_product_category", "id"),
                    ("ku_order_detail", "id"),
                ]
                for tbl, col in seqs:
                    cur.execute(f"SELECT setval(pg_get_serial_sequence(%s,%s), COALESCE(MAX({col}),0)) FROM {tbl}", (tbl, col))

        print("All data inserted successfully.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
