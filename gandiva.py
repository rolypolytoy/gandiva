import cv2
import numpy as np
import sys
from tqdm import tqdm
from scipy.signal import find_peaks, savgol_filter
from scipy import ndimage
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                               QWidget, QPushButton, QFileDialog, QLabel, QDoubleSpinBox, QComboBox, QSplashScreen)
from PySide6.QtCore import QThread, Signal, Qt, QTimer, QUrl, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPalette, QColor, QPixmap, QIcon
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import json



class SplashScreen(QSplashScreen):
    splash_finished = Signal()
    
    def __init__(self):
        screen = QApplication.primaryScreen().geometry()
        screen_width = screen.width()
        screen_height = screen.height()
        
        try:
            original_pixmap = QPixmap('Gandiva.png')
            if original_pixmap.isNull():
                pixmap = QPixmap(screen_width, screen_height)
                pixmap.fill(QColor(0, 0, 0))
            else:
                pixmap = QPixmap(screen_width, screen_height)
                pixmap.fill(QColor(0, 0, 0))
                
                scaled_image = original_pixmap.scaled(screen_width, screen_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                
                from PySide6.QtGui import QPainter
                painter = QPainter(pixmap)
                x = (screen_width - scaled_image.width()) // 2
                y = (screen_height - scaled_image.height()) // 2
                painter.drawPixmap(x, y, scaled_image)
                painter.end()
        except:
            pixmap = QPixmap(screen_width, screen_height)
            pixmap.fill(QColor(0, 0, 0))
            
        super().__init__(pixmap)
        self.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        
        try:
            self.media_player = QMediaPlayer()
            self.audio_output = QAudioOutput()
            self.media_player.setAudioOutput(self.audio_output)
            self.audio_output.setVolume(0.5)
        except:
            self.media_player = None
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.play_sound)
        self.timer.setSingleShot(True)
        self.timer.start(500)
        
        self.close_timer = QTimer()
        self.close_timer.timeout.connect(self.start_fadeout)
        self.close_timer.setSingleShot(True)

    def play_sound(self):
        if self.media_player:
            try:
                audio_path = os.path.abspath('Gandiva.mp3')
                if os.path.exists(audio_path):
                    self.media_player.setSource(QUrl.fromLocalFile(audio_path))
                    self.media_player.play()
            except:
                pass
        self.close_timer.start(4500)
    
    def start_fadeout(self):
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(800)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.fade_animation.finished.connect(self.close)
        self.fade_animation.start()

class LiveAnalysisThread(QThread):
    new_data_point = Signal(float, float)
    progress = Signal(int)
    finished = Signal()
    
    def __init__(self, rheed_analyzer, device_index):
        super().__init__()
        self.analyzer = rheed_analyzer
        self.device_index = device_index
        self.running = False
        self.paused = False
        self.frame_count = 0
        self.start_time = None
        
    def run(self):
        cap = cv2.VideoCapture(self.device_index)
        if not cap.isOpened():
            return
            
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        
        self.running = True
        import time
        self.start_time = time.time()
        frame_counter = 0
        
        while self.running:
            if not self.paused:
                ret, frame = cap.read()
                if not ret:
                    continue
                
                frame_counter += 1
                if frame_counter % 4 == 0:
                    if len(frame.shape) == 3:
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    else:
                        gray = frame.copy()
                    
                    flat_image = gray.flatten()
                    top_100_indices = np.argpartition(flat_image, -100)[-100:]
                    top_intensity = np.mean(flat_image[top_100_indices])
                    
                    p10 = np.percentile(flat_image, 10)
                    p90 = np.percentile(flat_image, 90)
                    background_mask = (flat_image >= p10) & (flat_image <= p90)
                    background_intensity = np.mean(flat_image[background_mask])
                    
                    brightness = top_intensity / background_intensity if background_intensity > 0 else 1.0
                    
                    current_time = time.time() - self.start_time
                    self.new_data_point.emit(current_time, brightness)
                    self.frame_count += 1
                
            time.sleep(1.0 / fps)
        
        cap.release()
        self.finished.emit()
    
    def stop(self):
        self.running = False
    
    def pause(self):
        self.paused = True
    
    def resume(self):
        self.paused = False

class AnalysisThread(QThread):
    progress = Signal(int)
    finished = Signal()
    
    def __init__(self, rheed_analyzer):
        super().__init__()
        self.analyzer = rheed_analyzer
    
    def run(self):
        cap = cv2.VideoCapture(self.analyzer.video_path)
        if not cap.isOpened():
            return
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % 4 == 0:
                if len(frame.shape) == 3:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                else:
                    gray = frame.copy()
                
                flat_image = gray.flatten()
                top_100_indices = np.argpartition(flat_image, -100)[-100:]
                top_intensity = np.mean(flat_image[top_100_indices])
                
                p10 = np.percentile(flat_image, 10)
                p90 = np.percentile(flat_image, 90)
                background_mask = (flat_image >= p10) & (flat_image <= p90)
                background_intensity = np.mean(flat_image[background_mask])
                
                brightness = top_intensity / background_intensity if background_intensity > 0 else 1.0
                
                self.analyzer.time_points.append(frame_count / fps)
                self.analyzer.brightness_values.append(brightness)
            
            frame_count += 1
            
            if frame_count % max(1, total_frames // 100) == 0:
                progress_percent = int((frame_count / total_frames) * 100)
                self.progress.emit(progress_percent)
        
        cap.release()
        
        smoothed = savgol_filter(self.analyzer.brightness_values, window_length=11, polyorder=3)
        intensity_range = max(smoothed) - min(smoothed)
        min_height = min(smoothed) + 0.3 * intensity_range
        min_distance = int(len(smoothed) * 0.1)
        
        self.analyzer.peaks, _ = find_peaks(smoothed, height=min_height, distance=min_distance)
        self.analyzer.peak_count = len(self.analyzer.peaks)
        
        self.finished.emit()

class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(16, 10), facecolor='white', dpi=100)
        super().__init__(self.fig)
        self.setParent(parent)
        self.ax = self.fig.add_subplot(111)
        self.analyzer = None
        
        self.fig.patch.set_facecolor('white')
        self.ax.set_facecolor('white')
        
        self.mpl_connect('motion_notify_event', self.on_hover)
        
        self.annotation = self.ax.annotate('', xy=(0,0), xytext=(20,20), 
                                         textcoords="offset points",
                                         bbox=dict(boxstyle="round", fc="white", alpha=0.9, edgecolor='gray'),
                                         arrowprops=dict(arrowstyle="->"))
        self.annotation.set_visible(False)
    
    def on_hover(self, event):
        if event.inaxes != self.ax or not self.analyzer:
            self.annotation.set_visible(False)
            self.draw_idle()
            return
        
        if hasattr(self, 'line') and self.line:
            cont, ind = self.line.contains(event)
            if cont:
                x = self.analyzer.time_points[ind['ind'][0]]
                
                smoothed = savgol_filter(self.analyzer.brightness_values, window_length=min(11, len(self.analyzer.brightness_values)), polyorder=3)
                min_val = np.min(smoothed)
                max_val = np.max(smoothed)
                if max_val > min_val:
                    y = ((smoothed[ind['ind'][0]] - min_val) / (max_val - min_val)) * 100
                else:
                    y = 50
                
                self.annotation.xy = (x, y)
                self.annotation.set_text(f'Time: {x:.2f}s\nIntensity: {y:.1f}%')
                self.annotation.set_visible(True)
                self.draw_idle()
            else:
                self.annotation.set_visible(False)
                self.draw_idle()
    
    def add_live_data_point(self, time_point, brightness):
        if len(self.analyzer.brightness_values) > 10:
            smoothed = savgol_filter(self.analyzer.brightness_values, window_length=min(11, len(self.analyzer.brightness_values)), polyorder=3)
            intensity_range = max(smoothed) - min(smoothed)
            min_height = min(smoothed) + 0.3 * intensity_range
            min_distance = max(1, int(len(smoothed) * 0.1))
            
            peaks, _ = find_peaks(smoothed, height=min_height, distance=min_distance)
            self.analyzer.peaks = peaks
            self.analyzer.peak_count = len(peaks)
        
        self.plot_data(self.analyzer)
    
    def plot_data(self, analyzer):
        self.analyzer = analyzer
        self.ax.clear()
        
        if not analyzer.brightness_values:
            return
        
        smoothed = savgol_filter(analyzer.brightness_values, window_length=min(11, len(analyzer.brightness_values)), polyorder=3)
        
        min_val = np.min(smoothed)
        max_val = np.max(smoothed)
        if max_val > min_val:
            smoothed_normalized = ((smoothed - min_val) / (max_val - min_val)) * 100
        else:
            smoothed_normalized = smoothed * 0 + 50
        
        self.line, = self.ax.plot(analyzer.time_points, smoothed_normalized, 
                                 linewidth=2, color='#1f3a93', picker=True, pickradius=5)
        
        self.ax.set_title('RHEED Growth', fontsize=18, fontweight='bold', pad=20)
        self.ax.set_xlabel('Time (s)', fontsize=14)
        self.ax.set_ylabel('Intensity (%)', fontsize=14)
        self.ax.grid(True, alpha=0.3)
        self.ax.set_ylim(0, 100)
        
        if len(analyzer.time_points) > 100:
            self.ax.set_xlim(max(0, max(analyzer.time_points) - 60), max(analyzer.time_points))
        
        self.fig.tight_layout()
        self.draw()

class RHEED(QMainWindow):
    def __init__(self):
        super().__init__()
        self.video_path = ""
        self.lattice_constant = 3.5
        self.time_points = []
        self.brightness_values = []
        self.peaks = None
        self.peak_count = 0
        self.live_thread = None
        self.is_live_mode = False
        
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('Gandiva - by Hume Nano')
        try:
            self.setWindowIcon(QIcon('Gandiva.ico'))
        except:
            self.setWindowIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))
        self.setGeometry(100, 100, 1400, 900)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        self.canvas = PlotCanvas(self)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas, stretch=1)
        
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(50)
        
        self.load_button = QPushButton('Load Video')
        self.load_button.clicked.connect(self.load_video)
        self.load_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        controls_layout.addWidget(self.load_button)
        
        self.device_combo = QComboBox()
        self.populate_video_devices()
        self.device_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
                min-width: 120px;
            }
        """)
        controls_layout.addWidget(self.device_combo)
        
        self.live_button = QPushButton('Start Live')
        self.live_button.clicked.connect(self.toggle_live_analysis)
        self.live_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        controls_layout.addWidget(self.live_button)
        
        self.pause_button = QPushButton('Pause')
        self.pause_button.clicked.connect(self.pause_live_analysis)
        self.pause_button.setVisible(False)
        self.pause_button.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        controls_layout.addWidget(self.pause_button)
        
        self.progress_label = QLabel('')
        self.progress_label.setStyleSheet("color: #7f8c8d; font-size: 12px; font-weight: bold;")
        controls_layout.addWidget(self.progress_label)
        
        lattice_container = QHBoxLayout()
        lattice_container.setSpacing(10)
        lattice_container.addWidget(QLabel('Lattice Constant (Å):'))
        self.lattice_spin = QDoubleSpinBox()
        self.lattice_spin.setRange(1.0, 10.0)
        self.lattice_spin.setValue(3.5)
        self.lattice_spin.setSingleStep(0.1)
        self.lattice_spin.setDecimals(2)
        self.lattice_spin.valueChanged.connect(self.update_lattice_constant)
        self.lattice_spin.setStyleSheet("""
            QDoubleSpinBox {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
        """)
        lattice_container.addWidget(self.lattice_spin)
        
        lattice_widget = QWidget()
        lattice_widget.setLayout(lattice_container)
        controls_layout.addWidget(lattice_widget)
        
        export_container = QHBoxLayout()
        export_container.setSpacing(10)
        
        self.export_combo = QComboBox()
        self.export_combo.addItems(['Export Data', 'Import Data'])
        self.export_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
                min-width: 100px;
            }
        """)
        export_container.addWidget(self.export_combo)
        
        self.export_button = QPushButton('Go')
        self.export_button.clicked.connect(self.handle_export_import)
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        export_container.addWidget(self.export_button)
        
        export_widget = QWidget()
        export_widget.setLayout(export_container)
        controls_layout.addWidget(export_widget)
        
        controls_layout.addStretch()
        
        self.info_label = QLabel('')
        self.info_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 12px;
                font-weight: bold;
                padding: 8px 12px;
                background-color: #f8f9fa;
                border: 1px solid #1f3a93;
                border-radius: 5px;
            }
        """)
        controls_layout.addWidget(self.info_label)
        
        layout.addLayout(controls_layout)
        central_widget.setLayout(layout)
    
    def populate_video_devices(self):
        self.device_combo.clear()
        self.device_combo.addItem("Select Camera...")
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                self.device_combo.addItem(f"Camera {i}")
                cap.release()
    
    def toggle_live_analysis(self):
        if not self.is_live_mode:
            device_text = self.device_combo.currentText()
            if device_text == "Select Camera...":
                return
            
            device_index = int(device_text.split()[-1])
            self.start_live_analysis(device_index)
        else:
            self.stop_live_analysis()
    
    def start_live_analysis(self, device_index):
        self.time_points = []
        self.brightness_values = []
        self.peaks = None
        self.peak_count = 0
        self.is_live_mode = True
        
        self.canvas.analyzer = self
        
        self.live_thread = LiveAnalysisThread(self, device_index)
        self.live_thread.new_data_point.connect(self.add_live_data_point)
        self.live_thread.finished.connect(self.live_analysis_finished)
        self.live_thread.start()
        
        self.live_button.setText('Stop Live')
        self.live_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.pause_button.setVisible(True)
        self.load_button.setEnabled(False)
        self.device_combo.setEnabled(False)
    
    def stop_live_analysis(self):
        if self.live_thread:
            self.live_thread.stop()
            self.live_thread.wait()
        
        self.is_live_mode = False
        self.live_button.setText('Start Live')
        self.live_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.pause_button.setVisible(False)
        self.load_button.setEnabled(True)
        self.device_combo.setEnabled(True)
    
    def pause_live_analysis(self):
        if self.live_thread:
            if self.pause_button.text() == 'Pause':
                self.live_thread.pause()
                self.pause_button.setText('Resume')
            else:
                self.live_thread.resume()
                self.pause_button.setText('Pause')
    
    def add_live_data_point(self, time_point, brightness):
        self.time_points.append(time_point)
        self.brightness_values.append(brightness)
        
        if len(self.brightness_values) > 10:
            smoothed = savgol_filter(self.brightness_values, window_length=min(11, len(self.brightness_values)), polyorder=3)
            intensity_range = max(smoothed) - min(smoothed)
            min_height = min(smoothed) + 0.1 * intensity_range
            min_distance = max(1, int(len(smoothed) * 0.05))
            
            peaks, _ = find_peaks(smoothed, height=min_height, distance=min_distance)
            self.peaks = peaks
            self.peak_count = len(peaks)
        
        self.canvas.add_live_data_point(time_point, brightness)
        self.update_info_display()
    
    def live_analysis_finished(self):
        self.stop_live_analysis()
    
    def load_video(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Open Video File', '', 
                                                  'Video Files (*.mp4 *.avi *.mov *.mkv);;All Files (*)')
        if file_path:
            self.video_path = file_path
            self.time_points = []
            self.brightness_values = []
            self.peaks = None
            self.peak_count = 0
            
            self.progress_label.setText('0%')
            
            self.analysis_thread = AnalysisThread(self)
            self.analysis_thread.progress.connect(self.update_progress)
            self.analysis_thread.finished.connect(self.analysis_complete)
            self.analysis_thread.start()
    
    def update_progress(self, progress):
        self.progress_label.setText(f'{progress}%')
    
    def update_lattice_constant(self, value):
        self.lattice_constant = value
        if self.brightness_values:
            self.canvas.plot_data(self)
            self.update_info_display()
    
    def analysis_complete(self):
        self.progress_label.setText('')
        self.canvas.plot_data(self)
        self.update_info_display()
    
    def update_info_display(self):
        if self.time_points:
            total_time_hrs = max(self.time_points) / 3600 if self.time_points else 0
            thickness_nm = (self.peak_count * self.lattice_constant) / 10
            growth_rate = thickness_nm / total_time_hrs if total_time_hrs > 0 else 0
            
            info_text = f"Layers: {self.peak_count} | Thickness: {thickness_nm:.2f} nm | Rate: {growth_rate:.1f} nm/hr"
            self.info_label.setText(info_text)
        else:
            self.info_label.setText('')
    
    def handle_export_import(self):
        if self.export_combo.currentText() == 'Export Data':
            self.export_data()
        else:
            self.import_data()
    
    def import_data(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Import Data', '', 
                                                  'JSON Files (*.json);;All Files (*)')
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                self.time_points = data['time_points']
                self.brightness_values = data['brightness_values']
                self.peak_count = data['peak_count']
                self.lattice_constant = data['lattice_constant']
                self.lattice_spin.setValue(self.lattice_constant)
                
                self.canvas.plot_data(self)
                self.update_info_display()
            except Exception as e:
                print(f"Error importing data: {e}")
    
    def export_data(self):
        if not self.time_points:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self, 'Export Data', '', 
                                                  'JSON Files (*.json);;CSV Files (*.csv);;All Files (*)')
        if file_path:
            total_time_hrs = max(self.time_points) / 3600 if self.time_points else 0
            thickness_nm = (self.peak_count * self.lattice_constant) / 10
            growth_rate = thickness_nm / total_time_hrs if total_time_hrs > 0 else 0
            
            if file_path.endswith('.json'):
                data = {
                    'time_points': self.time_points,
                    'brightness_values': self.brightness_values,
                    'peak_count': self.peak_count,
                    'lattice_constant': self.lattice_constant,
                    'thickness_nm': thickness_nm,
                    'growth_rate_nm_per_hr': growth_rate
                }
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2)
            else:
                import csv
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Time (s)', 'Intensity'])
                    for t, i in zip(self.time_points, self.brightness_values):
                        writer.writerow([t, i])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = RHEED()
    
    def show_main_window():
        window.showMaximized()
        window.raise_()
        window.activateWindow()
    
    main_window_timer = QTimer()
    main_window_timer.timeout.connect(show_main_window)
    main_window_timer.setSingleShot(True)
    main_window_timer.start(1000)
    
    splash = SplashScreen()
    splash.show()
    
    def hide_splash():
        splash.start_fadeout()
    
    splash.splash_finished.connect(hide_splash)
    
    sys.exit(app.exec())