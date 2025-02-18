import pandas as pd
import numpy as np


def _data_set(params: dict) -> dict:
    """
    Receives a list containing the model's parameter set, performs type conversions 
    (such as converting to datetime format), and returns the processed parameters 
    as a dictionary.

    Args:
        params (dict): The list containing the model's parameter set.
    Returns:
        dict: The parameters formatted as a dictionary.
    """
    prehib_start_time = np.datetime64(params["prehib_start_time"], "s")
    if pd.isna(params["hib_end_time"]):
        hib_end_time = None
    else:
        hib_end_time = np.datetime64(params["hib_end_time"], "s")

    if pd.isna(params["exclusion_start_time"]) or pd.isna(params["exclusion_end_time"]):
        exclusion_start_time, exclusion_end_time = None, None
    else:
        exclusion_start_time = np.datetime64(params["exclusion_start_time"], "s")
        exclusion_end_time = np.datetime64(params["exclusion_end_time"], "s")

    return {
        "id": str(params["ID"]),
        "group": str(params["group"]),
        "prehib_start_time": prehib_start_time,
        "hib_end_time": hib_end_time,
        "hib_start_tmp": np.float32(params["hib_start_tmp"]),
        "upper_threshold": np.float32(params["upper_threshold"]),
        "lower_threshold": np.float32(params["lower_threshold"]),
        "prehib_low_Tb_threshold": np.float32(params["prehib_low_Tb_threshold"]),
        "hib_start_discrimination": np.int32(params["hib_start_discrimination"]),
        "hib_end_discrimination": np.int32(params["hib_end_discrimination"]),
        "dead_discrimination": np.int32(params["dead_discrimination"]),
        "pa_discrimination": np.int32(params["pa_discrimination"]),
        "exclusion_start_time": exclusion_start_time,
        "exclusion_end_time": exclusion_end_time,
    }


def _structured() -> dict:
    """
    Initializes a dictionary for storing analysis results in the required format.

    Returns:
        dict: The initialized dictionary.
    """
    return {
        "interval": {},
        "status": "",
        "tmp": {
            "prehib": {},
            "hib_start": "",
            "hib_end": "",
            "PA": {},
            "ST": {},
            "DT": {},
            "Arousal Pending": {},
            "Cooling": {},
            "Rewarming": {},
            "posthib": {},
            "low_Tb": {},
        },
        "time": {
            "prehib": {},
            "hib_start": "",
            "hib_end": "",
            "PA": {},
            "ST": {},
            "DT": {},
            "Arousal Pending": {},
            "Cooling": {},
            "Rewarming": {},
            "posthib": {},
            "low_Tb": {},
        },
    }


def _get_start_time(time: list, prehib_start_time: np.datetime64) -> np.datetime64:
    """
    Receives time data and parameters, returning the hibernation start time.

    Args:
        time (list): The time data.
        params (dict): The parameters.
    Returns:
        numpy.datetime64: The hibernation start time.
    """
    for i in range(len(time)):
        if time[i] > prehib_start_time:
            if i == 0:
                return time[i]
            return time[i - 1]
    else:
        raise ValueError("Not found start time.")


def _get_end_time(time: list, hib_end_time: np.datetime64) -> np.datetime64:
    """
    Receives time data and parameters, returning the hibernation end time.

    Args:
        time (list): The time data.
        params (dict): The parameters.
    Returns:
        numpy.datetime64: The hibernation end time.
    """
    for i in range(len(time) - 1, 1, -1):
        if time[i] <= hib_end_time:
            return time[i]
    else:
        raise ValueError("Not found end time.")

def _modify_discrimination_to_interval(interval: int, params: dict) -> dict:
    """
    Modifies the discrimination parameter to the interval specified in the input 
    dictionary.
    Args:
        interval (int): The time interval.
        params (dict): The input dictionary containing the discrimination parameter.
    Returns:
        dict: The modified dictionary.
    """
    for name, val in params.items():
        if "discrimination" in name:
            params[name] = np.int32(val / interval)
    return params

def _is_hib_start(tmp: list, current_index: int, params: dict) -> bool:
    """
    Receives temperature data, the current index, time interval, and parameters, 
    returning a boolean value indicating whether the hibernation start condition
    is met.

    Args:
        tmp (list): The temperature data.
        current_index (int): The current index.
        params (dict): The parameters.
    Returns:
        bool: True if the hibernation start condition is met, False otherwise.
    """
    for i in range(1, params["hib_start_discrimination"] + 1):
        if tmp[current_index + i] < params["upper_threshold"] <= params[
            "hib_start_tmp"
        ] or (
            params["upper_threshold"] > params["hib_start_tmp"]
            and tmp[current_index + i] < params["hib_start_tmp"]
        ):
            continue
        else:
            return False
    return True


def _is_hib_end(
        tmp: list, 
        current_index: int,
        interval: int, 
        params: dict) -> bool:
    """
    Receives temperature data, the current index, time interval, and parameters, 
    returning a boolean value indicating whether the hibernation end condition is met.
    
    Args:
        tmp (list): The temperature data.
        current_index (int): The current index.
        interval (int): The time interval.
        params (dict): The parameters.
    Returns:
        bool: True if the hibernation end condition is met, False otherwise.
    """
    # end_point_index = interval * 24 * params["hib_end_discrimination"]
    end_point_index = params["hib_end_discrimination"]
    index = (
        end_point_index
        if len(tmp) > current_index + end_point_index
        else len(tmp) - current_index
    )
    count = 0
    for i in range(index):
        if count != interval:
            if (
                params["lower_threshold"]
                <= tmp[current_index + i]
                < params["upper_threshold"]
            ):
                count += 1
            else:
                count = 0
        else:
            return False
    return True


def _is_dead(tmp: list, current_index: int,params: dict) -> bool:
    """
    Receives temperature data, the current index, time interval, and parameters,
    returning a boolean value indicating whether the death condition is met. 
    
    Args:
        tmp (list): The temperature data.
        current_index (int): The current index.
        params (dict): The parameters.
    Returns:
        bool: True if the death condition is met, False otherwise.
    """
    # dead_point_index = interval * 24 * params["dead_discrimination"]
    dead_point_index = params["dead_discrimination"]
    index = (
        dead_point_index
        if len(tmp) > current_index + dead_point_index
        else len(tmp) - current_index
    )
    for i in range(index):
        if params["lower_threshold"] <= tmp[current_index + i]:
            return False
    return True


def _is_hib_stop(
        tmp: list, 
        current_index: int,
        params: dict) -> bool:
    """
    Receives temperature data, the current index, and parameters,
    returning a boolean value indicating whether the datalogger removal condition
    is met.

    Args:
        tmp (list): The temperature data.
        current_index (int): The current index.
        params (dict): The parameters.
    Returns:
        bool: True if the datalogger removal condition is met, False otherwise.
    """
    for i in range(1, len(tmp) - current_index):
        if (
            params["lower_threshold"] > tmp[current_index + i]
            or tmp[current_index + i] >= params["upper_threshold"]
        ):
            return False
    return True


def _get_interval(time: list) -> dict:
    """
    Calculates the time interval between data points (e.g., the time difference 
    between the first and second data points).

    Args:
        time (list): The time data.
    Returns:
        dict:  dictionary containing the time interval in various formats (seconds, 
        minutes, and a string representation).
    """
    interval = str(time[1] - time[0])
    seconds = int(interval.replace(" seconds", ""))
    minutes = int(seconds / 60)
    return {"seconds": seconds, "minutes": minutes, "with_seconds": interval}


def _get_dead_index(tmp: list, time: list, current_index: int, interval: int) -> int:
    """
    Calculates the index in the data where the death condition is determined
    to have occurred.

    Args:
        tmp (list): The temperature data.
        time (list): The time data.
        current_index (int): The current index.
        interval (int): The interval for dead descrimination.
    Returns:
        int: The index of the data point where death is determined to have occurred.
    """
    dead_tmp = None
    for i in range(interval):
        # 期間内で微妙な体温変動が発生し、目的の値より後ろの値が取得される可能性があるため小数点第一位を四捨五入した値にする
        target_tmp = round(tmp[current_index + i], 1)
        if dead_tmp is None or dead_tmp > target_tmp:
            dead_idx = i
    return dead_idx


def _append_proc(
        event_name: str,
        results: dict,
        process_tmp: list,
        process_time: list) -> None:
    """
    Appends processed temperature and time data to the results dictionary
    under the specified event name.

    Args:
        event_name (str): The name of the event (e.g., 'PA', 'ST', 'DT').
        results (dict): The dictionary storing the analysis results.
        process_tmp (list): The list of processed temperature data.
        process_time (list): The list of processed time data.
    """
    if None in process_tmp or None in process_time:
        return None
    elif 1 in results["tmp"][event_name]:
        event_num = next(iter(reversed(results["tmp"][event_name].keys()))) + 1
    else:
        event_num = 1

    results["tmp"][event_name][event_num] = process_tmp
    results["time"][event_name][event_num] = process_time


def _peak_counts(tmp: list, time: list, params: dict) -> dict:
    """
    Detects changes in hibernation status and analyzes the duration of each status.

    Args:
        tmp (list): The temperature data.
        time (list): The time data.
        params (dict): The parameters.
    Returns:
        dict: The dictionary storing the analysis results.
    """
    results = _structured()
    interval = _get_interval(time)
    params = _modify_discrimination_to_interval(interval["minutes"], params)
    results |= {
        "interval": interval,
        "ID": params["id"],
        "group": params["group"],
    }

    # For Non-Hibernation 
    if np.all(tmp > params["hib_start_tmp"]):
        _append_proc("prehib", results, tmp, time)
        results["status"] = "unhiber"
        return results

    params["prehib_start_time"] = _get_start_time(time, params["prehib_start_time"])
    for i in range(len(time)):
        if time[i] == params["prehib_start_time"]:
            tmp = tmp[i:]
            time = time[i:]
            break
    exclusion_flag = None not in [
        params["exclusion_start_time"],
        params["exclusion_end_time"],
    ]
    if params["hib_end_time"] is not None:
        params["hib_end_time"] = _get_end_time(time, params["hib_end_time"])

    previous_tmp, process_tmp, process_time = None, [], []
    for i in range(len(tmp)):
        if exclusion_flag and params["exclusion_start_time"] <= time[i]:
            if time[i] <= params["exclusion_end_time"]:
                process_tmp.append(np.nan)
                process_time.append(np.nan)
                continue
            else:
                exclusion_flag = False
                pass
        elif i == 0:
            process_tmp.append(tmp[i])
            process_time.append(time[i])
            continue
        elif params["hib_end_time"] == time[i]:
            results["tmp"]["hib_end"] = tmp[i]
            results["time"]["hib_end"] = time[i]
            break
        # For Post-Hibernation
        elif results["time"]["hib_end"] != "":
            for posthib_i in range(interval["minutes"] * 24 * 7):
                process_tmp.append(tmp[i + posthib_i])
                process_time.append(time[i + posthib_i])
                _append_proc("posthib", results, process_tmp, process_time)
            break
        # For Pre-Hibernation
        elif results["time"]["hib_start"] == "":
            process_tmp.append(tmp[i])
            process_time.append(time[i])

            # Check whether the hibernation beginning is accurate
            if _is_hib_start(tmp, i, params):
                results["tmp"]["hib_start"] = tmp[i + 1]
                results["time"]["hib_start"] = time[i + 1]
                if params["hib_start_tmp"] < params["upper_threshold"]:
                    for re_i in range(i, 1, -1):
                        if tmp[re_i] > params["upper_threshold"]:
                            previous_tmp = tmp[re_i]
                            break
                else:
                    previous_tmp = tmp[i]
                _append_proc("prehib", results, process_tmp, process_time)
                process_tmp, process_time = [], []
        elif (
            results["time"]["hib_start"] != ""
            and params["lower_threshold"] <= tmp[i] < params["upper_threshold"]
        ):
            if results["time"]["hib_end"] == "" and (
                params["lower_threshold"] > tmp[i - 1]
                or params["upper_threshold"] <= tmp[i - 1]
            ):
                # Check whether the data logger has been taken out
                if _is_hib_stop(tmp, i, params):
                    results["tmp"]["hib_end"] = tmp[i - 1]
                    results["time"]["hib_end"] = time[i - 1]
                    results["status"] = "dissection"
                    break
            process_tmp.append(tmp[i])
            process_time.append(time[i])
        elif tmp[i] < params["lower_threshold"]:
            # Check whether dead
            if results["time"]["hib_end"] == "" and _is_dead(tmp, i, params):
                dead_idx = _get_dead_index(tmp, time, i, params["dead_discrimination"])

                results["tmp"]["hib_end"] = tmp[i - 1]
                results["time"]["hib_end"] = time[i - 1]

                process_tmp += list(tmp[i : i + dead_idx])
                process_time += list(time[i : i + dead_idx])
                _append_proc("DT", results, process_tmp, process_time)
                process_tmp, process_time = [], []
                results["status"] = "dead"
                break
            # For Cooling
            elif previous_tmp >= params["upper_threshold"]:
                _append_proc("Cooling", results, process_tmp, process_time)
                process_tmp, process_time = [], []
                previous_tmp = tmp[i - 1]
            # For Arousal Pending
            elif previous_tmp < params["lower_threshold"]:
                _append_proc("Arousal Pending", results, process_tmp, process_time)
                process_tmp, process_time = [], []
                previous_tmp = tmp[i - 1]

            process_tmp.append(tmp[i])
            process_time.append(time[i])
            # For Deep torpor
            if tmp[i + 1] >= params["lower_threshold"]:
                _append_proc("DT", results, process_tmp, process_time)
                process_tmp, process_time = [], []
                previous_tmp = tmp[i]
        elif results["time"]["hib_start"] != "" and tmp[i] >= params["upper_threshold"]:
            # For Shallow Torpor
            if previous_tmp >= params["upper_threshold"]:
                _append_proc("ST", results, process_tmp, process_time)
                process_tmp, process_time = [], []
                previous_tmp = tmp[i - 1]
            # For Rewarming
            elif previous_tmp < params["lower_threshold"]:
                _append_proc("Rewarming", results, process_tmp, process_time)
                process_tmp, process_time = [], []
                previous_tmp = tmp[i - 1]
            # Check wether the hibernation is over
            if results["time"]["hib_end"] == "" and _is_hib_end(
                tmp, i, interval["minutes"], params
            ):
                results["tmp"]["hib_end"] = tmp[i - 1]
                results["time"]["hib_end"] = time[i - 1]
                results["status"] = "refractory"
                continue

            process_tmp.append(tmp[i])
            process_time.append(time[i])

            # For Periodic Arousal
            if tmp[i + 1] < params["upper_threshold"]:
                _append_proc("PA", results, process_tmp, process_time)
                process_tmp, process_time = [], []
                previous_tmp = tmp[i]
    return results


def modify_pa(results: dict, pa_discrimination: int) -> dict:
    """
    Modifies the PA (Periodic Arousal) events to ensure accurate classification.
    It addresses the issue where temporary ST (Shallow Torpor) events are incorrectly
    mixed with PA events occurring during the normal temperature state.

    Args:
        results (dict): The dictionary storing the analysis results.
        pa_discrimination (int): 
    Returns:
        dict: The dictionary storing the analysis results.
    """
    interval = results["interval"]["minutes"]

    temp_pa_time, temp_pa_tmp = [], []
    for pa_time, pa_tmp in zip(
        results["time"]["PA"].values(), results["tmp"]["PA"].values()
    ):
        for st_num, st_time in results["time"]["ST"].items():
            if len(st_time) < int(pa_discrimination / interval):
                if st_time[0] - pa_time[-1] == np.timedelta64(interval, "m"):
                    temp_pa_tmp.append(pa_tmp + results["tmp"]["ST"][st_num])
                    temp_pa_time.append(pa_time + st_time)
                    del results["tmp"]["ST"][st_num]
                    del results["time"]["ST"][st_num]
                    break
        else:
            temp_pa_tmp.append(pa_tmp)
            temp_pa_time.append(pa_time)

    merge_pa_time, merge_pa_tmp = [], []
    for pa_time, pa_tmp in zip(temp_pa_time, temp_pa_tmp):
        if len(merge_pa_time) == 0:
            merge_pa_tmp.append(pa_tmp)
            merge_pa_time.append(pa_time)
        elif merge_pa_time[-1][-1] + np.timedelta64(interval, "m") == pa_time[0]:
            merge_pa_tmp[-1].extend(pa_tmp)
            merge_pa_time[-1].extend(pa_time)
        else:
            merge_pa_tmp.append(pa_tmp)
            merge_pa_time.append(pa_time)

    results["tmp"]["PA"] = {i + 1: pa for i, pa in enumerate(merge_pa_tmp)}
    results["time"]["PA"] = {i + 1: pa for i, pa in enumerate(merge_pa_time)}
    results["tmp"]["ST"] = {
        i + 1: st for i, st in enumerate(results["tmp"]["ST"].values())
    }
    results["time"]["ST"] = {
        i + 1: st for i, st in enumerate(results["time"]["ST"].values())
    }
    return results


def get_low_tb_events(results: dict, prehib_low_Tb_threshold: int) -> dict:
    """
    Extracts events where the body temperature falls below a predefined threshold
    during the pre-hibernation period.

    Args:
        results (dict): The dictionary storing the analysis results.
        prehib_low_Tb_threshold (int): The parameters.
    Returns:
        dict: The dictionary storing the analysis results.
    """
    process_tmp, process_time = [], []
    tmp = results["tmp"]["prehib"][1]
    time = results["time"]["prehib"][1]
    for i in range(len(tmp) - 1):
        if tmp[i] < prehib_low_Tb_threshold:
            process_tmp.append(tmp[i])
            process_time.append(time[i])
            # For a single data
            if (
                tmp[i - 1] >= prehib_low_Tb_threshold
                and tmp[i + 1] >= prehib_low_Tb_threshold
            ):
                _append_proc("low_Tb", results, process_tmp, process_time)
                process_tmp, process_time = [], []
            # For muptiple data
            elif tmp[i + 1] >= prehib_low_Tb_threshold:
                _append_proc("low_Tb", results, process_tmp, process_time)
                process_tmp, process_time = [], []
    return results


def analyze(param_list: list, data: pd.DataFrame) -> dict:
    """
    The main function that performs the analysis.
    It preprocesses the data, analyzes the hibernation status,
    and modifies the results.

    Args:
        param_list (list): The list containing the model's parameter set.
        data (pandas.DataFrame): The input data containing temperature
        and time information.
    Returns:
        dict: The dictionary storing the analysis results.
    """
    tmp = data["Value"].values
    time = data["Date/Time"].values
    params = _data_set(param_list)
    res = _peak_counts(tmp, time, params)
    res = modify_pa(res, params["pa_discrimination"])
    if res["tmp"]["prehib"] and res["tmp"]["prehib"]:
        res = get_low_tb_events(res, params["prehib_low_Tb_threshold"])
    return res
