import csv

import matplotlib.pyplot as plt
from flask import Flask, Response
import os
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import io
import numpy as np


plt.rcParams['figure.figsize'] = [7.50, 3.50]
plt.rcParams['figure.autolayout'] = True


app = Flask(__name__)


def read_csv(filename):
    """
    Reads .csv file to list.

    Args:
        filename (str): Include .csv extension
    Returns:
        data (list): Nested list, with headers in first row
    """
    with open(f"./outputs/{filename}", "r") as f:
        reader = csv.reader(f)
        data = list(reader)
        data = [x for x in data if x != []]
    return data


def plot(data, axis):
    """
    Plots nested list using pyplot

    Args:
        data (list): Nested list, with headings in first row
    """
    headings = data.pop(0)
    plot_data = list()
    for row in data:
        plot_row = [float(num) for num in row]
        if plot_row.count(0.0) < len(plot_row):
            plot_data.append(plot_row)
    plot_data = np.array(plot_data).T.tolist()
    for row in plot_data:
        axis.plot(row)


@app.route('/make-plot/<filename>')
def plot_png(filename):
    fig = Figure()
    data = read_csv(filename)
    axis = fig.add_subplot(1, 1, 1)
    plot(data, axis)
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')


@app.route("/")
def data():
    body = str()
    for filename in os.listdir("./outputs"):
        body += f"<a href='/get_data_csv/{filename}'>{filename.replace('_', ' ')}</a><br>" \
                f"<a href='/make-plot/{filename}'>{filename.replace('_', ' ')} -- Plot data</a><br><br>"
    body += "<br><br>"
    for filename in os.listdir("./outputs"):
        body += f"<img src='/make-plot/{filename}'>"
    return f'''
        <html><body>
        {body}
        </body></html>
        '''


@app.route("/get_data_csv/<filename>")
def get_data_csv(filename):
    with open(f"outputs/{filename}") as fp:
        csv = fp.read()
    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host = '0.0.0.0', port = port)
