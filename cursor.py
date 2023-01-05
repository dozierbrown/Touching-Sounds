import sys

import math
from math import log10, floor
import numpy as np
import matplotlib.pyplot as plt

from gtts import gTTS
from io import BytesIO
from pydub import AudioSegment
from pydub.generators import Sine, WhiteNoise
from pydub.playback import play

from dataManagement import *
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
            #engine.say(text)
            #engine.runAndWait()
            #engine.stop()
            tts = gTTS(text=f'Intensity is {temp_i} Pascals', lang='en')
            self.speech_output(tts)
        elif event.key == 'v':
            tts = gTTS(text=f'This formant is F {formant_level}', lang='en')
            self.speech_output(tts)
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
            #Print values
            #print(f'{temp_x}, {temp_y}')
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
