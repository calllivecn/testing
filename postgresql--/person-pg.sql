
-- 1. 启用生成 UUID 的扩展 (如果尚未启用)
-- 在 PostgreSQL 13+ 中，gen_random_uuid() 通常内置于 pgcrypto 或直接可用
-- CREATE EXTENSION IF NOT EXISTS "pgcrypto"; 

-- 2. 创建枚举类型 (最佳实践：先定义类型)
CREATE TYPE "性别" AS enum('男', '女', '公', '母');
CREATE TYPE "感情状态" AS enum('已婚', '未婚', '单身', '离异', '分居', '丧偶');
CREATE TYPE "学历" AS enum('小学', '中学', '高中', '学士', '本科', '硕士', '博士', '其他');

-- 给婚姻状况枚举加注释
COMMENT ON TYPE "感情状态" IS '用户婚姻法律状态标识';

-- 给教育程度枚举加注释
COMMENT ON TYPE "学历" IS '用户受教育程度分类（从小学到博士）';


-- 3. 创建表结构
CREATE TABLE "玩家"(
    -- 【主键与基础标识】
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, -- 标准自增主键
    
    -- 【基本个人信息】
    "姓名" VARCHAR(50) NOT NULL,
    "性别" VARCHAR(16) DEFAULT '男',
    "生日" DATE,
    "感情状态" VARCHAR(50) DEFAULT '单身',
    "出生地" VARCHAR(100),
    "民族" VARCHAR(50),
    
    -- 【联系方式】
    email VARCHAR(100),
    phone VARCHAR(20),
    
    -- 【地址信息】
    "国家" VARCHAR(50) DEFAULT 'China',
    "城市" VARCHAR(50),
    "省" VARCHAR(50),
    "区/县" VARCHAR(50),
	"地址" VARCHAR(128),
    "邮编" VARCHAR(20),
    
    -- 【身份与证件】
    id_card_type VARCHAR(20) DEFAULT 'ID_CARD',
    id_card_number VARCHAR(50),
    id_card_expiry_date DATE,
    
    -- 【职业与教育】
    "职业" VARCHAR(100),
    "公司" VARCHAR(100),
    "职位" VARCHAR(100),
    "年薪" NUMERIC(12, 2),
	"受教育程度" "学历" DEFAULT '本科',
    "毕业院校" VARCHAR(100)
);
