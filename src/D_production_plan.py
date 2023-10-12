# %%
from A_constants import *
from B_utils import * 
from C_prepare_data import *
import warnings

warnings.filterwarnings("ignore")
pd.set_option('display.max_rows', 50)

# %%
def Line3_production_plan(df, start_date, end_date, df_daily_full_available_edited):
    df_line_info, df_inventory, df_shipping_plan, df_production_plan, \
    _, df_uph, df_basic_info = prepare_data(df, start_date, end_date)
    
    df_daily_full_available = df_daily_full_available_edited
    # print("==== Line 3 ==== \n")

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

        # print(f"======= Production plan start for {current_date}")
        uph = df_uph[(df_uph['LINE'] == '#3')].uph.values[0]
    
        current_date_full_available = df_daily_full_available[(df_daily_full_available["LINE"] == "#3") & 
                                                              (df_daily_full_available["date"] == current_date)].full_available.values[0]
        # print("-- Current date full production availability: ", current_date_full_available)
        
        current_date_priority = line_inventory_plan[(line_inventory_plan["Inventory"] < 0) & (line_inventory_plan.date <= satisfy_until_date)].sort_values(["date", "Inventory"])
        current_date_priority = current_date_priority.merge(df_shipping_plan, how = "left", on = ["PART NUMBER", "PROGRAM", "date", "day_of_week"])
        current_date_priority = current_date_priority[current_date_priority.Shipping_plan > 0] 
    
        current_date_production = {}

        while current_date_full_available >= 16:
            # print("-- Priority: \n")
            # display(current_date_priority.head(5))
        
            if (current_date_priority.shape[0] == 0) & (len(current_date_production) < 4):
                if current_date_full_available >= 28:
                    # print("-- Current target part: 96210-CW100EB")
                    # print("-- Current production availability: ", current_date_full_available)
                    
                    if len(current_date_production) != 0:
                        changeover_downtime = CHANGEOVER_DOWNTIME_DIFFERENT_PROGRAM
                    else:
                        changeover_downtime = 0 
                    
                    if changeover_downtime > 0:
                        # print("-- Change over downtime: ", changeover_downtime, " mins")
                        production_deduction = math.floor(changeover_downtime * uph / 60)
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
            elif (current_date_priority.shape[0] == 0) & (len(current_date_production) == 4):
                # print("-- There is no short inventory until next Wed, but We have produced 4 parts today. So we do not consider producing new parts today and keep producing current parts.")        
                current_date_priority = line_inventory_plan[(line_inventory_plan["Inventory"] < 0)].sort_values(["date", "Inventory"])
                current_date_priority = current_date_priority.merge(df_shipping_plan, how = "left", on = ["PART NUMBER", "PROGRAM", "date", "day_of_week"])
                current_date_priority = current_date_priority[current_date_priority.Shipping_plan > 0] 
                current_date_priority = current_date_priority[current_date_priority["PART NUMBER"].isin(current_date_production.keys())]
                # print("-- New priority: \n")
                # display(current_date_priority.head(5))
            
            else:
                if len(current_date_production) == 4:     
                    # print("-- We have produced 4 parts today. So we do not consider producing new parts today and keep producing current parts.")        
                    current_date_priority = line_inventory_plan[(line_inventory_plan["Inventory"] < 0)].sort_values(["date", "Inventory"])
                    current_date_priority = current_date_priority.merge(df_shipping_plan, how = "left", on = ["PART NUMBER", "PROGRAM", "date", "day_of_week"])
                    current_date_priority = current_date_priority[current_date_priority.Shipping_plan > 0] 
                    current_date_priority = current_date_priority[current_date_priority["PART NUMBER"].isin(current_date_production.keys())]
                    # print("-- New priority: \n")
                    # display(current_date_priority.head(5))
                    
                elif current_date_full_available <= 32:
                    # print("-- Since current full production availability is less than 32, we do not consider producing new parts today.")
                    current_date_priority = line_inventory_plan[(line_inventory_plan["Inventory"] < 0)].sort_values(["date", "Inventory"])
                    current_date_priority = current_date_priority.merge(df_shipping_plan, how = "left", on = ["PART NUMBER", "PROGRAM", "date", "day_of_week"])
                    current_date_priority = current_date_priority[current_date_priority.Shipping_plan > 0] 
                    current_date_priority = current_date_priority[current_date_priority["PART NUMBER"].isin(current_date_production.keys())]
                    # print("-- New priority: \n")
                    # display(current_date_priority.head(5))
                
                current_target_info = current_date_priority.iloc[0]
                        
                # print("-- Current target part: ", current_target_info["PART NUMBER"])
                # print("-- Current production availability: ", current_date_full_available)
                # print("-- Current target shortage: ", current_target_info["Inventory"], " on ", current_target_info["date"])
                
                production_amount = to_16_divisible(-current_target_info.Inventory, "up") + 16
                
                if production_amount <= current_date_full_available:
                    if current_date_production.get(current_target_info["PART NUMBER"]) == None:
                        current_date_production[current_target_info["PART NUMBER"]] = production_amount
                        if len(current_date_production) >= 2:
                            changeover_downtime = CHANGEOVER_DOWNTIME_SAME_PROGRAM
                            # print("-- Change over downtime: ", changeover_downtime, " mins")
                            production_deduction = math.floor(changeover_downtime * uph / 60)
                            # print(f"    -- UPH: {uph} -> {changeover_downtime} mins: {production_deduction} production availability deduction")
                            # print(f"    -- {current_date_full_available} - {production_deduction} = {current_date_full_available - production_deduction} production available")
                            current_date_full_available -= production_deduction
                            
                    else:
                        current_date_production[current_target_info["PART NUMBER"]] += production_amount
                    current_date_full_available -= production_amount
                    line_inventory_plan.loc[(line_inventory_plan.date == current_date) & 
                                            (line_inventory_plan["PART NUMBER"] == current_target_info["PART NUMBER"]), "Production_plan"] += production_amount
                    # print("-- Production plan: ", production_amount)
                
                else:
                    if current_date_production.get(current_target_info["PART NUMBER"]) == None:
                        if len(current_date_production) >= 1:
                            changeover_downtime = CHANGEOVER_DOWNTIME_SAME_PROGRAM
                            # print("-- Change over downtime: ", changeover_downtime, " mins")
                            production_deduction = math.floor(changeover_downtime * uph / 60)
                            # print(f"    -- UPH: {uph} -> {changeover_downtime} mins: {production_deduction} production availability deduction")
                            # print(f"    -- {current_date_full_available} - {production_deduction} = {current_date_full_available - production_deduction} production available")
                            current_date_full_available -= production_deduction
                             
                        current_date_production[current_target_info["PART NUMBER"]] = to_16_divisible(current_date_full_available, "down")
                    
                    else:
                        current_date_production[current_target_info["PART NUMBER"]] += to_16_divisible(current_date_full_available, "down")
                    line_inventory_plan.loc[(line_inventory_plan.date == current_date) & 
                                            (line_inventory_plan["PART NUMBER"] == current_target_info["PART NUMBER"]), "Production_plan"] += to_16_divisible(current_date_full_available, "down")
                    # print("-- Production plan: ", to_16_divisible(current_date_full_available, "down"))
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
                # print("-- Check inventory plan: \n")
                # display(line_inventory_plan[line_inventory_plan["PART NUMBER"] == current_target_info["PART NUMBER"]].sort_values("date").head(14))


                current_date_priority = current_date_priority.drop("Inventory", axis = 1).merge(line_inventory_plan[["PART NUMBER", "date", "Inventory"]], 
                                                                                                how = "left", on = ["PART NUMBER", "date"])
                current_date_priority = current_date_priority[(current_date_priority.Shipping_plan > 0) & (current_date_priority.Inventory < 0)] 
                current_date_priority = current_date_priority.sort_values(["date", "Inventory"])

                # if len(current_date_production) == 4:
                #     current_date_priority = current_date_priority[current_date_priority["PART NUMBER"].isin(current_date_production.keys())] 

                # print("-- After plan, production availability: ", current_date_full_available)
                # print("-- Current date production: ", current_date_production)
                # print("-------------------------------------------------------------------------------------------------\n")
            production_summary[current_date] = current_date_production
    
        current_date = (pd.to_datetime(current_date) + datetime.timedelta(days = 1)).strftime("%Y-%m-%d") 

        # print("\n")
    
    return production_summary

# %%
def Line3_production_plan_summary(df, start_date, end_date, production_summary, df_daily_full_available_edited):
    df_line_info, df_inventory, df_shipping_plan, df_production_plan, \
    _, df_uph, df_basic_info = prepare_data(df, start_date, end_date)
    
    df_daily_full_available = df_daily_full_available_edited
    
    summary_text_list = []
    
    # print("======= Production Summary for Line 3")
    summary_text_list.append("======= Production Summary for Line 3")
    for k, v in production_summary.items():
        current_date_full_available = df_daily_full_available[(df_daily_full_available["LINE"] == "#3") & 
                                                              (df_daily_full_available["date"] == k)].full_available.values[0]

        uph = df_uph[df_uph['LINE'] == '#3'].uph.values[0]

        production_plan_sum = 0
        for v_k, v_v in v.items():
            production_plan_sum += v_v

        num_change_over = len(v) - 1 
        num_change_over_btw_dfft_program = len(df_basic_info[df_basic_info['PART NUMBER'].isin(list(v.keys()))].PROGRAM.unique().tolist()) - 1
        num_change_over_btw_same_program = num_change_over - num_change_over_btw_dfft_program
        # print(f"[{k}]")
        summary_text_list.append(f"[{k}]")
        # print(f"-- Produce 4 wire parts")
        summary_text_list.append(f"-- Produce 4 wire parts")
        # print(f"-- UPH: {uph}")
        summary_text_list.append(f"-- UPH: {uph}")
        # print(f"-- Full production availability: {current_date_full_available}")
        summary_text_list.append(f"-- Full production availability: {current_date_full_available}")
        # print(f"-- Production plan:")
        summary_text_list.append(f"-- Production plan:")
        for v_k, v_v in v.items():
            # print(f"    -- {v_k} : {v_v}")
            summary_text_list.append(f"---- {v_k} : {v_v}")
        # print(f"-- Number of change over: {num_change_over}") 
        summary_text_list.append(f"-- Number of change over: {num_change_over}")
        # print(f"---- Between different program: {num_change_over_btw_dfft_program} -> {15 * num_change_over_btw_dfft_program} mins downtime")
        summary_text_list.append(f"---- Between different program: {num_change_over_btw_dfft_program} -> {CHANGEOVER_DOWNTIME_DIFFERENT_PROGRAM * num_change_over_btw_dfft_program} mins downtime")
        # print(f"---- Between same program: {num_change_over_btw_same_program} -> {5 * num_change_over_btw_same_program} mins downtime")
        summary_text_list.append(f"---- Between same program: {num_change_over_btw_same_program} -> {CHANGEOVER_DOWNTIME_SAME_PROGRAM * num_change_over_btw_same_program} mins downtime")
        
        total_changeover_downtime = (CHANGEOVER_DOWNTIME_DIFFERENT_PROGRAM * num_change_over_btw_dfft_program) + (CHANGEOVER_DOWNTIME_SAME_PROGRAM * num_change_over_btw_same_program)
        # print(f"----> Total {total_changeover_downtime} mins downtime")
        summary_text_list.append(f"----> Total {total_changeover_downtime} mins downtime")
        
        production_deduction = math.ceil(total_changeover_downtime * uph / 60)
        # print(f"----> UPH: {uph} -> {total_changeover_downtime} mins: {production_deduction} production availability deduction")
        summary_text_list.append(f"----> UPH: {uph} -> {total_changeover_downtime} mins: {production_deduction} production availability deduction")
        # print(f"----> {current_date_full_available} - {production_deduction} =  {current_date_full_available - production_deduction} production available")
        summary_text_list.append(f"----> {current_date_full_available} - {production_deduction} =  {current_date_full_available - production_deduction} production available")
        # print(f"-- Production plan sum: {production_plan_sum}")
        summary_text_list.append(f"-- Production plan sum: {production_plan_sum}")
        # print("\n")
        summary_text_list.append("\n")
        
    return summary_text_list
# %%
def Line2_production_plan(df, start_date, end_date, df_daily_full_available_edited):    
    df_line_info, df_inventory, df_shipping_plan, df_production_plan, \
    _, df_uph, df_basic_info = prepare_data(df, start_date, end_date)
    
    df_daily_full_available = df_daily_full_available_edited
    
    # print("==== Line 2 ==== \n")

    line_part_list = df_line_info[df_line_info["LINE"] == "#2"]["PART NUMBER"]
    line_inventory_plan = df_inventory[df_inventory["PART NUMBER"].isin(line_part_list)]
    line_inventory_plan = line_inventory_plan.merge(df_production_plan[df_production_plan["PART NUMBER"].isin(line_part_list)].drop("LINE", axis = 1), 
                                                    how = "left", on = ["PART NUMBER", "PROGRAM", "date","day_of_week"]) \
                                                    [["PART NUMBER", "PROGRAM", "date", "day_of_week", "Production_plan", "Inventory"]]
    line_inventory_plan["Production_plan"].fillna(0, inplace = True)

    line_cw100_plan = df_production_plan[(df_production_plan["PART NUMBER"] == "96210-CW100EB") & 
                                         (df_production_plan["LINE"] == "#2")].fillna(0).sort_values("date")

    current_date = start_date
    
    production_summary = {}
    
    while current_date != (pd.to_datetime(end_date) + datetime.timedelta(days = 1)).strftime("%Y-%m-%d"):
        # print(f"======= Production plan start for {current_date}")

        satisfy_until_date = (pd.to_datetime(current_date) + 
                              datetime.timedelta(days = 10) - 
                              datetime.timedelta(days = (pd.to_datetime(current_date).weekday() + 1))).strftime("%Y-%m-%d")

        current_date_priority = line_inventory_plan[line_inventory_plan["Inventory"] < 0].sort_values(["date", "Inventory"])
        current_date_priority = current_date_priority.merge(df_shipping_plan, how = "left", on = ["PART NUMBER", "PROGRAM", "date", "day_of_week"])
        current_date_priority = current_date_priority[current_date_priority.Shipping_plan > 0] 

        # print("-- Original priority:")
        # display(current_date_priority.head(5))

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
    
        while current_date_full_available >= 16:
            # print("-- Changed priority:")
            # display(current_date_priority.head(5))
        
            if (current_date_priority[current_date_priority.date < satisfy_until_date].shape[0] == 0) & \
               (len(current_date_production) < 4) & \
               (current_wire == "4 wire"):
                # print("-- There are no remaining KIA antenna parts until next week. Move to CW100EB part.")
                # print("-- Current target part: 96210-CW100EB")
                # print("-- Current production availability: ", current_date_full_available)
            
                if len(current_date_production) != 0:
                    changeover_downtime = CHANGEOVER_DOWNTIME_DIFFERENT_PROGRAM
                    # print("-- Change over downtime: ", changeover_downtime, " mins")
                    production_deduction = math.floor(changeover_downtime * uph / 60)
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
                    changeover_downtime = CHANGEOVER_DOWNTIME_SAME_PROGRAM

                elif (len(current_date_produced_program_list) >= 1) & \
                     (current_program not in current_date_produced_program_list): 
                    changeover_downtime = CHANGEOVER_DOWNTIME_DIFFERENT_PROGRAM

                else: changeover_downtime = 0

                current_date_produced_program_list.append(current_program)

                if changeover_downtime > 0:
                    # print("-- Change over downtime: ", changeover_downtime, " mins")
                    production_deduction = math.floor(changeover_downtime * uph / 60)
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

    return production_summary
# %%
def Line2_production_plan_summary(df, start_date, end_date, production_summary, df_daily_full_available_edited):
    df_line_info, df_inventory, df_shipping_plan, df_production_plan, \
    _, df_uph, df_basic_info = prepare_data(df, start_date, end_date)
    
    df_daily_full_available = df_daily_full_available_edited
    
    summary_text_list = []
    
    # print("======= Production Summary for Line 2")
    summary_text_list.append("======= Production Summary for Line 2")
    for k, v in production_summary.items():
        if len(v) >= 1:
            num_wire = df_basic_info[df_basic_info["PART NUMBER"] == list(v.keys())[0]].num_wire.values[0]
    
            uph = df_uph[(df_uph['LINE'] == '#2') & (df_uph["num_wire"] == num_wire)].uph.values[0]
    
            current_date_full_available = df_daily_full_available[(df_daily_full_available["LINE"] == "#2") & 
                                                                  (df_daily_full_available["num_wire"] == num_wire) &
                                                                  (df_daily_full_available["date"] == k)].full_available.values[0]
    
            production_plan_sum = 0
            for v_k, v_v in v.items():
                production_plan_sum += v_v
    
            num_change_over = len(v) - 1 
            num_change_over_btw_dfft_program = len(df_basic_info[df_basic_info['PART NUMBER'].isin(list(v.keys()))].PROGRAM.unique().tolist()) - 1
            num_change_over_btw_same_program = num_change_over - num_change_over_btw_dfft_program
            
            # print(f"[{k}]")
            summary_text_list.append(f"[{k}]")
            # print(f"-- Produce {num_wire} parts")
            summary_text_list.append(f"-- Produce {num_wire} parts")
            # print(f"-- UPH: {uph}")
            summary_text_list.append(f"-- UPH: {uph}")
            # print(f"-- Full production availability: {current_date_full_available}")
            summary_text_list.append(f"-- Full production availability: {current_date_full_available}")
            # print(f"-- Production plan:")
            summary_text_list.append(f"-- Production plan:")
            for v_k, v_v in v.items():
                # print(f"    -- {v_k} : {v_v}")
                summary_text_list.append(f"---- {v_k} : {v_v}")
            # print(f"-- Number of change over: {num_change_over}") 
            summary_text_list.append(f"-- Number of change over: {num_change_over}")
            # print(f"---- Between different program: {num_change_over_btw_dfft_program} -> {15 * num_change_over_btw_dfft_program} mins downtime")
            summary_text_list.append(f"---- Between different program: {num_change_over_btw_dfft_program} -> {CHANGEOVER_DOWNTIME_DIFFERENT_PROGRAM * num_change_over_btw_dfft_program} mins downtime")
            # print(f"---- Between same program: {num_change_over_btw_same_program} -> {5 * num_change_over_btw_same_program} mins downtime")
            summary_text_list.append(f"---- Between same program: {num_change_over_btw_same_program} -> {CHANGEOVER_DOWNTIME_SAME_PROGRAM * num_change_over_btw_same_program} mins downtime")
            
            total_changeover_downtime = CHANGEOVER_DOWNTIME_DIFFERENT_PROGRAM * num_change_over_btw_dfft_program + CHANGEOVER_DOWNTIME_SAME_PROGRAM * num_change_over_btw_same_program
            # print(f"----> Total {total_changeover_downtime} mins downtime")
            summary_text_list.append(f"----> Total {total_changeover_downtime} mins downtime")
            
            production_deduction = math.ceil(total_changeover_downtime * uph / 60)
            # print(f"----> UPH: {uph} -> {total_changeover_downtime} mins: {production_deduction} production availability deduction")
            summary_text_list.append(f"----> UPH: {uph} -> {total_changeover_downtime} mins: {production_deduction} production availability deduction")
            # print(f"----> {current_date_full_available} - {production_deduction} =  {current_date_full_available - production_deduction} production available")
            summary_text_list.append(f"----> {current_date_full_available} - {production_deduction} =  {current_date_full_available - production_deduction} production available")
            # print(f"-- Production plan sum: {production_plan_sum}")
            summary_text_list.append(f"-- Production plan sum: {production_plan_sum}")
            
            # print("\n")
            summary_text_list.append("\n")
    
    return summary_text_list   
# %%
