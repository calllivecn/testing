
-- 1. 启用生成 UUID 的扩展 (如果尚未启用)
-- 在 PostgreSQL 13+ 中，gen_random_uuid() 通常内置于 pgcrypto 或直接可用
CREATE EXTENSION IF NOT EXISTS "pgcrypto"; 

-- 2. 创建枚举类型 (最佳实践：先定义类型)
CREATE TYPE gender_enum AS ENUM ('M', 'F', 'O', 'U');
CREATE TYPE marital_status_enum AS ENUM ('SINGLE', 'MARRIED', 'DIVORCED', 'WIDOWED', 'SEPARATED');
CREATE TYPE education_level_enum AS ENUM ('PRIMARY', 'HIGH_SCHOOL', 'BACHELOR', 'MASTER', 'DOCTORATE', 'OTHER');
CREATE TYPE person_status_enum AS ENUM ('ACTIVE', 'INACTIVE', 'BANNED', 'DELETED');

-- 3. 创建表结构
CREATE TABLE person (
    -- 【主键与基础标识】
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, -- 标准自增主键
    uuid UUID NOT NULL DEFAULT gen_random_uuid(),       -- 全局唯一标识符
    
    -- 【基本个人信息】
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    middle_name VARCHAR(50),
    nickname VARCHAR(50),
    gender gender_enum DEFAULT 'U',
    date_of_birth DATE,
    place_of_birth VARCHAR(100),
    nationality VARCHAR(50) DEFAULT 'CN',
    ethnicity VARCHAR(50),
    marital_status marital_status_enum DEFAULT 'SINGLE',
    
    -- 【联系方式】
    email_primary VARCHAR(100) UNIQUE,
    email_secondary VARCHAR(100),
    phone_mobile VARCHAR(20),
    phone_home VARCHAR(20),
    phone_work VARCHAR(20),
    
    -- 【地址信息】
    address_country VARCHAR(50) DEFAULT 'China',
    address_province VARCHAR(50),
    address_city VARCHAR(50),
    address_district VARCHAR(50),
    address_street VARCHAR(200),
    address_zip_code VARCHAR(20),
    latitude NUMERIC(10, 8), -- PG 中 DECIMAL 和 NUMERIC 等价
    longitude NUMERIC(11, 8),
    
    -- 【身份与证件】
    id_card_type VARCHAR(20) DEFAULT 'ID_CARD',
    id_card_number VARCHAR(50) UNIQUE,
    id_card_expiry_date DATE,
    passport_number VARCHAR(50),
    
    -- 【职业与教育】
    occupation VARCHAR(100),
    company_name VARCHAR(100),
    job_title VARCHAR(100),
    annual_salary NUMERIC(12, 2),
    education_level education_level_enum,
    graduation_school VARCHAR(100),
    
    -- 【PostgreSQL 特色字段：数组】
    tags TEXT[] DEFAULT ARRAY[]::TEXT[], -- 标签数组，例如 {'vip', 'tester'}
    
    -- 【生物特征与媒体】
    avatar_url VARCHAR(255),
    fingerprint_hash CHAR(64),
    face_id_data TEXT,
    signature_blob BYTEA,            -- PG 中使用 BYTEA 存储二进制数据 (对应 MySQL BLOB)
    resume_content TEXT,             -- PG 中 TEXT 无长度限制，性能优于 VARCHAR(N)
    
    -- 【账户与安全】
    username VARCHAR(50) UNIQUE,
    password_hash VARCHAR(255) NOT NULL DEFAULT '',
    salt VARCHAR(50),
    failed_login_attempts INT DEFAULT 0,
    last_login_ip INET,              -- PG 特有：原生支持 IP 地址类型 (IPv4/IPv6)
    last_login_time TIMESTAMPTZ,     -- 带时区的时间戳
    is_email_verified BOOLEAN DEFAULT FALSE,
    is_phone_verified BOOLEAN DEFAULT FALSE,
    
    -- 【系统元数据】
    status person_status_enum DEFAULT 'ACTIVE',
    version INT DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_by BIGINT DEFAULT 0,
    deleted_at TIMESTAMPTZ,          -- 逻辑删除时间
    remarks VARCHAR(500),
    extra_json JSONB DEFAULT '{}'::JSONB -- 使用 JSONB 获得更好的查询性能和索引支持
);

-- 4. 添加注释 (可选，但推荐用于文档化)
COMMENT ON TABLE person IS '人员信息全量测试表 (PostgreSQL 版本)';
COMMENT ON COLUMN person.uuid IS '全局唯一标识符';
COMMENT ON COLUMN person.signature_blob IS '电子签名二进制数据';
COMMENT ON COLUMN person.last_login_ip IS '最后登录IP (使用INET类型)';
COMMENT ON COLUMN person.extra_json IS '扩展字段 (使用JSONB类型)';

-- 5. 创建索引示例 (针对常用查询字段)
CREATE INDEX idx_person_email ON person(email_primary);
CREATE INDEX idx_person_created_at ON person(created_at DESC);
CREATE INDEX idx_person_status ON person(status);
-- GIN 索引用于加速 JSONB 和 数组 查询
CREATE INDEX idx_person_extra_json ON person USING GIN (extra_json);
CREATE INDEX idx_person_tags ON person USING GIN (tags);

