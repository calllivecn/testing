
import time
from decimal import Decimal

import psycopg
from faker import Faker
from psycopg.rows import dict_row
from psycopg import sql

# 数据库连接配置
# 格式: "dbname=test user=postgres password=secret host=localhost"
CONN_STR = "host=10.1.3.20 dbname=calllivecn user=postgres password=zx,pgsql"

# 初始化
fake = Faker(['zh_CN'])

民族例表 = (
    "汉族", "壮族", "回族", "满族", "维吾尔族", "苗族", "彝族", "土家族",
    "藏族", "蒙古族", "侗族", "布依族", "瑶族", "白族", "朝鲜族", "哈尼族",
    "黎族", "哈萨克族", "傣族", "畲族", "傈僳族", "仡佬族", "东乡族", "拉祜族",
    "水族", "佤族", "纳西族", "羌族", "土族", "仫佬族", "锡伯族", "柯尔克孜族",
    "达斡尔族", "撒拉族", "布朗族", "毛南族", "塔吉克族", "阿昌族", "普米族",
    "鄂温克族", "怒族", "京族", "基诺族", "德昂族", "保安族", "俄罗斯族",
    "裕固族", "乌兹别克族", "门巴族", "鄂伦春族", "独龙族", "塔塔尔族",
    "赫哲族", "高山族", "珞巴族", "景颇族"
)

学历 = ('小学', '中学', '高中', '学士', '本科', '硕士', '博士', '其他')

感情状态 = ('已婚', '未婚', '单身', '离异', '分居', '丧偶')

def get_single_row():
    """生成单行数据的逻辑"""
    return (
        fake.name()[:50],
        fake.random_element(['男', '女', '公', '母']),
        fake.date_of_birth(minimum_age=1, maximum_age=120),
        fake.random_element(感情状态),
        fake.city()[:100],
        fake.random_element(民族例表),
        fake.email()[:100],
        fake.phone_number()[:20],
        '中国',
        fake.province()[:50],
        fake.city()[:50],
        fake.district()[:50],
        fake.address()[:128],
        fake.postcode()[:20],
        'ID_CARD',
        fake.ssn()[:50],
        fake.date_between(start_date='today', end_date='+10y'),
        fake.job()[:100],
        fake.company()[:100],
        fake.job()[:100],
        Decimal(fake.random_int(min=30000, max=2000000)),
        fake.random_element(学历),
        f"{fake.city()}{fake.random_element(['大学', '学院'])}"
    )

def run_import():
    total_needed = 9_000_000
    batch_size = 10_000  # 每 1 万条提交一次
    
    columns = (
        "姓名", "性别", "生日", "感情状态",
        "出生地", "民族",
        "email", "phone",
        "国家", "省", "城市", "区/县", "地址", "邮编",
        "id_card_type", "id_card_number", "id_card_expiry_date",
        "职业", "公司", "职位", "年薪",
        "受教育程度", "毕业院校"
    )

    start_time = time.time()
    inserted_total = 0

    # 使用 sql.Identifier 自动为每个字段加上双引号并转义
    # 结果类似于: "姓名", "性别", "年龄", "区/县"
    columns_sql = sql.SQL(", ").join(map(sql.Identifier, columns))
    
    # 构建最终的 COPY 语句
    copy_query = sql.SQL("COPY {} ({}) FROM STDIN (FORMAT BINARY)").format(
        sql.Identifier("玩家"),
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

