# 日新增、N天留存 统计
## 数据源 data_source
|  字段   | 类型  | 说明 |
|  ----  | ----  | ---- |
| ds  | bigint | 分区时间，格式：2022121301 |
| env  | string | 环境：test, production |
| datatype | string | 数据类型，例：pk - PK挑战的流水日志 |
| tag | string | 数据标签 |
| action | string | 用户操作 |

## 统计日新增用户
说明：计算每个UID最开始的PK日期，然后按日期统计每日新增PK用户数。
```sql
WITH rawdata AS (
SELECT
  ds AS ds,
  uid AS uid
FROM
  data_source
WHERE
  (
    (
      (ds >= 2022090300)
      AND 
      (ds < 2023040101)
    )
    AND 
    (
      env IN ('test')
      AND datatype IN ('pk')
      AND tag IN ('tag')
      AND action IN ('challenge')
    )
  )
)

select 
  t1.ds as ds,
  count(distinct(uid)) as index_uid_0
from 
    (
      SELECT
        distinct(cast(ds / 100 as bigint)) AS ds
      FROM
        rawdata
    ) t1 
    left join
    (
      SELECT
        uid AS uid,
        min(cast(ds / 100 as bigint)) AS ds
      FROM
        rawdata
      group by
        uid
    ) t2
    on t1.ds=t2.ds
group by
  ds
order by
  ds desc
limit
  1000;
```

## 统计次日留存
```sql
WITH rawdata AS (
SELECT
  ds AS ds,
  uid AS uid
FROM
  data_source
WHERE
  (
    (
      (ds >= 2022090300)
      AND 
      (ds < 2023040101)
    )
    AND 
    (
      env IN ('test')
      AND datatype IN ('pk')
      AND addtype IN ('tag')
      AND action IN ('challenge')
    )
  )
),
firstpk AS (
  select 
    t1.ds as ds,
    t2.uid as uid
  from 
    (
      SELECT
        distinct(cast(ds / 100 as bigint)) AS ds
      FROM
        rawdata
    ) t1 
    left join
    (
      SELECT
        uid AS uid,
        min(cast(ds / 100 as bigint)) AS ds
      FROM
        rawdata
      group by
        uid
    ) t2
    on t1.ds=t2.ds
)
 
select t1.ds as '日期', t1.count as '日新增', t2.ncount as '次日留存'
FROM (
  SELECT ds, count(distinct(uid)) as count
  FROM firstpk
  GROUP BY ds
) t1 LEFT JOIN (
  SELECT firstpk.ds, count(pkhistory.uid) as ncount
  FROM firstpk
  JOIN (
    SELECT
      uid AS uid,
      cast(ds / 100 as bigint) AS pkdate
    FROM
      rawdata
    group by
      uid, pkdate
  ) pkhistory
  ON firstpk.uid = pkhistory.uid AND 
    UNIX_TIMESTAMP(cast(pkhistory.pkdate as string), 'yyyyMMdd') - UNIX_TIMESTAMP(cast(firstpk.ds as string), 'yyyyMMdd') = 86400
  group by
    firstpk.ds
) t2
on t1.ds = t2.ds
order by
  t1.ds desc
limit
  1000;
```

## int to string with leading zero
```sql
-- test
> select LPAD(1, 4, 0);
+---------------+
| LPAD(1, 4, 0) |
+---------------+
| 0001          |
+---------------+

-- convert int to string
update t_advisor set advisor_id=LPAD(id, 4, 0);
```

## 查询自定义多行数据
Assume you have a table sales with columns id, product, and amount.

id	product	amount
1	Product A	100
2	Product B	200
3	Product C	300

```sql
SELECT 
    'Total Sales' AS description, 
    SUM(amount) AS calculated_value
FROM sales
UNION ALL
SELECT 
    'Average Sales' AS description, 
    AVG(amount) AS calculated_value
FROM sales;
```

## row index
```sql
SELECT 
    ROW_NUMBER() OVER (ORDER BY year, month) AS row_index,
    year,
    month,
    total_followers
FROM 
    followers_by_month;
```
