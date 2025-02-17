from flask import Flask, render_template, request, send_file, session
from pandas.errors import EmptyDataError

from analysis import categorizer, filer
from setting import SESSION_LIMIT_TIME

app = Flask(__name__, static_folder="static")
app.secret_key = 'secretkey'
app.config['PERMANENT_SESSION_LIFETIME'] = SESSION_LIMIT_TIME

# Top page
@app.route("/")
def top_page():
    filer.rmdirs()
    return render_template("top.html")


# Updates page
@app.route("/updates")
def updates_page():
    return render_template("updates.html")


# Installations page
@app.route("/instructions")
def instructions_page():
    return render_template("instructions.html")


# Data upload page
@app.route("/upload")
def uploads_page():
    filer.mkdirs()
    return render_template("data_upload.html")


# Data visualizetion page
@app.route("/visualization", methods=["POST"])
def visualization():
    try:
        files = filer.save_files(request.files.getlist("data_csv"), "DATA")
        session["files"] = files
        # create data format from the file
        data, errors = filer.data_format(files)
        session['attrs'] = filer.get_min_attr(data)
        if len(set(session["attrs"].values())) == 1:
            action_route = "/parameter_input"
        else:
            action_route = "/parameter_upload"

        # display figure of each file at html
        filer.save_figures(data)
        session['figures'] = filer.fig_list(files)
        print(f"session: {session}")

        return render_template(
            "visualization.html",
            figures=session.get("figures", {}),
            errors=errors,
            action_route=action_route
        )
    except (FileNotFoundError, IsADirectoryError):
        return render_template(
            "data_upload.html",
            msg="You must upload one or more csvfile data."
        )
    except EmptyDataError:
        return render_template(
            "data_upload.html",
            msg="Empty data files have been detected."
        )
    except (KeyError, TypeError, UnicodeDecodeError):
        return render_template(
            "data_upload.html",
            msg="Upload valid analysis data."
        )
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return render_template(
            "data_upload.html",
            msg=f"Error detected.: {str(e)}"
        )


# Input parameters page for only
@app.route("/parameter_input", methods=["GET", "POST"])
def input_params():
    session["form_tag"] = "input"
    if request.form.getlist("file_name"):
        session["files"] = request.form.getlist("file_name")
    if len(set(session["attrs"].values())) == 1:
        attr = list(set(session["attrs"].values()))[0]
    else:
        attr = 60
    return render_template(
        "params_input.html",
        files=session.get("files", []),
        interval=attr
    )


# Input parameters page for csv format
@app.route("/parameter_upload", methods=["GET", "POST"])
def input_csv():
    session["form_tag"] = "upload"
    if request.form.getlist("file_name"):
        session["files"] = request.form.getlist("file_name")
    return render_template("params_upload.html", files=session.get("files", []))

# Preview parameters page
@app.route("/parameter_upload/preview", methods=["POST"])
def preview_params():
    files = session.get("files", [])
    params = filer.save_files(request.files.getlist("params_csv"), "PARAMS")
    headers, tables = filer.preview_params(params[0], session["attrs"])
    if isinstance(tables, list):
        return render_template(
            "params_upload.html",
            files=files,
            table=tables,
            header=headers
        )
    else:
        return render_template(
            "params_upload.html",
            files=files,
            msg=tables
        )


# Analyze data page
@app.route("/analyze", methods=["POST"])
def analysis():
    files = session.get("files", [])
    data, _ = filer.data_format(files)
    session["folder_name"], folder_path = filer.create_unique_dir(
        request.form.get("folder_name")
    )
    try:
        if request.form.getlist("param"):
            parameters_dict = filer.pick_up_parameter(
                files,
                request.form.getlist("param")
            )
        else:
            parameters_dict = filer.read_parameters()
        event_set, div_set = {}, {}
        for file in files:
            if file in parameters_dict.keys():
                peaks = categorizer.analyze(parameters_dict[file], data[file])
                filer.save_artifacts(folder_path, file, peaks)
                div_set |= filer.plot_coloring_events(
                    file,
                    folder_path,
                    data[file],
                    peaks
                )
                event_set |= {file: filer.output(peaks)}
        return render_template("analysis.html", divs=div_set, summary=event_set)
    except (AttributeError, TypeError):
        import traceback
        print(traceback.format_exc())
        return render_template(
            f"params_{session['form_tag']}.html",
            files=files,
            msg="Select a valid parameter file."
        )
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return render_template(
            f"params_{session['form_tag']}.html",
            files=files,
            msg=f"Error detected.: {str(e)}"
        )


@app.route("/downloads", methods=["GET", "POST"])
@app.route("/downloads/<path:file_name>", methods=["GET", "POST"])
def download_artifacts(file_name=None):
    zip_file = filer.download_zip(session.get('folder_name', ''), file_name)
    return send_file(zip_file, as_attachment=True)


@app.route("/delete", methods=["POST"])
def reset_directory():
    filer.rmdirs()
    session.clear()
    return render_template("top.html")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
