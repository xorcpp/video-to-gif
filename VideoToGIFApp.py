import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel, QFileDialog, QVBoxLayout, QWidget,
    QSlider, QSpinBox, QHBoxLayout, QTimeEdit, QComboBox, QMessageBox
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import Qt, QUrl, QTime
import warnings

# Suppress Deprecation Warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


class ClickableVideoWidget(QVideoWidget):
    def __init__(self, main_app, parent=None):
        super().__init__(parent)
        self.main_app = main_app  # Reference to the main application

    def mousePressEvent(self, event):
        self.main_app.toggle_play_pause()  # Toggle play/pause on click


class VideoToGIFApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video to GIF Converter")
        self.setGeometry(100, 100, 800, 600)
        self.is_playing = False  # Playback state
        self.initUI()

    def initUI(self):
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()

        # Video preview
        self.video_widget = ClickableVideoWidget(self)  # Pass self to the video widget
        layout.addWidget(self.video_widget)

        # File selection
        self.file_button = QPushButton("Select Video")
        self.file_button.clicked.connect(self.open_file_dialog)
        layout.addWidget(self.file_button)

        # Trim controls
        trim_layout = QVBoxLayout()

        # Start controls
        start_layout = QHBoxLayout()
        self.start_time_label = QLabel("Start Time:")
        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setDisplayFormat("HH:mm:ss.zzz")
        self.start_time_edit.setTime(QTime(0, 0, 0, 0))
        self.start_time_edit.timeChanged.connect(self.update_start_from_time_edit)
        start_layout.addWidget(self.start_time_label)
        start_layout.addWidget(self.start_time_edit)

        self.start_slider = QSlider(Qt.Horizontal)
        self.start_slider.valueChanged.connect(self.update_start_from_slider)  # Real-time update
        start_layout.addWidget(self.start_slider)

        trim_layout.addLayout(start_layout)

        # End controls
        end_layout = QHBoxLayout()
        self.end_time_label = QLabel("End Time:")
        self.end_time_edit = QTimeEdit()
        self.end_time_edit.setDisplayFormat("HH:mm:ss.zzz")
        self.end_time_edit.setTime(QTime(0, 0, 0, 0))
        self.end_time_edit.timeChanged.connect(self.update_end_from_time_edit)
        end_layout.addWidget(self.end_time_label)
        end_layout.addWidget(self.end_time_edit)

        self.end_slider = QSlider(Qt.Horizontal)
        self.end_slider.valueChanged.connect(self.update_end_from_slider)  # Real-time update
        end_layout.addWidget(self.end_slider)

        trim_layout.addLayout(end_layout)
        layout.addLayout(trim_layout)

        # Advanced options
        advanced_layout = QVBoxLayout()

        self.resolution_label = QLabel("Resolution:")
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["360p", "SD (480p)", "HD (720p)", "Full HD (1080p)"])
        advanced_layout.addWidget(self.resolution_label)
        advanced_layout.addWidget(self.resolution_combo)

        self.frames_spinbox = QSpinBox()
        self.frames_spinbox.setRange(1, 30)
        self.frames_spinbox.setValue(10)
        advanced_layout.addWidget(QLabel("Frames per second:"))
        advanced_layout.addWidget(self.frames_spinbox)

        self.output_path_button = QPushButton("Select Output Path")
        self.output_path_button.clicked.connect(self.select_output_path)
        advanced_layout.addWidget(self.output_path_button)

        layout.addLayout(advanced_layout)

        # Convert button
        self.convert_button = QPushButton("Convert to GIF")
        self.convert_button.clicked.connect(self.convert_to_gif)
        layout.addWidget(self.convert_button)

        # About button
        self.about_button = QPushButton("About")
        self.about_button.clicked.connect(self.show_about_dialog)
        layout.addWidget(self.about_button)

        main_widget.setLayout(layout)

    def show_about_dialog(self):
        QMessageBox.information(self, "About", "Created by @pywriter\nVideo to GIF Converter v1.0")

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", "Video Files (*.mp4 *.avi *.mov)")
        if file_path:
            self.video_path = file_path
            self.load_video()

    def load_video(self):
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.video_path)))
        self.media_player.durationChanged.connect(self.setup_controls)
        self.media_player.play()
        self.is_playing = True

    def setup_controls(self, duration):
        self.duration = duration

        # Set up sliders
        self.start_slider.setRange(0, duration)
        self.end_slider.setRange(0, duration)
        self.end_slider.setValue(duration)

        # Adjust slider steps for higher precision
        self.start_slider.setSingleStep(100)  # 100 milliseconds
        self.end_slider.setSingleStep(100)

        # Synchronize sliders with time edits
        self.start_time_edit.setTime(self.milliseconds_to_qtime(0))
        self.end_time_edit.setTime(self.milliseconds_to_qtime(duration))

    def update_start_from_slider(self):
        position = self.start_slider.value()
        self.start_time_edit.setTime(self.milliseconds_to_qtime(position))
        self.media_player.setPosition(position)  # Seek the video to the new position

    def update_end_from_slider(self):
        position = self.end_slider.value()
        self.end_time_edit.setTime(self.milliseconds_to_qtime(position))
        self.media_player.setPosition(position)  # Seek to the new position

    def update_start_from_time_edit(self, time):
        milliseconds = self.qtime_to_milliseconds(time)
        self.start_slider.setValue(milliseconds)

    def update_end_from_time_edit(self, time):
        milliseconds = self.qtime_to_milliseconds(time)
        self.end_slider.setValue(milliseconds)

    def milliseconds_to_qtime(self, ms):
        s = ms // 1000
        ms = ms % 1000
        m = s // 60
        s = s % 60
        h = m // 60
        m = m % 60
        return QTime(h, m, s, ms)

    def qtime_to_milliseconds(self, qtime):
        return ((qtime.hour() * 3600 + qtime.minute() * 60 + qtime.second()) * 1000 + qtime.msec())

    def toggle_play_pause(self):
        if self.is_playing:
            self.media_player.pause()
        else:
            self.media_player.play()
        self.is_playing = not self.is_playing

    def select_output_path(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder_path:
            self.output_folder = folder_path

    def convert_to_gif(self):
        start_ms = self.start_slider.value()
        end_ms = self.end_slider.value()

        if end_ms <= start_ms:
            print("Start time must be less than end time.")
            return

        start_time = start_ms / 1000.0  # Convert to seconds
        duration = (end_ms - start_ms) / 1000.0  # Duration in seconds

        fps = self.frames_spinbox.value()

        # Map resolution
        resolution_map = {
            "360p": "360",
            "SD (480p)": "480",
            "HD (720p)": "720",
            "Full HD (1080p)": "1080"
        }
        resolution = resolution_map[self.resolution_combo.currentText()]

        # Generate palette
        palette_path = os.path.join(self.output_folder, "palette.png")
        gif_path = os.path.join(self.output_folder, "output.gif")
        palette_command = (
            f"ffmpeg -y -ss {start_time:.2f} -t {duration:.2f} "
            f"-i \"{self.video_path}\" -vf \"fps={fps},scale=-1:{resolution}:flags=lanczos,palettegen\" \"{palette_path}\""
        )
        os.system(palette_command)

        # Generate optimized GIF with palette
        gif_command = (
            f"ffmpeg -y -ss {start_time:.2f} -t {duration:.2f} "
            f"-i \"{self.video_path}\" -i \"{palette_path}\" "
            f"-lavfi \"fps={fps},scale=-1:{resolution}:flags=lanczos [x]; [x][1:v] paletteuse\" \"{gif_path}\""
        )
        os.system(gif_command)

        print(f"Conversion complete! GIF saved to: {gif_path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoToGIFApp()
    window.show()
    sys.exit(app.exec_())
