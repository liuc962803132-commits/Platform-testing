import sqlite3
import pandas as pd
import streamlit as st
import os
import shutil

# --- 配置 ---
DB_NAME = '调查监测二分院.db'


def get_conn():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_NAME)
    return conn


def run_sql(sql, params=()):
    """
    执行写入操作（INSERT, UPDATE, DELETE）
    :param sql: SQL语句
    :param params: 参数元组
    """
    with get_conn() as conn:
        conn.execute(sql, params)
        conn.commit()


def query_df(sql):
    """
    执行查询操作，返回DataFrame
    :param sql: SQL语句
    :return: Pandas DataFrame
    """
    with get_conn() as conn:
        return pd.read_sql_query(sql, conn)


def init_db():
    """
    初始化数据库表结构
    如果表不存在则创建，如果结构变更则尝试平滑升级
    """
    conn = get_conn()
    cursor = conn.cursor()

    # 1. 创建所有基础表
    # 工作记录表：记录每日工作量
    cursor.execute('''CREATE TABLE IF NOT EXISTS 工作记录表 (
        记录ID INTEGER PRIMARY KEY AUTOINCREMENT, 用户ID INTEGER NOT NULL, 记录日期 DATE NOT NULL, 
        工作量 REAL DEFAULT 0, 备注 TEXT, 提交时间 DATETIME DEFAULT CURRENT_TIMESTAMP, 
        子任务ID INTEGER, 阶段名称 TEXT)''')

    # 用户信息表：存储所有人员信息
    cursor.execute('''CREATE TABLE IF NOT EXISTS 用户信息表 (
        用户ID INTEGER PRIMARY KEY AUTOINCREMENT, 姓名 TEXT, 密码 TEXT, 系统角色 TEXT, 
        所属部门 TEXT, 所属公司 TEXT, 账号状态 TEXT, 人员性质 TEXT, 离职时间 DATE)''')

    # 请假申请表：管理请假流程
    cursor.execute('''CREATE TABLE IF NOT EXISTS 请假申请表 (
        请假ID INTEGER PRIMARY KEY AUTOINCREMENT, 申请人ID INTEGER NOT NULL, 
        开始日期 DATE NOT NULL, 结束日期 DATE NOT NULL, 申请时间 DATETIME DEFAULT CURRENT_TIMESTAMP, 
        状态 TEXT DEFAULT '待审批', 审批人ID INTEGER, 审批时间 DATETIME)''')

    # 项目人员分配表：记录人员在不同时间段参与的项目（核心考勤依据）
    cursor.execute('''CREATE TABLE IF NOT EXISTS 项目人员分配表 (
        分配ID INTEGER PRIMARY KEY AUTOINCREMENT, 项目ID INTEGER NOT NULL, 用户ID INTEGER NOT NULL, 
        分配时间 DATETIME DEFAULT CURRENT_TIMESTAMP, 开始日期 DATE, 
        UNIQUE(项目ID, 用户ID, 开始日期))''')

    # 项目信息表：项目基础信息
    cursor.execute('''CREATE TABLE IF NOT EXISTS 项目信息表 (
        项目ID INTEGER PRIMARY KEY AUTOINCREMENT, 项目名称 TEXT, 项目状态 TEXT, 
        项目开始时间 DATE, 项目结束时间 DATE)''')

    # 考勤记录表：记录特殊考勤状态（请假、路途、手动调整）
    cursor.execute('''CREATE TABLE IF NOT EXISTS 考勤记录表 (
        考勤ID INTEGER PRIMARY KEY AUTOINCREMENT, 用户ID INTEGER NOT NULL, 日期 DATE NOT NULL, 
        项目ID INTEGER, 状态 TEXT NOT NULL, 修改人ID INTEGER, 修改时间 DATETIME, 
        UNIQUE(用户ID, 日期))''')

    # 子任务表：项目的具体任务分解
    cursor.execute('''CREATE TABLE IF NOT EXISTS 子任务表 (
        子任务ID INTEGER PRIMARY KEY AUTOINCREMENT, 项目ID INTEGER, 子任务名称 TEXT, 工作量 REAL)''')

    # 任务阶段进度表：记录任务的三个阶段（生产、一查、二查）信息
    cursor.execute('''CREATE TABLE IF NOT EXISTS 任务阶段进度表 (
        进度ID INTEGER PRIMARY KEY AUTOINCREMENT, 子任务ID INTEGER, 阶段名称 TEXT, 
        作业人员ID INTEGER, 开始时间 DATE, 预计结束时间 DATE)''')

    # 项目人员关联表：记录项目负责人、公司负责人等角色
    cursor.execute('''CREATE TABLE IF NOT EXISTS 项目人员关联表 (
        关联ID INTEGER PRIMARY KEY AUTOINCREMENT, 项目ID INTEGER, 项目角色 TEXT, 用户ID INTEGER)''')

    # 2. 数据库结构升级逻辑（自动检测并添加新字段）
    try:
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='项目人员分配表'")
        schema = cursor.fetchone()[0]
        # 检查是否包含 '开始日期' 字段，如果不包含则升级表结构
        if '开始日期' not in schema:
            st.info("正在升级数据库以支持时间段考勤...")
            # 备份数据库
            if os.path.exists(DB_NAME): shutil.copyfile(DB_NAME, f"{DB_NAME}.bak")
            # 重命名旧表
            cursor.execute("ALTER TABLE 项目人员分配表 RENAME TO temp_alloc_old")
            # 创建新表结构
            cursor.execute('''CREATE TABLE 项目人员分配表 (
                分配ID INTEGER PRIMARY KEY AUTOINCREMENT, 项目ID INTEGER NOT NULL, 用户ID INTEGER NOT NULL, 
                分配时间 DATETIME DEFAULT CURRENT_TIMESTAMP, 开始日期 DATE, 
                UNIQUE(项目ID, 用户ID, 开始日期))''')
            # 迁移数据
            cursor.execute(
                "INSERT INTO 项目人员分配表 (项目ID, 用户ID, 分配时间, 开始日期) SELECT 项目ID, 用户ID, 分配时间, 开始日期 FROM temp_alloc_old")
            # 删除旧表
            cursor.execute("DROP TABLE temp_alloc_old")
            conn.commit()
            st.success("升级成功！")
    except:
        pass

    conn.commit()
    conn.close()
