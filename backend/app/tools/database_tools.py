from langchain_core.tools import tool
import sqlite3
import pandas as pd
from pathlib import Path

# 使用 pathlib 动态获取绝对路径，最稳妥的方式
# __file__ 是当前文件路径 (app/tools/database_tools.py)
# .parent 是 tools 目录
# .parent.parent 是 app 目录
APP_DIR = Path(__file__).resolve().parent.parent
DB_PATH = APP_DIR / "data" / "company.db"


@tool
def execute_sql_query(sql_query: str) -> str:
    """
    连接企业数据库执行 SQL 查询并返回结果。
    注意：数据库里有两张表：
    1. orders (订单表: order_id, order_date, region, product_name, price, quantity, total_amount)
    2. returns (退货表: return_id, order_id, order_date, region, product_name, price, quantity, total_amount, return_reason, refund_amount)
    请编写标准的 SQLite 语法查询。
    """
    print(f"\n[Agent 正在执行 SQL]: {sql_query}")

    # 1. 检查数据库文件是否存在
    if not DB_PATH.exists():
        return f"错误：数据库文件不存在！请先在终端运行 'python app/data/init_db.py' 生成数据。预期路径：{DB_PATH}"

    try:
        # 2. 强制只读模式打开数据库，防止 AI 幻觉执行删表操作
        # 构造 SQLite 的 URI 格式: file:路径?mode=ro
        db_uri = f"file:{DB_PATH.as_posix()}?mode=ro"
        conn = sqlite3.connect(db_uri, uri=True)

        # 3. 执行查询并转换为 DataFrame
        df = pd.read_sql_query(sql_query, conn)
        conn.close()

        if df.empty:
            return "查询成功，但未找到符合条件的数据。"

        # 4. 限制返回的行数，防止数据太多导致大模型 Token 溢出报错
        if len(df) > 50:
            result = df.head(50).to_markdown(index=False)
            return f"查询成功！结果共有 {len(df)} 行，这里展示前 50 行：\n{result}"

        # 5. 转换为 Markdown 表格返回给大模型
        return df.to_markdown(index=False)

    except Exception as e:
        return f"SQL 执行报错，请检查语法或表名：{str(e)}"
