
-- 这是MySQL版本

CREATE TABLE person (
    -- 【主键与基础标识】
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    uuid CHAR(36) NOT NULL DEFAULT (UUID()) COMMENT '全局唯一标识符',
    
    -- 【基本个人信息】
    first_name VARCHAR(50) NOT NULL COMMENT '名',
    last_name VARCHAR(50) NOT NULL COMMENT '姓',
    middle_name VARCHAR(50) DEFAULT NULL COMMENT '中间名',
    nickname VARCHAR(50) DEFAULT NULL COMMENT '昵称',
    gender ENUM('M', 'F', 'O', 'U') DEFAULT 'U' COMMENT '性别 (M:男, F:女, O:其他, U:未知)',
    date_of_birth DATE DEFAULT NULL COMMENT '出生日期',
    place_of_birth VARCHAR(100) DEFAULT NULL COMMENT '出生地',
    nationality VARCHAR(50) DEFAULT 'CN' COMMENT '国籍',
    ethnicity VARCHAR(50) DEFAULT NULL COMMENT '民族/种族',
    marital_status ENUM('SINGLE', 'MARRIED', 'DIVORCED', 'WIDOWED', 'SEPARATED') DEFAULT 'SINGLE' COMMENT '婚姻状况',
    
    -- 【联系方式】
    email_primary VARCHAR(100) UNIQUE COMMENT '主要邮箱',
    email_secondary VARCHAR(100) DEFAULT NULL COMMENT '备用邮箱',
    phone_mobile VARCHAR(20) COMMENT '手机号码',
    phone_home VARCHAR(20) DEFAULT NULL COMMENT '家庭电话',
    phone_work VARCHAR(20) DEFAULT NULL COMMENT '工作电话',
    
    -- 【地址信息】
    address_country VARCHAR(50) DEFAULT 'China' COMMENT '国家',
    address_province VARCHAR(50) DEFAULT NULL COMMENT '省/州',
    address_city VARCHAR(50) DEFAULT NULL COMMENT '城市',
    address_district VARCHAR(50) DEFAULT NULL COMMENT '区/县',
    address_street VARCHAR(200) DEFAULT NULL COMMENT '街道详细地址',
    address_zip_code VARCHAR(20) DEFAULT NULL COMMENT '邮政编码',
    latitude DECIMAL(10, 8) DEFAULT NULL COMMENT '纬度 (用于地理位置)',
    longitude DECIMAL(11, 8) DEFAULT NULL COMMENT '经度 (用于地理位置)',
    
    -- 【身份与证件】
    id_card_type VARCHAR(20) DEFAULT 'ID_CARD' COMMENT '证件类型 (ID_CARD, PASSPORT, etc.)',
    id_card_number VARCHAR(50) UNIQUE COMMENT '证件号码',
    id_card_expiry_date DATE DEFAULT NULL COMMENT '证件有效期',
    passport_number VARCHAR(50) DEFAULT NULL COMMENT '护照号码',
    
    -- 【职业与教育】
    occupation VARCHAR(100) DEFAULT NULL COMMENT '职业',
    company_name VARCHAR(100) DEFAULT NULL COMMENT '公司名称',
    job_title VARCHAR(100) DEFAULT NULL COMMENT '职位头衔',
    annual_salary DECIMAL(12, 2) DEFAULT NULL COMMENT '年薪',
    education_level ENUM('PRIMARY', 'HIGH_SCHOOL', 'BACHELOR', 'MASTER', 'DOCTORATE', 'OTHER') DEFAULT NULL COMMENT '最高学历',
    graduation_school VARCHAR(100) DEFAULT NULL COMMENT '毕业院校',
    
    -- 【生物特征与媒体 (测试用大字段)】
    avatar_url VARCHAR(255) DEFAULT NULL COMMENT '头像URL',
    fingerprint_hash CHAR(64) DEFAULT NULL COMMENT '指纹哈希 (模拟)',
    face_id_data TEXT DEFAULT NULL COMMENT '面部识别数据 (模拟)',
    signature_blob BLOB DEFAULT NULL COMMENT '电子签名二进制数据',
    resume_content LONGTEXT DEFAULT NULL COMMENT '简历全文内容',
    
    -- 【账户与安全 (测试用)】
    username VARCHAR(50) UNIQUE COMMENT '登录用户名',
    password_hash VARCHAR(255) NOT NULL DEFAULT '' COMMENT '密码哈希',
    salt VARCHAR(50) DEFAULT NULL COMMENT '密码盐值',
    failed_login_attempts INT DEFAULT 0 COMMENT '连续登录失败次数',
    last_login_ip VARCHAR(45) DEFAULT NULL COMMENT '最后登录IP (支持IPv6)',
    last_login_time DATETIME DEFAULT NULL COMMENT '最后登录时间',
    is_email_verified BOOLEAN DEFAULT FALSE COMMENT '邮箱是否验证',
    is_phone_verified BOOLEAN DEFAULT FALSE COMMENT '手机是否验证',
    
    -- 【系统元数据】
    status TINYINT DEFAULT 1 COMMENT '状态 (1:正常, 0:禁用, -1:删除)',
    version INT DEFAULT 1 COMMENT '乐观锁版本号',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    created_by BIGINT DEFAULT 0 COMMENT '创建人ID',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    updated_by BIGINT DEFAULT 0 COMMENT '更新人ID',
    deleted_at DATETIME DEFAULT NULL COMMENT '逻辑删除时间',
    remarks VARCHAR(500) DEFAULT NULL COMMENT '备注信息',
    extra_json JSON DEFAULT NULL COMMENT '扩展字段 (JSON格式)'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='人员信息全量测试表';
