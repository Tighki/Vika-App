"""SQLite: люди, заявки, экскурсии, брони, лавка, заказы, оценки, журнал.

Пароли хранятся как хеш. Повторный запуск не дублирует демонстрационные строки.
"""

import hashlib
import os
import re
import sqlite3
import sys
from datetime import datetime

ROLES = ("admin", "guide", "producer", "tourist")
THEMES = ("nature", "history", "gastro", "city", "active", "other")
REGIONS = ("karelia", "altai", "golden_ring", "kaliningrad", "baikal", "other")
PRIORITIES = ("low", "normal", "high")
REQUEST_STATUSES = ("new", "assigned", "done", "cancelled")
TOUR_STATUSES = ("open", "full", "completed", "cancelled")
BOOKING_STATUSES = ("confirmed", "completed", "cancelled")
ORDER_STATUSES = ("new", "accepted", "ready", "completed", "cancelled")
PRODUCT_CATEGORIES = ("food", "drink", "craft", "souvenir")
REVIEW_KINDS = ("guide", "tour", "product")

ROLE_RU = {
    "admin": "Администратор",
    "guide": "Гид",
    "producer": "Производитель",
    "tourist": "Турист",
}
THEME_RU = {
    "nature": "Природа",
    "history": "История",
    "gastro": "Гастрономия",
    "city": "Город",
    "active": "Активный отдых",
    "other": "Универсальный",
}
REGION_RU = {
    "karelia": "Карелия",
    "altai": "Алтай",
    "golden_ring": "Золотое кольцо",
    "kaliningrad": "Калининград",
    "baikal": "Байкал",
    "other": "Любой регион",
}
PRIORITY_RU = {
    "low": "Низкий",
    "normal": "Обычный",
    "high": "Высокий",
}
REQUEST_STATUS_RU = {
    "new": "Новая",
    "assigned": "Назначена",
    "done": "Завершена",
    "cancelled": "Отменена",
}
TOUR_STATUS_RU = {
    "open": "Есть места",
    "full": "Мест нет",
    "completed": "Завершена",
    "cancelled": "Отменена",
}
BOOKING_STATUS_RU = {
    "confirmed": "Подтверждена",
    "completed": "Завершена",
    "cancelled": "Отменена",
}
ORDER_STATUS_RU = {
    "new": "Новый",
    "accepted": "Принят",
    "ready": "Готов",
    "completed": "Выдан",
    "cancelled": "Отменён",
}
PRODUCT_CATEGORY_RU = {
    "food": "Еда",
    "drink": "Напитки",
    "craft": "Ремесло",
    "souvenir": "Сувенир",
}

ORDER_FLOW = {
    "new": {"accepted", "cancelled"},
    "accepted": {"ready", "cancelled"},
    "ready": {"completed", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}


def _app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def db_path():
    override = os.environ.get("TRAVELHUB_DB")
    if override:
        parent = os.path.dirname(os.path.abspath(override))
        if parent:
            os.makedirs(parent, exist_ok=True)
        return override
    root = _app_dir()
    data_dir = os.path.join(root, "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "travelhub.db")


def connect():
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today():
    return datetime.now().strftime("%Y-%m-%d")


def hash_password(password, salt=None):
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password, stored):
    try:
        salt_hex, _digest = stored.split("$", 1)
    except ValueError:
        return False
    return hash_password(password, bytes.fromhex(salt_hex)) == stored


def _public(row):
    if row is None:
        return None
    data = dict(row)
    data.pop("password", None)
    return data


def init_db():
    conn = connect()
    with conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                login       TEXT NOT NULL UNIQUE,
                password    TEXT NOT NULL,
                full_name   TEXT NOT NULL,
                role        TEXT NOT NULL DEFAULT 'tourist'
                                CHECK (role IN ('admin', 'guide', 'producer', 'tourist')),
                specialty   TEXT NOT NULL DEFAULT 'other',
                region      TEXT NOT NULL DEFAULT 'other',
                about       TEXT NOT NULL DEFAULT '',
                is_active   INTEGER NOT NULL DEFAULT 1,
                created_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS requests (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                title           TEXT NOT NULL,
                description     TEXT NOT NULL DEFAULT '',
                theme           TEXT NOT NULL DEFAULT 'other',
                region          TEXT NOT NULL DEFAULT 'other',
                people          INTEGER NOT NULL DEFAULT 1 CHECK (people > 0),
                preferred_date  TEXT NOT NULL DEFAULT '',
                priority        TEXT NOT NULL DEFAULT 'normal',
                status          TEXT NOT NULL DEFAULT 'new',
                tourist_id      INTEGER NOT NULL REFERENCES users(id),
                guide_id        INTEGER REFERENCES users(id),
                created_at      TEXT NOT NULL
            );

            CREATE UNIQUE INDEX IF NOT EXISTS ux_open_request
            ON requests(tourist_id, title)
            WHERE status IN ('new', 'assigned');

            CREATE TABLE IF NOT EXISTS tours (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                title           TEXT NOT NULL,
                description     TEXT NOT NULL DEFAULT '',
                theme           TEXT NOT NULL,
                region          TEXT NOT NULL,
                tour_date       TEXT NOT NULL,
                duration_hours  INTEGER NOT NULL CHECK (duration_hours > 0),
                price           INTEGER NOT NULL CHECK (price > 0),
                capacity        INTEGER NOT NULL CHECK (capacity > 0),
                guide_id        INTEGER NOT NULL REFERENCES users(id),
                status          TEXT NOT NULL DEFAULT 'open',
                created_at      TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS bookings (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                tour_id     INTEGER NOT NULL REFERENCES tours(id),
                tourist_id  INTEGER NOT NULL REFERENCES users(id),
                people      INTEGER NOT NULL CHECK (people > 0),
                status      TEXT NOT NULL DEFAULT 'confirmed',
                created_at  TEXT NOT NULL
            );

            CREATE UNIQUE INDEX IF NOT EXISTS ux_booking_active
            ON bookings(tour_id, tourist_id)
            WHERE status = 'confirmed';

            CREATE TABLE IF NOT EXISTS products (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                producer_id  INTEGER NOT NULL REFERENCES users(id),
                name         TEXT NOT NULL,
                description  TEXT NOT NULL DEFAULT '',
                category     TEXT NOT NULL,
                price        INTEGER NOT NULL CHECK (price > 0),
                stock        INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
                is_active    INTEGER NOT NULL DEFAULT 1,
                created_at   TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS orders (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                tourist_id   INTEGER NOT NULL REFERENCES users(id),
                producer_id  INTEGER NOT NULL REFERENCES users(id),
                status       TEXT NOT NULL DEFAULT 'new',
                total        INTEGER NOT NULL CHECK (total >= 0),
                created_at   TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id    INTEGER NOT NULL REFERENCES orders(id),
                product_id  INTEGER NOT NULL REFERENCES products(id),
                name        TEXT NOT NULL,
                qty         INTEGER NOT NULL CHECK (qty > 0),
                price       INTEGER NOT NULL CHECK (price > 0)
            );

            CREATE TABLE IF NOT EXISTS reviews (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                author_id   INTEGER NOT NULL REFERENCES users(id),
                target_kind TEXT NOT NULL,
                target_id   INTEGER NOT NULL,
                rating      INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                body        TEXT NOT NULL DEFAULT '',
                created_at  TEXT NOT NULL,
                UNIQUE (author_id, target_kind, target_id)
            );

            CREATE TABLE IF NOT EXISTS messages (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id  INTEGER NOT NULL REFERENCES requests(id),
                user_id     INTEGER NOT NULL REFERENCES users(id),
                body        TEXT NOT NULL,
                created_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_kind TEXT NOT NULL,
                entity_id   INTEGER NOT NULL,
                user_id     INTEGER,
                action      TEXT NOT NULL,
                created_at  TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS ix_requests_tourist ON requests(tourist_id);
            CREATE INDEX IF NOT EXISTS ix_requests_guide ON requests(guide_id);
            CREATE INDEX IF NOT EXISTS ix_tours_guide ON tours(guide_id);
            CREATE INDEX IF NOT EXISTS ix_bookings_tour ON bookings(tour_id);
            CREATE INDEX IF NOT EXISTS ix_bookings_tourist ON bookings(tourist_id);
            CREATE INDEX IF NOT EXISTS ix_products_producer ON products(producer_id);
            CREATE INDEX IF NOT EXISTS ix_orders_tourist ON orders(tourist_id);
            CREATE INDEX IF NOT EXISTS ix_orders_producer ON orders(producer_id);
            CREATE INDEX IF NOT EXISTS ix_messages_request ON messages(request_id);
            CREATE INDEX IF NOT EXISTS ix_history_entity ON history(entity_kind, entity_id);
            """
        )
    _seed(conn)
    conn.close()


def _seed(conn):
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        with conn:
            conn.execute(
                "INSERT INTO users (login, password, full_name, role, specialty, region, about, created_at)"
                " VALUES (?, ?, ?, 'admin', 'other', 'other', ?, ?)",
                ("admin", hash_password("admin"), "Администратор TravelHub", "Ведёт каталог, людей и распределение заявок.", "2026-08-01 09:00:00"),
            )
    _seed_demo(conn)


def _seed_demo(conn):
    people = (
        ("sokolov", "guide", "Алексей Соколов", "guide", "nature", "karelia", "Вожу по Карелии: водопады, шхеры, острова."),
        ("belova", "guide", "Ирина Белова", "guide", "history", "golden_ring", "Историк, маршруты по Золотому кольцу."),
        ("kuznetsov", "guide", "Дмитрий Кузнецов", "guide", "gastro", "kaliningrad", "Гастрономические прогулки по Калининграду."),
        ("morozova", "guide", "Наталья Морозова", "guide", "city", "baikal", "Городские маршруты на Байкале."),
        ("volkova", "guide", "Анна Волкова", "guide", "active", "altai", "Пешие выходы по Алтаю."),
        ("lebedev", "guide", "Павел Лебедев", "guide", "other", "other", "Беру разные направления, если коллеги заняты."),
        ("pavlova", "producer", "Марина Павлова", "producer", "other", "altai", "Пасека в Уймонской долине."),
        ("romanova", "producer", "Елена Романова", "producer", "other", "karelia", "Береста и лён, мастерская в Петрозаводске."),
        ("orlov", "producer", "Сергей Орлов", "producer", "other", "kaliningrad", "Копчение рыбы и сладости, Калининград."),
        ("ivanova", "tourist", "Анна Иванова", "tourist", "other", "karelia", ""),
        ("petrov", "tourist", "Игорь Петров", "tourist", "other", "golden_ring", ""),
        ("smirnova", "tourist", "Ольга Смирнова", "tourist", "other", "kaliningrad", ""),
    )
    with conn:
        for login, password, full_name, role, specialty, region, about in people:
            if conn.execute("SELECT 1 FROM users WHERE login = ?", (login,)).fetchone():
                continue
            conn.execute(
                "INSERT INTO users (login, password, full_name, role, specialty, region, about, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (login, hash_password(password), full_name, role, specialty, region, about, "2026-08-15 10:00:00"),
            )
    if conn.execute("SELECT COUNT(*) FROM tours").fetchone()[0]:
        return

    ids = {
        row["login"]: row["id"]
        for row in conn.execute("SELECT id, login FROM users").fetchall()
    }

    def add_tour(key, title, description, theme, region, tour_date, hours, price, capacity, guide, status, created):
        cur = conn.execute(
            "INSERT INTO tours (title, description, theme, region, tour_date, duration_hours, price, capacity, guide_id, status, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (title, description, theme, region, tour_date, hours, price, capacity, ids[guide], status, created),
        )
        tour_id = cur.lastrowid
        _log(conn, "tour", tour_id, ids[guide], "Экскурсия опубликована", created)
        if status == "completed":
            _log(conn, "tour", tour_id, ids[guide], "Статус: Завершена", tour_date + " 18:00:00")
        if status == "full":
            _log(conn, "tour", tour_id, None, "Свободных мест не осталось", created)
        tours[key] = tour_id

    def add_booking(tour_key, tourist, people_count, status, created):
        cur = conn.execute(
            "INSERT INTO bookings (tour_id, tourist_id, people, status, created_at) VALUES (?, ?, ?, ?, ?)",
            (tours[tour_key], ids[tourist], people_count, status, created),
        )
        action = "Бронь оформлена" if status == "confirmed" else "Бронь завершена вместе с экскурсией"
        _log(conn, "booking", cur.lastrowid, ids[tourist], action, created)

    def add_request(title, description, theme, region, people_count, preferred, priority, tourist, guide, status, created):
        cur = conn.execute(
            "INSERT INTO requests (title, description, theme, region, people, preferred_date, priority, status, tourist_id, guide_id, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                title,
                description,
                theme,
                region,
                people_count,
                preferred,
                priority,
                status,
                ids[tourist],
                ids[guide] if guide else None,
                created,
            ),
        )
        request_id = cur.lastrowid
        _log(conn, "request", request_id, ids[tourist], "Заявка создана", created)
        if guide:
            name = conn.execute("SELECT full_name FROM users WHERE id = ?", (ids[guide],)).fetchone()["full_name"]
            _log(conn, "request", request_id, None, f"Назначен гид: {name}", created)
        if status == "done":
            _log(conn, "request", request_id, ids[guide], "Статус: Завершена", created)
        return request_id

    def add_product(key, producer, name, description, category, price, stock):
        cur = conn.execute(
            "INSERT INTO products (producer_id, name, description, category, price, stock, is_active, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, 1, ?)",
            (ids[producer], name, description, category, price, stock, "2026-09-01 11:00:00"),
        )
        products[key] = {"id": cur.lastrowid, "producer": producer, "name": name, "price": price}

    def add_order(tourist, product_key, qty, status, created):
        product = products[product_key]
        total = product["price"] * qty
        cur = conn.execute(
            "INSERT INTO orders (tourist_id, producer_id, status, total, created_at) VALUES (?, ?, ?, ?, ?)",
            (ids[tourist], ids[product["producer"]], status, total, created),
        )
        order_id = cur.lastrowid
        conn.execute(
            "INSERT INTO order_items (order_id, product_id, name, qty, price) VALUES (?, ?, ?, ?, ?)",
            (order_id, product["id"], product["name"], qty, product["price"]),
        )
        _log(conn, "order", order_id, ids[tourist], "Заказ оформлен", created)
        if status != "new":
            _log(conn, "order", order_id, ids[product["producer"]], f"Статус: {ORDER_STATUS_RU[status]}", created)
        return order_id

    def add_review(author, kind, target_id, rating, body, created):
        conn.execute(
            "INSERT INTO reviews (author_id, target_kind, target_id, rating, body, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (ids[author], kind, target_id, rating, body, created),
        )

    tours = {}
    products = {}
    with conn:
        add_tour(
            "ruskeala",
            "Рускеала: мрамор и водопады",
            "Пеший маршрут по каньону, подземному озеру и смотровым. Обувь непромокаемая.",
            "nature", "karelia", "2026-10-18", 4, 3500, 8, "sokolov", "open", "2026-09-20 12:00:00",
        )
        add_tour(
            "suzdal",
            "Суздаль за один день",
            "Кремль, торговые ряды и монастыри. Обед в трапезной входит в цену.",
            "history", "golden_ring", "2026-10-24", 8, 5200, 12, "belova", "open", "2026-09-18 12:00:00",
        )
        add_tour(
            "marzipan",
            "Калининград: сыр, марципан и порт",
            "Рынок, сыроварня и короткая остановка у производителя копчёной рыбы.",
            "gastro", "kaliningrad", "2026-10-20", 5, 4100, 10, "kuznetsov", "open", "2026-09-21 12:00:00",
        )
        add_tour(
            "listvyanka",
            "Листвянка и нерпинарий",
            "Набережная, рынок омуля и нерпы. Подходит для первой поездки на Байкал.",
            "city", "baikal", "2026-11-03", 6, 4800, 8, "morozova", "open", "2026-09-22 12:00:00",
        )
        add_tour(
            "chuy",
            "Чуйский тракт: смотровые площадки",
            "Выезд на смотровые, чай на перевале. Нужна куртка от ветра.",
            "active", "altai", "2026-10-28", 7, 6400, 6, "volkova", "open", "2026-09-19 12:00:00",
        )
        add_tour(
            "ladoga",
            "Ладожские шхеры без спешки",
            "Короткая прогулка по берегу и смотровым. Темп спокойный, дети допустимы.",
            "nature", "karelia", "2026-10-19", 3, 2800, 2, "lebedev", "full", "2026-09-25 12:00:00",
        )
        add_tour(
            "valaam",
            "Валаам: монастырь и бухты",
            "Прошедшая поездка: скиты, внутренние бухты и обратный катер.",
            "history", "karelia", "2026-09-12", 9, 7900, 15, "sokolov", "completed", "2026-08-20 12:00:00",
        )
        add_tour(
            "vladimir",
            "Владимир: соборы и вал",
            "Прошедшая поездка по Успенскому и Дмитриевскому соборам.",
            "history", "golden_ring", "2026-09-06", 6, 4600, 12, "belova", "completed", "2026-08-18 12:00:00",
        )
        add_tour(
            "gates",
            "Кёнигсбергские ворота и кухня",
            "Прошедший маршрут: ворота, кафе с местной выпечкой и порт.",
            "gastro", "kaliningrad", "2026-09-03", 4, 3600, 10, "kuznetsov", "completed", "2026-08-16 12:00:00",
        )

        add_booking("ruskeala", "ivanova", 2, "confirmed", "2026-10-02 14:10:00")
        add_booking("ruskeala", "petrov", 4, "confirmed", "2026-10-04 11:20:00")
        add_booking("suzdal", "petrov", 1, "confirmed", "2026-10-03 09:40:00")
        add_booking("marzipan", "smirnova", 2, "confirmed", "2026-10-05 16:05:00")
        add_booking("listvyanka", "petrov", 1, "confirmed", "2026-10-06 13:15:00")
        add_booking("chuy", "smirnova", 2, "confirmed", "2026-10-07 18:45:00")
        add_booking("ladoga", "ivanova", 2, "confirmed", "2026-10-01 10:00:00")
        add_booking("valaam", "ivanova", 2, "completed", "2026-08-21 10:00:00")
        add_booking("valaam", "petrov", 1, "completed", "2026-08-22 10:00:00")
        add_booking("vladimir", "petrov", 2, "completed", "2026-08-19 10:00:00")
        add_booking("vladimir", "smirnova", 1, "completed", "2026-08-19 12:00:00")
        add_booking("gates", "ivanova", 1, "completed", "2026-08-17 10:00:00")
        add_booking("gates", "smirnova", 2, "completed", "2026-08-17 11:30:00")

        add_review("ivanova", "guide", ids["sokolov"], 5, "На Валааме всё по времени, детям было интересно.", "2026-09-13 19:00:00")
        add_review("petrov", "guide", ids["sokolov"], 4, "Хороший маршрут, на катере было тесно.", "2026-09-13 20:10:00")
        add_review("ivanova", "tour", tours["valaam"], 5, "Бухты красивые, гид не торопил группу.", "2026-09-13 19:05:00")
        add_review("petrov", "guide", ids["belova"], 5, "Соборы объяснила просто, без лекции на час.", "2026-09-07 18:00:00")
        add_review("smirnova", "guide", ids["belova"], 4, "Интересно, но обед затянулся.", "2026-09-07 18:20:00")
        add_review("ivanova", "guide", ids["kuznetsov"], 5, "Марципан и порт сложились в один понятный день.", "2026-09-04 17:40:00")
        add_review("smirnova", "guide", ids["kuznetsov"], 4, "Вкусно, группа в кафе была великовата.", "2026-09-04 18:00:00")

        done_id = add_request(
            "Золотое кольцо: Владимир и Суздаль",
            "Нужен был исторический день для семьи из четырёх человек.",
            "history", "golden_ring", 4, "2026-09-06", "normal", "petrov", "belova", "done", "2026-08-28 09:00:00",
        )
        conn.execute(
            "INSERT INTO messages (request_id, user_id, body, created_at) VALUES (?, ?, ?, ?)",
            (done_id, ids["petrov"], "Можно без долгой дороги между городами?", "2026-08-28 12:00:00"),
        )
        conn.execute(
            "INSERT INTO messages (request_id, user_id, body, created_at) VALUES (?, ?, ?, ?)",
            (done_id, ids["belova"], "Собрала оба города в один выезд, обед уже в цене.", "2026-08-28 15:00:00"),
        )

        family_id = add_request(
            "Семейный маршрут по Кижам",
            "Двое взрослых и дети 7 и 10 лет. Нужен спокойный темп и обед.",
            "history", "karelia", 4, "2026-10-22", "high", "ivanova", None, "new", "2026-10-10 09:30:00",
        )
        gastro_id = add_request(
            "Гастродень в Калининграде",
            "Хотим сыр, рыбу и сладости. Готовы зайти к местным производителям.",
            "gastro", "kaliningrad", 2, "2026-10-21", "normal", "petrov", None, "new", "2026-10-10 11:00:00",
        )
        add_request(
            "Треккинг к Шавлинским озёрам",
            "Двое взрослых, опыт походов есть. Нужен гид на активный маршрут.",
            "active", "altai", 2, "2026-11-08", "high", "smirnova", None, "new", "2026-10-11 08:40:00",
        )
        add_request(
            "Обзорная по Байкалу",
            "Первый приезд. Хочется город и берег за один день, без палатки.",
            "city", "baikal", 2, "2026-11-05", "normal", "ivanova", None, "new", "2026-10-11 09:10:00",
        )
        add_request(
            "Спокойный день без жёсткого маршрута",
            "Направление не важно. Нужен неспешный день на двоих.",
            "other", "other", 2, "2026-10-30", "low", "smirnova", None, "new", "2026-10-11 09:20:00",
        )

        add_product("honey", "pavlova", "Горный мёд", "Разнотравье с пасеки в Уймонской долине, банка 500 г.", "food", 650, 18)
        add_product("jam", "pavlova", "Облепиховое варенье", "Без красителей, банка 300 г.", "food", 380, 12)
        add_product("tea", "pavlova", "Чай с чабрецом", "Сбор с горных склонов, пачка 50 г.", "drink", 290, 15)
        add_product("box", "romanova", "Шкатулка из бересты", "Ручная работа, петрозаводская мастерская.", "craft", 1800, 4)
        add_product("linen", "romanova", "Льняная дорожка", "Домотканый лён, длина 140 см.", "craft", 2200, 6)
        add_product("eel", "orlov", "Копчёный угорь", "Холодное копчение, вакуум 200 г.", "food", 960, 8)
        add_product("sweet", "orlov", "Марципан ручной работы", "Плитка 150 г, калининградская мастерская.", "souvenir", 540, 11)

        honey_order = add_order("ivanova", "honey", 2, "completed", "2026-09-15 13:00:00")
        add_order("petrov", "box", 1, "accepted", "2026-10-08 17:20:00")
        add_order("smirnova", "sweet", 3, "new", "2026-10-11 10:05:00")
        add_review(
            "ivanova", "product", products["honey"]["id"], 5,
            "Густой, забрала после поездки на Алтай.", "2026-09-20 12:00:00",
        )
        _log(conn, "order", honey_order, ids["ivanova"], "Турист забрал заказ", "2026-09-16 12:00:00")

    from travelhub import matching

    matching.distribute(family_id, None)
    matching.distribute(gastro_id, None)
    with conn:
        family = conn.execute("SELECT guide_id FROM requests WHERE id = ?", (family_id,)).fetchone()
        gastro = conn.execute("SELECT guide_id FROM requests WHERE id = ?", (gastro_id,)).fetchone()
        if family and family["guide_id"] == ids["belova"]:
            conn.execute(
                "INSERT INTO messages (request_id, user_id, body, created_at) VALUES (?, ?, ?, ?)",
                (family_id, ids["ivanova"], "Можно с детьми 7 и 10 лет? Младшему тяжело долго идти.", "2026-10-10 12:00:00"),
            )
            conn.execute(
                "INSERT INTO messages (request_id, user_id, body, created_at) VALUES (?, ?, ?, ?)",
                (family_id, ids["belova"], "Да. Темп спокойный, на Кижах будет час на обед.", "2026-10-10 12:40:00"),
            )
        if gastro and gastro["guide_id"] == ids["kuznetsov"]:
            conn.execute(
                "INSERT INTO messages (request_id, user_id, body, created_at) VALUES (?, ?, ?, ?)",
                (gastro_id, ids["petrov"], "Есть ли в программе сырная лавка?", "2026-10-10 13:00:00"),
            )
            conn.execute(
                "INSERT INTO messages (request_id, user_id, body, created_at) VALUES (?, ?, ?, ?)",
                (gastro_id, ids["kuznetsov"], "Да, заходим к производителю в порту. Можно купить с собой.", "2026-10-10 13:25:00"),
            )


def _log(conn, kind, entity_id, user_id, action, created_at=None):
    conn.execute(
        "INSERT INTO history (entity_kind, entity_id, user_id, action, created_at) VALUES (?, ?, ?, ?, ?)",
        (kind, entity_id, user_id, action, created_at or now()),
    )


def list_history(kind, entity_id):
    conn = connect()
    rows = conn.execute(
        "SELECT h.*, u.full_name AS user_name FROM history h"
        " LEFT JOIN users u ON u.id = h.user_id"
        " WHERE h.entity_kind = ? AND h.entity_id = ? ORDER BY h.id",
        (kind, entity_id),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def _as_int(value, minimum, maximum, label):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None, f"{label}: нужно целое число"
    if number < minimum or number > maximum:
        return None, f"{label}: от {minimum} до {maximum}"
    return number, None


def _parse_date(text, allow_empty=False, not_past=False):
    text = (text or "").strip()
    if not text and allow_empty:
        return "", None
    try:
        datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        return None, "Дата в формате ГГГГ-ММ-ДД"
    if not_past and text < today():
        return None, "Дата уже прошла"
    return text, None


def _open_request_duplicate(conn, tourist_id, title, exclude_id=None):
    key = title.strip().casefold()
    rows = conn.execute(
        "SELECT id, title FROM requests WHERE tourist_id = ? AND status IN ('new', 'assigned')",
        (tourist_id,),
    ).fetchall()
    for row in rows:
        if exclude_id is not None and row["id"] == exclude_id:
            continue
        if row["title"].strip().casefold() == key:
            return row["id"]
    return None


# --- users ---

def create_user(login, password, full_name, role="tourist", specialty="other", region="other", about="", is_active=1):
    login = login.strip().lower()
    full_name = full_name.strip()
    about = about.strip()
    if not re.fullmatch(r"[a-z0-9_]{3,32}", login):
        return False, "Логин: 3–32 символа, латиница, цифры и _"
    if not full_name or len(full_name) > 80:
        return False, "Укажите ФИО, не длиннее 80 символов"
    if len(password) < 4 or len(password) > 64:
        return False, "Пароль от 4 до 64 символов"
    if role not in ROLES:
        return False, "Неизвестная роль"
    if specialty not in THEMES:
        return False, "Неизвестное направление"
    if region not in REGIONS:
        return False, "Неизвестный регион"
    if len(about) > 300:
        return False, "Текст «о себе» слишком длинный"
    conn = connect()
    try:
        with conn:
            conn.execute(
                "INSERT INTO users (login, password, full_name, role, specialty, region, about, is_active, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (login, hash_password(password), full_name, role, specialty, region, about, int(is_active), now()),
            )
        return True, "Пользователь создан"
    except sqlite3.IntegrityError:
        return False, "Логин уже занят"
    finally:
        conn.close()


def authenticate(login, password):
    conn = connect()
    row = conn.execute(
        "SELECT * FROM users WHERE login = ?",
        (login.strip().lower(),),
    ).fetchone()
    conn.close()
    if not row or not verify_password(password, row["password"]):
        return None, "Неверный логин или пароль"
    if not row["is_active"]:
        return None, "Учётная запись отключена"
    return _public(row), None


def get_user(user_id):
    conn = connect()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return _public(row)


def list_users(role=None):
    conn = connect()
    if role:
        rows = conn.execute("SELECT * FROM users WHERE role = ? ORDER BY id", (role,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
    conn.close()
    return [_public(row) for row in rows]


def list_guides(only_active=True):
    conn = connect()
    sql = (
        "SELECT u.*,"
        " (SELECT COUNT(*) FROM reviews r WHERE r.target_kind = 'guide' AND r.target_id = u.id) AS review_count,"
        " (SELECT AVG(r.rating) FROM reviews r WHERE r.target_kind = 'guide' AND r.target_id = u.id) AS review_avg"
        " FROM users u WHERE u.role = 'guide'"
    )
    if only_active:
        sql += " AND u.is_active = 1"
    sql += " ORDER BY u.id"
    rows = conn.execute(sql).fetchall()
    conn.close()
    return [_public(row) for row in rows]


def guide_rating(guide):
    count = int(guide.get("review_count") or 0)
    if count <= 0 or guide.get("review_avg") is None:
        return None
    return float(guide["review_avg"])


def update_user(user_id, **fields):
    allowed = {"full_name", "role", "specialty", "region", "about", "is_active", "password"}
    values = {key: value for key, value in fields.items() if key in allowed and value is not None}
    if "password" in values:
        if not str(values["password"]):
            values.pop("password")
        elif len(values["password"]) < 4 or len(values["password"]) > 64:
            return False, "Пароль от 4 до 64 символов"
        else:
            values["password"] = hash_password(values["password"])
    if "full_name" in values:
        values["full_name"] = values["full_name"].strip()
        if not values["full_name"] or len(values["full_name"]) > 80:
            return False, "Укажите ФИО, не длиннее 80 символов"
    if "about" in values:
        values["about"] = values["about"].strip()
        if len(values["about"]) > 300:
            return False, "Текст «о себе» слишком длинный"
    if "role" in values and values["role"] not in ROLES:
        return False, "Неизвестная роль"
    if "specialty" in values and values["specialty"] not in THEMES:
        return False, "Неизвестное направление"
    if "region" in values and values["region"] not in REGIONS:
        return False, "Неизвестный регион"
    if "is_active" in values:
        values["is_active"] = int(values["is_active"])
    if not values:
        return False, "Нет изменений"

    conn = connect()
    try:
        with conn:
            current = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            if not current:
                return False, "Пользователь не найден"
            new_role = values.get("role", current["role"])
            new_active = int(values.get("is_active", current["is_active"]))
            loses_admin = (
                current["role"] == "admin"
                and current["is_active"]
                and not (new_role == "admin" and new_active == 1)
            )
            if loses_admin:
                others = conn.execute(
                    "SELECT COUNT(*) FROM users WHERE role = 'admin' AND is_active = 1 AND id != ?",
                    (user_id,),
                ).fetchone()[0]
                if others == 0:
                    return False, "Нельзя снять последнего активного администратора"
            assignments = ", ".join(f"{key} = ?" for key in values)
            conn.execute(
                f"UPDATE users SET {assignments} WHERE id = ?",
                (*values.values(), user_id),
            )
            released = 0
            was_guide = current["role"] == "guide" and current["is_active"]
            stays_guide = new_role == "guide" and new_active == 1
            if was_guide and not stays_guide:
                released = _release_guide_requests(conn, user_id, user_id)
        if released:
            return True, f"Сохранено. В очередь возвращено заявок: {released}"
        return True, "Сохранено"
    finally:
        conn.close()


def _release_guide_requests(conn, guide_id, actor_id):
    rows = conn.execute(
        "SELECT id, tourist_id, title FROM requests WHERE guide_id = ? AND status = 'assigned'",
        (guide_id,),
    ).fetchall()
    released = 0
    for row in rows:
        if _open_request_duplicate(conn, row["tourist_id"], row["title"], row["id"]):
            conn.execute("UPDATE requests SET status = 'cancelled' WHERE id = ?", (row["id"],))
            _log(conn, "request", row["id"], actor_id, "Заявка отменена: у туриста уже есть такая открытая")
            continue
        conn.execute(
            "UPDATE requests SET guide_id = NULL, status = 'new' WHERE id = ?",
            (row["id"],),
        )
        _log(conn, "request", row["id"], actor_id, "Гид снят, заявка возвращена в очередь")
        released += 1
    return released


# --- requests ---

def create_request(title, description, theme, region, people, preferred_date, priority, tourist_id):
    title = title.strip()
    description = description.strip()
    if not title:
        return None, "Укажите тему"
    if len(title) > 120:
        return None, "Тема слишком длинная"
    if len(description) > 2000:
        return None, "Описание слишком длинное"
    if theme not in THEMES:
        return None, "Неизвестное направление"
    if region not in REGIONS:
        return None, "Неизвестный регион"
    if priority not in PRIORITIES:
        return None, "Неизвестный приоритет"
    people_count, error = _as_int(people, 1, 20, "Число людей")
    if error:
        return None, error
    preferred, error = _parse_date(preferred_date, allow_empty=True, not_past=True)
    if error:
        return None, error
    conn = connect()
    try:
        with conn:
            tourist = conn.execute(
                "SELECT role, is_active FROM users WHERE id = ?",
                (tourist_id,),
            ).fetchone()
            if not tourist or tourist["role"] != "tourist" or not tourist["is_active"]:
                return None, "Заявку создаёт активный турист"
            if _open_request_duplicate(conn, tourist_id, title):
                return None, "Такая заявка уже открыта"
            cur = conn.execute(
                "INSERT INTO requests (title, description, theme, region, people, preferred_date, priority, status, tourist_id, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, 'new', ?, ?)",
                (title, description, theme, region, people_count, preferred, priority, tourist_id, now()),
            )
            request_id = cur.lastrowid
            _log(conn, "request", request_id, tourist_id, "Заявка создана")
        return request_id, None
    except sqlite3.IntegrityError:
        return None, "Такая заявка уже открыта"
    finally:
        conn.close()


_REQUEST_SQL = (
    "SELECT r.*, t.full_name AS tourist_name, g.full_name AS guide_name"
    " FROM requests r"
    " JOIN users t ON t.id = r.tourist_id"
    " LEFT JOIN users g ON g.id = r.guide_id"
)


def list_requests(tourist_id=None, guide_id=None, status=None):
    conn = connect()
    sql = _REQUEST_SQL + " WHERE 1=1"
    params = []
    if tourist_id is not None:
        sql += " AND r.tourist_id = ?"
        params.append(tourist_id)
    if guide_id is not None:
        sql += " AND r.guide_id = ?"
        params.append(guide_id)
    if status:
        sql += " AND r.status = ?"
        params.append(status)
    sql += " ORDER BY r.id DESC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_request(request_id):
    conn = connect()
    row = conn.execute(_REQUEST_SQL + " WHERE r.id = ?", (request_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def assign_request(request_id, guide_id, actor_id=None, note=""):
    conn = connect()
    try:
        with conn:
            current = conn.execute("SELECT * FROM requests WHERE id = ?", (request_id,)).fetchone()
            if not current:
                return False, "Заявка не найдена"
            if current["status"] not in ("new", "assigned"):
                return False, "Заявка уже закрыта"
            if current["guide_id"] == guide_id and current["status"] == "assigned":
                return True, "Уже назначено"
            guide = conn.execute(
                "SELECT full_name, role, is_active FROM users WHERE id = ?",
                (guide_id,),
            ).fetchone()
            if not guide or guide["role"] != "guide" or not guide["is_active"]:
                return False, "Нужен активный гид"
            conn.execute(
                "UPDATE requests SET guide_id = ?, status = 'assigned' WHERE id = ?",
                (guide_id, request_id),
            )
            action = f"Назначен гид: {guide['full_name']}"
            if note:
                action += f" ({note})"
            _log(conn, "request", request_id, actor_id, action)
        return True, "Гид назначен"
    finally:
        conn.close()


def take_request(request_id, guide_id):
    conn = connect()
    try:
        row = conn.execute(
            "SELECT guide_id, status FROM requests WHERE id = ?",
            (request_id,),
        ).fetchone()
        guide = conn.execute(
            "SELECT role, is_active FROM users WHERE id = ?",
            (guide_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return False, "Заявка не найдена"
    if not guide or guide["role"] != "guide" or not guide["is_active"]:
        return False, "Взять заявку может только активный гид"
    if row["status"] != "new" or row["guide_id"] is not None:
        return False, "Заявка уже назначена"
    ok, message = assign_request(request_id, guide_id, guide_id, note="гид взял сам")
    if ok:
        return True, "Заявка у вас"
    return False, message


def set_request_status(request_id, status, actor_id):
    if status not in ("done", "cancelled"):
        return False, "Неизвестный статус"
    conn = connect()
    try:
        with conn:
            current = conn.execute("SELECT * FROM requests WHERE id = ?", (request_id,)).fetchone()
            actor = conn.execute("SELECT * FROM users WHERE id = ?", (actor_id,)).fetchone()
            if not current:
                return False, "Заявка не найдена"
            if not actor or not actor["is_active"]:
                return False, "Недостаточно прав"
            if current["status"] in ("done", "cancelled"):
                return False, "Заявка уже закрыта"
            is_admin = actor["role"] == "admin"
            is_author = actor["id"] == current["tourist_id"]
            is_guide = actor["role"] == "guide" and actor["id"] == current["guide_id"]
            if status == "done":
                if current["status"] != "assigned" or not current["guide_id"]:
                    return False, "Завершить можно только назначенную заявку"
                if not (is_admin or is_guide):
                    return False, "Недостаточно прав"
            else:
                if not (is_admin or is_author or is_guide):
                    return False, "Недостаточно прав"
            conn.execute(
                "UPDATE requests SET status = ? WHERE id = ?",
                (status, request_id),
            )
            _log(conn, "request", request_id, actor_id, f"Статус: {REQUEST_STATUS_RU[status]}")
        return True, "Статус обновлён"
    finally:
        conn.close()


def add_message(request_id, user_id, body):
    body = body.strip()
    if not body:
        return False, "Введите текст"
    if len(body) > 1000:
        return False, "Сообщение слишком длинное"
    conn = connect()
    try:
        with conn:
            request = conn.execute("SELECT * FROM requests WHERE id = ?", (request_id,)).fetchone()
            user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            if not request:
                return False, "Заявка не найдена"
            if not user or not user["is_active"]:
                return False, "Недостаточно прав"
            allowed = (
                user["role"] == "admin"
                or user["id"] == request["tourist_id"]
                or (user["role"] == "guide" and user["id"] == request["guide_id"])
            )
            if not allowed:
                return False, "Писать могут турист, назначенный гид и администратор"
            if request["status"] in ("done", "cancelled"):
                return False, "Переписка по закрытой заявке завершена"
            conn.execute(
                "INSERT INTO messages (request_id, user_id, body, created_at) VALUES (?, ?, ?, ?)",
                (request_id, user_id, body, now()),
            )
            _log(conn, "request", request_id, user_id, "Добавлено сообщение")
        return True, "Сообщение отправлено"
    finally:
        conn.close()


def list_messages(request_id):
    conn = connect()
    rows = conn.execute(
        "SELECT m.*, u.full_name AS user_name FROM messages m"
        " JOIN users u ON u.id = m.user_id WHERE m.request_id = ? ORDER BY m.id",
        (request_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def active_load(guide_id):
    conn = connect()
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM requests WHERE guide_id = ? AND status = 'assigned'",
        (guide_id,),
    ).fetchone()
    conn.close()
    return row["c"]


# --- tours and bookings ---

_TOUR_SQL = (
    "SELECT t.*, g.full_name AS guide_name, g.specialty AS guide_specialty,"
    " g.region AS guide_region,"
    " (SELECT COUNT(*) FROM reviews r WHERE r.target_kind = 'guide' AND r.target_id = g.id) AS review_count,"
    " (SELECT AVG(r.rating) FROM reviews r WHERE r.target_kind = 'guide' AND r.target_id = g.id) AS review_avg,"
    " t.capacity - COALESCE(("
    "     SELECT SUM(b.people) FROM bookings b"
    "     WHERE b.tour_id = t.id AND b.status = 'confirmed'"
    " ), 0) AS seats_left"
    " FROM tours t JOIN users g ON g.id = t.guide_id"
)


def create_tour(title, description, theme, region, tour_date, duration_hours, price, capacity, guide_id):
    title = title.strip()
    description = description.strip()
    if not title or len(title) > 120:
        return None, "Укажите название, не длиннее 120 символов"
    if len(description) > 2000:
        return None, "Описание слишком длинное"
    if theme not in THEMES or theme == "other":
        return None, "Выберите направление экскурсии"
    if region not in REGIONS or region == "other":
        return None, "Выберите регион экскурсии"
    parsed_date, error = _parse_date(tour_date, not_past=True)
    if error:
        return None, error
    hours, error = _as_int(duration_hours, 1, 16, "Длительность, часы")
    if error:
        return None, error
    amount, error = _as_int(price, 100, 500_000, "Цена")
    if error:
        return None, error
    seats, error = _as_int(capacity, 1, 40, "Число мест")
    if error:
        return None, error
    conn = connect()
    try:
        with conn:
            guide = conn.execute(
                "SELECT role, is_active FROM users WHERE id = ?",
                (guide_id,),
            ).fetchone()
            if not guide or guide["role"] != "guide" or not guide["is_active"]:
                return None, "Экскурсию публикует активный гид"
            cur = conn.execute(
                "INSERT INTO tours (title, description, theme, region, tour_date, duration_hours, price, capacity, guide_id, status, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)",
                (title, description, theme, region, parsed_date, hours, amount, seats, guide_id, now()),
            )
            tour_id = cur.lastrowid
            _log(conn, "tour", tour_id, guide_id, "Экскурсия опубликована")
        return tour_id, None
    finally:
        conn.close()


def list_tours(guide_id=None, status=None):
    conn = connect()
    sql = _TOUR_SQL + " WHERE 1=1"
    params = []
    if guide_id is not None:
        sql += " AND t.guide_id = ?"
        params.append(guide_id)
    if status:
        sql += " AND t.status = ?"
        params.append(status)
    sql += " ORDER BY t.tour_date, t.id"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_tour(tour_id):
    conn = connect()
    row = conn.execute(_TOUR_SQL + " WHERE t.id = ?", (tour_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def _taken_seats(conn, tour_id):
    return conn.execute(
        "SELECT COALESCE(SUM(people), 0) FROM bookings WHERE tour_id = ? AND status = 'confirmed'",
        (tour_id,),
    ).fetchone()[0]


def _sync_tour_capacity(conn, tour_id, actor_id):
    tour = conn.execute("SELECT status, capacity FROM tours WHERE id = ?", (tour_id,)).fetchone()
    if not tour or tour["status"] in ("completed", "cancelled"):
        return
    taken = _taken_seats(conn, tour_id)
    new_status = "full" if taken >= tour["capacity"] else "open"
    if new_status == tour["status"]:
        return
    conn.execute("UPDATE tours SET status = ? WHERE id = ?", (new_status, tour_id))
    if new_status == "full":
        _log(conn, "tour", tour_id, actor_id, "Свободных мест не осталось")
    else:
        _log(conn, "tour", tour_id, actor_id, "Снова есть свободные места")


def set_tour_status(tour_id, status, actor_id):
    if status not in ("completed", "cancelled"):
        return False, "Неизвестный статус"
    conn = connect()
    try:
        with conn:
            tour = conn.execute("SELECT * FROM tours WHERE id = ?", (tour_id,)).fetchone()
            actor = conn.execute("SELECT * FROM users WHERE id = ?", (actor_id,)).fetchone()
            if not tour:
                return False, "Экскурсия не найдена"
            if not actor or not actor["is_active"]:
                return False, "Недостаточно прав"
            if tour["status"] in ("completed", "cancelled"):
                return False, "Экскурсия уже закрыта"
            is_owner = actor["role"] == "guide" and actor["id"] == tour["guide_id"]
            if not (actor["role"] == "admin" or is_owner):
                return False, "Недостаточно прав"
            rows = conn.execute(
                "SELECT id FROM bookings WHERE tour_id = ? AND status = 'confirmed'",
                (tour_id,),
            ).fetchall()
            if status == "completed":
                for row in rows:
                    conn.execute("UPDATE bookings SET status = 'completed' WHERE id = ?", (row["id"],))
                    _log(conn, "booking", row["id"], actor_id, "Бронь завершена вместе с экскурсией")
            else:
                for row in rows:
                    conn.execute("UPDATE bookings SET status = 'cancelled' WHERE id = ?", (row["id"],))
                    _log(conn, "booking", row["id"], actor_id, "Бронь снята: экскурсия отменена")
            conn.execute("UPDATE tours SET status = ? WHERE id = ?", (status, tour_id))
            _log(conn, "tour", tour_id, actor_id, f"Статус: {TOUR_STATUS_RU[status]}")
        if status == "cancelled":
            return True, f"Экскурсия отменена. Снято броней: {len(rows)}"
        return True, "Экскурсия завершена"
    finally:
        conn.close()


def book_tour(tour_id, tourist_id, people):
    people_count, error = _as_int(people, 1, 40, "Число людей")
    if error:
        return None, error
    conn = connect()
    try:
        with conn:
            tour = conn.execute("SELECT * FROM tours WHERE id = ?", (tour_id,)).fetchone()
            tourist = conn.execute("SELECT * FROM users WHERE id = ?", (tourist_id,)).fetchone()
            if not tour:
                return None, "Экскурсия не найдена"
            if not tourist or tourist["role"] != "tourist" or not tourist["is_active"]:
                return None, "Бронь оформляет активный турист"
            if tour["status"] != "open":
                return None, "На эту экскурсию сейчас нельзя записаться"
            existing = conn.execute(
                "SELECT id FROM bookings WHERE tour_id = ? AND tourist_id = ? AND status = 'confirmed'",
                (tour_id, tourist_id),
            ).fetchone()
            if existing:
                return None, "Вы уже записаны на эту экскурсию"
            left = tour["capacity"] - _taken_seats(conn, tour_id)
            if people_count > left:
                return None, f"Свободно мест: {left}"
            cur = conn.execute(
                "INSERT INTO bookings (tour_id, tourist_id, people, status, created_at) VALUES (?, ?, ?, 'confirmed', ?)",
                (tour_id, tourist_id, people_count, now()),
            )
            booking_id = cur.lastrowid
            _log(conn, "booking", booking_id, tourist_id, "Бронь оформлена")
            _log(conn, "tour", tour_id, tourist_id, f"Новая бронь: {people_count} чел.")
            _sync_tour_capacity(conn, tour_id, tourist_id)
        return booking_id, None
    except sqlite3.IntegrityError:
        return None, "Вы уже записаны на эту экскурсию"
    finally:
        conn.close()


def cancel_booking(booking_id, actor_id):
    conn = connect()
    try:
        with conn:
            booking = conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
            actor = conn.execute("SELECT * FROM users WHERE id = ?", (actor_id,)).fetchone()
            if not booking:
                return False, "Бронь не найдена"
            if not actor or not actor["is_active"]:
                return False, "Недостаточно прав"
            if booking["status"] != "confirmed":
                return False, "Снять можно только действующую бронь"
            tour = conn.execute("SELECT * FROM tours WHERE id = ?", (booking["tour_id"],)).fetchone()
            is_owner = actor["id"] == booking["tourist_id"]
            is_guide = actor["role"] == "guide" and tour and actor["id"] == tour["guide_id"]
            if not (is_owner or is_guide or actor["role"] == "admin"):
                return False, "Недостаточно прав"
            conn.execute("UPDATE bookings SET status = 'cancelled' WHERE id = ?", (booking_id,))
            _log(conn, "booking", booking_id, actor_id, "Бронь снята")
            _sync_tour_capacity(conn, booking["tour_id"], actor_id)
        return True, "Бронь снята"
    finally:
        conn.close()


_BOOKING_SQL = (
    "SELECT b.*, tour.title AS tour_title, tour.tour_date AS tour_date, tour.price AS price,"
    " tour.status AS tour_status, tour.guide_id AS guide_id,"
    " guide.full_name AS guide_name, tourist.full_name AS tourist_name"
    " FROM bookings b"
    " JOIN tours tour ON tour.id = b.tour_id"
    " JOIN users guide ON guide.id = tour.guide_id"
    " JOIN users tourist ON tourist.id = b.tourist_id"
)


def list_bookings(tourist_id=None, guide_id=None, tour_id=None):
    conn = connect()
    sql = _BOOKING_SQL + " WHERE 1=1"
    params = []
    if tourist_id is not None:
        sql += " AND b.tourist_id = ?"
        params.append(tourist_id)
    if guide_id is not None:
        sql += " AND tour.guide_id = ?"
        params.append(guide_id)
    if tour_id is not None:
        sql += " AND b.tour_id = ?"
        params.append(tour_id)
    sql += " ORDER BY b.id DESC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_booking(booking_id):
    conn = connect()
    row = conn.execute(_BOOKING_SQL + " WHERE b.id = ?", (booking_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def confirmed_booking(tour_id, tourist_id):
    conn = connect()
    row = conn.execute(
        "SELECT * FROM bookings WHERE tour_id = ? AND tourist_id = ? AND status = 'confirmed'",
        (tour_id, tourist_id),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# --- products and orders ---

def create_product(producer_id, name, description, category, price, stock):
    name = name.strip()
    description = description.strip()
    if not name or len(name) > 80:
        return None, "Укажите название, не длиннее 80 символов"
    if len(description) > 1000:
        return None, "Описание слишком длинное"
    if category not in PRODUCT_CATEGORIES:
        return None, "Неизвестная категория"
    amount, error = _as_int(price, 1, 500_000, "Цена")
    if error:
        return None, error
    qty, error = _as_int(stock, 0, 10_000, "Остаток")
    if error:
        return None, error
    conn = connect()
    try:
        with conn:
            producer = conn.execute("SELECT * FROM users WHERE id = ?", (producer_id,)).fetchone()
            if not producer or producer["role"] != "producer" or not producer["is_active"]:
                return None, "Товар добавляет активный производитель"
            if _product_name_taken(conn, producer_id, name):
                return None, "Такой товар уже есть"
            cur = conn.execute(
                "INSERT INTO products (producer_id, name, description, category, price, stock, is_active, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, 1, ?)",
                (producer_id, name, description, category, amount, qty, now()),
            )
        return cur.lastrowid, None
    finally:
        conn.close()


def _product_name_taken(conn, producer_id, name, exclude_id=None):
    key = name.strip().casefold()
    rows = conn.execute(
        "SELECT id, name FROM products WHERE producer_id = ?",
        (producer_id,),
    ).fetchall()
    for row in rows:
        if exclude_id is not None and row["id"] == exclude_id:
            continue
        if row["name"].strip().casefold() == key:
            return True
    return False


def update_product(product_id, actor_id, **fields):
    allowed = {"name", "description", "category", "price", "stock", "is_active"}
    values = {key: value for key, value in fields.items() if key in allowed and value is not None}
    conn = connect()
    try:
        with conn:
            product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            actor = conn.execute("SELECT * FROM users WHERE id = ?", (actor_id,)).fetchone()
            if not product:
                return False, "Товар не найден"
            if not actor or not actor["is_active"]:
                return False, "Недостаточно прав"
            if actor["role"] != "admin" and actor["id"] != product["producer_id"]:
                return False, "Недостаточно прав"
            if "name" in values:
                values["name"] = values["name"].strip()
                if not values["name"] or len(values["name"]) > 80:
                    return False, "Укажите название, не длиннее 80 символов"
                if _product_name_taken(conn, product["producer_id"], values["name"], product_id):
                    return False, "Такой товар уже есть"
            if "description" in values:
                values["description"] = values["description"].strip()
                if len(values["description"]) > 1000:
                    return False, "Описание слишком длинное"
            if "category" in values and values["category"] not in PRODUCT_CATEGORIES:
                return False, "Неизвестная категория"
            if "price" in values:
                amount, error = _as_int(values["price"], 1, 500_000, "Цена")
                if error:
                    return False, error
                values["price"] = amount
            if "stock" in values:
                qty, error = _as_int(values["stock"], 0, 10_000, "Остаток")
                if error:
                    return False, error
                values["stock"] = qty
            if "is_active" in values:
                values["is_active"] = 1 if values["is_active"] else 0
            if not values:
                return False, "Нет изменений"
            assignments = ", ".join(f"{key} = ?" for key in values)
            conn.execute(
                f"UPDATE products SET {assignments} WHERE id = ?",
                (*values.values(), product_id),
            )
        return True, "Товар сохранён"
    finally:
        conn.close()


_PRODUCT_SQL = (
    "SELECT p.*, u.full_name AS producer_name, u.region AS region, u.is_active AS producer_active"
    " FROM products p JOIN users u ON u.id = p.producer_id"
)


def list_products(producer_id=None, region=None, only_market=False):
    conn = connect()
    sql = _PRODUCT_SQL + " WHERE 1=1"
    params = []
    if producer_id is not None:
        sql += " AND p.producer_id = ?"
        params.append(producer_id)
    if region:
        sql += " AND u.region = ?"
        params.append(region)
    if only_market:
        sql += " AND p.is_active = 1 AND u.is_active = 1 AND u.role = 'producer'"
    sql += " ORDER BY p.name"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_product(product_id):
    conn = connect()
    row = conn.execute(_PRODUCT_SQL + " WHERE p.id = ?", (product_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_order(tourist_id, product_id, qty):
    amount, error = _as_int(qty, 1, 20, "Количество")
    if error:
        return None, error
    conn = connect()
    try:
        with conn:
            tourist = conn.execute("SELECT * FROM users WHERE id = ?", (tourist_id,)).fetchone()
            product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            if not tourist or tourist["role"] != "tourist" or not tourist["is_active"]:
                return None, "Заказ оформляет активный турист"
            if not product or not product["is_active"]:
                return None, "Товар недоступен"
            producer = conn.execute("SELECT * FROM users WHERE id = ?", (product["producer_id"],)).fetchone()
            if not producer or producer["role"] != "producer" or not producer["is_active"]:
                return None, "Производитель сейчас недоступен"
            if amount > product["stock"]:
                return None, f"На складе осталось: {product['stock']}"
            conn.execute(
                "UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?",
                (amount, product_id, amount),
            )
            total = product["price"] * amount
            cur = conn.execute(
                "INSERT INTO orders (tourist_id, producer_id, status, total, created_at) VALUES (?, ?, 'new', ?, ?)",
                (tourist_id, product["producer_id"], total, now()),
            )
            order_id = cur.lastrowid
            conn.execute(
                "INSERT INTO order_items (order_id, product_id, name, qty, price) VALUES (?, ?, ?, ?, ?)",
                (order_id, product_id, product["name"], amount, product["price"]),
            )
            _log(conn, "order", order_id, tourist_id, "Заказ оформлен")
        return order_id, None
    finally:
        conn.close()


_ORDER_SQL = (
    "SELECT o.*, t.full_name AS tourist_name, p.full_name AS producer_name,"
    " (SELECT group_concat(oi.name || ' × ' || oi.qty, ', ') FROM order_items oi WHERE oi.order_id = o.id) AS items_label"
    " FROM orders o"
    " JOIN users t ON t.id = o.tourist_id"
    " JOIN users p ON p.id = o.producer_id"
)


def list_orders(tourist_id=None, producer_id=None):
    conn = connect()
    sql = _ORDER_SQL + " WHERE 1=1"
    params = []
    if tourist_id is not None:
        sql += " AND o.tourist_id = ?"
        params.append(tourist_id)
    if producer_id is not None:
        sql += " AND o.producer_id = ?"
        params.append(producer_id)
    sql += " ORDER BY o.id DESC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_order(order_id):
    conn = connect()
    row = conn.execute(_ORDER_SQL + " WHERE o.id = ?", (order_id,)).fetchone()
    items = []
    if row:
        items = [
            dict(item)
            for item in conn.execute(
                "SELECT * FROM order_items WHERE order_id = ? ORDER BY id",
                (order_id,),
            ).fetchall()
        ]
    conn.close()
    if not row:
        return None
    data = dict(row)
    data["items"] = items
    return data


def set_order_status(order_id, status, actor_id):
    if status not in ORDER_STATUSES:
        return False, "Неизвестный статус"
    conn = connect()
    try:
        with conn:
            order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
            actor = conn.execute("SELECT * FROM users WHERE id = ?", (actor_id,)).fetchone()
            if not order:
                return False, "Заказ не найден"
            if not actor or not actor["is_active"]:
                return False, "Недостаточно прав"
            if status not in ORDER_FLOW[order["status"]]:
                return False, "Так статус сменить нельзя"
            is_producer = actor["role"] == "producer" and actor["id"] == order["producer_id"]
            is_tourist = actor["id"] == order["tourist_id"]
            is_admin = actor["role"] == "admin"
            if status == "cancelled":
                tourist_can = is_tourist and order["status"] == "new"
                if not (is_admin or is_producer or tourist_can):
                    return False, "Отменить заказ может производитель, администратор или турист, пока заказ новый"
            elif not (is_admin or is_producer):
                return False, "Статус заказа меняет производитель"
            if status == "cancelled":
                for item in conn.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)):
                    conn.execute(
                        "UPDATE products SET stock = stock + ? WHERE id = ?",
                        (item["qty"], item["product_id"]),
                    )
            conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
            _log(conn, "order", order_id, actor_id, f"Статус: {ORDER_STATUS_RU[status]}")
        return True, "Статус заказа обновлён"
    finally:
        conn.close()


# --- reviews ---

def can_review(author_id, kind, target_id):
    if find_review(author_id, kind, target_id):
        return False
    conn = connect()
    try:
        return _review_eligible(conn, author_id, kind, target_id)
    finally:
        conn.close()


def find_review(author_id, kind, target_id):
    conn = connect()
    row = conn.execute(
        "SELECT r.*, u.full_name AS author_name FROM reviews r"
        " JOIN users u ON u.id = r.author_id"
        " WHERE r.author_id = ? AND r.target_kind = ? AND r.target_id = ?",
        (author_id, kind, target_id),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def _review_eligible(conn, author_id, kind, target_id):
    author = conn.execute("SELECT role FROM users WHERE id = ?", (author_id,)).fetchone()
    if not author or author["role"] != "tourist":
        return False
    if kind == "guide":
        request = conn.execute(
            "SELECT 1 FROM requests WHERE tourist_id = ? AND guide_id = ? AND status = 'done'",
            (author_id, target_id),
        ).fetchone()
        booking = conn.execute(
            "SELECT 1 FROM bookings b JOIN tours t ON t.id = b.tour_id"
            " WHERE b.tourist_id = ? AND t.guide_id = ? AND b.status = 'completed'",
            (author_id, target_id),
        ).fetchone()
        return bool(request or booking)
    if kind == "tour":
        return bool(conn.execute(
            "SELECT 1 FROM bookings WHERE tourist_id = ? AND tour_id = ? AND status = 'completed'",
            (author_id, target_id),
        ).fetchone())
    if kind == "product":
        return bool(conn.execute(
            "SELECT 1 FROM orders o JOIN order_items i ON i.order_id = o.id"
            " WHERE o.tourist_id = ? AND i.product_id = ? AND o.status = 'completed'",
            (author_id, target_id),
        ).fetchone())
    return False


def add_review(author_id, kind, target_id, rating, body):
    if kind not in REVIEW_KINDS:
        return False, "Неизвестный тип оценки"
    stars, error = _as_int(rating, 1, 5, "Оценка")
    if error:
        return False, error
    body = (body or "").strip()
    if len(body) > 500:
        return False, "Текст оценки слишком длинный"
    conn = connect()
    try:
        with conn:
            existing = conn.execute(
                "SELECT 1 FROM reviews WHERE author_id = ? AND target_kind = ? AND target_id = ?",
                (author_id, kind, target_id),
            ).fetchone()
            if existing:
                return False, "Вы уже оставляли оценку"
            if not _review_eligible(conn, author_id, kind, target_id):
                return False, "Оценку можно поставить после завершения"
            conn.execute(
                "INSERT INTO reviews (author_id, target_kind, target_id, rating, body, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (author_id, kind, target_id, stars, body, now()),
            )
        return True, "Оценка сохранена"
    except sqlite3.IntegrityError:
        return False, "Вы уже оставляли оценку"
    finally:
        conn.close()


def stats():
    conn = connect()

    def scalar(sql, params=()):
        return conn.execute(sql, params).fetchone()[0]

    data = {
        "users": scalar("SELECT COUNT(*) FROM users"),
        "guides": scalar("SELECT COUNT(*) FROM users WHERE role = 'guide' AND is_active = 1"),
        "producers": scalar("SELECT COUNT(*) FROM users WHERE role = 'producer' AND is_active = 1"),
        "tourists": scalar("SELECT COUNT(*) FROM users WHERE role = 'tourist' AND is_active = 1"),
        "unassigned": scalar(
            "SELECT COUNT(*) FROM requests WHERE guide_id IS NULL AND status = 'new'"
        ),
        "open_tours": scalar("SELECT COUNT(*) FROM tours WHERE status IN ('open', 'full')"),
        "active_bookings": scalar("SELECT COUNT(*) FROM bookings WHERE status = 'confirmed'"),
        "new_orders": scalar("SELECT COUNT(*) FROM orders WHERE status = 'new'"),
        "products": scalar(
            "SELECT COUNT(*) FROM products p JOIN users u ON u.id = p.producer_id"
            " WHERE p.is_active = 1 AND u.is_active = 1 AND u.role = 'producer'"
        ),
    }
    conn.close()
    return data
