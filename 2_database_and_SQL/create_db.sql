CREATE TABLE ku_user_status (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ku_user (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(15),
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    photo TEXT,
    status BIGINT REFERENCES ku_user_status(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE ku_user_location_type (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ku_user_location_status (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ku_user_location (
    id BIGSERIAL PRIMARY KEY,
    type BIGINT REFERENCES ku_user_location_type(id),
    status BIGINT REFERENCES ku_user_location_status(id),
    user_id BIGINT REFERENCES ku_user(id),
    location TEXT,
    address TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE ku_order_status (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ku_order (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES ku_user(id),
    status BIGINT REFERENCES ku_order_status(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE ku_product_status (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ku_category (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ku_product (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    effective_date DATE,
    effective_until DATE,
    photo TEXT,
    price NUMERIC(12,2),
    status BIGINT REFERENCES ku_product_status(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE ku_product_category (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT REFERENCES ku_product(id),
    category_id BIGINT REFERENCES ku_category(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE ku_order_detail_status (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ku_order_detail (
    id BIGSERIAL PRIMARY KEY,
    user_location_id BIGINT REFERENCES ku_user_location(id),
    order_id BIGINT REFERENCES ku_order(id),
    product_id BIGINT REFERENCES ku_product(id),
    quantity NUMERIC(12,2),
    delivery_date DATE,
    status BIGINT REFERENCES ku_order_detail_status(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_user_status ON ku_user(status);
CREATE INDEX idx_order_user ON ku_order(user_id);
CREATE INDEX idx_order_status ON ku_order(status);
CREATE INDEX idx_product_status ON ku_product(status);
CREATE INDEX idx_order_detail_order ON ku_order_detail(order_id);
CREATE INDEX idx_order_detail_product ON ku_order_detail(product_id);

