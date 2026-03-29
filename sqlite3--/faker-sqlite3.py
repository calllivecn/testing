import time
import sqlite3
from datetime import date

from faker import Faker

"""
-- SQLite 对应的表结构说明
CREATE TABLE zx(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(32),
    age INTEGER,
    birth DATE,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

# 数据库文件路径 (如果不存在会自动创建)
DB_PATH = "calllivecn.db"

# 初始化
fake = Faker(['zh_CN'])
today_year = date.today().year

def get_single_row():
    """生成单行数据的逻辑"""
    birth = fake.date_of_birth(minimum_age=18, maximum_age=60)
    age = today_year - birth.year
    return (
        fake.name()[:32],
        age,
        birth.isoformat()
    )

def init_db(conn):
    """初始化数据库表并设置提升性能的参数"""
    # 创建表
    conn.execute('''
        CREATE TABLE IF NOT EXISTS zx(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(32),
            age INTEGER,
            birth DATE,
            created DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    
    # 极大地提升 SQLite 的批量写入性能
    conn.execute("PRAGMA journal_mode = WAL;")       # 开启预写式日志
    conn.execute("PRAGMA synchronous = OFF;")        # 关闭同步，允许异步写入磁盘
    conn.execute("PRAGMA cache_size = 100000;")      # 增加缓存
    conn.execute("PRAGMA temp_store = MEMORY;")      # 临时表存放在内存

def run_import():
    total_needed = 20_000_000
    batch_size = 10_000  # 每 1 万条提交一次

    
    start_time = time.time()
    inserted_total = 0

    # 构建 INSERT 语句 (?, ?, ? 是 SQLite 的参数占位符)
    insert_query = "INSERT INTO zx (name, age, birth) VALUES (?, ?, ?)"

    try:
        # 连接 SQLite (使用 isolation_level=None 配合上下文管理器控制事务)
        with sqlite3.connect(DB_PATH) as conn:
            
            init_db(conn) # 初始化表与配置
            
            while inserted_total < total_needed:
                try:
                    # 使用生成器直接喂给 executemany，降低内存消耗
                    batch_data = (get_single_row() for _ in range(batch_size))
                    
                    # 每一批使用事务进行提交，with conn: 会在块结束时自动 commit() 或在报错时 rollback()
                    with conn:
                        conn.executemany(insert_query, batch_data)
                    
                    inserted_total += batch_size
                    elapsed = time.time() - start_time
                    
                    speed = int(inserted_total / elapsed) if elapsed > 0 else 0
                    print(f"已成功提交: {inserted_total}/{total_needed} | 速度: {speed} 行/秒")
                        
                except sqlite3.IntegrityError as e:
                    # 在 SQLite 中对应 PG 的 UniqueViolation 错误是 IntegrityError
                    print(f"警告：当前批次发现重复/违规数据，已跳过该 1w 条记录。错误详情: {e}")
                    inserted_total += batch_size 
                except Exception as e:
                    print(f"发生非预期错误: {e}")
                    break

        print(f"最终导入完成！实际处理数量: {inserted_total} | 总耗时: {time.time() - start_time:.2f}s")

    except Exception as e:
        print(f"连接或操作数据库失败: {e}")

if __name__ == "__main__":
    run_import()
