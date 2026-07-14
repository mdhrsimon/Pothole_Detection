import os
import sqlalchemy as sa


def main():
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:root@127.0.0.1:5432/pothole_db",
    )
    engine = sa.create_engine(db_url)

    statements = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'user'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE",
        "ALTER TABLE potholes ADD COLUMN IF NOT EXISTS reported_by_user_id INTEGER",
        "ALTER TABLE potholes ADD COLUMN IF NOT EXISTS assigned_to_worker_id INTEGER",
        "ALTER TABLE potholes ADD COLUMN IF NOT EXISTS after_image_path VARCHAR(255)",
        "ALTER TABLE potholes ADD COLUMN IF NOT EXISTS fix_notes VARCHAR(255)",
        "ALTER TABLE potholes ADD COLUMN IF NOT EXISTS fix_timestamp TIMESTAMP",
        "ALTER TABLE potholes ADD COLUMN IF NOT EXISTS fix_latitude DOUBLE PRECISION",
        "ALTER TABLE potholes ADD COLUMN IF NOT EXISTS fix_longitude DOUBLE PRECISION",
        "ALTER TABLE potholes ADD COLUMN IF NOT EXISTS approved_by_admin_id INTEGER",
        "ALTER TABLE potholes ADD COLUMN IF NOT EXISTS approval_timestamp TIMESTAMP",
        "ALTER TABLE potholes ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP",
        "ALTER TABLE potholes ADD COLUMN IF NOT EXISTS status VARCHAR(30) NOT NULL DEFAULT 'open'",
        "ALTER TABLE potholes ADD COLUMN IF NOT EXISTS status_note VARCHAR(255)",
    ]

    with engine.begin() as conn:
        for sql in statements:
            conn.exec_driver_sql(sql)

    print("Schema migration complete.")


if __name__ == "__main__":
    main()