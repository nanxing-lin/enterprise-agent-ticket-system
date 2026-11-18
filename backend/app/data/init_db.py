# backend/app/data/init_db.py
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# 获取当前文件所在目录，确保数据库生成在 data 文件夹下
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "company.db")


def generate_mock_data():
    print("开始生成模拟业务数据...")

    # 1. 生成 2023年1月 到 2023年12月 的订单数据 (模拟 1000 条)
    np.random.seed(42)  # 保证每次生成的数据一样
    dates = [datetime(2023, 1, 1) + timedelta(days=np.random.randint(0, 365)) for _ in range(1000)]
    regions = np.random.choice(["华东区", "华南区", "华北区", "西南区"], 1000)
    products = np.random.choice(["智能手表", "无线耳机", "机械键盘", "显示器", "扫地机器人"], 1000)
    prices = np.random.choice([299, 499, 899, 1299, 2499], 1000)
    quantities = np.random.randint(1, 5, 1000)

    orders_df = pd.DataFrame({
        "order_id": [f"ORD{i:04d}" for i in range(1, 1001)],
        "order_date": [d.strftime("%Y-%m-%d") for d in dates],
        "region": regions,
        "product_name": products,
        "price": prices,
        "quantity": quantities,
        "total_amount": prices * quantities
    })

    # 2. 生成 退货数据 (模拟 200 条，关联到订单)
    # 故意让华东区在 11月、12月 的退货变多，方便后面Agent分析出“异常”
    returns_df = orders_df.sample(200, random_state=42).copy()
    returns_df["return_id"] = [f"RET{i:04d}" for i in range(1, 201)]
    returns_df["return_reason"] = np.random.choice(["质量问题", "不喜欢", "发错货", "七天无理由"], 200)
    returns_df["refund_amount"] = returns_df["total_amount"]

    # 制造一点数据倾斜，让“华东区”在第四季度退货率偏高
    mask = (returns_df["region"] == "华东区") & (returns_df["order_date"] >= "2023-10-01")
    returns_df.loc[mask, "return_reason"] = "质量问题"

    # 3. 写入 SQLite 数据库
    conn = sqlite3.connect(DB_PATH)
    orders_df.to_sql("orders", conn, if_exists="replace", index=False)
    returns_df.to_sql("returns", conn, if_exists="replace", index=False)
    conn.close()

    print(f"数据生成完毕！数据库文件已保存至: {DB_PATH}")
    print(f"共生成订单 {len(orders_df)} 条，退货 {len(returns_df)} 条。")


if __name__ == "__main__":
    generate_mock_data()