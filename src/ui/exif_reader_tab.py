import sys
import json
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog, QComboBox,
    QTableWidget, QTableWidgetItem, QApplication, QLabel, QLineEdit
)
from PyQt5.QtCore import Qt
import exifread

# Ajout pour FITS
try:
    from astropy.io import fits
except ImportError:
    fits = None

HISTORY_FILE = "exif_history.json"
MAX_HISTORY = 5

def read_exif(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == ".fits":
            if fits is None:
                return {"Error": "astropy n'est pas installé"}
            with fits.open(file_path) as hdul:
                header = hdul[0].header
                return {str(k): str(v) for k, v in header.items()}
        else:
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)
                return {str(tag): str(value) for tag, value in tags.items()}
    except Exception as e:
        return {"Error": str(e)}

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history[:MAX_HISTORY], f)

class ExifReaderTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        self.select_btn = QPushButton("Sélectionner un fichier")
        self.select_btn.clicked.connect(self.select_file)
        self.layout.addWidget(self.select_btn)

        self.history_combo = QComboBox()
        self.history_combo.currentIndexChanged.connect(self.load_from_history)
        self.layout.addWidget(QLabel("Historique des fichiers :"))
        self.layout.addWidget(self.history_combo)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Rechercher un tag ou une valeur...")
        self.search_bar.textChanged.connect(self.filter_table)
        self.layout.addWidget(self.search_bar)

        self.table = QTableWidget()
        self.layout.addWidget(self.table)

        self.history = load_history()
        self.current_exif = {}
        self.update_history_combo()

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Choisir un fichier",
            "",
            "Images (*.jpg *.jpeg *.png *.cr2 *.CR2 *.cr3 *.CR3 *.fits *.FITS)"
        )
        if file_path:
            self.add_to_history(file_path)
            self.display_exif(file_path)

    def add_to_history(self, file_path):
        if file_path in self.history:
            self.history.remove(file_path)
        self.history.insert(0, file_path)
        save_history(self.history)
        self.update_history_combo()

    def update_history_combo(self):
        self.history_combo.blockSignals(True)
        self.history_combo.clear()
        self.history_combo.addItems(self.history)
        self.history_combo.blockSignals(False)

    def load_from_history(self, index):
        if 0 <= index < len(self.history):
            self.display_exif(self.history[index])

    def display_exif(self, file_path):
        exif = read_exif(file_path)
        self.current_exif = exif
        self.populate_table(exif)
        self.search_bar.clear()

    def populate_table(self, exif):
        self.table.clear()
        self.table.setRowCount(len(exif))
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Tag", "Valeur"])
        for row, (tag, value) in enumerate(exif.items()):
            self.table.setItem(row, 0, QTableWidgetItem(str(tag)))
            self.table.setItem(row, 1, QTableWidgetItem(str(value)))
        self.table.resizeColumnsToContents()

    def filter_table(self, text):
        text = text.lower()
        self.table.setRowCount(0)
        filtered = [
            (tag, value)
            for tag, value in self.current_exif.items()
            if text in str(tag).lower() or text in str(value).lower()
        ]
        self.table.setRowCount(len(filtered))
        for row, (tag, value) in enumerate(filtered):
            self.table.setItem(row, 0, QTableWidgetItem(str(tag)))
            self.table.setItem(row, 1, QTableWidgetItem(str(value)))
        self.table.resizeColumnsToContents()

# Pour tester l'onglet seul
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ExifReaderTab()
    window.show()
    sys.exit(app.exec_())