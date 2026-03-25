# 测试使用postgresql

- 安装: pip install psycopg[binary,pool]

- SQLAlchemy (ORM 方案)

### 如果你不希望直接编写原始 SQL，而是想用 Python 对象来操作数据库，SQLAlchemy 是首选。它底层通常也是调用 psycopg。

```Python
from sqlalchemy import create_engine
# 使用 psycopg3 作为驱动
engine = create_engine("postgresql+psycopg://user:pass@localhost/dbname")
```

## 生成测试使用数据

- pip install faker

## 官方推荐的 GUI的客户端

- https://www.pgadmin.org/
- 容器名: docker.io/dpage/pgadmin4:latest

