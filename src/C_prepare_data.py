# %%
from A_constants import *
import pandas as pd 
import numpy as np 
import datetime

def prepare_data(df, PLAN_START_DATE, PLAN_FINISH_DATE):

        df_line_info = df[df.LINE != "ALL"][["PART NUMBER", "LINE"]].drop_duplicates()
        df_line_info.loc[df_line_info["PART NUMBER"] == "96210-CW100EB", "LINE"] = "ALL"
        df_line_info = df_line_info.drop_duplicates()
        df_line_info = df_line_info[df_line_info["PART NUMBER"].str.split("-").str[1].str[:3] != "R51"]
        df_line_info.dropna(inplace = True)
 
        df_inventory = df[df["LIST"] == "Inventory"].drop("LINE", axis = 1).drop_duplicates()
        df_inventory = pd.melt(df_inventory, id_vars = ["PROGRAM", "PART NUMBER", "LIST"], 
                               var_name = "date", value_name = "Inventory").drop("LIST", axis = 1) \
                       [["PART NUMBER", "PROGRAM", "date", "Inventory"]]
        df_inventory["date"] = pd.to_datetime(df_inventory.date)
        df_inventory["day_of_week"] = df_inventory["date"].dt.strftime("%a")
        df_inventory = df_inventory[~df_inventory.date.isna()]
        df_inventory = df_inventory[df_inventory.date >= PLAN_START_DATE]

        df_shipping_plan = df[df["LIST"] == "Shipping Plan"].drop("LINE", axis = 1).drop_duplicates()
        df_shipping_plan = pd.melt(df_shipping_plan, id_vars = ["PROGRAM", "PART NUMBER", "LIST"], 
                                   var_name = "date", value_name = "Shipping_plan").drop("LIST", axis = 1) \
                           [["PART NUMBER", "PROGRAM", "date", "Shipping_plan"]]
        df_shipping_plan["date"] = pd.to_datetime(df_shipping_plan.date)
        df_shipping_plan["day_of_week"] = df_shipping_plan["date"].dt.strftime("%a")
        df_shipping_plan = df_shipping_plan[df_shipping_plan.date >= PLAN_START_DATE]


        df_production_plan = df[df["LIST"] == "Production Plan"]
        df_production_plan = pd.melt(df_production_plan, id_vars = ["LINE", "PROGRAM", "PART NUMBER", "LIST"], 
                                     var_name = "date", value_name = "Production_plan").drop("LIST", axis = 1) \
                             [["LINE", "PART NUMBER", "PROGRAM", "date", "Production_plan"]]
        df_production_plan["date"] = pd.to_datetime(df_production_plan.date)
        df_production_plan["day_of_week"] = df_production_plan["date"].dt.strftime("%a")
        df_production_plan = df_production_plan[~df_production_plan.date.isna()]
        df_production_plan = df_production_plan[df_production_plan.date >= PLAN_START_DATE]
        df_production_plan = df_production_plan[~df_production_plan["LINE"].isna()] 
        df_production_plan["Production_plan"] = 0

        df_daily_full_available =  pd.DataFrame([["#1", "2 wire"], 
                                                 ["#2", "2 wire"],
                                                 ["#2", "4 wire"],\
                                                 ["#3", "4 wire"]], columns = ["LINE", "num_wire"])

        two_weeks_list = [PLAN_START_DATE]
        for i in range(1, (pd.to_datetime(PLAN_FINISH_DATE) - pd.to_datetime(PLAN_START_DATE)).days + 1):
            two_weeks_list.append((pd.to_datetime(PLAN_START_DATE) + datetime.timedelta(days = i)).strftime("%Y-%m-%d"))

        two_weeks_list = pd.DataFrame(two_weeks_list, columns = ["date"])

        df_daily_full_available = df_daily_full_available.merge(two_weeks_list, how = "cross")
        df_daily_full_available.loc[df_daily_full_available["LINE"] == "#1", "full_available"] = LINE_1_FULL_AVAILABILITY
        df_daily_full_available.loc[(df_daily_full_available["LINE"] == "#2") & (df_daily_full_available["num_wire"] == "2 wire"), "full_available"] = LINE_2_2WIRE_FULL_AVAILABILITY
        df_daily_full_available.loc[(df_daily_full_available["LINE"] == "#2") & (df_daily_full_available["num_wire"] == "4 wire"), "full_available"] = LINE_2_4WIRE_FULL_AVAILABILITY
        df_daily_full_available.loc[df_daily_full_available["LINE"] == "#3", "full_available"] = LINE_3_FULL_AVAILABILITY
        df_daily_full_available["day_of_week"] = pd.to_datetime(df_daily_full_available["date"]).dt.strftime("%a")
        df_daily_full_available.loc[df_daily_full_available.day_of_week.isin(["Sat", "Sun"]) , "full_available"] = 0

        df_uph = df_daily_full_available[["LINE", "num_wire"]].drop_duplicates()
        df_uph.loc[df_uph["LINE"] == "#1", "uph"] = LINE_1_UPH
        df_uph.loc[(df_uph["LINE"] == "#2") & (df_uph["num_wire"] == "2 wire"), "uph"] = LINE_2_2WIRE_UPH
        df_uph.loc[(df_uph["LINE"] == "#2") & (df_uph["num_wire"] == "4 wire"), "uph"] = LINE_2_4WIRE_UPH
        df_uph.loc[df_uph["LINE"] == "#3", "uph"] = LINE_3_UPH

        df_basic_info = df[["PROGRAM", "PART NUMBER"]].drop_duplicates()
        df_basic_info.loc[df_basic_info["PART NUMBER"].str.split("-").str[1].str[:5].isin(["R5400", "CW000"]), "num_wire"] = "2 wire"
        df_basic_info.loc[df_basic_info["PART NUMBER"].isin(df_line_info[df_line_info["LINE"].isin(["#3", "ALL"])]["PART NUMBER"]), "num_wire"] = "4 wire"
        df_basic_info.loc[df_basic_info["PART NUMBER"].str.split("-").str[1].str[:5].isin(["R5600"]), "num_wire"] = "4 wire"

        df_basic_info.loc[df_basic_info["PART NUMBER"].str.split("-").str[1].str[:2].isin(["CW"]), "P/Q"] = HMMA_PACK_QUANTITY
        df_basic_info["P/Q"].fillna(KIA_PACK_QUANTITY, inplace = True)
        
        return df_line_info, df_inventory, df_shipping_plan, df_production_plan, df_daily_full_available, df_uph, df_basic_info
