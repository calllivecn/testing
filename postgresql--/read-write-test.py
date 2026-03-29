
import random
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

import psycopg
from psycopg import sql
from faker import Faker

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseTester:
    def __init__(self, conn_string: str, id_range: Tuple[int, int], loop_count: int = 100):
        """
        初始化测试器
        :param conn_string: 数据库连接字符串 (例如: "postgresql://user:password@host:port/dbname")
        :param id_range: ID 范围的元组 (min_id, max_id)
        :param loop_count: 测试循环次数
        """
        self.conn_string = conn_string
        self.min_id, self.max_id = id_range
        self.loop_count = loop_count
        self.fake = Faker()
        
        # 确保 Faker 生成的年龄符合 smallint 范围 (0-32767)
        # 这里我们限制在 18-100 岁
        
    def get_random_id(self) -> int:
        """1. 在指定 id 范围内生成随机的 id"""
        return random.randint(self.min_id, self.max_id)

    def get_random_operation(self) -> str:
        """2. 生成 choice: ["select", "update", "delete"] 的操作模式"""
        #return random.choice(["select", "update", "delete"])
        return random.choice(["select", "update"])

    def generate_random_data(self) -> dict:
        """3. 生成需要修改的字段数据"""
        return {
            "name": self.fake.name()[:32], # 限制长度以符合 varchar(32)
            "age": random.randint(1, 99),
            "birth": self.fake.date_of_birth(minimum_age=1, maximum_age=90),
            # created 字段通常由数据库默认值生成，这里不手动生成
        }

    def execute_operation(self, conn: psycopg.Connection):
        """执行单次随机操作"""
        op_type = self.get_random_operation()
        target_id = self.get_random_id()
        
        with conn.cursor() as cur:
            try:
                if op_type == "select":
                    # 模拟查询
                    cur.execute("SELECT id, name, age, birth FROM public.zx WHERE id = %s", (target_id,))
                    result = cur.fetchone()
                    # logger.debug(f"SELECT id={target_id}: {'Found' if result else 'Not Found'}")

                elif op_type == "update":
                    # 模拟更新
                    new_data = self.generate_random_data()
                    # 随机决定更新哪些字段，或者更新全部
                    update_fields = []
                    values = []
                    
                    # 随机选择更新部分字段，增加测试多样性
                    if random.random() > 0.3: update_fields.append("name = %s"); values.append(new_data['name'])
                    if random.random() > 0.3: update_fields.append("age = %s"); values.append(new_data['age'])
                    if random.random() > 0.3: update_fields.append("birth = %s"); values.append(new_data['birth'])
                    
                    # 如果没有选中任何字段，默认更新 name
                    if not update_fields:
                        update_fields.append("name = %s")
                        values.append(new_data['name'])

                    values.append(target_id) # 用于 WHERE 子句
                    
                    query = sql.SQL("UPDATE public.zx SET {} WHERE id = %s").format(
                        sql.SQL(", ").join(map(sql.SQL, update_fields))
                    )
                    cur.execute(query, values)

                elif op_type == "delete":
                    # 模拟删除 (注意：在生产环境慎用 DELETE，这里仅作测试)
                    # 为了测试可持续性，实际场景中通常会配合 INSERT 使用，
                    # 或者仅仅执行 DELETE 语句看影响行数。
                    cur.execute("DELETE FROM public.zx WHERE id = %s", (target_id,))
                
                conn.commit()
                # logger.info(f"Success: {op_type.upper()} on ID {target_id}")

            except Exception as e:
                conn.rollback()
                logger.error(f"Error executing {op_type} on ID {target_id}: {e}")

    def run(self):
        """主运行循环"""
        logger.info(f"Starting DB Test with {self.loop_count} iterations...")
        
        try:
            # 建立连接 (psycopg 3 自动连接)
            with psycopg.connect(self.conn_string) as conn:
                logger.info("Connected to database.")
                
                for i in range(self.loop_count):
                    self.execute_operation(conn)
                    
                    # 可选：简单的防抖/延迟，模拟真实请求间隔
                    # time.sleep(0.01) 
                    
                logger.info("Test loop finished.")
                
        except psycopg.OperationalError as e:
            logger.error(f"Database connection failed: {e}")

# --- 配置与执行 ---

if __name__ == "__main__":
    # 请修改下方的连接字符串以匹配你的数据库环境
    # 格式: "postgresql://用户名:密码@主机:端口/数据库名"
    DB_CONN_STRING = "postgresql://zx:zx,pgsql@10.1.3.1:5432/calllivecn"
    
    # 定义 ID 范围 (例如 1 到 10000)
    ID_RANGE = (1, 20000000)
    
    # 实例化并运行
    tester = DatabaseTester(
        conn_string=DB_CONN_STRING, 
        id_range=ID_RANGE, 
        loop_count=500000  # 测试次数
    )
    
    tester.run()
