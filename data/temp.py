# %%
import pandas as pd 
import numpy as np 
import datetime

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
import math 

def to_16_divisible(number, mode):
    if mode == "up":
        return math.ceil(number / 16) * 16
    if mode == "down":
        return math.floor(number / 16) * 16

def to_28_divisible(number, mode):
    if mode == "up":
        return math.ceil(number / 28) * 28
    if mode == "down":
        return math.floor(number / 28) * 28
    if mode == "round":
        return round(number / 28) * 28

# %%
df = pd.read_excel("input_data_100423.xlsx", sheet_name = "Combi Ant", skiprows = 3)
df = df.iloc[1:, 3:]
df

# %%
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

# %%
def Line2_production_plan(df, start_date, end_date):
    output_text_list = []
    
    df_line_info, df_inventory, df_shipping_plan, df_production_plan, \
    df_daily_full_available, df_uph, df_basic_info = prepare_data(df, start_date, end_date)
    
    # print("==== Line 2 ==== \n")
    output_text_list.append("==== Line 2 ==== \n")

    line_part_list = df_line_info[df_line_info["LINE"] == "#2"]["PART NUMBER"]
    line_inventory_plan = df_inventory[df_inventory["PART NUMBER"].isin(line_part_list)]
    line_inventory_plan = line_inventory_plan.merge(df_production_plan[df_production_plan["PART NUMBER"].isin(line_part_list)].drop("LINE", axis = 1), 
                                                    how = "left", on = ["PART NUMBER", "PROGRAM", "date","day_of_week"]) \
                                                    [["PART NUMBER", "PROGRAM", "date", "day_of_week", "Production_plan", "Inventory"]]
    line_inventory_plan["Production_plan"].fillna(0, inplace = True)

    line_cw100_plan = df_production_plan[(df_production_plan["PART NUMBER"] == "96210-CW100EB") & 
                                         (df_production_plan["LINE"] == "#2")].fillna(0).sort_values("date")

    current_date = DEFAULT_PLAN_START_DATE
    
    production_summary = {}
    
    while current_date != (pd.to_datetime(DEFAULT_PLAN_FINISH_DATE) + datetime.timedelta(days = 1)).strftime("%Y-%m-%d"):
        
        output_text_list.append(f"======= Production plan start for {current_date}")

        satisfy_until_date = (pd.to_datetime(current_date) + 
                              datetime.timedelta(days = 10) - 
                              datetime.timedelta(days = (pd.to_datetime(current_date).weekday() + 1))).strftime("%Y-%m-%d")

        current_date_priority = line_inventory_plan[line_inventory_plan["Inventory"] < 0].sort_values(["date", "Inventory"])
        current_date_priority = current_date_priority.merge(df_shipping_plan, how = "left", on = ["PART NUMBER", "PROGRAM", "date", "day_of_week"])
        current_date_priority = current_date_priority[current_date_priority.Shipping_plan > 0] 

        # print("-- Original priority:")
        output_text_list.append("-- Original priority:")
        # display(current_date_priority.head(5))
        # output_text_list.append(current_date_priority.head(5))

        current_wire = df_basic_info[df_basic_info["PART NUMBER"] == current_date_priority.iloc[0]["PART NUMBER"]].num_wire.values[0]
        uph = df_uph[(df_uph['LINE'] == '#2') & (df_uph["num_wire"] == current_wire)].uph.values[0]

        # print(f"-- Produce {current_wire} parts")
        # print(f"-- UPH: {uph}")

        current_date_priority = current_date_priority[current_date_priority["PART NUMBER"].isin(df_basic_info[df_basic_info.num_wire == current_wire]["PART NUMBER"])]
        current_date_full_available = df_daily_full_available[(df_daily_full_available.date == current_date) & 
                                                                  (df_daily_full_available.LINE == "#2") &
                                                                  (df_daily_full_available.num_wire == current_wire)].full_available.values[0]

        # print("-- Current date full production availability: ", current_date_full_available)

        current_date_production = {}
        current_date_produced_program_list = []
    
        while current_date_full_available > 16:
            # print("-- Changed priority:")
            # display(current_date_priority.head(5))
        
            if (current_date_priority[current_date_priority.date < satisfy_until_date].shape[0] == 0) & \
               (len(current_date_production) < 4) & \
               (current_wire == "4 wire"):
                # print("-- There are no remaining KIA antenna parts until next week. Move to CW100EB part.")
                # print("-- Current target part: 96210-CW100EB")
                # print("-- Current production availability: ", current_date_full_available)
            
                if len(current_date_production) != 0:
                    changeover_downtime = 15
                    # print("-- Change over downtime: ", changeover_downtime, " mins")
                    production_deduction = math.ceil(changeover_downtime * uph / 60)
                    # print(f"    -- UPH: {uph} -> {changeover_downtime} mins: {production_deduction} production availability deduction")
                    # print(f"    -- {current_date_full_available} - {production_deduction} = {current_date_full_available - production_deduction} production available")
                    current_date_full_available -= production_deduction
            
                # print("-- Production plan: ", to_28_divisible(current_date_full_available, "round"))
                line_cw100_plan.loc[line_cw100_plan.date == current_date, "Production_plan"] = to_28_divisible(current_date_full_available, "round")
                current_date_production["96210-CW100EB"] = to_28_divisible(current_date_full_available, "round")
                current_date_full_available -= to_28_divisible(current_date_full_available, "round")
                # print("-- Check inventory plan: \n")
                # display(line_cw100_plan.head(14))
                # print("-- After plan, production availability: ", current_date_full_available)
                # print("-- Current date production: ", current_date_production, "\n")

                current_date_full_available = 0
        
            else:
                current_target_info = current_date_priority.iloc[0]

                current_program = df_basic_info[df_basic_info["PART NUMBER"] == current_target_info["PART NUMBER"]].PROGRAM.values[0]

                # print("-- Current target part: ", current_target_info["PART NUMBER"])
                # print("-- Current production availability: ", current_date_full_available)

                last_shipping_plan = df_shipping_plan[df_shipping_plan["PART NUMBER"] == current_target_info["PART NUMBER"]].dropna().date.max()

                if current_target_info["date"] == last_shipping_plan:
                    production_amount = - current_target_info.Inventory

                elif current_target_info["PART NUMBER"].split("-")[1][:2] == "CW":
                    production_amount = to_28_divisible(-current_target_info.Inventory, "up") + 28

                elif (len(current_target_info["PART NUMBER"].split("-")[1]) >= 6) & \
                     (current_target_info["PART NUMBER"].split("-")[1][:5] == "R5400"):
                    production_amount = -current_target_info.Inventory

                else:
                    production_amount = to_16_divisible(-current_target_info.Inventory, "up") + 16

                if (current_program in current_date_produced_program_list) & \
                   (current_target_info["PART NUMBER"] not in list(current_date_production.keys())): 
                    changeover_downtime = 5

                elif (len(current_date_produced_program_list) >= 1) & \
                     (current_program not in current_date_produced_program_list): 
                    changeover_downtime = 15

                else: changeover_downtime = 0

                current_date_produced_program_list.append(current_program)

                if changeover_downtime > 0:
                    # print("-- Change over downtime: ", changeover_downtime, " mins")
                    production_deduction = math.ceil(changeover_downtime * uph / 60)
                    # print(f"    -- UPH: {uph} -> {changeover_downtime} mins: {production_deduction} production availability deduction")
                    # print(f"    -- {current_date_full_available} - {production_deduction} = {current_date_full_available - production_deduction} production available")
                    current_date_full_available -= production_deduction

                # print("-- Current target shortage: ", -current_target_info["Inventory"], " on ", current_target_info["date"])

                if production_amount > current_date_full_available:
                    if current_target_info["PART NUMBER"].split("-")[1][:2] == "CW":
                        production_amount = to_28_divisible(current_date_full_available, "down")
                    else:
                        production_amount = to_16_divisible(current_date_full_available, "down")

                if current_date_production.get(current_target_info["PART NUMBER"]) == None:
                    current_date_production[current_target_info["PART NUMBER"]] = production_amount
                else:
                    current_date_production[current_target_info["PART NUMBER"]] += production_amount

                current_date_full_available -= production_amount
                line_inventory_plan.loc[(line_inventory_plan.date == current_date) & 
                                        (line_inventory_plan["PART NUMBER"] == current_target_info["PART NUMBER"]), "Production_plan"] += production_amount
                # print("-- Production plan: ", production_amount) 

                current_date_priority = current_date_priority[~((current_date_priority["PART NUMBER"] == current_target_info["PART NUMBER"]) & 
                                                                (current_date_priority["date"] == current_target_info["date"]))]

                current_target_inventory_plan = line_inventory_plan[line_inventory_plan["PART NUMBER"] == current_target_info["PART NUMBER"]]
                current_target_inventory_plan = current_target_inventory_plan.drop("Inventory", axis = 1).merge(df_inventory[["PART NUMBER", "date", "Inventory"]], 
                                                                                                                how = "left", on = ["PART NUMBER", "date"])
                current_target_inventory_plan["production_plan_cumsum"] = current_target_inventory_plan.sort_values(["PART NUMBER", "date"]).groupby(["PART NUMBER"])[["Production_plan"]].cumsum()
                current_target_inventory_plan["Inventory"] = current_target_inventory_plan.Inventory + current_target_inventory_plan.production_plan_cumsum
                line_inventory_plan = pd.concat([
                    line_inventory_plan[line_inventory_plan["PART NUMBER"] != current_target_info["PART NUMBER"]],
                    line_inventory_plan[line_inventory_plan["PART NUMBER"] == current_target_info["PART NUMBER"]] \
                        .drop("Inventory", axis = 1).merge(current_target_inventory_plan[["PART NUMBER", "date", "Inventory"]],
                                                           how = "left", on = ["PART NUMBER", "date"])
                ])

                # print("-- Check inventory plan: \n")
                # display(line_inventory_plan[line_inventory_plan["PART NUMBER"] == current_target_info["PART NUMBER"]].sort_values("date").head(14))

                current_date_priority = current_date_priority.drop("Inventory", axis = 1).merge(line_inventory_plan[["PART NUMBER", "date", "Inventory"]],                                                                            how = "left", on = ["PART NUMBER", "date"])
                current_date_priority = current_date_priority[(current_date_priority.Shipping_plan > 0) & (current_date_priority.Inventory < 0)] 
                current_date_priority = current_date_priority.sort_values(["date", "Inventory"])
                if (len(current_date_production) == 4) & (current_wire == "4 wire"):
                        current_date_priority = current_date_priority[current_date_priority["PART NUMBER"].isin(current_date_production.keys())] 

                # print("-- After plan, production availability: ", current_date_full_available)
                # print("-- Current date production: ", current_date_production)
                # print("-------------------------------------------------------------------------------------------------\n")
    
        production_summary[current_date] = current_date_production
        current_date = (pd.to_datetime(current_date) + datetime.timedelta(days = 1)).strftime("%Y-%m-%d") 
        # print(" ")

    return output_text_list, production_summary

def Line3_production_plan(df, start_date, end_date):
    output_text_list = []
    df_line_info, df_inventory, df_shipping_plan, df_production_plan, \
    df_daily_full_available, df_uph, df_basic_info = prepare_data(df, start_date, end_date)
    
    print("==== Line 3 ==== \n")
    output_text_list.append("==== Line 3 ==== \n")

    line_part_list = df_line_info[df_line_info["LINE"] == "#3"]["PART NUMBER"]
    line_inventory_plan = df_inventory[df_inventory["PART NUMBER"].isin(line_part_list)]
    line_inventory_plan = line_inventory_plan.merge(df_production_plan[df_production_plan["PART NUMBER"].isin(line_part_list)].drop("LINE", axis = 1), 
                                                    how = "left", on = ["PART NUMBER", "PROGRAM", "date","day_of_week"]) \
                                                    [["PART NUMBER", "PROGRAM", "date", "day_of_week", "Production_plan", "Inventory"]]
    line_inventory_plan["Production_plan"].fillna(0, inplace = True)

    line_cw100_plan = df_production_plan[(df_production_plan["PART NUMBER"] == "96210-CW100EB") & 
                                         (df_production_plan["LINE"] == "#3")].fillna(0).sort_values("date")

    current_date = start_date
    
    production_summary = {}
    
    while current_date != (pd.to_datetime(end_date) + datetime.timedelta(days = 1)).strftime("%Y-%m-%d"): 
        satisfy_until_date = (pd.to_datetime(current_date) + 
                              datetime.timedelta(days = 10) - 
                              datetime.timedelta(days = (pd.to_datetime(current_date).weekday() + 1))).strftime("%Y-%m-%d")

        print(f"======= Production plan start for {current_date}")
        output_text_list.append(f"======= Production plan start for {current_date}")
    
        current_date_full_available = df_daily_full_available[(df_daily_full_available["LINE"] == "#3") & 
                                                              (df_daily_full_available["date"] == current_date)].full_available.values[0]
        print("-- Current date full production availability: ", current_date_full_available)
        output_text_list.append(f"-- Current date full production availability: {current_date_full_available}")
        
        current_date_priority = line_inventory_plan[(line_inventory_plan["Inventory"] < 0) & (line_inventory_plan.date <= satisfy_until_date)].sort_values(["date", "Inventory"])
        current_date_priority = current_date_priority.merge(df_shipping_plan, how = "left", on = ["PART NUMBER", "PROGRAM", "date", "day_of_week"])
        current_date_priority = current_date_priority[current_date_priority.Shipping_plan > 0] 
        current_target_before_date = current_date_priority.date.min()
    
        current_date_production = {}

        while current_date_full_available > 16:
            print("-- Priority: \n")
            output_text_list.append("-- Priority: \n")
            print(current_date_priority.head(5))
            #output_text_list.append(current_date_priority.head(5))
        
            if current_date_priority.shape[0] == 0:
                if (len(current_date_production) != 0):
                    print("== Add pack quantity before move to 'CW100'")

                    for k, v in current_date_production.items():
                        print("-- Part number: ", k)

                        p_q = df_basic_info[df_basic_info["PART NUMBER"] == k]["P/Q"].values[0]

                        if p_q <= current_date_full_available:
                            print("-- Before production plan: ", v)
                            print("-- Pack quantity: ", p_q)
                            v += p_q 
                            print("-- After production plan: ", v)

                            current_date_production[k] = v

                            print("-- Before production availability: ", current_date_full_available)
                            current_date_full_available -= p_q 
                            print("-- After production availability: ", current_date_full_available)

                            line_inventory_plan.loc[(line_inventory_plan.date == current_date) & 
                                                    (line_inventory_plan["PART NUMBER"] == k), "Production_plan"] = v
                            line_inventory_plan.loc[line_inventory_plan["PART NUMBER"] == k, "Inventory"] += p_q

                            print("-- Check inventory plan: \n")
                            display(line_inventory_plan[line_inventory_plan["PART NUMBER"] == k].sort_values("date").head(14))
            
                if current_date_full_available >= 28:
                    print("-- Current target part: 96210-CW100EB")
                    print("-- Current production availability: ", current_date_full_available)
                    print("-- Change over deduction: ", -5, "production availability")
                    current_date_full_available -=  5

                    print("-- Production plan: ", to_28_divisible(current_date_full_available, "round"))
                    line_cw100_plan.loc[line_cw100_plan.date == current_date, "Production_plan"] = to_28_divisible(current_date_full_available, "round")
                    current_date_production["96210-CW100EB"] = to_28_divisible(current_date_full_available, "round")
                    current_date_full_available -= to_28_divisible(current_date_full_available, "round")

                    print("-- Check inventory plan: \n")
                    display(line_cw100_plan.head(14))

                    print("-- After plan, production availability: ", current_date_full_available)
                    print("-- Current date production: ", current_date_production, "\n")
            
                current_date_full_available = 0

            else:
                current_target_info = current_date_priority.iloc[0]
        
                if current_target_info.date > current_target_before_date:
                    # 16씩 순차적으로 더해
                    print("== Add pack quantity before move to next target date")
                    for k, v in current_date_production.items():
                        print("-- Part number: ", k)

                        p_q = df_basic_info[df_basic_info["PART NUMBER"] == k]["P/Q"].values[0]

                        if p_q <= current_date_full_available:
                            print("-- Before production plan: ", v)
                            print("-- Pack quantity: ", p_q)
                            v += p_q 
                            print("-- After production plan: ", v)

                            current_date_production[k] = v

                            print("-- Before production availability: ", current_date_full_available)
                            current_date_full_available -= p_q 
                            print("-- After production availability: ", current_date_full_available)

                            line_inventory_plan.loc[(line_inventory_plan.date == current_date) & 
                                                    (line_inventory_plan["PART NUMBER"] == k), "Production_plan"] = v
                            line_inventory_plan.loc[line_inventory_plan["PART NUMBER"] == k, "Inventory"] += p_q

                            print("-- Check inventory plan: \n")
                            display(line_inventory_plan[line_inventory_plan["PART NUMBER"] == k].sort_values("date").head(14))

                    current_target_before_date = current_target_info.date
                else:
                    current_target_before_date = current_target_info.date

                    print("-- Current target part: ", current_target_info["PART NUMBER"])
                    print("-- Current production availability: ", current_date_full_available)
                    print("-- Current target shortage: ", current_target_info["Inventory"], " on ", current_target_info["date"])

                    if to_16_divisible(-current_target_info.Inventory, "up") <= current_date_full_available:
                        if current_date_production.get(current_target_info["PART NUMBER"]) == None:
                            current_date_production[current_target_info["PART NUMBER"]] = to_16_divisible(-current_target_info.Inventory, "up")

                            if len(current_date_production) >= 2:
                                current_date_full_available -= 5
                                print("-- Change over deduction: ", -5, " production availability")

                        else:
                            current_date_production[current_target_info["PART NUMBER"]] += to_16_divisible(-current_target_info.Inventory, "up")


                        current_date_full_available -= to_16_divisible(-current_target_info.Inventory, "up")
                        line_inventory_plan.loc[(line_inventory_plan.date == current_date) & 
                                                (line_inventory_plan["PART NUMBER"] == current_target_info["PART NUMBER"]), "Production_plan"] += to_16_divisible(-current_target_info.Inventory, "up")
                        print("-- Production plan: ", to_16_divisible(-current_target_info.Inventory, "up"))
                    else:
                        if current_date_production.get(current_target_info["PART NUMBER"]) == None:
                            if len(current_date_production) >= 1:
                                current_date_full_available -= 5
                                print("-- Change over deduction: ", -5, " production availability")
                            
                            current_date_production[current_target_info["PART NUMBER"]] = to_16_divisible(current_date_full_available, "down")
                        
                        
                    
                        else:
                            current_date_production[current_target_info["PART NUMBER"]] += to_16_divisible(current_date_full_available, "down")

                        line_inventory_plan.loc[(line_inventory_plan.date == current_date) & 
                                                (line_inventory_plan["PART NUMBER"] == current_target_info["PART NUMBER"]), "Production_plan"] += to_16_divisible(current_date_full_available, "down")
                        print("-- Production plan: ", to_16_divisible(current_date_full_available, "down"))
                        current_date_full_available -= to_16_divisible(current_date_full_available, "down")


                    current_date_priority = current_date_priority[~((current_date_priority["PART NUMBER"] == current_target_info["PART NUMBER"]) & 
                                                                    (current_date_priority["date"] == current_target_info["date"]))]

                    current_target_inventory_plan = line_inventory_plan[line_inventory_plan["PART NUMBER"] == current_target_info["PART NUMBER"]]
                    current_target_inventory_plan = current_target_inventory_plan.drop("Inventory", axis = 1).merge(df_inventory[["PART NUMBER", "date", "Inventory"]], 
                                                                                                                    how = "left", on = ["PART NUMBER", "date"])
                    current_target_inventory_plan["production_plan_cumsum"] = current_target_inventory_plan.sort_values(["PART NUMBER", "date"]).groupby(["PART NUMBER"])[["Production_plan"]].cumsum()
                    current_target_inventory_plan["Inventory"] = current_target_inventory_plan.Inventory + current_target_inventory_plan.production_plan_cumsum

                    line_inventory_plan = pd.concat([
                        line_inventory_plan[line_inventory_plan["PART NUMBER"] != current_target_info["PART NUMBER"]],
                        line_inventory_plan[line_inventory_plan["PART NUMBER"] == current_target_info["PART NUMBER"]] \
                            .drop("Inventory", axis = 1).merge(current_target_inventory_plan[["PART NUMBER", "date", "Inventory"]],
                                                               how = "left", on = ["PART NUMBER", "date"])
                    ])

                    print("-- Check inventory plan: \n")
                    display(line_inventory_plan[line_inventory_plan["PART NUMBER"] == current_target_info["PART NUMBER"]].sort_values("date").head(14))


                current_date_priority = current_date_priority.drop("Inventory", axis = 1).merge(line_inventory_plan[["PART NUMBER", "date", "Inventory"]], 
                                                                                                how = "left", on = ["PART NUMBER", "date"])
                current_date_priority = current_date_priority[(current_date_priority.Shipping_plan > 0) & (current_date_priority.Inventory < 0)] 
                current_date_priority = current_date_priority.sort_values(["date", "Inventory"])

                if len(current_date_production) == 4:
                    current_date_priority = current_date_priority[current_date_priority["PART NUMBER"].isin(current_date_production.keys())] 

                print("-- After plan, production availability: ", current_date_full_available)
                print("-- Current date production: ", current_date_production)
                print("-------------------------------------------------------------------------------------------------\n")
            production_summary[current_date] = current_date_production
    
        current_date = (pd.to_datetime(current_date) + datetime.timedelta(days = 1)).strftime("%Y-%m-%d") 

        print("\n")
    
    return output_text_list, production_summary

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
line2_production_summary = Line2_production_plan(df, DEFAULT_PLAN_START_DATE, DEFAULT_PLAN_FINISH_DATE)
output_text_list, line3_production_summary = Line3_production_plan(df, DEFAULT_PLAN_START_DATE, DEFAULT_PLAN_FINISH_DATE)

# %%
output_text_list[0]
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
production_summary_df_pivot = pd.pivot_table(production_summary_df, index = ["PART NUMBER", "LINE"],
                                             values = "Production Plan", columns = "date").fillna(0).reset_index() \
                                                                                          .sort_values(["LINE", "PART NUMBER"])
# %%
production_summary_df_pivot.index = range(1, production_summary_df_pivot.shape[0] + 1)
# %%
production_summary_df_pivot
