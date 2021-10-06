import csv
from matplotlib import pyplot as p


def read_csv(filename):
    """
    Reads .csv file to list.

    Args:
        filename (str): Do not include .csv extension
    Returns:
        data (list): Nested list, with headers in first row
    """
    with open("data/" + filename + ".csv", "r") as f:
        reader = csv.reader(f)
        data = list(reader)
        data = [x for x in data if x != []]
    return data


def plot(data):
    """
    Plots nested list using pyplot

    Args:
        data (list): Nested list, with headings in first row
    """
    headings = data.pop(0)
    plot_data = list()
    for row in range(0, len(data)):
        temp = list()
        for col in range(0, len(data[row])):
            temp.append(float(data[row][col]))
        plot_data.append(temp)
    for row in plot_data:
        p.plot(row)


print(read_csv("bid_data"))
p.subplot(131)
plot(read_csv("bid_data"))

p.subplot(132)
plot(read_csv("diffs_data"))

p.subplot(133)
plot(read_csv("mean_diffs_data"))

p.show()
