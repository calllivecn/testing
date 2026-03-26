
import time
from decimal import Decimal
from datetime import date

import psycopg
from faker import Faker
from psycopg.rows import dict_row
from psycopg import sql

"""
-- 创建对应的表
create table zx(
    id bigint GENERATED ALWAYS AS IDENTITY primary key,
    name varchar(32),
    age int,
    birth date,
    created timestamp WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP);
"""

# 数据库连接配置
# 格式: "dbname=test user=postgres password=secret host=localhost"
CONN_STR = "host=10.1.3.20 dbname=calllivecn user=postgres password=zx,pgsql"

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
        birth
    )

def run_import():
    total_needed = 2000_0000
    batch_size = 1_0000  # 每 1 万条提交一次
    
    columns = ("name", "age", "birth")

    start_time = time.time()
    inserted_total = 0

    # 使用 sql.Identifier 自动为每个字段加上双引号并转义
    columns_sql = sql.SQL(", ").join(map(sql.Identifier, columns))
    
    # 构建最终的 COPY 语句
    copy_query = sql.SQL("COPY {} ({}) FROM STDIN (FORMAT BINARY)").format(
        sql.Identifier("zx"),
        columns_sql
    )

    try:
        # 建立长连接
        with psycopg.connect(CONN_STR, autocommit=False) as conn:
            while inserted_total < total_needed:
                try:
                    with conn.cursor() as cur:
                        # 每一批开启一个新的 COPY 事务
                        with cur.copy(copy_query) as copy:
                            for _ in range(batch_size):
                                copy.write_row(get_single_row())
                        
                        # COPY 块结束后立即提交
                        conn.commit()
                        inserted_total += batch_size
                        
                        elapsed = time.time() - start_time
                        print(f"已成功提交: {inserted_total}/{total_needed} | 速度: {int(inserted_total/elapsed)} 行/秒")
                        
                except psycopg.errors.UniqueViolation as e:
                    # 如果这一批次有重复键，回滚本批次，继续下一批
                    conn.rollback()
                    print(f"警告：当前批次发现重复数据，已跳过该 1w 条记录。错误详情: {e.diag.message_primary}")
                    # 注意：这里你可以选择减小 batch_size 重试，或者直接跳过
                    inserted_total += batch_size 
                except Exception as e:
                    conn.rollback()
                    print(f"发生非预期错误: {e}")
                    break

            print(f"最终导入完成！实际处理数量: {inserted_total} | 总耗时: {time.time() - start_time:.2f}s")

    except Exception as e:
        print(f"连接数据库失败: {e}")

if __name__ == "__main__":
    run_import()

