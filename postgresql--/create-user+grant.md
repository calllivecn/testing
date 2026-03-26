
## 快速配置模板 (针对新用户)

- 如果你创建了一个新用户 zx，想让它能正常读取 public 模式下的所有现有表，通常需要运行以下“三板斧”：

	```shell
	-- 1. 确保能连库 (通常默认就有，但显式写一下更保险)
	GRANT CONNECT ON DATABASE your_db_name TO zx;
	
	-- 2. 确保能进模式 (PG 15+ 必须做)
	GRANT USAGE ON SCHEMA public TO zx;
	
	-- 3. 确保能查表 (授予现有表的权限)
	GRANT SELECT ON ALL TABLES IN SCHEMA public TO zx;
	
	-- (可选) 确保将来新建的表也能自动查 (设置默认权限)
	-- 注意：这需要由表的所有者（通常是 postgres 或应用账号）来运行
	ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO zx;
	```

