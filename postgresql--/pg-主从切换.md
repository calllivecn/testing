# postgresql 主从切换，手动：

- 1. 

- 在新主库上执行：

```sql
# SELECT pg_create_physical_replication_slot('slot1');
 pg_create_physical_replication_slot
-------------------------------------
 (slot1,)
(1 row)
```

