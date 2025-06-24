import sys
import os
import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog, QComboBox,
    QLabel, QApplication, QSlider, QHBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QRectF
import numpy as np
import pyqtgraph as pg
from .star_detection import detect_stars

try:
    from astropy.io import fits
except ImportError:
    fits = None

HISTORY_FILE = "fits_history.json"
MAX_HISTORY = 5

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history[:MAX_HISTORY], f)

def fits_to_qimage(data, vmin=None, vmax=None):
    if data is None:
        return None, "Aucune donnée image"
    try:
        data = np.nan_to_num(data)
        if vmin is None:
            vmin = np.percentile(data, 1)
        if vmax is None:
            vmax = np.percentile(data, 99)
        data = np.clip(data, vmin, vmax)
        data = data - vmin
        if vmax - vmin > 0:
            data = data / (vmax - vmin) * 255
        data = data.astype(np.uint8)
        h, w = data.shape
        # S'assurer que les données sont contiguës
        data_c = np.require(data, np.uint8, 'C')
        qimg = QImage(data_c.data, w, h, w, QImage.Format_Grayscale8)
        return qimg.copy(), None  # copy pour éviter les soucis de GC
    except Exception as e:
        return None, str(e)

class ZoomableGraphicsView(QGraphicsView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setDragMode(QGraphicsView.ScrollHandDrag)

    def wheelEvent(self, event):
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor
        if event.angleDelta().y() > 0:
            self.scale(zoom_in_factor, zoom_in_factor)
        else:
            self.scale(zoom_out_factor, zoom_out_factor)

class FitsViewerTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        self.select_btn = QPushButton("Sélectionner un fichier FITS")
        self.select_btn.clicked.connect(self.select_file)
        self.layout.addWidget(self.select_btn)

        self.history_combo = QComboBox()
        self.history_combo.currentIndexChanged.connect(self.load_from_history)
        self.layout.addWidget(QLabel("Historique des fichiers :"))
        self.layout.addWidget(self.history_combo)

        # Sliders pour réglage histogramme
        slider_layout = QHBoxLayout()
        self.min_slider = QSlider(Qt.Horizontal)
        self.max_slider = QSlider(Qt.Horizontal)
        self.min_slider.setMinimum(0)
        self.min_slider.setMaximum(100)
        self.max_slider.setMinimum(0)
        self.max_slider.setMaximum(100)
        self.min_slider.setValue(1)
        self.max_slider.setValue(99)
        self.min_slider.valueChanged.connect(self.update_image)
        self.max_slider.valueChanged.connect(self.update_image)
        slider_layout.addWidget(QLabel("Min"))
        slider_layout.addWidget(self.min_slider)
        slider_layout.addWidget(QLabel("Max"))
        slider_layout.addWidget(self.max_slider)
        self.layout.addLayout(slider_layout)

        self.nb_stars_label = QLabel("Nombre d'étoiles détectées : -")
        self.layout.addWidget(self.nb_stars_label)

        self.roundness_label = QLabel("Roundness moyenne : -")
        self.layout.addWidget(self.roundness_label)

        self.history = load_history()
        self.update_history_combo()
        self.current_data = None

        self.image_view = ZoomableGraphicsView()
        self.image_scene = QGraphicsScene()
        self.image_view.setScene(self.image_scene)
        self.image_view.setFixedHeight(600)
        self.layout.addWidget(self.image_view)

        self.hist_widget = pg.PlotWidget(title="Histogramme")
        self.hist_widget.setLabel('left', 'Pixels')
        self.hist_widget.setLabel('bottom', 'Valeur')
        self.hist_widget.setFixedHeight(200)
        self.layout.addWidget(self.hist_widget)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Choisir un fichier FITS",
            "",
            "Fichiers FITS (*.fits *.fit *.FITS *.FIT)"
        )
        if file_path:
            self.add_to_history(file_path)
            self.load_fits(file_path)

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
            self.load_fits(self.history[index])

    def load_fits(self, file_path):
        if fits is None:
            self.image_label.setText("astropy n'est pas installé")
            return
        try:
            with fits.open(file_path) as hdul:
                data = None
                for hdu in hdul:
                    d = hdu.data
                    if d is not None:
                        if d.ndim == 3:
                            d = d[0]
                        if d.ndim == 2:
                            data = d
                            break
                if data is None:
                    self.image_label.setText("Aucune image 2D trouvée dans ce FITS")
                    self.current_data = None
                    self.hist_widget.clear()
                    return
                self.current_data = data
                # Détection d'étoiles et rondité
                nb_stars, roundness1, roundness2 = detect_stars(self.current_data)
                self.nb_stars_label.setText(f"Nombre d'étoiles détectées : {nb_stars}")
                if roundness1 is not None:
                    self.roundness_label.setText(f"Roundness moyenne : {roundness1:.3f} / {roundness2:.3f}")
                else:
                    self.roundness_label.setText("Roundness moyenne : -")
                self.min_slider.setValue(1)
                self.max_slider.setValue(99)
                self.update_image()
        except Exception as e:
            self.image_label.setText(str(e))
            self.current_data = None
            self.hist_widget.clear()

    def update_image(self):
        if self.current_data is None:
            self.hist_widget.clear()
            return

        # Force float64 pour éviter les soucis de cast
        data = np.array(self.current_data, dtype=np.float64)
        flat = data.flatten()
        flat = flat[np.isfinite(flat)]
        if flat.size == 0:
            self.image_label.setText("Aucune donnée exploitable")
            self.hist_widget.clear()
            return

        min_percent = self.min_slider.value()
        max_percent = self.max_slider.value()
        if min_percent is None or max_percent is None:
            self.image_label.setText("Valeur slider invalide")
            self.hist_widget.clear()
            return
        if min_percent >= max_percent:
            self.image_label.setText("Min doit être inférieur à Max")
            self.hist_widget.clear()
            return

        try:
            vmin = float(np.percentile(flat, min_percent))
            vmax = float(np.percentile(flat, max_percent))
        except Exception as e:
            self.image_label.setText(f"Erreur percentiles : {e}")
            self.hist_widget.clear()
            return

        if vmax is None or vmin is None or vmax - vmin == 0:
            self.image_label.setText("vmax et vmin identiques ou invalides, image plate")
            self.hist_widget.clear()
            return

        # Affichage de l'image
        qimg, error = fits_to_qimage(data, vmin, vmax)
        if qimg is not None:
            self.show_image(qimg, reset_zoom=False)
        else:
            self.image_scene.clear()

        # Histogramme sur les données affichées (après vmin/vmax)
        self.hist_widget.clear()
        data_disp = np.clip(flat, vmin, vmax)
        if vmax - vmin > 0:
            data_disp = (data_disp - vmin) / (vmax - vmin) * 255
        else:
            data_disp = np.zeros_like(data_disp)
        y, x = np.histogram(data_disp.astype(np.float64), bins=128)
        # Pour stepMode=False, x[:-1] et y doivent avoir la même taille
        self.hist_widget.plot(x[:-1], y, stepMode=False, fillLevel=0, brush=(150,150,255,150))
        self.hist_widget.setXRange(0, 255, padding=0)
        self.hist_widget.setYRange(0, max(y)*1.05 if y.max() > 0 else 1, padding=0)
        self.hist_widget.repaint()

        # Détection d'étoiles
        nb_stars, roundness1, roundness2 = detect_stars(self.current_data)
        self.nb_stars_label.setText(f"Nombre d'étoiles détectées : {nb_stars}")
        if roundness1 is not None:
            self.roundness_label.setText(f"Roundness moyenne : {roundness1:.3f} / {roundness2:.3f}")
        else:
            self.roundness_label.setText("Roundness moyenne : -")
        print(f"Nombre d'étoiles détectées : {nb_stars}")

    def show_image(self, qimg, reset_zoom=False):
        self.image_scene.clear()
        pixmap = QPixmap.fromImage(qimg)
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.image_scene.addItem(self.pixmap_item)
        self.image_view.setSceneRect(QRectF(pixmap.rect()))
        if reset_zoom:
            self.image_view.resetTransform()

# Pour tester l'onglet seul
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FitsViewerTab()
    window.show()
    sys.exit(app.exec_())