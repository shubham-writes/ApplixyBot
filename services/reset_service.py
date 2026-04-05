from datetime import date

async def check_and_reset_daily(telegram_id: int, db_pool):
    today = date.today()
    # Also check if pro plan has expired
    await db_pool.execute("""
        UPDATE users SET
          jobs_seen_today = CASE 
            WHEN jobs_reset_at < $2 THEN 0 
            ELSE jobs_seen_today END,
          jobs_reset_at = CASE 
            WHEN jobs_reset_at < $2 THEN $2 
            ELSE jobs_reset_at END,
          cover_letters_today = CASE 
            WHEN cover_letters_reset_at < $2 THEN 0 
            ELSE cover_letters_today END,
          cover_letters_reset_at = CASE 
            WHEN cover_letters_reset_at < $2 THEN $2 
            ELSE cover_letters_reset_at END,
          plan = CASE
            WHEN plan = 'pro' AND plan_expires_at < CURRENT_TIMESTAMP THEN 'free'
            ELSE plan END
        WHERE telegram_id = $1
    """, telegram_id, today)
