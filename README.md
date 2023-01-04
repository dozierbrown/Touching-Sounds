# Touching-Sounds
This Repository Holds the Source Code and Paper of an Application built for the Touching Sounds Project. This Software Sonifies Praat Formant Data and Allows Users to Aubibly Interpret Spectrogram Information.

## Paper and Presentations
* Current draft of paper is listed above as [Touching_Sounds_Background.pdf](https://github.com/dozierbrown/Touching-Sounds/blob/main/Touching_Sounds_Background.pdf)
* Touching Sounds Interactive Exhibit initially presented in the Frank Melville Jr. Library's Central Reading Room at SUNY Stony Brook University in Spring 2022

## Authors
* Brian Dozier Brown<sup>1</sup>

<sup>1</sup>: Department of Music, Stony Brook University.

## Declaration
A significant portion of this application's functionality was conceptualized by Dr. Margaret Schedel and Nikhil Vohra. I would like to acknowledge their contributions to the sonification project in addition Dr. Marie Huffman, Dr. Ellen Broselow, Alex Yeung, Heather Weston, Samantha Bravo, and Namyoung Um. 

## Instructions for Use

* Download the associated code package and move it to your desired location. For instance,
```
~/pathtodirectory/Touching-Sounds
```
Once downloaded, run it in a Python Environment. Alternatively, the `.py` file will run on its own.

* Whenever you run the program, a dialogue box should open requesting an input file. Please input a short sound file for the application to process. Once the audio is processed, a screen with a spectrogram will be produced. 

* Here are the current controls for exploring the spectrogram and its formant.

* Press "b" for SNR sound output of intensity at the cursor.

* Press "up arrow" to go to next formant up

* Press "down arrow" to go to next formant below

* Press "left arrow" to trace along formant to the left

* Press "right arrow" to trace along formant to the right

* Press "i" for speech output of current intensity value

* Press "v" for speech output of current formant 

* Press "p" for speech output of current time and frequency

* Press "s" to save current figure as a PNG
