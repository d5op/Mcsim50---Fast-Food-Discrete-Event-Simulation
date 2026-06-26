import os
from cs50 import SQL
import mcsim1
import json
import plotly.express as px
import pandas as pd

from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from help import login_required, graph_gen, cal

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///mcsim.db")
db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL, hash TEXT NOT NULL);")
db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users (username);")
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/", methods=["GET", "POST"])
@login_required
def index():

    if request.method == "POST":

        mcsim1.Global_Variables.total_sim_result = []
        mcsim1.Global_Variables.input = {}

        mcsim1.Global_Variables.end_time_list = []
        mcsim1.Global_Variables.log_list = []

        location = request.form.get("location").lower()
        time = request.form.get("time").lower()
        counter = request.form.get("counter").strip()
        staff = request.form.get("staff").strip()
        duration = request.form.get("duration").strip()
        cycle = request.form.get("cycle").strip()

        if not location or not time or not counter or not staff or not duration or not cycle:
            flash("!!!Missing Important Field/s!!!", "danger")
            return redirect("/")
        try:
            counter = int(counter)
            staff = int(staff)
            duration = int(duration)
            cycle = int(cycle)
        except:
            flash("!!!All Fields Must Be Positive Integers!!!", "danger")
            return redirect("/")

        if counter < 1 or staff < 1 or duration < 1 or cycle < 1:
            flash("!!!All Fields Must Be Greater Than 0!!!", "danger")
            return redirect("/")
        if duration < 60:
            flash("!!!Duration Must Be Greater Than 60Min!!!", "danger")
            return redirect("/")
        mcsim1.Global_Variables.ask_input(location, time, counter, staff, duration, cycle)


        return redirect("/gen")
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if not request.form.get("username"):
            flash("!!!Must Provide Username!!!", "danger")
            return redirect("/login")
        if not request.form.get("password"):
            flash("!!!Must Provide Password!!!", "danger")
            return redirect("/login")
    
        rows = db.execute(
                "SELECT * FROM users WHERE username = ?", request.form.get("username")
            )
        if len(rows) != 1 or not check_password_hash(
                rows[0]["hash"], request.form.get("password")
            ):
                flash("!!!Invalid Username And/Or Password!!!", "danger")
                return redirect("/login")
        session["user_id"] = rows[0]["id"]
        flash("---Log in Sucessfully---", "primary")
        return redirect("/")

    else:
        return render_template("login.html")
    
@app.route("/logout")
def logout():
    """Log user out"""

    session.clear()

    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        re_password = request.form.get("confirm")
        if not username:
            flash("!!!Missing Username!!!", "danger")
            return redirect("/register")
        if not password:
            flash("!!!Missing Password!!!", "danger")
            return redirect("/register")
        if password != re_password:
            flash("!!!Passsword Must Match!!!", "danger")
            return redirect("/register")
        
        hashed = generate_password_hash(password)

        try:
            db.execute("INSERT INTO users (username, hash) VALUEs (?,?)", username, hashed)
        except:
            flash("!!!Username Already Exist!!!")
            return redirect("/register")
        flash("---Account created sucessfully---", "primary")
        return redirect("/")
    else:
        return render_template("register.html")
@app.route("/gen", methods=["GET", "POST"])
def gen():
    if request.method == "POST":
        button = request.form.get("button")
        if button == "log":
            return redirect("/log")
        if button == "save":
            user_id = session["user_id"]
            input_dic = json.dumps(mcsim1.Global_Variables.input)
            result_dic = json.dumps(mcsim1.Global_Variables.total_sim_result)
            time = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
            avg_exceed_time = sum(mcsim1.Global_Variables.end_time_list) / len(mcsim1.Global_Variables.end_time_list)

            db.execute("INSERT INTO sim (user_id, inputs, waiting, time, t_exceed) VALUES (?,?,?,?,?)", user_id, input_dic, result_dic, time, avg_exceed_time)
            return redirect("/gen")
    else:
        if len(mcsim1.Global_Variables.input) < 1:
            flash("!!!Must Generate Result First!!!", "danger")
            return redirect("/")
        cycle = mcsim1.Global_Variables.input["cycle"]
        for i in range(cycle):
            #!!!This check is smart and important, it prevent rerunning either from reloading or redireting into this page
            if len(mcsim1.Global_Variables.total_sim_result) < cycle:
                test = mcsim1.Mcdonald_Sim()
                mcsim1.Global_Variables.log_list.append(f"Run{i+1}:")
                test.run()

        avg_exceed_time = sum(mcsim1.Global_Variables.end_time_list) / len(mcsim1.Global_Variables.end_time_list)
        
        count_list, serve_list, leave_list, avg_waittime, all_waits = cal(mcsim1.Global_Variables.total_sim_result)

        graph_his, graph_pie, graph_line, graph_sca, graph_left, graph_live = graph_gen(all_waits, serve_list, leave_list,
                                                                                         mcsim1.Global_Variables.total_sim_result)

        return render_template("gen.html", cycle_time = cycle, count_list=count_list, serve_list=serve_list, leave_list=leave_list,
                                avg_waittime=avg_waittime, avg_exceed_time=avg_exceed_time, graph_his=graph_his,
                                graph_pie=graph_pie, graph_line=graph_line, graph_sca=graph_sca, graph_left=graph_left
                                , graph_live=graph_live, input=mcsim1.Global_Variables.input, zip=zip)  


@app.route("/log")
def log():
    return render_template("log.html", log_list=mcsim1.Global_Variables.log_list)

@app.route("/save", methods=["POST", "GET"])
def save():
    cur_user = session["user_id"]
    
    if request.method == "POST":
            id = int(request.form.get("button"))
            session["d_id"] = id
            return redirect("/graph") 
    else:
        all_inputs = []
        data = db.execute("SELECT time, inputs, id FROM sim WHERE user_id = ?", cur_user)
        for row in data:
            input_dict = json.loads(row["inputs"])
            all_inputs.append({
                "id": row["id"],
                "time": row["time"],
                "input": input_dict
            })
        return render_template("save.html", all_inputs=all_inputs)  
    
@app.route("/graph")
def graph():
    id = session.get("d_id")

    row = db.execute("SELECT inputs, waiting, t_exceed FROM sim WHERE id = ?", id)[0]

    wait_list_dict = json.loads(row['waiting'])
    input_list = json.loads(row['inputs'])
    cycle = input_list["cycle"]

    count_list, serve_list, leave_list, avg_waittime, all_waits = cal(wait_list_dict)
    avg_exceed_time = row['t_exceed']
    graph_his, graph_pie, graph_line, graph_sca, graph_left, graph_live = graph_gen(all_waits, serve_list, leave_list,
                                                                                    wait_list_dict)
    
    return render_template("graph.html", cycle_time = cycle, count_list=count_list, serve_list=serve_list, leave_list=leave_list,
                        avg_waittime=avg_waittime, avg_exceed_time=avg_exceed_time, graph_his=graph_his,
                        graph_pie=graph_pie, graph_line=graph_line, graph_sca=graph_sca, graph_left=graph_left
                        , graph_live=graph_live, input=input_list, zip=zip)

@app.route("/video")
def video():
    return render_template("video.html")