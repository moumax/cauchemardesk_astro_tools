from PyQt5.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel
from .solar_tab import SolarTab 
from .renamer_tab import RenamerTab
from .exif_reader_tab import ExifReaderTab
from .fit_reader_tab import FitsViewerTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("My PyQt5 App")
        self.setGeometry(100, 100, 800, 800)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Onglet Accueil
        home_tab = QWidget()
        home_layout = QVBoxLayout()
        home_layout.addWidget(QLabel("Bienvenue sur l'accueil !"))
        home_tab.setLayout(home_layout)
        self.tabs.addTab(home_tab, "Accueil")

        # Onglet renamer
        self.tabs.addTab(RenamerTab(), "Renamer")

        # Onglet météo solaire (nouveau widget)
        self.tabs.addTab(SolarTab(), "météo solaire")

        # Onglet Exif Reader
        self.tabs.addTab(ExifReaderTab(), "Exif Reader")

        # Onglet FITS Viewer
        self.tabs.addTab(FitsViewerTab(), "FITS Viewer")