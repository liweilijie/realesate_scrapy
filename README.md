# real estate

## mysql

```sql


stop slave;
set sql_log_bin = off;
set gtid_next='c9c7ff18-1548-11f0-ab89-d843ae574ed2:239827';
begin;commit;
set gtid_next='automatic';
set sql_log_bin = on;
start slave;
show slave status\G
                 
                 
```