from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import requests

class SolarTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        solar_layout = QVBoxLayout()

        self.solar_spots_label = QLabel("Taches solaires")
        self.solar_spots_label.setAlignment(Qt.AlignCenter)
        solar_layout.addWidget(self.solar_spots_label)

        self.solar_spots_image = QLabel()
        self.solar_spots_image.setAlignment(Qt.AlignCenter)
        solar_layout.addWidget(self.solar_spots_image)

        self.solar_prom_label = QLabel("Protubérances solaires")
        self.solar_prom_label.setAlignment(Qt.AlignCenter)
        solar_layout.addWidget(self.solar_prom_label)

        self.solar_prom_image = QLabel()
        self.solar_prom_image.setAlignment(Qt.AlignCenter)
        solar_layout.addWidget(self.solar_prom_image)

        self.solar_ejection_label = QLabel("Ejection de masse coronale")
        self.solar_ejection_label.setAlignment(Qt.AlignCenter)
        solar_layout.addWidget(self.solar_ejection_label)

        self.solar_ejection_image = QLabel()
        self.solar_ejection_image.setAlignment(Qt.AlignCenter)
        solar_layout.addWidget(self.solar_ejection_image)

        refresh_button = QPushButton("Rafraîchir les images")
        refresh_button.clicked.connect(self.refresh_solar_images)
        solar_layout.addWidget(refresh_button)

        # Ajout du layout dans un widget pour le scroll
        solar_content = QWidget()
        solar_content.setLayout(solar_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(solar_content)

        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

        self.refresh_solar_images()

    def refresh_solar_images(self):
        # Taches solaires
        url_spots = "https://www.spaceweatherlive.com/images/SDO/SDO_HMIIF_1024.jpg"
        self.load_image(url_spots, self.solar_spots_image, "Erreur lors du chargement des taches solaires.")

        # Protubérances solaires
        url_prom = "https://sdo.gsfc.nasa.gov/assets/img/latest/latest_1024_0131.jpg"
        self.load_image(url_prom, self.solar_prom_image, "Erreur lors du chargement des protubérances.")

        # Ejection des masse coronale
        url_ejection = "https://sohowww.nascom.nasa.gov/data/realtime/c2/1024/latest.jpg"
        self.load_image(url_ejection, self.solar_ejection_image, "Erreur lors du chargement des éjections de masse coronale.")

    def load_image(self, url, label_widget, error_text):
        try:
            response = requests.get(url)
            response.raise_for_status()
            image = QPixmap()
            image.loadFromData(response.content)
            label_widget.setPixmap(image.scaled(600, 600, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except Exception:
            label_widget.setText(error_text)