from flask import Flask,render_template

app = Flask(__name__)
@app.route("/")
def hello():
    name = "Anuj sharma"
    return render_template('index.html',name2 = name)
@app.route("/about")
def Anuj():
    name = 'Anuj sharma'
    li1 = ["anuj", "sharma", 22]
    return render_template("about.html",name=name,li = li1)

app.run(debug=True)