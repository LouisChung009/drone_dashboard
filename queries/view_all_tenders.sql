-- 查詢所有 drone_tenders 資料，每頁顯示 1000 筆
-- 執行這個查詢可以看到所有清理後的資料

SELECT 
    id,
    source_name,
    source_record_id,
    title,
    agency,
    award_amount,
    currency,
    award_date,
    supplier_name_cleaned as supplier_name,
    uei_sam,
    cage_code,
    data_source_url,
    created_at
FROM drone_tenders
ORDER BY id
LIMIT 1000;

-- 如果需要看後續的資料，可以使用 OFFSET：
-- SELECT ... OFFSET 1000 LIMIT 1000;
-- SELECT ... OFFSET 2000 LIMIT 1000;
