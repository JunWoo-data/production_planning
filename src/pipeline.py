# %%
from D_production_plan import *


# %%
# TODO: Change full production availability if needed
# target_date = "2023-09-15"
# full_available_changed = 0
# #df_daily_full_available.loc[df_daily_full_available.date == target_date, "full_available"] = full_available_changed
# df_daily_full_available.loc[df_daily_full_available.date == target_date, "full_available"] = df_daily_full_available.loc[df_daily_full_available.date == target_date, "full_available"] / 2
# df_daily_full_available

# %%
##############################
### Line 2 production plan ###
##############################

Line2_production_summary = Line2_production_plan()

# %%
Line2_production_plan_summary(Line2_production_summary)

# %%
##############################
### Line 3 production plan ###
##############################

Line3_production_summary = Line3_production_plan()

# %%
Line3_production_plan_summary(Line3_production_summary)


# %%
