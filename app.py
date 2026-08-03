from flask import Flask, render_template
import os

app = Flask(__name__)

@app.route("/")
def inicio():
    return render_template("orden_mantenimiento.html")

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )