import pandas as pd
from datetime import date, datetime
import database as db


def add_idx(df):
    """为DataFrame添加序号列"""
    if df.empty: return df
    df.insert(0, '序号', range(1, len(df) + 1))
    return df


def date_to_str(d):
    """
    增强版日期转字符串函数
    支持: None, NaN, datetime.date, datetime.datetime, pandas.Timestamp, 字符串
    """
    # 1. 处理空值
    if d is None or (isinstance(d, float) and pd.isna(d)):
        return None
    if pd.isna(d):  # 处理 pandas 的 NaT
        return None

    # 2. 处理 date 对象 (最常见的情况)
    if isinstance(d, date) and not isinstance(d, datetime):
        return d.isoformat()

    # 3. 处理 datetime 对象 (Streamlit 有时返回这个)
    if isinstance(d, datetime):
        return d.date().isoformat()

    # 4. 处理 pandas Timestamp
    if isinstance(d, pd.Timestamp):
        return d.date().isoformat()

    # 5. 处理字符串 (如果是字符串直接返回，或者尝试解析)
    if isinstance(d, str):
        try:
            # 尝试解析并格式化，确保格式统一为 YYYY-MM-DD
            return pd.to_datetime(d).date().isoformat()
        except:
            return d  # 如果解析失败，原样返回

    # 6. 兜底处理
    try:
        return pd.to_datetime(d).date().isoformat()
    except:
        return None


def safe_divide(numerator, denominator):
    """安全除法"""
    try:
        n = float(numerator) if numerator is not None and pd.notna(numerator) else 0.0
        d = float(denominator) if denominator is not None and pd.notna(denominator) else 0.0
        return n / d if d != 0 else 0.0
    except:
        return 0.0


def calc_progress_str(numerator, denominator):
    """计算百分比"""
    pct = safe_divide(numerator, denominator) * 100
    return f"{pct:.1f}%"


def check_login(username, password):
    """登录验证"""
    user = db.query_df(
        f"SELECT 用户ID, 姓名, 密码, 系统角色, 所属部门, 所属公司, 账号状态, 离职时间 FROM 用户信息表 WHERE 姓名='{username}'")
    if not user.empty and user.iloc[0]['密码'] == password:
        return user.iloc[0].to_dict()
    return None
