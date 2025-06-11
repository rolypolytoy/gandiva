import cv2
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import os

class VideoBrightnessTracker:
    def __init__(self, video_path, n_pixels=100, sample_rate=1):
        self.video_path = video_path
        self.n_pixels = n_pixels
        self.sample_rate = sample_rate
        self.time_points = []
        self.brightness_values = []
    
    def analyze(self):
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {self.video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        frame_count = 0
        pbar = tqdm(total=total_frames//self.sample_rate, desc="Processing frames")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % self.sample_rate == 0:
                if len(frame.shape) == 3:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                else:
                    gray = frame.copy()
                
                flat_image = gray.flatten()
                top_n_indices = np.argpartition(flat_image, -self.n_pixels)[-self.n_pixels:]
                brightness = np.mean(flat_image[top_n_indices])
                
                self.time_points.append(frame_count / fps)
                self.brightness_values.append(brightness)
                pbar.update(1)
            
            frame_count += 1
        
        pbar.close()
        cap.release()
    
    def plot(self):
        plt.figure(figsize=(12, 6))
        plt.plot(self.time_points, self.brightness_values, linewidth=1.5, color='blue')
        plt.title(f'RHEED Growth')
        plt.xlabel('Time (s)')
        plt.ylabel('Intensity')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    video_path = "video.mp4"
    tracker = VideoBrightnessTracker(video_path, n_pixels=100, sample_rate=1)
    tracker.analyze()
    tracker.plot()