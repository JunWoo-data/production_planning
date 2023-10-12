# %%
import pandas as pd 
import numpy as np 
import datetime

# %%
from A_constants import *
from B_utils import *
from C_prepare_data import *
from D_production_plan import *

# %%
TARGET_INPUT_SHEET_NAME = "Combi Ant"

DEFAULT_PLAN_START_DATE = "2023-10-09"
DEFAULT_PLAN_FINISH_DATE = "2023-10-15"

LINE_1_UPH = 70
LINE_2_2WIRE_UPH = 67
LINE_2_4WIRE_UPH = 64
LINE_3_UPH = 57

LINE_1_FULL_AVAILABILITY = 644
LINE_2_2WIRE_FULL_AVAILABILITY = 672
LINE_2_4WIRE_FULL_AVAILABILITY = 592
LINE_3_FULL_AVAILABILITY = 528

HMMA_PACK_QUANTITY = 28
KIA_PACK_QUANTITY = 16


# %%
df = pd.read_excel("../data/input_data_100723.xlsx", sheet_name = "Combi Ant", skiprows = 3)
df = df.iloc[1:, 3:]
df


# %%
df_line_info, df_inventory, df_shipping_plan, df_production_plan, \
df_daily_full_available, df_uph, df_basic_info = prepare_data(df, DEFAULT_PLAN_START_DATE, DEFAULT_PLAN_FINISH_DATE)
df_daily_full_available
# %%
df_production_plan
# %%
df_daily_full_available_pivot = pd.pivot_table(df_daily_full_available.drop("day_of_week", axis = 1), values = "full_available", 
                                              index = ["LINE", "num_wire"], columns = ["date"])
df_daily_full_available_pivot = df_daily_full_available_pivot.reset_index()
df_daily_full_available_pivot

# %%
df_daily_full_available_pivot_edited = pd.melt(df_daily_full_available_pivot, id_vars = ["LINE", "num_wire"], var_name = "date", value_name = "full_available")
df_daily_full_available_pivot_edited[df_daily_full_available_pivot_edited["LINE"] == "#1"]


# %%
# %%
pd.melt(df_inventory, id_vars = ["PROGRAM", "PART NUMBER", "LIST"], 
                               var_name = "date", value_name = "Inventory").drop("LIST", axis = 1) \
                       [["PART NUMBER", "PROGRAM", "date", "Inventory"]]

# %%
df_production_plan_pivot[[]]
# %%
df_production_plan_pivot.index.names = ["Index"]

# %%
df_production_plan_pivot.reset_index()

# %%
df_production_plan_pivot.to_dict("records")

# %%
[{"name": i, "id": i} for i in df_production_plan_pivot.columns]
# %%
line2_production_summary = Line2_production_plan(df, DEFAULT_PLAN_START_DATE, DEFAULT_PLAN_FINISH_DATE, df_daily_full_available)
line3_production_summary = Line3_production_plan(df, DEFAULT_PLAN_START_DATE, DEFAULT_PLAN_FINISH_DATE, df_daily_full_available)

# %%
line2_production_summary_df = pd.DataFrame(columns = ["PART NUMBER", "LINE", "date", "Production Plan"])
line3_production_summary_df = pd.DataFrame(columns = ["PART NUMBER", "LINE", "date", "Production Plan"])
# %%
for k, v in line2_production_summary.items():
    for v_k, v_v in v.items():
        line2_production_summary_df = pd.concat([line2_production_summary_df, 
                                                 pd.DataFrame({"PART NUMBER": [v_k], "LINE": ["#2"], "date": [k], "Production Plan": [v_v]})])

# %%
for k, v in line3_production_summary.items():
    for v_k, v_v in v.items():
        line3_production_summary_df = pd.concat([line3_production_summary_df, 
                                                 pd.DataFrame({"PART NUMBER": [v_k], "LINE": ["#3"], "date": [k], "Production Plan": [v_v]})])

# %%
date_list = [DEFAULT_PLAN_START_DATE]
for i in range(1, (pd.to_datetime(DEFAULT_PLAN_FINISH_DATE) - pd.to_datetime(DEFAULT_PLAN_START_DATE)).days + 1):
    date_list.append((pd.to_datetime(DEFAULT_PLAN_START_DATE) + datetime.timedelta(days = i)).strftime("%Y-%m-%d"))
line1_production_summary_df = pd.DataFrame(date_list, columns = ["date"])
line1_production_summary_df["PART NUMBER"] = "96210-CW100EB"
line1_production_summary_df["LINE"] = "#1"
line1_production_summary_df = line1_production_summary_df.merge(df_daily_full_available.loc[df_daily_full_available["LINE"] == "#1", ["date", "full_available"]],
                                                                how = "left", on = "date").rename(columns = {"full_available": "Production Plan"})
line1_production_summary_df = line1_production_summary_df[["PART NUMBER", "LINE", "date", "Production Plan"]]
# %%
line1_production_summary_df


# %%
production_summary_df = pd.concat([line1_production_summary_df, line2_production_summary_df, line3_production_summary_df])

# %%
production_summary_df
# %%
production_summary_df["date"] = pd.to_datetime(production_summary_df.date)
production_summary_df
# %%
production_summary_df_pivot = pd.pivot_table(production_summary_df, index = ["PART NUMBER", "LINE"],
                                             values = "Production Plan", columns = "date").fillna(0).reset_index() \
                                                                                          .sort_values(["LINE", "PART NUMBER"])
# %%
production_summary_df_pivot.index = range(1, production_summary_df_pivot.shape[0] + 1)
# %%
production_summary_df_pivot

# %%
part_order = pd.DataFrame(df_production_plan["PART NUMBER"].unique(), columns = ["PART NUMBER"])
part_order["part_order_num"] = range(0, part_order.shape[0])
part_order

# %%
original_production_plan = pd.melt(df[(df["LIST"] == "Production Plan") & (~df["LINE"].isna())].drop(["PROGRAM","LIST"], axis = 1),
                                   id_vars = ["PART NUMBER", "LINE"], var_name = "date", value_name = "Original production_plan")

original_production_plan["date"] = pd.to_datetime(original_production_plan.date)
original_production_plan = original_production_plan.merge(production_summary_df, how = "left", on = ["PART NUMBER", "LINE", "date"])
original_production_plan[~original_production_plan["Production Plan"].isna()]

# %%
original_production_plan.loc[~original_production_plan["Production Plan"].isna(), "Production Plan Result"] \
    = original_production_plan[~original_production_plan["Production Plan"].isna()]["Production Plan"]

original_production_plan.loc[original_production_plan["Production Plan"].isna(), "Production Plan Result"] \
    = original_production_plan[original_production_plan["Production Plan"].isna()]["Original production_plan"]

# %%
original_production_plan.drop(["Original production_plan", "Production Plan"], axis = 1, inplace = True)
# %%
original_production_plan.fillna(0, inplace = True)

# %%
original_production_plan["date"] = original_production_plan["date"].dt.strftime("%Y-%m-%d")
original_production_plan

# %%
original_production_plan = original_production_plan[(original_production_plan.date >= DEFAULT_PLAN_START_DATE) & 
                                                    (original_production_plan.date <= DEFAULT_PLAN_FINISH_DATE)]
# %%
production_plan_result = pd.pivot_table(original_production_plan, index = ["PART NUMBER", "LINE"],
                                        values = "Production Plan Result", columns = "date").reset_index() 
production_plan_result = production_plan_result.merge(part_order, how = "left", on = "PART NUMBER")

# %%
production_plan_result = production_plan_result.sort_values(["part_order_num", "LINE"])

# %%
production_plan_result.index = range(1, production_plan_result.shape[0] + 1)

# %%
production_plan_result
# %%
df[(df["LIST"] == "Production Plan") & (~df["LINE"].isna())]
# %%
