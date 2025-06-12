## Gandiva

What is Gandiva? It's an analysis tool intended for [RHEED](https://www.sciencedirect.com/topics/materials-science/reflection-high-energy-electron-diffraction#:~:text=In%20subject%20area%3A%20Materials%20Science,roughness%20in%20epitaxial%20thin%20films), a nanocharacterization method used to monitor film growth in molecular beam epitaxy systems. It's open-sourced and uses a tremendously simple heuristic to calculate the rate of crystal growth.

Since the peak 'brightness' of RHEED oscillates, reaching its peaks when new layers are empty and at their troughs when 50% completion of a layer exists, having a method of automatically analyzing and analyzing the information is important. Gandiva uses a simple heuristic- it turns the video to grayscale (from 0 to 255 in brightness), finds the 100 brightest pixels in the frame, averages their brightness, and graphs it with relation to time. It's fast enough to be real time (>60 frames per second on a laptop with OpenCV), and can be made significantly faster by simply having it check once every 2, 5, or 10 frames rather than every frame, increasing in speed by the same factor.

# Example

Using this video of RHEED footage as the input:
![gif](https://github.com/user-attachments/assets/f09e0b12-95b8-45f5-ab7b-db17d02f7f3e)

The software outputs the following plot (via matplotlib):
![plot](https://github.com/user-attachments/assets/0b54f231-cf61-464e-8504-f8adc9b9da7e)

The trademark oscillations of RHEED are clearly visible, and this generated at around ~80 frames/second, which means it's fast enough for real-time. Adding support for analysis while video is being streamed is trivial to do, and automatic waveform analysis (for layer counting) is trivial to do on top of this.

# Installation and Usage
Open the script in main.py, put the video file in the same repository, modify the script to have your filename as its input, and run. You need to have [Python](https://www.python.org/downloads/) (>3.8) as well as install the following libraries via pip:
```
pip install opencv-python matplotlib tqdm numpy
```

Good luck!
