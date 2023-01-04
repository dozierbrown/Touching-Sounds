import parselmouth, sys, os, shutil, platform, struct, logging, threading, time

import multiprocessing as mp
import math
from math import log10, floor
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

import json
from json import JSONEncoder
from parselmouth.praat import call

from PIL import Image
import pyttsx3

from gtts import gTTS
from io import BytesIO
import pyaudio
from pydub import AudioSegment
from pydub.generators import Sine, WhiteNoise
from pydub.playback import play
import tkinter as tk
from tkinter import filedialog

start = time.perf_counter()

sns.set() # Use seaborn's default style to make attractive graphs

#Plot nice figures using Python's "standard" matplotlib library
#Prompt User for File Input

file_path = filedialog.askopenfilename()
#Create Sound Object from Audio File
snd = parselmouth.Sound(file_path)
#snd = parselmouth.Sound("//Users/brianbrown/Documents/Tactile Spectrograms/Audio files of exhibit spectrograms/13_lonely_starbucks.wav")

#Extract Formant Object from Parent Sound Object
formant = snd.to_formant_burg()

#Get formant times
t = [formant.frame_number_to_time(x) for x in range(1, formant.nt+1)]

#Create np array for time values
time_values = np.zeros((formant.nt, 1))
#Assign time values to np array
for x in range(formant.nt):
    time_values[x] = t[x]

#Create np array for formant values
formant_values = np.zeros((formant.nt, 5))
#Assign formant values into np array
for x in range(formant.nt):
    for y in range(5):
        formant_values[x, y] = formant.get_value_at_time(formant_number = (y+1), time = t[x])

#Concatenate time values with formant
time_formant_values = np.concatenate((time_values, formant_values), axis=1)

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
    global t, time_values, formant_values, time_formant_values

    #Plot Formant Values
    plt.plot(formant.xs(), formant_values, 'd', markersize = 2, color = 'w')
    plt.plot(formant.xs(), formant_values, 'd', markersize = 1)
    plt.grid(False)
    plt.ylim(0, 6000)

#Dump JSON File Function
def dump_JSON():
    global t, time_values, formant_values, time_formant_values

    #Set up numpy encoder
    class NumpyArrayEncoder(JSONEncoder):
        def default(self,obj):
            if isinstance(obj,np.ndarray):
                return obj.tolist()
            return JSONEncoder.default(self,obj)

    #Serialize time_formant_values numpy array into JSON
    numpyData = {"newArray": time_formant_values}
    print("serialize NumPy array into JSON and write into a file")
    with open("numpyData.json", "w") as write_file:
        json.dump(numpyData, write_file, cls=NumpyArrayEncoder)
    print("Done writing serialized NumPy array into file")

    #Set-up Path Variables
    path = "/Users/brianbrown"
    targetPath = "/Users/brianbrown/Documents/Processing/ModeOne"

    source = "numpyData.json"
    destination = "/Documents/Processing/ModeOne/data"

    sourcePath = path + "/" + source
    destinationPath = path + "/" + destination

    #Check if file already exists in destination folder
    if os.path.isdir(destinationPath + "/" + source) :
        print(source, "exists in the destination path!")
        shutil.rmtree(destinationPath + "/" + source)

    elif os.path.isfile(destinationPath + "/" + source) :
        os.remove(destinationPath + "/" + source)
        print(source, "deleted in", destination)

#Function for Rounding Sig Figs
def round_sig(x, sig=2):
    return round(x, sig-int(floor(log10(abs(x))))-1)

#Create copy of sound file, and pre-emphasize copied fragment
pre_emphasized_snd = snd.copy()
pre_emphasized_snd.pre_emphasize()
#Create Spectrogram Object from Pre-Emphasized Sound
spectrogram = pre_emphasized_snd.to_spectrogram(window_length=0.005, maximum_frequency=6000)

#Create np.array for intensity Value
intensity_values = np.zeros((formant.nt, 5))
#Create Temp Formant Values
temp_formant_values = formant_values
for i in range(formant.nt):
    for j in range(5):
        if math.isnan(temp_formant_values[i, j]) == True:
            temp_formant_values[i, j] = 1
        else:
            temp_formant_values[i, j] = round_sig(temp_formant_values[i, j], sig=4)
#Assign intensity values into np array
for x in range(formant.nt):
    for y in range(5):
        intensity_values[x, y] = spectrogram.get_power_at(time = t[x], frequency = temp_formant_values[x, y])
#low, high
scaled_intensity_values = np.interp(intensity_values, (intensity_values.min(), intensity_values.max()), (+30, 0))
#high, low
op_scaled_intensity_values = np.interp(intensity_values, (intensity_values.min(), intensity_values.max()), (40, +70))

num_times = np.zeros((formant.nt, 1))
for x in range (formant.nt):
    num_times[x] = ((x*2)/formant.nt) - 1

engine = pyttsx3.init()

#Set ax as current ax
ax = plt.gca()
#Set fig as current fig
fig = plt.gcf()
#Create Variable To Navigate Formant Number, and Variable for Tracing index
formant_level = 0
index = 0
#Arrange data into a line of values according to formant_level
line, = ax.plot(time_values, formant_values[:, formant_level], 'none')

#Set audio sample rate
sample_rate = 44100

#frequency
frequency = 5000
#freq = formant_values[index, formant_level]

type = "sine"

volume = 0.05

duration = 100

#Class for Blitted Cursor and Keyboard Commands
class BlittedCursor:
    """
    A cross hair cursor using blitting for faster redraw.
    """
    def __init__(self, ax, line):
        self.ax = ax
        self.background = None
        self.horizontal_line = ax.axhline(color='k', lw=0.8, ls='--')
        self.vertical_line = ax.axvline(color='k', lw=0.8, ls='--')
        self.x, self.y = line.get_data()
        self._last_index = None
        # text location in figure coordinates
        self.text = ax.text(0.6, 1.03, '', transform=ax.transAxes)
        self._creating_background = False
        ax.figure.canvas.mpl_connect('draw_event', self.on_draw)

    #Save Matplotlib figure as image
    def on_draw(self, event):
        self.create_new_background()

    #Function to draw crosshairs
    def set_cross_hair_visible(self, visible):
        need_redraw = self.horizontal_line.get_visible() != visible
        self.horizontal_line.set_visible(visible)
        self.vertical_line.set_visible(visible)
        self.text.set_visible(visible)
        return need_redraw

    #Function to create background
    def create_new_background(self):
        if self._creating_background:
            # discard calls triggered from within this function
            return
        self._creating_background = True
        self.set_cross_hair_visible(False)
        self.ax.figure.canvas.draw()
        self.background = self.ax.figure.canvas.copy_from_bbox(self.ax.bbox)
        self.set_cross_hair_visible(True)
        self._creating_background = False

    #Updates mouse position
    def update_mouse(self):
        x = self.x[index]
        y = self.y[index]
        self.horizontal_line.set_ydata(y)
        self.vertical_line.set_xdata(x)
        self.text.set_text('time = %1.2f, frequency = %1.2f' % (x, y))

        self.ax.figure.canvas.draw()
        self.ax.figure.canvas.restore_region(self.background)
        self.ax.draw_artist(self.horizontal_line)
        self.ax.draw_artist(self.vertical_line)
        self.ax.draw_artist(self.text)
        self.ax.figure.canvas.blit(self.ax.bbox)

    #Function detecting mouse events
    def on_mouse_move(self, event):
        if self.background is None:
            self.create_new_background()
        if not event.inaxes:
            self._last_index = None
            need_redraw = self.set_cross_hair_visible(False)
            if need_redraw:
                self.ax.figure.canvas.draw()
                self.ax.figure.canvas.restore_region(self.background)
                self.ax.figure.canvas.blit(self.ax.bbox)
        else:
            self.set_cross_hair_visible(True)
            # update the line positions
            global index
            x, y = event.xdata, event.ydata
            index = min(np.searchsorted(self.x, x), len(self.x) - 1)
            if index == self._last_index:
                return  # still on the same data point. Nothing to do.
            self._last_index = index
            self.update_mouse()

    def speech_output(self,tts):
        fp = BytesIO()
        #Write text to file-like object
        tts.write_to_fp(fp)
        fp.seek(0)
        #Load and play audio file
        song = AudioSegment.from_file(fp, format="mp3")
        play(song)

    #Navigation and Input Controls
    def on_press(self, event):
        global line, formant_level, index, intensity_values, frequency, scaled_intensity_values, op_scaled_intensity_values, max_time, num_times, engine
        #print('press', event.key)
        sys.stdout.flush()
        #Increase formant by 1
        if event.key == 'up':
            if formant_level < 4:
                formant_level += 1
                frequency = formant_values[index, formant_level]
                line, = ax.plot(time_values, formant_values[:, formant_level], 'none')
                self.x, self.y = line.get_data()
                self.update_mouse()
            else:
                formant_level = 4
        #Decrease formant by 1
        elif event.key == 'down':
            if formant_level > 0:
                formant_level -= 1
                frequency = formant_values[index, formant_level]
                line, = ax.plot(time_values, formant_values[:, formant_level], 'none')
                self.x, self.y = line.get_data()
                self.update_mouse()
            else:
                formant_level = 0
        #Move to the right along traced formant
        elif event.key == 'right':
            index += 1
            frequency = int(formant_values[index, formant_level])
            self.update_mouse()
            #print(frequency)
        #Move to the left along traced formant
        elif event.key == 'left':
            index -= 1
            frequency = int(formant_values[index, formant_level])
            self.update_mouse()
            #print(frequency)
        #Save figure as a .png
        elif event.key == 's':
            plt.savefig('Figure.png')
        #Print & verbalize current time and frequency data
        elif event.key == 'i':
            temp_i = intensity_values[index, formant_level]
            temp_i = round_sig(temp_i, sig=4)
            text = f'Intensity is {temp_i} Pascals'
            tts = gTTS(text=f'Intensity is {temp_i} Pascals', lang='en')
            self.speech_output(tts)
        #Verbalize current formant
        elif event.key == 'v':
            tts = gTTS(text=f'This formant is F {formant_level}', lang='en')
            self.speech_output(tts)
        #Verbalize current time and frequency
        elif event.key == 'p':
            #Check for NaN and round data to sig fig
            if math.isnan(self.x[index]) == True:
                temp_x = "Not a Number"
            else:
                temp_x = round_sig(self.x[index], sig=3)
            if math.isnan(self.y[index]) == True:
                temp_y = "Not a Number"
            else:
                temp_y = round_sig(self.y[index], sig=4)
            #Google Translate Text to Speech
            tts = gTTS(text=f'Time is {temp_x} seconds, Frequency is {temp_y} Hertz', lang='en')
            self.speech_output(tts)
        elif event.key == 'b':
            frequency = int(formant_values[index, formant_level])
            temp_i = scaled_intensity_values[index, formant_level]
            temp_u = op_scaled_intensity_values[index,formant_level]
            tone1 = Sine(frequency).to_audio_segment(duration=100) - temp_i
            tone2 = WhiteNoise().to_audio_segment(duration=100) - temp_u
            combined = tone1.overlay(tone2)
            time_combined = combined.pan(num_times[index])
            play(time_combined)

#Plot Figure
def plot():
    #Instantiate and Draw Blitted Cursor
    blitted_cursor = BlittedCursor(ax, line)
    #Detect keypressed events
    fig.canvas.mpl_connect('key_press_event', blitted_cursor.on_press)
    #Detect mousemovement events
    fig.canvas.mpl_connect('motion_notify_event', blitted_cursor.on_mouse_move)

    draw_spectrogram(spectrogram)
    plt.twinx()
    draw_formant(formant)
    dump_JSON()
    plt.xlim([snd.xmin, snd.xmax])
    plt.show()

plot()

finish = time.perf_counter()
print(f'Finished in {round(finish-start, 2)} second(s)')
