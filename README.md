## Gandiva

What is Gandiva? It's an analysis tool intended for [RHEED](https://www.sciencedirect.com/topics/materials-science/reflection-high-energy-electron-diffraction#:~:text=In%20subject%20area%3A%20Materials%20Science,roughness%20in%20epitaxial%20thin%20films), a nanocharacterization method used to monitor film quality and timings in molecular beam epitaxy systems. It's open-sourced and uses a tremendously simple heuristic to calculate the rate of crystal growth.

Since the peak 'brightness' of RHEED oscillates, reaching its peaks when new layers are empty and at their troughs when 50% completion of a layer exists, having a method of automatically analyzing and analyzing the information is important. Gandiva uses a simple heuristic- it turns the video to grayscale (from 0 to 255 in brightness), finds the 100 brightest pixels in the frame, averages their brightness, and graphs it with relation to time. It's fast enough to be real time (>60 frames per second on a laptop with OpenCV), and can be made significantly faster by simply having it check once every 2, 5, or 10 frames rather than every frame, increasing in speed by the same factor.

# Example

