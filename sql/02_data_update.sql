-- Fix two rows where 2020 was accidentally typed as 2026.

UPDATE expenses_raw
SET date = '14.11.2020'
WHERE date = '14.11.2026'
  AND expense_description = 'Packaging materials'
  AND total_spent = '€7,48';

UPDATE expenses_raw
SET date = '14.11.2020'
WHERE date = '14.11.2026'
  AND expense_description = 'Shipping'
  AND total_spent = '€47,21';