import tkinter as tk
from tkinter import ttk
from tkinter import *
from PIL import ImageTk, Image
from tkinter import messagebox as mb
from tkinter.font import BOLD, Font

import os
import argparse
import cv2
import numpy as np
import sys
import glob
import importlib.util
from time import sleep
from picamera import PiCamera
from threading import Thread
import SERIAL

# Global Vars
LARGEFONT = ("Segoe UI", 15)
SMALLFONT = ("Segoe UI", 10)
APP = ""
CONTAINER = ""
PAGE = 0
SERIAL = ""

TIMELABEL1 = None
TIMELABEL2 = None
TIMELABEL2 = None

TIMER = None

CONTROLLER = None

CLASSES = []
SCORES = []
IMAGENO = 1

# Define and parse input arguments
parser = argparse.ArgumentParser()
parser.add_argument('--modeldir', help='Folder the .tflite file is located in',
                    required=True)
parser.add_argument('--graph', help='Name of the .tflite file, if different than detect.tflite',
                    default='model4_fpnlite_grayscale.tflite')
parser.add_argument('--labels', help='Name of the labelmap file, if different than labelmap.txt',
                    default='labelmap.txt')
parser.add_argument('--threshold', help='Minimum confidence threshold for displaying detected objects',
                    default=0.3)
parser.add_argument('--image', help='Name of the single image to perform detection on. To run detection on multiple images, use --imagedir',
                    default=None)
parser.add_argument('--imagedir', help='Name of the folder containing images to perform detection on. Folder must contain only images.',
                    default=None)
parser.add_argument('--edgetpu', help='Use Coral Edge TPU Accelerator to speed up detection',
                    action='store_true')
parser.add_argument('--grayscale', help='Using GrayScale Image',
                    action='store_true')
parser.add_argument('--dev', help='Set dev/ttyACM',
                    action=None)



args = parser.parse_args()

MODEL_NAME = args.modeldir
GRAPH_NAME = args.graph
LABELMAP_NAME = args.labels
min_conf_threshold = float(args.threshold)
use_TPU = args.edgetpu
use_GRAYSCALE = args.grayscale
TTYACM_PORT = args.dev



# Parse input image name and directory. 
IM_NAME = args.image
IM_DIR = args.imagedir

# If both an image AND a folder are specified, throw an error
if (IM_NAME and IM_DIR):
    print('Error! Please only use the --image argument or the --imagedir argument, not both. Issue "python TFLite_detection_image.py -h" for help.')
    sys.exit()

# If neither an image or a folder are specified, default to using 'test1.jpg' for image name
#if (not IM_NAME and not IM_DIR):
#    IM_NAME = 'test1.jpg'

class SSCleaner(tk.Tk):
    # Init function for SSCleaner
    def __init__(self, *args, **kwargs):
        global CONTAINER
        global TIMER

        # Init function for Tk
        tk.Tk.__init__(self, *args, **kwargs)

        # Set application title and window size
        self.title('Smart Syringe Cleaner')
        self.geometry('800x480')
        self.attributes('-fullscreen', True)

        # Option to quit the program
        self.bind("<Escape>", quit)

        # Create container
        CONTAINER = tk.Frame(self)
        CONTAINER.pack(side="top", fill="both", expand=True)

        CONTAINER.grid_rowconfigure(0, weight=1)
        CONTAINER.grid_columnconfigure(0, weight=1)

        TIMER = Timer()

        # Initialize frames to empty array
        self.frames = {}
        # self.shared_data = pd.DataFrame([])

        # Iterate through tuple consisting of the different page layouts
        for F in (mainPage, washingPage, dryPage, sterilisingPage, collectionPage):

            frame = F(CONTAINER, self)
            frame.config(background='white')
            # Initialize frame of object from mainPage and resultPage respectively
            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(mainPage)

    # Show current frame passed as parameter
    def show_frame(self, cont, arg=None):

        frame = self.frames[cont]
        frame.tkraise()

        if PAGE == 0 or PAGE == 4:
            pass
        else:
            cont.start()

    # Pass details of the page to another page
    def get_page(self, page_class):
        return self.frames[page_class]
    
    # Close application
    def quit(self):
	    self.destroy()

# Style Config


def resizedButtonImage(img):
    resized_image = img.resize((100, 100), Image.ANTIALIAS)
    return resized_image

    # Style Config

# Function config


def nextFrame(controller, steps, currentClass):
    # 0 = mainPage
    # 1 = washingPage
    # 2 = dryPage
    # 3 = sterilisingPage
    # 4 = collectionPage
    indexPage = {0: mainPage, 1: washingPage,
                 2: dryPage, 3: sterilisingPage, 4: collectionPage}

    global CONTAINER
    global APP
    global PAGE

    if steps is None or steps == 4:
        PAGE = 0
    else:
        PAGE = steps + 1

    nextPage = indexPage[PAGE]

    # Refresh result page to show updated table
    APP.frames[currentClass].destroy()
    APP.frames[currentClass] = currentClass(CONTAINER, APP)
    APP.frames[currentClass].config(background='white')
    APP.frames[currentClass].grid(row=0, column=0, sticky="nsew")
    APP.frames[currentClass].tkraise()
   
    SERIAL.write(b"stop\n")
    controller.show_frame(nextPage)


def popup_window(controller, steps, page):
    if mb.askyesno('Exit', 'Are you sure?'):
        TIMER.reset()
        nextFrame(controller, steps, page)
    else:
        pass

class Timer():
    def __init__(self):
        # Configure the timer under the reset function
        self.timer = 20
        self.action = False
        self.steps = 0

    def setlabel(self, label, currentClass):
        self.label = label
        self.currentClass = currentClass

    def countdown(self):
        # global #SERIAL
        # Initial is false
        if self.action == True:
            if self.timer < 0:
                # self.#SERIAL.stop
                nextFrame(CONTROLLER, PAGE, self.currentClass)
            else:
                seconds = self.timer % (24 * 3600)
                hour = seconds // 3600
                seconds %= 3600
                minutes = seconds // 60
                seconds %= 60
                
                # Checks if this is the drying page and trigger this check every 20 seconds
                if PAGE == 2 and self.timer % 20 == 0 and self.timer != 0:
                    #Edit this to get humility to activate camera
                    Thread(target=startCamera).start()

                    # Init all the classes total
                    dry = 0
                    wet = 0
                    moist = 0

                    # Check if classes and scores are not empty, mostly for the first run of this code
                    if len(CLASSES) != 0 and len(SCORES) != 0:
                        print(CLASSES)
                        print(SCORES)

                        # Iterate all classes in the list
                        for index, obj in enumerate(CLASSES):
                            #Check class score and see if it is accurate enough for us to use
                            if SCORES[index] > 0.5:
                                # Check class and add it to the class total
                                # 0 and 1 for dry syringe and plunger
                                if obj == 0 or obj == 1:
                                    dry += 1
                                # 2 and 3 for wet syringe and plunger
                                elif obj == 2 or obj == 3:
                                    wet += 1
                                # 4 and 5 for moist syringe and plunger
                                elif obj == 4 or obj == 5:
                                    moist += 1

                    
                    #Outside the loop, check total of each class and see which one highest
                    #If wet and timer running out, add more time
                    #If moist and timer too high, can reduce time
                    #If moist and not enough time, can add time
                    #If dry, can stop in like 5 or 10 seconds
                    print("dry: " + str(dry))
                    print("wet: " + str(wet))
                    print("moist: " + str(moist))

                    # Add 60 sec if timer below 20
                    if (wet > 0 or moist > 0) and self.timer <= 21:
                        self.timer = 60 + 1 # This +1 is to counter the -1 later in the code

                    # Reduce anything more than 10 mins to 5 mins if moist already
                    if moist >= 2 and self.timer >= 600:
                        self.timer = 300 + 1

                    # Anything dry then can move on to next phase, must be lower than 20 sec
                    # So that countdown will not take another photo
                    if dry >= 4:
                        self.timer = 15 + 1
            

                    #ALL TIME CHANGES WILL TAKE EFFECT ON THE NEXT CALL OF COUNTDOWN()


                self.label.configure(text="%d:%02d:%02d" %
                                     (hour, minutes, seconds))

                self.timer = self.timer - 1
                self.label.after(1000, self.countdown)

    def start_resume(self, steps):
        global PAGE
        if PAGE == steps:
            # When the action start
            if self.action == False:
                self.action = True
                self.steps = steps
                self.countdown()

                if self.steps == 1:
                    SERIAL.write(b"wash\n")
                elif self.steps == 2:
                    SERIAL.write(b"dry\n")
                    print("Dry")
                elif self.steps == 3:
                    SERIAL.write(b"ster\n")
     
                print("resume")
               
            # If click again it will resume
            else:
                self.action = False
                self.SERIAL.stop
                SERIAL.write(b"stop\n")
                print("pause")

    def reset(self):
        global SERIAL
        #self.timer = 3
        self.timer = 50
        self.action = False
        SERIAL.write(b"stop\n")


# Frame for the main page


class mainPage(tk.Frame):
    def __init__(self, parent, controller, attr=None):
        tk.Frame.__init__(self, parent)

        # Initializing the label type
        style = ttk.Style()
        style.configure("BW.TLabel", foreground="black", background="white")
        
        self.controller = controller
        self.grid_columnconfigure(1, weight=1)

        self.steps = 0

        # Creating Font, with a "size of 25" and weight of BOLD
        self.bold25 = Font(self, size=25, weight=BOLD)
        self.normalfont = Font(self, size=16)

        # Row 0 - Title
        label = ttk.Label(self, text="Smart Syringe Cleaner",
                          font=self.bold25, borderwidth=0, background="white")

        label.grid(row=0, column=1, padx=10, pady=10)

        # Row 1
        syringeImgPath = Image.open("Photos/syringe_start.png")
        resizeSyringeImg = syringeImgPath.resize((150, 150), Image.ANTIALIAS)
        syringeImg = ImageTk.PhotoImage(resizeSyringeImg)

        syringeImgLabel = ttk.Label(self, image=syringeImg)
        syringeImgLabel.image = syringeImg

        syringeImgLabel.grid(row=1, column=1, padx=10, pady=20)

        # Row 2 -  Button to start the machine
        label_sub = ttk.Label(self, text="Please place your syringe to start cleaning",
                              font=self.normalfont, borderwidth=0, background="white")

        label_sub.grid(row=2, column=1, padx=10, pady=20)
        # Row 3 -  Button to start the machine
        button = tk.Button(self, text="Start",  bg='#2196F3',
                           fg='white', padx=10, pady=20, font=self.normalfont, width=30,
                           command=lambda: nextFrame(self.controller, self.steps, mainPage))

        button.grid(row=3, column=1, padx=10, pady=20)


class washingPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        global TIMELABEL1
        global CONTROLLER

        self.steps = 1

        # Set the controller to global
        CONTROLLER = controller
        self.controller = controller

        # Creating Font, with a "size of 25" and weight of BOLD
        self.bold25 = Font(self, size=25, weight=BOLD)
        self.bold20 = Font(self, size=20, weight=BOLD)
        self.normalfont = Font(self, size=18)

        # self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.f1 = tk.Frame(self)

        # Row 0
        progressbar1Path = Image.open("Photos/ProgressBar1.png")
        progressbar1Img = ImageTk.PhotoImage(progressbar1Path)

        label = ttk.Label(self, image=progressbar1Img)
        label.image = progressbar1Img
        label.grid(row=0, column=1, padx=10, pady=10)

        # Label
        usecaseLabel = ttk.Label(
            self, text="Cleaning in progress...", font=self.bold20, style="BW.TLabel")
        usecaseLabel.grid(row=1, column=1, padx=10, pady=10)

        # Set the time label
        timelabel = ttk.Label(
            self, text="", font=self.normalfont, style="BW.TLabel")
        timelabel.grid(row=2, column=1, padx=10, pady=10)

        TIMELABEL1 = timelabel

        # Row 10 - Button to return to main page
        self.f1.grid(row=3, column=1, padx=10, pady=50)

        # Configure the different button
        # Intialize button state is resume
        self.buttonState = False
        self.buttonResumeStop = tk.Button(self.f1, text="Resume/Pause",
                                          command=lambda: self.buttonPauseStop())

        buttonResumePath = Image.open("Photos/button/play.png")
        buttonResumeImg = ImageTk.PhotoImage(
            resizedButtonImage(buttonResumePath))

        self.buttonResumeStop.config(image=buttonResumeImg, padx=20, pady=20)
        self.buttonResumeStop.padx = 20
        self.buttonResumeStop.pady = 20
        self.buttonResumeStop.image = buttonResumeImg
        self.buttonResumeStop.grid(column=0, row=3)

        # Stop buttton
        self.buttonStop = tk.Button(self.f1, text="Stop",
                                    command=self.stop)

        buttonStopPath = Image.open("Photos/button/stop.png")
        buttonStopImg = ImageTk.PhotoImage(resizedButtonImage(buttonStopPath))

        self.buttonStop.config(image=buttonStopImg, padx=20, pady=20)
        self.buttonStop.padx = 20
        self.buttonStop.pady = 20
        self.buttonStop.image = buttonStopImg

        self.buttonStop.grid(column=1, row=3)

    def buttonPauseStop(self):
        TIMER.start_resume(self.steps)

        if self.buttonState is False:
            # Save the state for the next click
            self.buttonState = True
            buttonPath = Image.open("Photos/button/pause.png")
            buttonImg = ImageTk.PhotoImage(
                resizedButtonImage(buttonPath))
        else:
            self.buttonState = False
            buttonPath = Image.open("Photos/button/play.png")
            buttonImg = ImageTk.PhotoImage(resizedButtonImage(buttonPath))

        self.buttonResumeStop.config(image=buttonImg)
        self.buttonResumeStop.image = buttonImg

    def stop(self):
        global SERIAL
        SERIAL.write(b"stop\n")
        popup_window(self.controller, None, washingPage)

    def start():
        global SERIAL
        
        SERIAL.write(b"wash\n")
        TIMER.reset()
        TIMER.setlabel(TIMELABEL1, washingPage)
        TIMER.start_resume(1)


class dryPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        global TIMELABEL2
        global CONTROLLER

        # Creating Font, with a "size of 25" and weight of BOLD
        self.bold25 = Font(self, size=25, weight=BOLD)
        self.bold20 = Font(self, size=20, weight=BOLD)
        self.normalfont = Font(self, size=18)

        # Set the controller to global
        CONTROLLER = controller
        self.controller = controller

        # self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.f1 = tk.Frame(self)

        # Current index page is 2
        self.steps = 2

        # Row 0

        progressbar2Path = Image.open("Photos/ProgressBar2.png")
        progressbar2Img = ImageTk.PhotoImage(progressbar2Path)
        label = ttk.Label(self, image=progressbar2Img)
        label.image = progressbar2Img
        label.grid(row=0, column=1, padx=10, pady=10)

        usecaseLabel = ttk.Label(
            self, text="Drying in progress...",  style="BW.TLabel", font=self.bold20)
        usecaseLabel.grid(row=1, column=1, padx=10, pady=10)

        # Set the time label
        timelabel = ttk.Label(
            self, text="", font=self.normalfont, style="BW.TLabel")
        timelabel.grid(row=2, column=1, padx=10, pady=10)

        TIMELABEL2 = timelabel

        # Row 10 - Button to return to main page
        self.f1.grid(row=3, column=1, padx=10, pady=50)

        # Configure the different button
        # Intialize button state is resume
        self.buttonState = False
        self.buttonResumeStop = ttk.Button(self.f1, text="Resume/Pause",
                                           command=lambda: self.buttonPauseStop())

        buttonResumePath = Image.open("Photos/button/play.png")
        buttonResumeImg = ImageTk.PhotoImage(
            resizedButtonImage(buttonResumePath))

        self.buttonResumeStop.config(image=buttonResumeImg)
        self.buttonResumeStop.image = buttonResumeImg
        self.buttonResumeStop.grid(column=0, row=0)

        # Stop buttton
        self.buttonStop = ttk.Button(self.f1, text="Stop",
                                     command=self.stop)

        buttonStopPath = Image.open("Photos/button/stop.png")
        buttonStopImg = ImageTk.PhotoImage(resizedButtonImage(buttonStopPath))

        self.buttonStop.config(image=buttonStopImg)
        self.buttonStop.image = buttonStopImg

        self.buttonStop.grid(column=1, row=0)

    def buttonPauseStop(self):
        TIMER.start_resume(self.steps)

        if self.buttonState is False:
            # Save the state for the next click
            self.buttonState = True
            buttonPath = Image.open("Photos/button/pause.png")
            buttonImg = ImageTk.PhotoImage(
                resizedButtonImage(buttonPath))
        else:
            self.buttonState = False
            buttonPath = Image.open("Photos/button/play.png")
            buttonImg = ImageTk.PhotoImage(resizedButtonImage(buttonPath))

        self.buttonResumeStop.config(image=buttonImg)
        self.buttonResumeStop.image = buttonImg

    def stop(self):
        global SERIAL
        SERIAL.write(b"stop\n")
        popup_window(self.controller, None, dryPage)

    def start():
        global SERIAL

        SERIAL.write(b"dry\n")
        TIMER.reset()
        TIMER.setlabel(TIMELABEL2, dryPage)
        TIMER.start_resume(2)


class sterilisingPage(tk.Frame):
    def __init__(self, parent, controller, attr=None):
        tk.Frame.__init__(self, parent)

        global TIMELABEL3
        global CONTROLLER

        # Creating Font, with a "size of 25" and weight of BOLD
        self.bold25 = Font(self, size=25, weight=BOLD)
        self.bold20 = Font(self, size=20, weight=BOLD)
        self.normalfont = Font(self, size=18)

        CONTROLLER = controller
        self.controller = controller
        # self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.f1 = tk.Frame(self)

        # Current index page is 3
        self.steps = 3

        # Row 0
        # label = ttk.Label(self, text="", font=LARGEFONT)
        # label.grid(row=0, column=1, padx=10, pady=10)
        progressbar3Path = Image.open("Photos/ProgressBar3.png")
        progressbar3Img = ImageTk.PhotoImage(progressbar3Path)
        label = ttk.Label(self, image=progressbar3Img)
        label.image = progressbar3Img
        label.grid(row=0, column=1, padx=10, pady=10)

        usecaseLabel = ttk.Label(
            self, text="Sterilising in progress...", font=self.bold20, style="BW.TLabel")
        usecaseLabel.grid(row=1, column=1, padx=10, pady=10)

        # Set the time label
        timelabel = ttk.Label(
            self, text="", font=self.normalfont, style="BW.TLabel")
        timelabel.grid(row=2, column=1, padx=10, pady=10)

        TIMELABEL3 = timelabel

        # Row 10 - Button to return to main page
        self.f1.grid(row=3, column=1, padx=10, pady=50)

        # Configure the different button
        # Intialize button state is resume
        self.buttonState = False
        self.buttonResumeStop = ttk.Button(self.f1, text="Resume/Pause",
                                           command=lambda: self.buttonPauseStop())

        buttonResumePath = Image.open("Photos/button/play.png")
        buttonResumeImg = ImageTk.PhotoImage(
            resizedButtonImage(buttonResumePath))

        self.buttonResumeStop.config(image=buttonResumeImg)
        self.buttonResumeStop.image = buttonResumeImg
        self.buttonResumeStop.grid(column=0, row=0)

        # Stop buttton
        self.buttonStop = ttk.Button(self.f1, text="Stop",
                                     command=self.stop)

        buttonStopPath = Image.open("Photos/button/stop.png")
        buttonStopImg = ImageTk.PhotoImage(resizedButtonImage(buttonStopPath))

        self.buttonStop.config(image=buttonStopImg)
        self.buttonStop.image = buttonStopImg

        self.buttonStop.grid(column=1, row=0)

    def buttonPauseStop(self):
        TIMER.start_resume(self.steps)

        if self.buttonState is False:
            # Save the state for the next click
            self.buttonState = True
            buttonPath = Image.open("Photos/button/pause.png")
            buttonImg = ImageTk.PhotoImage(
                resizedButtonImage(buttonPath))
        else:
            self.buttonState = False
            buttonPath = Image.open("Photos/button/play.png")
            buttonImg = ImageTk.PhotoImage(resizedButtonImage(buttonPath))

        self.buttonResumeStop.config(image=buttonImg)
        self.buttonResumeStop.image = buttonImg

    def stop(self):
        popup_window(self.controller, None, sterilisingPage)

    def start():
        global SERIAL

        SERIAL.write(b"ster\n")
        TIMER.reset()
        TIMER.setlabel(TIMELABEL3, sterilisingPage)
        TIMER.start_resume(3)


class collectionPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        # Creating Font, with a "size of 25" and weight of BOLD
        self.bold25 = Font(self, size=25, weight=BOLD)
        self.bold20 = Font(self, size=20, weight=BOLD)
        self.normalfont = Font(self, size=18)

        self.controller = controller
        # self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        f1 = tk.Frame(self)

        # Current index page is 3
        self.steps = 4

        # Row 0 - Title
        label = ttk.Label(self, text="Smart Syringe Cleaner",
                          font=self.bold25, borderwidth=0, background="white")

        label.grid(row=0, column=1, padx=10, pady=10)

        # Row 1
        syringeImgPath = Image.open("Photos/syringe_completed.png")
        resizeSyringeImg = syringeImgPath.resize((150, 150), Image.ANTIALIAS)
        syringeImg = ImageTk.PhotoImage(resizeSyringeImg)

        syringeImgLabel = ttk.Label(self, image=syringeImg)
        syringeImgLabel.image = syringeImg

        syringeImgLabel.grid(row=1, column=1, padx=10, pady=20)

        # Row 2 -  Button to start the machine
        label_sub = ttk.Label(self, text="Completed! Please collect your syringe!",
                              font=self.normalfont, borderwidth=0, background="white")

        label_sub.grid(row=2, column=1, padx=10, pady=20)
        # Row 3 -  Button to start the machine
        button = tk.Button(self, text="Collect",  bg='#2196F3',
                           fg='white', padx=10, pady=20, font=self.normalfont, width=30,
                           command=lambda: nextFrame(self.controller, self.steps, collectionPage))

        button.grid(row=3, column=1, padx=10, pady=20)



# Camera code
def startCamera():
    global GRAPH_NAME
    global CLASSES
    global SCORES
    global IM_NAME
    global IMAGENO

    camera = PiCamera()
    camera.resolution = (640, 480)
    #camera.start_preview()
    # Camera warm-up time
    sleep(2)
    if use_GRAYSCALE:
        camera.color_effects = (128,128)
    camera.capture('test{}.jpg'.format(IMAGENO))
    camera.close()

    # Set image to open for cv2
    IM_NAME = 'test{}.jpg'.format(IMAGENO)

    # Import TensorFlow libraries
    # If tflite_runtime is installed, import interpreter from tflite_runtime, else import from regular tensorflow
    # If using Coral Edge TPU, import the load_delegate library
    pkg = importlib.util.find_spec('tflite_runtime')
    if pkg:
        from tflite_runtime.interpreter import Interpreter
        if use_TPU:
            from tflite_runtime.interpreter import load_delegate
    else:
        from tensorflow.lite.python.interpreter import Interpreter
        if use_TPU:
            from tensorflow.lite.python.interpreter import load_delegate

    # If using Edge TPU, assign filename for Edge TPU model
    if use_TPU:
        # If user has specified the name of the .tflite file, use that name, otherwise use default 'edgetpu.tflite'
        if (GRAPH_NAME == 'detect.tflite'):
            GRAPH_NAME = 'edgetpu.tflite'


    # Get path to current working directory
    CWD_PATH = os.getcwd()

    # Define path to images and grab all image filenames
    if IM_DIR:
        PATH_TO_IMAGES = os.path.join(CWD_PATH,IM_DIR)
        images = glob.glob(PATH_TO_IMAGES + '/*')

    elif IM_NAME:
        PATH_TO_IMAGES = os.path.join(CWD_PATH,IM_NAME)
        images = glob.glob(PATH_TO_IMAGES)

    # Path to .tflite file, which contains the model that is used for object detection
    PATH_TO_CKPT = os.path.join(CWD_PATH,MODEL_NAME,GRAPH_NAME)

    # Path to label map file
    PATH_TO_LABELS = os.path.join(CWD_PATH,MODEL_NAME,LABELMAP_NAME)

    # Load the label map
    with open(PATH_TO_LABELS, 'r') as f:
        labels = [line.strip() for line in f.readlines()]

    # Have to do a weird fix for label map if using the COCO "starter model" from
    # https://www.tensorflow.org/lite/models/object_detection/overview
    # First label is '???', which has to be removed.
    if labels[0] == '???':
        del(labels[0])

    # Load the Tensorflow Lite model.
    # If using Edge TPU, use special load_delegate argument
    if use_TPU:
        interpreter = Interpreter(model_path=PATH_TO_CKPT,
                                experimental_delegates=[load_delegate('libedgetpu.so.1.0')])
        print(PATH_TO_CKPT)
    else:
        interpreter = Interpreter(model_path=PATH_TO_CKPT)

    interpreter.allocate_tensors()

    # Get model details
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    height = input_details[0]['shape'][1]
    width = input_details[0]['shape'][2]

    floating_model = (input_details[0]['dtype'] == np.float32)

    input_mean = 127.5
    input_std = 127.5

    # Loop over every image and perform detection
    for image_path in images:

        # Load image and resize to expected shape [1xHxWx3]
        image = cv2.imread(image_path)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        imH, imW, _ = image.shape 
        image_resized = cv2.resize(image_rgb, (width, height))
        input_data = np.expand_dims(image_resized, axis=0)

        # Normalize pixel values if using a floating model (i.e. if model is non-quantized)
        if floating_model:
            input_data = (np.float32(input_data) - input_mean) / input_std

        # Perform the actual detection by running the model with the image as input
        interpreter.set_tensor(input_details[0]['index'],input_data)
        interpreter.invoke()

        # Retrieve detection results
        boxes = interpreter.get_tensor(output_details[0]['index'])[0] # Bounding box coordinates of detected objects
        #classes = interpreter.get_tensor(output_details[1]['index'])[0] # Class index of detected objects
        #scores = interpreter.get_tensor(output_details[2]['index'])[0] # Confidence of detected objects
        #num = interpreter.get_tensor(output_details[3]['index'])[0]  # Total number of detected objects (inaccurate and not needed)

        CLASSES = interpreter.get_tensor(output_details[1]['index'])[0] # Class index of detected objects
        SCORES = interpreter.get_tensor(output_details[2]['index'])[0] # Confidence of detected objects

        # Loop over all detections and draw detection box if confidence is above minimum threshold
        for i in range(len(SCORES)):
            if ((SCORES[i] > min_conf_threshold) and (SCORES[i] <= 1.0)):

                # Get bounding box coordinates and draw box
                # Interpreter can return coordinates that are outside of image dimensions, need to force them to be within image using max() and min()
                ymin = int(max(1,(boxes[i][0] * imH)))
                xmin = int(max(1,(boxes[i][1] * imW)))
                ymax = int(min(imH,(boxes[i][2] * imH)))
                xmax = int(min(imW,(boxes[i][3] * imW)))
                
                cv2.rectangle(image, (xmin,ymin), (xmax,ymax), (10, 255, 0), 2)

                # Draw label
                object_name = labels[int(CLASSES[i])] # Look up object name from "labels" array using class index
                label = '%s: %d%%' % (object_name, int(SCORES[i]*100)) # Example: 'person: 72%'
                labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2) # Get font size
                label_ymin = max(ymin, labelSize[1] + 10) # Make sure not to draw label too close to top of window
                cv2.rectangle(image, (xmin, label_ymin-labelSize[1]-10), (xmin+labelSize[0], label_ymin+baseLine-10), (255, 255, 255), cv2.FILLED) # Draw white box to put label text in
                cv2.putText(image, label, (xmin, label_ymin-7), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2) # Draw label text

    # All the results have been drawn on the image, now write the image
    #cv2.imshow('Object detector', image)
    cv2.imwrite("test{}.jpg".format(IMAGENO), image)

    # Clean up
    cv2.destroyAllWindows()

    IMAGENO += 1 # Increment image no for next file
    return

def main():
    # Import global var
    global APP
    global SERIAL

    SERIAL = SERIAL.SERIAL('/dev/{}'.format(TTYACM_PORT), 9600, timeout=1)
    SERIAL.flush()

    APP = SSCleaner()
    APP.mainloop()


if __name__ == "__main__":
    main()
