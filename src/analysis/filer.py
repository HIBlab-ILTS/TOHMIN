import csv
import numpy as np
import os
import pandas as pd
import re
import shutil
from typing import Union
import zipfile

import glob
import plotly.graph_objects as go

from setting import DATA_DIR_PATH, PARAMS_DIR_PATH, FIGS_DIR_PATH, ARTIFACTS_DIR_PATH


def mkdirs():
    """
    Creates directories for storing data, parameters, figures,
    and artifacts if they don't exist.
    """
    os.makedirs(DATA_DIR_PATH, exist_ok=True)
    os.makedirs(PARAMS_DIR_PATH, exist_ok=True)
    os.makedirs(FIGS_DIR_PATH, exist_ok=True)
    os.makedirs(ARTIFACTS_DIR_PATH, exist_ok=True)


def rmdirs():
    """
    Removes the directories for data, parameters, and figures, if they exist.
    """
    for dir_path in [DATA_DIR_PATH, PARAMS_DIR_PATH, FIGS_DIR_PATH]:
        try:
            shutil.rmtree(dir_path)
        except FileNotFoundError:
            print(f"already deleted {DATA_DIR_PATH}")


def download_zip(folder_name: str, file_name: str) -> str:
    """
    Creates a zip file containing the analysis results, including CSV files,
    SVG figures, and an HTML report.

    Args:
        folder_name (str): The name of the folder containing the analysis results.
        file_name (str): The name of the zip file to be created.
    Returns:
        str: The path of the created zip file.
    """
    if file_name is not None:
        folder_name = f"{folder_name}/{file_name.replace('.csv', '')}"
    dir_path = os.path.join(os.path.join(ARTIFACTS_DIR_PATH, folder_name))
    with zipfile.ZipFile(f"{dir_path}.zip", "w") as zip_file:
        for file in glob.glob(f"{dir_path}/**", recursive=True):
            if re.search(r"\.(csv|svg|html)$", file):
                zip_file.write(file)
    return f"{dir_path}.zip"


def get_min_attr(data: dict) -> dict:
    """
    Calculates the interval between data points for each CSV file.
    This interval is used minimum attributes of the some parameters.
    
    Args:
        data (dict): The dataframes of each CSV file.
    Returns:
        dict: The dictionary containing the minimum interval (in minutes) for each file.
    """
    attrs = {}
    for file_name, df in data.items():
        interval = df["Date/Time"][1] - df["Date/Time"][0]
        attrs[file_name] = int(interval.total_seconds() // 60)
    return attrs


def get_header_info(file_name: str) -> Union[int, str]:
    """
    Opens the specified CSV file and reads it line by line to determine
    the header index and the type of data logger used (iBottun, nanotag and arco).

    Args:
        file_name (str): The name of the CSV file to be analyzed (including the path
                         if the file is not in the current directory).
    Returns:
        Union[int, str]: The header index or the type of data logger used.
    """
    logger_pattern = {
        "Date/Time,Unit,Value": "iBottun",
        "日時,振動数(積分値),SE,温度(平均値),SE,,": "nanotag",
        # "": "arco",
    }
    with open(file_name) as f:
        newline_count = 0
        for i, line in enumerate(f.readlines()):
            if line == "\n":
                newline_count += 1
            elif (logger_type := logger_pattern.get(line.strip())) is not None:
                return i - newline_count, logger_type


def adjust_year(dt: str) -> str:
    """
    Adjusts the year format in the datetime string
    if it is not in the standard 'YYYY-MM-DD' format.

    Args:
        dt (str): The datetime string to be adjusted.
    Returns:
        str: The adjusted datetime string in the 'YYYY-MM-DD' format.
    """
    year = re.search("[0-9]+", dt)
    if (len(year.group()) == 6 or len(year.group()) <= 2) \
        and int(year.group()[:2]) <= 31:
        dt = "20" + dt
    return dt


def data_format(files: list) -> tuple:
    """
    Reads CSV files, formats data into a DataFrame, and performs basic data cleaning.

    Args:
        files (list): A list of CSV file names to be analyzed (including the path
                      if the file is not in the current directory
    Returns:
        dict: A dictionary where the keys are the file names and the values are
              the corresponding DataFrames after formatting and cleaning.
    Note:
        The row included NaN is deleted, if the data has NaN.
        And the index of start set 0.
    """
    replace_patterns = {
        'nanotag': {"日時": "Date/Time", "温度(平均値)": "Value"}
    }

    data = {}
    errors = {}
    for file in files:
        file_path = os.path.join(DATA_DIR_PATH, file)
        header_index, file_type = get_header_info(file_path)
        try:
            if file_type == 'nanotag':
                df = pd.read_csv(file_path, header=header_index, encoding="Shift-JIS")
                df.rename(columns=replace_patterns[file_type], inplace=True)
                df = df[["Date/Time", "Value"]]
            else:
                df = pd.read_csv(file_path, header=header_index, encoding="Shift-JIS")
            if df.isnull().values.sum() != 0:
                print("DataError: Founded NaN data")
            df["Date/Time"] = df["Date/Time"].apply(adjust_year).astype("datetime64[s]")
            data[file] = df
        except pd.errors.ParserError as e:
            print(f"data_format parse error in {file}: {str(e)}")
            errors[file] = str(e)
        except Exception as e:
            print(f"Other case error in {file}: {str(e)}")
            errors[file] = str(e)
    return data, errors


def data_format_for_arco(file):
    """
    Processes data specifically for the ARCO data logger format, cleaning 
    and converting it into a DataFrame.
    """
    dir_path = os.path.join(os.getcwd(), DATA_DIR_PATH)
    with open(
        os.path.join(dir_path, f"alco_{file.filename}.csv"), "w", newline="\n"
    ) as csvfile:
        w = csv.writer(csvfile)
        f = open(file)
        for line in f.readlines():
            if line.count(",") == 1:
                continue
            elif line.count(",") == 34:
                w.writerow(
                    line.replace('"', "").replace("\n", "").replace("#", "").split(",")
                )
            elif line == "*****MarkComment*****":
                continue
            else:
                raise "new ARCO data pattern: {}".format(line)
    print(f"Successfully!! 'arco_{file.filename}.csv' was created.")
    return pd.read_csv(
        os.path.join(dir_path, f"arco_{file.filename}.csv"), header=0, skiprows=[1]
    )


def convert_datetime(param_dt: str) -> str:
    """
    Convert datetime string to datetime.Timestamp type.

    Args:
        param_dt (str): The date/time string to be converted.
    Returns:
        str: The converted datetime.Timestamp type string.
    """
    try:
        if not isinstance(param_dt, str):
            return float("nan")
        trans_dt = param_dt.replace("/", "-").replace("  ", " ")
        date, time = trans_dt.split(" ")
        # format date string
        if re.search(r"^\d{4}-\d{2}-\d{2}$", date):
            year, month, day = date.split("-")
        elif re.search(r"^\d{8}$", date):
            year = date[:4]
            month = date[4:6]
            day = date[6:]
        elif re.search(r"^(\d+)-(\d+)-(\d+)$", date):
            year, month, day = re.search(r"^(\d+)-(\d+)-(\d+)$", date).groups()
            if len(year) == 2:
                year = f"20{year}" if int(year) < 50 else f"19{year}"
            if len(month) == 1:
                month = f"0{month}"
            if len(day) == 1:
                day = f"0{day}"
        else:
            print(f"new date pattern.: {date}")

        # format time string
        if not re.search(r"^\d{2}:\d{2}$", time):
            h_m = re.search(r"^(\d):(\d)", time)
            if h_m:
                hour = h_m[1] if len(h_m[1]) == 2 else f"0{h_m[1]}"
                minutes = h_m[2] if len(h_m[2]) == 2 else f"0{h_m[2]}"
            else:
                print(f"new time pattern.: {param_dt}")
        else:
            hour, minutes = time.split(":")

        return f"{year}-{month}-{day} {hour}:{minutes}"
    except Exception as e:
        print(e)


def create_unique_dir(unique_name: str) -> Union[str, str]:
    """
    Creates a unique directory for storing analysis results.

    Args:
        unique_name (str): The name of the directory to be created.
    Returns:
        Union[str, str]: The name of the created directory and the directory path.
    """
    with os.scandir(ARTIFACTS_DIR_PATH) as ents:
        names = [ent.name for ent in ents if ent.is_dir()]
    num = 0
    while unique_name in names:
        num += 1
        if f"{unique_name}_{num}" not in names:
            unique_name = f"{unique_name}_{num}"
            break
    # create new directory
    os.makedirs(os.path.join(ARTIFACTS_DIR_PATH, unique_name))
    return unique_name, os.path.join(ARTIFACTS_DIR_PATH, unique_name)


def create_specific_dir(dir_path: str, file_name: str) -> str:
    """
    Creates a specific directory for storing analysis results.

    Args:
        dir_path (str): The path of the directory to be created.
        file_name (str): The name of the file for which the directory is being created.
    Returns:
        str: The path of the created directory.
    """
    dir_path = os.path.join(dir_path, file_name.replace(".csv", ""))
    os.makedirs(dir_path, exist_ok=True)
    csvfile_name_path = os.path.join(dir_path, file_name.replace(".csv", ""))
    os.makedirs(csvfile_name_path, exist_ok=True)
    return csvfile_name_path


def save_artifacts(folder_path: str, file: str, results: dict) -> None:
    """
    Saves the analysis results to two CSV files: one for the processed data
    and one for the analysis summary.

    Args:
        folder_path (str): The path to the directory where the CSV file will be saved.
        file (str): The name of the CSV file to be saved.
        results (dict): The analysis results to be saved.
    """
    id_name = results["ID"]
    group = results["group"]
    dir_path = create_specific_dir(folder_path, file)

    # for delta_data
    with open(
        os.path.join(dir_path, f"hib_analysis_{id_name}.csv"), "w", newline="\n"
    ) as file:
        w = csv.writer(file)
        w.writerow(["Status", results["status"]])
        w.writerow(
            [
                "ID",
                "Event Name",
                "Event Number",
                "First Point of Event",
                "Last Point of Event",
                "Delta Time",
                "Unit",
                "Group",
            ]
        )
        if results["status"] == "unhiber":
            w.writerow(["", "", "", "", "", "", "", ""])
        else:
            for e_name, e_info in results["time"].items():
                if e_name == "hib_start":
                    delta_time = results["time"]["hib_end"] - results["time"][e_name]
                    time, unit = str(delta_time).split(" ")
                    w.writerow(
                        [
                            id_name,
                            "hibernation",
                            "1",
                            results["time"][e_name],
                            results["time"]["hib_end"],
                            time,
                            unit,
                            group,
                        ]
                    )
                elif e_name not in ["hib_end", "posthib"]:
                    for e_num, e_data in e_info.items():
                        delta_time = (
                            e_data[-1] - e_data[0]
                            if len(e_data) != 1
                            else results["interval"]["with_seconds"]
                        )
                        time, unit = str(delta_time).split(" ")
                        if e_name == "prehib":
                            e_name = "pre_hibernation"
                        w.writerow(
                            [
                                id_name,
                                e_name,
                                e_num,
                                e_data[0],
                                e_data[-1],
                                time,
                                unit,
                                group,
                            ]
                        )
    print(f"Successfully. 'hib_analysis_{id_name}.csv' was created.")

    # for process_data
    with open(
        os.path.join(dir_path, f"hib_process_data_{id_name}.csv"), "w", newline="\n"
    ) as file:
        w = csv.writer(file)
        w.writerow(["Status", results["status"]])
        w.writerow(["ID", "Event Name", "Event Number", "Date Time", "Value", "Group"])
        for e_name, e_info in results["time"].items():
            if e_name not in ["hib_start", "hib_end", "prehib", "posthib"]:
                for e_num in e_info.keys():
                    for e_time, e_tmp in zip(
                        results["time"][e_name][e_num], results["tmp"][e_name][e_num]
                    ):
                        w.writerow([id_name, e_name, e_num, e_time, e_tmp, group])
    print(f"Successfully. 'hib_proc_{id_name}.csv' was created.")


def save_files(files: list, target: str) -> list:
    """
    Saves uploaded data and parameter files to local directories.

    Args:
        files (list): A list of uploaded files.
        target (str): The target directory ("DATA" or "PARAMS").
    Returns:
        list: A list of saved filenames.
    """
    dir_tag = DATA_DIR_PATH if target == "DATA" else PARAMS_DIR_PATH
    file_names = []
    for file in files:
        file.save(os.path.join(dir_tag, file.filename))
        file_names.append(file.filename)
    return file_names


def output(results: dict) -> dict:
    """
    Prints a summary of the hibernation analysis results to the console.

    Args:
        results (dict): The analysis results.
    Returns:
        dict: The updated analysis results with the summary.
    """
    display_set = {}
    print("-" * 60)
    for event_name in results["time"].keys():
        if event_name in ["hib_start", "hib_end"]:
            pass
        else:
            print(f"{event_name}:", len(results["time"][f"{event_name}"]))
            display_set |= {event_name: len(results["time"][f"{event_name}"])}
    print("-" * 60)
    # for jinja2
    display_set['AP'] = display_set.pop('Arousal Pending')
    return display_set


def pick_up_parameter(files: list, params: list) -> dict:
    """
    Constructs a dictionary of parameters for each file in the input list.

    Args:
        files (list): A list of file names.
        params (list): A list of parameter values corresponding to the inputed patrameters.
    Returns:
        dict: A dictionary where keys are file names and values are dictionaries of parameters.
    """
    param_set = {
        "ID": params[0],
        "group": params[1],
        "prehib_start_time": params[2],
        "hib_end_time": np.nan if params[3] == '' else params[3],
        "hib_start_tmp": params[6],
        "upper_threshold": params[7],
        "lower_threshold": params[8],
        "prehib_low_Tb_threshold": params[9],
        "hib_start_discrimination": params[10],
        "hib_end_discrimination": params[11],
        "dead_discrimination": params[12],
        "pa_discrimination": params[13],
        "exclusion_start_time": np.nan if params[4] == '' else params[4],
        "exclusion_end_time": np.nan if params[5] == '' else params[5]
    }
    parameters_dict = {}
    for file in files:
        parameters_dict |= {file: param_set}
    return parameters_dict


def read_parameters() -> dict:
    """
    Reads parameters from a CSV file and performs validation checks.
    
    Returns:
        dict: A dictionary containing the parameters.
    """
    dir_path = os.path.join(os.getcwd(), PARAMS_DIR_PATH)
    csvfile = os.listdir(dir_path)[0]
    df = pd.read_csv(os.path.join(dir_path, csvfile), header=0, na_values=np.nan)
    df.dropna(subset=["file_name"], inplace=True)

    # check NaN in essential parameters
    no_nan_columns = [
        "file_name",
        "ID",
        "prehib_start_time",
        "hib_start_tmp",
        "upper_threshold",
        "lower_threshold",
        "hib_start_discrimination",
        "hib_end_discrimination",
        "dead_discrimination",
    ]
    for col in no_nan_columns:
        if df[col].isna().any():
            print(f"NaN contains in {col} column.")

    # check the duplicated parameters
    check_vals = df.to_dict()
    if len(set(check_vals["file_name"].values())) != len(
        check_vals["file_name"].values()
    ):
        raise ValueError("file_name is deplicated.")
    elif len(set(check_vals["ID"].values())) != len(check_vals["ID"].values()):
        raise ValueError("ID is deplicated.")

    df["file_name"] = df["file_name"].apply(lambda nm: f"{nm.replace('.csv', '')}.csv")
    df["prehib_start_time"] = df["prehib_start_time"].apply(convert_datetime)
    df["hib_end_time"] = df["hib_end_time"].apply(convert_datetime)
    df["exclusion_start_time"] = df["exclusion_start_time"].apply(convert_datetime)
    df["exclusion_end_time"] = df["exclusion_end_time"].apply(convert_datetime)

    df = df.set_index("file_name")
    return df.to_dict("index")


def save_figures(data_list: list) -> None:
    """
    Saves figures of the raw temperature data as SVG files.

    Args:
        data_list (list): A list of dictionaries containing raw temperature data.
    """
    for file_name, data in data_list.items():
        fig = go.Figure(
            go.Scatter(
                x=data["Date/Time"],
                y=data["Value"],
                mode="lines"
            )
        )
        fig.update_layout(
            xaxis_title="Datetime",
            xaxis=dict(showgrid=False),
            yaxis_title="body_tmp",
            yaxis=dict(showgrid=False)
        )
        fig.write_image(
            os.path.join(FIGS_DIR_PATH, f"{file_name.replace('.csv', '.svg')}")
        )
        fig.write_image(
            os.path.join(FIGS_DIR_PATH, f"{file_name.replace('.csv', '_full.svg')}")
        )


def fig_list(files: list) -> dict:
    """
    Creates a dictionary of file names and their corresponding SVG figure paths.

    Args:
        files (list): A list of uploaded files.
    Returns:
        dict: A dictionary containing file names as keys
        and SVG figure paths as values.
    """
    fig = {}
    for file in files:
        fig[file] = os.path.join(FIGS_DIR_PATH, f"{file.replace('.csv', '.svg')}")
    return fig

def validate_values(param_df: pd.DataFrame, headers: set, attr: dict) -> None:
    """
    Pick up essential parameters from the uploaded CSV file.

    Args:
        param (list): A list of essential parameters from the CSV file.
    Raises:
        ValueError: If essential parameters are empty.
    """
    # if essential parameter was empty
    non_required = {
        'group',
        'hib_end_time',
        'exclusion_start_time',
        'exclusion_end_time'
    }
    check_cols = headers.difference(non_required)
    for col in check_cols:
        if param_df[col].isnull().values.any():
            raise ValueError(f"{col} has one and more empty.")
    
    # check validate
    param_df["file_name"] = param_df["file_name"].apply(
        lambda nm: f"{nm.replace('.csv', '')}.csv"
    )
    for name, min in attr.items():
        check_df = param_df[param_df["file_name"] == name]
        if check_df.empty:
            raise ValueError(f"Not found parameter in {name}.")
        # check tempurature column
        for col in ['hib_start_tmp', 'upper_threshold', 'lower_threshold']:
            if not -10 <= int(check_df[col].iloc[0]) <= 50:
                raise ValueError(f"Out of range {col} value in {name}.")
        value = int(check_df['prehib_low_Tb_threshold'].iloc[0])
        if not int(check_df['hib_start_tmp'].iloc[0]) <= value <= 50:
            raise ValueError(f"Out of range prehib_low_Tb_threshold value in {name}.")
        # check discrimination column
        for col, max in [
            ('hib_start_discrimination', 7200),
            ('hib_end_discrimination', 43200),
            ('dead_discrimination', 43200),
            ('pa_discrimination', 360)
        ]:
            if not min <= int(check_df[col].iloc[0]) <= max:
                raise ValueError(f"Out of range {col} value in {name}.")


def preview_params(file_name: str, attrs: dict) -> tuple:
    """
    Reads and validates parameters from a CSV file for previewing.

    Args:
        file_name (str): The filename of the CSV file.
    Returns:
        tuple: Two lists containing the previewed parameters.
    """
    headers = {
        'file_name',
        'ID',
        'group',
        'prehib_start_time',
        'hib_end_time',
        'hib_start_tmp',
        'upper_threshold',
        'lower_threshold',
        'prehib_low_Tb_threshold',
        'hib_start_discrimination',
        'hib_end_discrimination',
        'dead_discrimination',
        'pa_discrimination',
        'exclusion_start_time',
        'exclusion_end_time'
    }
    try:
        tb = pd.read_csv(
            os.path.join(PARAMS_DIR_PATH, file_name), header=0
        )
        # check format
        if set(tb.columns) != headers:
            raise ValueError("The format of parameters is wrong.")
        validate_values(tb, headers, attrs)
        return tb.columns.tolist(), tb.values.tolist()
    except ValueError as e:
        print(e)
        return ValueError(str(e))
    except Exception as e:
        print(e)
        return 'Please upload the accurate data again'


def color_code() -> dict:
    """
    Defines color codes for different hibernation events.

    Returns:
        dict: A dictionary containing event names as keys
        and corresponding color codes as values.
    """
    return {
        "ST": "khaki",
        "Rewarming": "lightcoral",
        "PA": "lightblue",
        "Cooling": "darkgreen",
        "Arousal Pending": "blue",
        "DT": "purple",
        "low_Tb": "lightgreen",
    }


def plot_coloring_events(
        file_name: str,
        folder_path: str,
        df: pd.DataFrame,
        peaks: dict) -> dict:
    """
    Generates a graph with color-coded hibernation events and saves it
    as an SVG and HTML file.

    Args:
        file_name (str): The filename of the CSV file.
        folder_path (str): The path to the folder where the files will be saved.
        df (pd.DataFrame): A DataFrame containing the raw temperature data.
        peaks (dict): A dictionary containing peak temperatures and times.
    Returns:
        dict: A dictionary containing the HTML file paths.
    """
    dir_path = os.path.join(folder_path, file_name.replace(".csv", ""))
    fig = go.Figure(
        go.Scatter(
            x=df["Date/Time"],
            y=df["Value"],
            mode="lines",
            line=dict(color="grey"),
            showlegend=False,
        )
    )

    for event_name, color in color_code().items():
        event_tmp = peaks["tmp"][event_name].values()
        event_time = peaks["time"][event_name].values()
        for tmp, time in zip(event_tmp, event_time):
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=tmp,
                    mode="lines",
                    line=dict(color=color),
                    showlegend=False,
                )
            )
    fig.update_layout(xaxis_title="Datetime", yaxis_title="body_tmp")

    fig.write_image(
        os.path.join(dir_path, f"{file_name.replace('.csv', '.svg')}"),
        format="svg",
        engine="kaleido",
    )
    # need to connect the internet for using interactive data on browser
    fig.write_html(
        os.path.join(dir_path, f"{file_name.replace('.csv', '.html')}"),
        full_html=False,
        include_plotlyjs="cdn",
    )
    return {file_name: fig.to_html(full_html=False, include_plotlyjs="cdn")}
