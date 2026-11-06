-- Run this file to create the database tables. Do not run until the database is set up and DATABASE_URL is configured in .env.

CREATE EXTENSION IF NOT EXISTS "pgcrypto"; -- enables gen_random_uuid() to auto-generate UUID primary keys

CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       TEXT UNIQUE NOT NULL,
    password    TEXT NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE meetings (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title       TEXT NOT NULL,
    attendees   TEXT NOT NULL,
    date        TEXT NOT NULL,
    status      TEXT DEFAULT 'pending',
    notes       TEXT DEFAULT '',
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE action_items (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task        TEXT NOT NULL,
    owner       TEXT NOT NULL,
    due_date    TEXT NOT NULL,
    meeting_id  UUID REFERENCES meetings(id) ON DELETE CASCADE
);
