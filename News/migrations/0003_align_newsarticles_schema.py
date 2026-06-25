from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("News", "0002_newsarticles_delete_newsarticle"),
    ]

    operations = [
        migrations.RunSQL(
            sql=r"""
            ALTER TABLE IF EXISTS news_articles
                ADD COLUMN IF NOT EXISTS summary text,
                ADD COLUMN IF NOT EXISTS content text,
                ADD COLUMN IF NOT EXISTS tags jsonb,
                ADD COLUMN IF NOT EXISTS topics jsonb,
                ADD COLUMN IF NOT EXISTS sentiment_score numeric(4,3),
                ADD COLUMN IF NOT EXISTS fetched_at timestamp with time zone,
                ADD COLUMN IF NOT EXISTS created_at timestamp with time zone,
                ADD COLUMN IF NOT EXISTS updated_at timestamp with time zone;
            """,
            reverse_sql=r"""
            -- No-op safe reverse
            """,
        ),
        migrations.RunSQL(
            sql=r"""
            -- Ensure URL uniqueness index exists
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes WHERE schemaname = 'public' AND indexname = 'news_articles_url_uniq_idx'
                ) THEN
                    CREATE UNIQUE INDEX news_articles_url_uniq_idx ON news_articles ((url));
                END IF;
            END$$;
            """,
            reverse_sql=r"""
            DROP INDEX IF EXISTS news_articles_url_uniq_idx;
            """,
        ),
    ]
