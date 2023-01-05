import parselmouth, os

import math
from math import log10, floor
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

import json
from json import JSONEncoder
from parselmouth.praat import call

import tkinter as tk
from tkinter import filedialog

#Prompt User for File Upload
file_path = filedialog.askopenfilename()

#Create Sound Object from Audio File
snd = parselmouth.Sound(file_path)

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

#Create copy of sound file, and pre-emphasize copied fragment
pre_emphasized_snd = snd.copy()
pre_emphasized_snd.pre_emphasize()

#Create Spectrogram Object from Pre-Emphasized Sound
spectrogram = pre_emphasized_snd.to_spectrogram(window_length=0.005, maximum_frequency=6000)

#Create np.array for intensity Value
intensity_values = np.zeros((formant.nt, 5))

#Function for Rounding Sig Figs
def round_sig(x, sig=2):
    return round(x, sig-int(floor(log10(abs(x))))-1)

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
#Scale values from low to high
scaled_intensity_values = np.interp(intensity_values, (intensity_values.min(), intensity_values.max()), (+30, 0))
#Flip scaled values from high to low
op_scaled_intensity_values = np.interp(intensity_values, (intensity_values.min(), intensity_values.max()), (40, +70))

#Number of Time Steps
num_times = np.zeros((formant.nt, 1))
for x in range (formant.nt):
    num_times[x] = ((x*2)/formant.nt) - 1

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

#Set Frequency
frequency = 5000
#Set type of waveform
type = "sine"
#Set Amplitude
volume = 0.05
#Set duration
duration = 100
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
    specData = {"newArray": time_formant_values}
    print("serialize NumPy array into JSON and write into a file")
    with open("specData.json", "w") as write_file:
        json.dump(specData, write_file, cls=NumpyArrayEncoder)
    print("Done writing serialized NumPy array into file")

    #Set-up Path Variables
    path = "/Users/brianbrown"
    targetPath = "/Users/brianbrown/Documents/Processing/ModeOne"

    source = "specData.json"
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
