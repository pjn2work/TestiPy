import pandas as pd

from testipy.lib_modules import textdecor
from testipy.configs import enums_data

pd.options.display.float_format = "{:,.3f}".format
pd.options.display.max_columns = None
pd.options.display.width = 220


def _get_state_dummies(df, columns=("Package", "Suite", "Test", "Level")):
    df_dummies = df.copy()

    # get dummies for States
    df_dummies = pd.get_dummies(df_dummies, columns=["State"], prefix="", prefix_sep="")

    # assure all states
    dict_states = dict()
    for state in enums_data.SEVERITY_STATES_ORDER:
        if state not in df_dummies.columns:
            df_dummies[state] = 0
        dict_states[state] = "sum"

    # aggregate mode
    aggregate = {"T#": "size", "Steps": "sum", "Duration": "sum", "Start time": "min", "End time": "max"}  # , "Reason": "unique"
    aggregate.update(dict_states)

    # group by tests
    df_dummies = df_dummies.groupby(columns).agg(aggregate).rename(columns={"T#": "Total"}, inplace=False)

    # calc Passed percentage
    df_dummies["%PASS"] = df_dummies[enums_data.STATE_PASSED] / df_dummies["Total"]
    df_dummies["%PASS"] = round(df_dummies["%PASS"] * 100.0, 2)
    df_dummies["Duration"] = round(df_dummies["Duration"], 3)
    df_dummies["E"] = df_dummies["%PASS"].apply(textdecor.get_emoji)

    # sort df
    df_dummies = df_dummies.reset_index().sort_values(by=["Start time"], ascending=True)

    return df_dummies


def _get_state_summary(df, columns=("Package", "Suite", "Test", "Level", "State", "Usecase", "Reason")):
    df_ss = df.copy()

    # group by Reason of State
    df_ss = df_ss.groupby(columns).agg({"T#": "size", "Steps": "sum", "Duration": "sum", "Start time": "min", "End time": "max"}).rename(columns={"T#": "Total"}, inplace=False)

    # calc percentage of each row
    df_ss["%"] = df_ss["Total"] / df_ss["Total"].sum()
    df_ss["%"] = round(df_ss["%"] * 100.0, 2)
    df_ss["Duration"] = round(df_ss["Duration"], 3)

    # sort df
    df_ss = df_ss.reset_index().sort_values(by=["Start time"], ascending=True)

    return df_ss


def reduce_datetime(df, endwith=":%S"):
    for column in df.select_dtypes(include='datetime64').columns:
        df[column] = df[column].dt.strftime(f"%Y-%m-%d %H:%M{endwith}")
    return df


# -----------------------------------------------------------------------------------------------------
"""
                                                        Total  Duration          Start time            End time  PASSED  FAILED  SKIPPED  %PASSED
Package Suite         Test                                                                                                                                     
demo    suite_demo_01 test_01_show_internal_counters        2      0.20 2020-02-05 14:51:34 2020-02-05 14:51:34       2       0        0   100.00
                      test_02_division_by_zero              2      0.00 2020-02-05 14:51:34 2020-02-05 14:51:34       1       1        0    50.00
"""


def get_test_dummies(df):
    return _get_state_dummies(df, columns=["Package", "Suite", "Test", "Level"]) #, "TAGs"


def get_suite_dummies(df):
    return _get_state_dummies(df, columns=["Package", "Suite", "Level"])


def get_package_dummies(df):
    return _get_state_dummies(df, columns=["Package", "Level"])


# -----------------------------------------------------------------------------------------------------
"""
Package    Suite        Test           Prio    Level  State    Usecase       Reason          Total   Steps    Duration  Start time               %
---------  -----------  -----------  ------  -------  -------  ------------  ------------  -------  ------  ----------  -------------------  -----
qa.team01  suiteDemo01  GetClients       50        1  PASSED   before login  received 401        1       0       0.271  2020-06-19 15:14:20  33.33
qa.team01  suiteDemo01  Login            40        1  PASSED                 received 200        1       0       0.201  2020-06-19 15:14:20  33.33
qa.team01  suiteDemo01  GetClients       30        1  PASSED   after login   received 200        1       0       0.191  2020-06-19 15:14:20  33.33
"""


def get_test_ros_summary(df):
    return _get_state_summary(df, ["Package", "Suite", "Test", "Prio", "Level", "State", "Usecase", "Reason"])


# -----------------------------------------------------------------------------------------------------
"""
                              Total  Duration          Start time            End time
Package Suite         State                                                                        
demo    suite_demo_01 FAILED      2  0.901410 2020-02-05 14:14:22 2020-02-05 14:14:23
                      PASSED      7  0.202453 2020-02-05 14:14:22 2020-02-05 14:14:23
"""


def get_suite_state_summary(df):
    return _get_state_summary(df, ["Package", "Suite", "Level", "State"])


def get_package_state_summary(df):
    return _get_state_summary(df, ["Package", "Level", "State"])


def get_levels_state_summary(df):
    return _get_state_summary(df, ["Level", "State"])


def get_state_summary(df):
    return _get_state_summary(df, ["State"])

# -----------------------------------------------------------------------------------------------------
