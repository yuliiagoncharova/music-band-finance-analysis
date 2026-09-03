-- Data quality checks for processed and enriched analytical tables.

-- Check that all required tables and columns exist in database and that columns have right data types.

WITH expected_columns AS (
    SELECT *
    FROM (
        VALUES
            -- expenses_enriched
            ('expenses_enriched', 'expense_date', 'date'),
            ('expenses_enriched', 'expense_description', 'text'),
            ('expenses_enriched', 'total_spent_eur', 'numeric'),
            ('expenses_enriched', 'expense_type', 'text'),

            -- merchandise_enriched
            ('merchandise_enriched', 'purchase_date', 'date'),
            ('merchandise_enriched', 'sales_reference', 'text'),
            ('merchandise_enriched', 'item', 'text'),
            ('merchandise_enriched', 'quantity', 'integer'),
            ('merchandise_enriched', 'purchase_total_eur', 'numeric'),
            ('merchandise_enriched', 'item_type', 'text'),

            -- merch_production_cost_processed
            ('merch_production_cost_processed', 'cost_year', 'integer'),
            ('merch_production_cost_processed', 'item_type', 'text'),
            ('merch_production_cost_processed', 'avg_production_cost_eur', 'numeric'),

            -- profit_per_month_processed
            ('profit_per_month_processed', 'report_month', 'date'),
            ('profit_per_month_processed', 'gross_revenue_eur', 'numeric'),
            ('profit_per_month_processed', 'gross_profit_eur', 'numeric'),
            ('profit_per_month_processed', 'gross_margin_pct', 'numeric'),

            -- live_shows_processed
            ('live_shows_processed', 'show_date', 'date'),

            -- releases_processed
            ('releases_processed', 'release_date', 'date'),
            ('releases_processed', 'release_type', 'text'),

            -- merch_drops_processed
            ('merch_drops_processed', 'drop_date', 'date'),
            ('merch_drops_processed', 'item_type', 'text'),
            ('merch_drops_processed', 'new_designs_count', 'integer'),

            -- merch_promotions_processed
            ('merch_promotions_processed', 'promotion_date', 'date'),
            ('merch_promotions_processed', 'promotion_type', 'text')

    ) AS expected_columns (
        table_name,
        column_name,
        expected_data_type
    )
)


SELECT
    'missing_table' AS to_check,
    expected_columns.table_name AS issue
FROM expected_columns
LEFT JOIN information_schema.tables AS existing_tables
    ON existing_tables.table_name = expected_columns.table_name
WHERE existing_tables.table_name IS NULL

UNION ALL

SELECT
    'missing_column' AS check_name,
    expected_columns.column_name AS issue
FROM expected_columns
LEFT JOIN information_schema.columns AS existing_columns
    ON expected_columns.column_name = existing_columns.column_name
   AND expected_columns.table_name = existing_columns.table_name
WHERE existing_columns.column_name IS NULL

UNION ALL

SELECT
    'wrong_data_type' AS check_name,
    expected_columns.column_name AS issue
FROM expected_columns
JOIN information_schema.columns AS existing_columns
    ON existing_columns.table_name = expected_columns.table_name
   AND expected_columns.column_name = existing_columns.column_name
WHERE existing_columns.data_type
      IS DISTINCT FROM expected_columns.expected_data_type;


-- Check that required fields in tables used for analysis contain no NULL values.

SELECT
	expense_date,
	total_spent_eur,
	expense_type
FROM expenses_enriched
WHERE expense_date IS NULL
	OR total_spent_eur IS NULL
	OR expense_type IS NULL;

SELECT
	purchase_date,
	purchase_total_eur,
	item_type
FROM merchandise_enriched
WHERE purchase_date IS NULL
	OR purchase_total_eur IS NULL
	OR item_type IS NULL;

SELECT
	report_month,
	gross_revenue_eur,
	gross_profit_eur,
	gross_margin_pct
FROM profit_per_month_processed
WHERE report_month IS NULL
	OR gross_revenue_eur IS NULL
	OR gross_profit_eur IS NULL
	OR gross_margin_pct IS NULL;

SELECT
	show_date
FROM live_shows_processed
WHERE show_date IS NULL;

SELECT
	release_date,
	release_type
FROM releases_processed
WHERE release_date IS NULL
	OR release_type IS NULL;

SELECT
	drop_date,
	item_type,
	new_designs_count
FROM merch_drops_processed
WHERE drop_date IS NULL
	OR item_type IS NULL
	OR new_designs_count IS NULL;

SELECT
	promotion_date,
	promotion_type
FROM merch_promotions_processed
WHERE promotion_date IS NULL
	OR promotion_type IS NULL;

SELECT
	item_type,
	cost_year
FROM merch_production_cost_processed
WHERE item_type IS NULL
	OR cost_year IS NULL;


-- Check for duplicate records where unique values or combinations are required.

-- Check profit_per_month_processed for duplicate report months.

WITH duplicates AS (
	SELECT
		*,
		COUNT(*) OVER (
			PARTITION BY
			report_month
		) AS duplicates_count
	FROM profit_per_month_processed
)

SELECT
	report_month,
	gross_revenue_eur,
	gross_profit_eur,
	gross_margin_pct,
	duplicates_count
FROM duplicates
WHERE duplicates_count >1;


-- Check merch_production_cost_processed for duplicate item type and cost year combinations.

WITH duplicates AS (
	SELECT
		*,
		COUNT(*) OVER (
			PARTITION BY
			item_type,
			cost_year
		) AS duplicates_count
	FROM merch_production_cost_processed
)

SELECT
	item_type,
	avg_production_cost_eur,
	cost_year
FROM duplicates
WHERE duplicates_count >1;


-- Check merch_drops_processed for duplicate drop date and item type combinations.

WITH duplicates AS (
	SELECT
		*,
		COUNT(*) OVER (
			PARTITION BY
			drop_date,
			item_type
		) AS duplicates_count
	FROM merch_drops_processed
)

SELECT
	drop_date,
	item_type,
	new_designs_count
FROM duplicates
WHERE duplicates_count >1;


-- Check whether each sold merchandise type has a matching production cost record for the same year.

WITH merch AS (
	SELECT
		merch_sold.item_type,
		EXTRACT(YEAR FROM purchase_date)::INTEGER AS sales_year,
		prod_cost.item_type AS matched_item_type,
		prod_cost.cost_year
	FROM merchandise_enriched AS merch_sold
	
	LEFT JOIN merch_production_cost_processed AS prod_cost
		ON EXTRACT(YEAR FROM purchase_date)::INTEGER = prod_cost.cost_year
		AND merch_sold.item_type = prod_cost.item_type
)

SELECT DISTINCT
	merch.item_type AS missing_type,
	merch.sales_year AS missing_year
FROM merch
WHERE (
	merch.matched_item_type IS NULL
	OR merch.cost_year IS NULL
	)
AND merch.item_type <> 'other';


-- Check whether sold merchandise has missing production cost values.

WITH merch AS (
    SELECT
        merch_sold.item_type,
        EXTRACT(YEAR FROM merch_sold.purchase_date)::INTEGER AS sales_year,
        prod_cost.item_type AS matched_item_type,
        prod_cost.cost_year,
        prod_cost.avg_production_cost_eur
    FROM merchandise_enriched AS merch_sold

    LEFT JOIN merch_production_cost_processed AS prod_cost
        ON EXTRACT(YEAR FROM merch_sold.purchase_date)::INTEGER = prod_cost.cost_year
        AND merch_sold.item_type = prod_cost.item_type
)

SELECT DISTINCT
    merch.item_type AS missing_cost_type,
    merch.sales_year AS missing_cost_year
FROM merch
WHERE merch.matched_item_type IS NOT NULL
    AND merch.avg_production_cost_eur IS NULL
    AND merch.item_type <> 'other';


-- Check tables required for analysis for impossible numeric values.

SELECT
	expense_date,
	expense_description,
	total_spent_eur,
	expense_type
FROM expenses_enriched
WHERE total_spent_eur <= 0;


SELECT
    purchase_date,
    item_type,
    quantity,
    purchase_total_eur
FROM merchandise_enriched
WHERE purchase_total_eur <= 0
    OR quantity <= 0;


SELECT
    report_month,
    gross_revenue_eur,
    gross_profit_eur,
    gross_margin_pct
FROM profit_per_month_processed
WHERE gross_revenue_eur < 0;


SELECT
    drop_date,
    item_type,
    new_designs_count
FROM merch_drops_processed
WHERE new_designs_count <= 0;


SELECT
    item_type,
    cost_year,
    avg_production_cost_eur
FROM merch_production_cost_processed
WHERE avg_production_cost_eur <= 0;