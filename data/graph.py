import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('flows_test.csv')


plot_df = df[["timestamp", "flow_duration"]]
lines = plot_df.plot.line()
plt.show()