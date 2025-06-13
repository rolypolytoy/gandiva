## Gandiva

Gandiva is a tool for use in Molecular Beam Epitaxy systems (MBE) outfitted with RHEED (reflective high energy electron diffraction), a method of in-situ crystal monitoring. It can parse video footage- either pre-recorded or in real-time- and generate waveforms based on visual input from RHEED. What this means is, with only a camera, you can digitize your RHEED data, and:

- Get waveforms generated with respect to time, for real-time analysis of crystal layer growth.
- Observe how many layers are made, the thickness of the film, and the growth rate per hour, simply by inputting the lattice constant of your material, and allowing it to run unopposed.
- Export and import data to and from the app, in .json/.csv, and as images.

It has a sleek interface with QT's Python bindings, uses OpenCV for >100FPS analysis speeds on most devices, and has an integration with Matplotlib to provide graphs that don't look out of place from a publication. It also uses the GNU All-Permissive License so you can genuinely modify it in any manner possible, beyond what's allowed in most open-source licenses. That license is just 'I'm putting a license here so you know I forfeit my right to a license' and it basically means you can modify it, use it commercially or noncommercially and there's no obligation that any derivatives are open source as well.

# Interface

If you upload the following video to Gandiva:
![gif](https://github.com/user-attachments/assets/e0a8ad34-410c-4c5a-8964-71d7224bcf7f)

The user interface displays this:
![image](https://github.com/user-attachments/assets/a21790e9-2d73-4c28-8338-d9f0d3396228)

It can also provide real-time analysis with the 'Start Live' tool. Make sure to select the correct camera device for it, since there may be multiple.

# Installation

Download [Gandiva.exe](https://github.com/rolypolytoy/gandiva/releases/tag/v1.0.0) from the releases page, run it, and don't delete the Gandiva shortcut on your Desktop. 
