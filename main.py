import parselmouth, time

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

import json
from parselmouth.praat import call

from dataManagement import *
from cursor import BlittedCursor

#Begin Counter
start = time.perf_counter()

# Use seaborn's default style to make attractive graphs
sns.set()

#Draw Spectrogram Function
def draw_spectrogram(spectrogram, dynamic_range=70):
    X, Y = spectrogram.x_grid(), spectrogram.y_grid()
    sg_db = 10 * np.log10(spectrogram.values)
    plt.pcolormesh(X, Y, sg_db, vmin=sg_db.max() - dynamic_range, cmap='binary')
    plt.ylim([spectrogram.ymin, spectrogram.ymax])
    #plt.xlim([spectrogram.xmin, spectrogram.xmax])
    plt.xlabel("Time [s]")
    plt.ylabel("Frequency [Hz]")

#Draw Formant Funtion
def draw_formant(formant):

    #Plot Formant Values
    plt.plot(formant.xs(), formant_values, 'd', markersize = 2, color = 'w')
    plt.plot(formant.xs(), formant_values, 'd', markersize = 1)
    plt.grid(False)
    plt.ylim(0, 6000)

#Plot Figure
def plot():
    #Instantiate and Draw Blitted Cursor
    blitted_cursor = BlittedCursor(ax, line)
    #Detect keypressed events
    fig.canvas.mpl_connect('key_press_event', blitted_cursor.on_press)
    #Detect mousemovement events
    fig.canvas.mpl_connect('motion_notify_event', blitted_cursor.on_mouse_move)
    #Draw Spectrogram with Current Data
    draw_spectrogram(spectrogram)
    plt.twinx()
    #Draw Formants with Current Data
    draw_formant(formant)
    #Dump Formant Data into JSON File
    dump_JSON()
    #Set Boundaries of X-Axis
    plt.xlim([snd.xmin, snd.xmax])
    #Show Plot
    plt.show()

plot()

#End Counter when Program Closes
finish = time.perf_counter()
print(f'Finished in {round(finish-start, 2)} second(s)')
