# CSC3003_OIP_Object_Detection
 
## Installation
This project is using TensorFlow 2.5.0. Compatibility of the version can be found at [TensorFlow GPU Support](https://www.tensorflow.org/install/source#gpu)

- Visual Studio C++
- [CUDA](https://developer.nvidia.com/cuda-downloads)
- [cuDNN](https://developer.nvidia.com/cudnn)
- [Anacoda](https://docs.anaconda.com/anaconda/install/index.html)


## Gathering and Labeling Data
The image must be in [Pascal Voc](https://www.tensorflow.org/lite/api_docs/python/tflite_model_maker/object_detector/DataLoader#from_pascal_voc) format

The (labelImg)[https://github.com/tzutalin/labelImg] is a GUI that is able to generate the file for the images. It is fast to label and annotate the image.
It is able to support YOLO3, Pascal Voc etc,

![demo](docs/demo3.jpg)

### For Windows
Install the follwing using pip
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/download)
- [lxml](http://lxml.de/installation.html)

```
pyrcc4 -o libs/resources.py resources.qrc
For pyqt5, pyrcc5 -o libs/resources.py resources.qrc

python labelImg.py
python labelImg.py [IMAGE_PATH] [PRE-DEFINED CLASS FILE]
```
Open the cmd and cd to the directory that the folder is saved

### For Windows + Anaconda
Open the Anaconda Prompt and go to the labelImg directory

```
conda install pyqt=5
conda install -c anaconda lxml
pyrcc5 -o libs/resources.py resources.qrc
python labelImg.py
python labelImg.py [IMAGE_PATH] [PRE-DEFINED CLASS FILE]
```

[Watch the video here](https://www.youtube.com/watch?v=p0nR2YsCY_U&ab_channel=TzuTaLin)
 
## TensorflowLite 2.5.0 Object Detection 
The project will focus on 3 main aspect for the data training
1) Setting up of the environment
2) Running the TFLITE_Model_Maker.ipynb
Before we start, we have to set up our environment using anacoda.

Open the anacoda3 command prompt for windows and run it as an administrator

![anacoda](docs/demo3.jpg)


conda activate tensorflow

Last updated : 24/8/2021