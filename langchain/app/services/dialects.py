"""Prompt rules per query language. Edit here to tune generation per datastore."""

CLICKHOUSE_RULES = (
    "- Always use fully qualified table names (database.table).\n"
    "- For Map columns read values with col['key'], using the keys listed in the schema.\n"
    "- Use ClickHouse functions (JSONExtractString, toStartOfHour, toDate, countIf, etc.)."
    "- Use a single table when it can answer the question. JOIN only when the answer needs "
    "data from more than one table.\n"
    "- Join only on the keys listed under 'Join keys' in the notes. Never invent a join key. "
    "If no key is documented for the tables needed, use one table only.\n"
    "- Give every table an alias and prefix every column with it (e.g. e.app_id).\n"
    "- ClickHouse keeps the RIGHT table of a JOIN in memory: put the smaller or more filtered "
    "table on the right, and filter (including the time range) or aggregate each side in a "
    "subquery before joining.\n"
    "- Use INNER JOIN for matching rows only, LEFT JOIN to keep unmatched rows. Aggregate "
    "before joining to avoid duplicated rows."
)

ESQL_RULES = (
    "- The query must start with FROM <index-pattern>, "
    "using only index patterns listed in the schema.\n"
    "- Chain commands with | (WHERE, EVAL, STATS ... BY, SORT, KEEP, LIMIT).\n"
    "- Time filter example: WHERE @timestamp > NOW() - 24 hours\n"
    "- Time bucket example: STATS errors = COUNT(*) BY hour = DATE_TRUNC(1 hour, @timestamp)\n"
    '- Text matching: use LIKE "*word*" or RLIKE; compare strings with double quotes.\n'
    "- Wrap field names containing special characters such as '-' in backticks.\n"
    "- Do not use LOOKUP or ENRICH."
)
