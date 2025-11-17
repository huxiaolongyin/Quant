import pandas as pd

columns = [
    "交易所名称",
    "交易所缩写",
    "板块",
    "A股代码",
    "A股代码全称",
    "A股简称",
    "英文名称",
    "公司全称",
    "A股上市日期",
    "所属行业",
    "省份",
    "城市",
]


def classify_board(code):
    if not isinstance(code, str):
        code = str(code)
    if code.startswith(("600", "601", "603", "605")):
        return "主板"
    elif code.startswith("688"):
        return "科创板"
    elif code.startswith("300"):
        return "创业板"
    elif code.startswith(("430", "830", "870", "880")):
        return "北交所"
    elif code.startswith("002"):
        return "中小板"
    else:
        return "未知"


# 读取原始 Excel 数据
sz_df = pd.read_excel("data/A股列表.xlsx")

# 添加固定字段
sz_df["交易所名称"] = "深圳证券交易所"
sz_df["交易所缩写"] = "SZ"
sz_df["A股代码"] = sz_df["A股代码"].astype(str).str.zfill(6)
sz_df["A股代码全称"] = sz_df["A股代码"] + "." + sz_df["交易所缩写"]

# 映射已有字段
sz_df.rename(columns={"省    份": "省份", "城     市": "城市"}, inplace=True)

sz_df = sz_df[columns]

sz_df.to_csv(
    "stocks.csv",
    sep=";",
    # mode="a",
    header=True,
    index=False,
    encoding="utf-8-sig",
)


# 读取原始 Excel 数据
sh_df = pd.read_excel("data/GPLIST.xls")

# 添加固定字段
sh_df["交易所名称"] = "上海证券交易所"
sh_df["交易所缩写"] = "SH"
sh_df["板块"] = sh_df["A股代码"].apply(classify_board)
sh_df["A股代码"] = sh_df["A股代码"].astype(str).str.zfill(6)
sh_df["公司全称"] = ""  # 若有原始字段可替换
sh_df["行业"] = ""
sh_df["省份"] = ""
sh_df["城市"] = ""
sh_df["所属行业"] = ""
sh_df["A股上市日期"] = pd.to_datetime(
    sh_df["上市日期"], format="%Y%m%d", errors="coerce"
).dt.strftime("%Y-%m-%d")
sh_df["A股代码全称"] = sh_df["A股代码"] + "." + sh_df["交易所缩写"]

# 映射已有字段
sh_df.rename(
    columns={
        "公司英文全称": "英文名称",
        "证券简称": "A股简称",
    },
    inplace=True,
)

# 调整列顺序为目标格式
sh_df = sh_df[columns]

# 写入 CSV 文件（追加模式）
sh_df.to_csv(
    "stocks.csv", sep=";", mode="a", header=False, index=False, encoding="utf-8-sig"
)
