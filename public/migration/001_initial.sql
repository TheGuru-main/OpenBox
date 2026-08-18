-- OpenBox initial schema

CREATE TABLE IF NOT EXISTS users (
    phone VARCHAR(20) PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    gsp_col INTEGER NOT NULL,
    gsp_row INTEGER NOT NULL,
    premium BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS files (
    id VARCHAR(36) PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    size_bytes INTEGER NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    category VARCHAR(20) NOT NULL,
    L INTEGER NOT NULL,
    S INTEGER NOT NULL,
    c INTEGER NOT NULL,
    gsp_col INTEGER NOT NULL,
    gsp_row INTEGER NOT NULL,
    uploaded_by VARCHAR(20) REFERENCES users(phone),
    price FLOAT DEFAULT 0.0,
    description TEXT DEFAULT '',
    download_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    id VARCHAR(36) PRIMARY KEY,
    from_phone VARCHAR(20) NOT NULL,
    to_phone VARCHAR(20) NOT NULL,
    body TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notifications (
    id VARCHAR(36) PRIMARY KEY,
    user_phone VARCHAR(20) NOT NULL,
    title VARCHAR(255) DEFAULT '',
    body TEXT DEFAULT '',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payments (
    id VARCHAR(36) PRIMARY KEY,
    user_phone VARCHAR(20) NOT NULL,
    file_id VARCHAR(36) REFERENCES files(id),
    amount FLOAT DEFAULT 0.0,
    reference VARCHAR(100) DEFAULT '',
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS settings (
    user_phone VARCHAR(20) PRIMARY KEY,
    language VARCHAR(10) DEFAULT 'en',
    notifications_enabled BOOLEAN DEFAULT TRUE,
    theme VARCHAR(20) DEFAULT 'neon-blue'
);