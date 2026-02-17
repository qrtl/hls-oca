def migrate(cr, version):
    """Copy eta_date and etd_date values to shipping_schedule_note field."""
    cr.execute("""
        UPDATE purchase_order
        SET shipping_schedule_note =
            CASE
                WHEN etd_date IS NOT NULL AND eta_date IS NOT NULL
                THEN 'ETD: ' || TRIM(etd_date) || '  ETA: ' || TRIM(eta_date)
                WHEN etd_date IS NOT NULL
                THEN 'ETD: ' || TRIM(etd_date)
                WHEN eta_date IS NOT NULL
                THEN 'ETA: ' || TRIM(eta_date)
            END
        WHERE etd_date IS NOT NULL OR eta_date IS NOT NULL
    """)
