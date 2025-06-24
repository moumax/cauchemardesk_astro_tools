from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog,
    QListWidget, QLineEdit, QMessageBox, QCheckBox, QComboBox, QListWidgetItem
)
from PyQt5.QtGui import QColor, QBrush
import os
import exifread
import collections
import json

class RenamerTab(QWidget):
    def __init__(self):
        super().__init__()
        self.folder = None
        self.filenames = []
        self.last_renames = []
        self.fav_folders = []  # Liste des dossiers favoris
        self.setup_ui()
        self.load_favs()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        self.info_label = QLabel("Sélectionnez un dossier pour afficher ses fichiers.")
        main_layout.addWidget(self.info_label)

        self.select_button = QPushButton("Choisir un dossier…")
        self.select_button.clicked.connect(self.select_folder)
        main_layout.addWidget(self.select_button)

        # Favoris
        fav_layout = QHBoxLayout()
        self.fav_combo = QComboBox()
        self.fav_combo.setEditable(False)
        self.fav_combo.currentIndexChanged.connect(self.select_fav_folder)
        fav_layout.addWidget(QLabel("Favoris :"))
        fav_layout.addWidget(self.fav_combo)
        self.add_fav_button = QPushButton("Ajouter aux favoris")
        self.add_fav_button.clicked.connect(self.add_current_folder_to_fav)
        fav_layout.addWidget(self.add_fav_button)
        self.remove_fav_button = QPushButton("Supprimer des favoris")
        self.remove_fav_button.clicked.connect(self.remove_selected_fav)
        fav_layout.addWidget(self.remove_fav_button)
        main_layout.addLayout(fav_layout)

        # Options EXIF
        exif_layout = QHBoxLayout()
        self.date_checkbox = QCheckBox("Inclure la date de prise de vue (EXIF)")
        self.date_checkbox.stateChanged.connect(self.update_preview)
        exif_layout.addWidget(self.date_checkbox)
        self.model_checkbox = QCheckBox("Inclure le matériel utilisé (EXIF)")
        self.model_checkbox.stateChanged.connect(self.update_preview)
        exif_layout.addWidget(self.model_checkbox)
        main_layout.addLayout(exif_layout)

        # Liste de remplacement
        self.replace_checkbox = QCheckBox("Remplacer le nom par les infos EXIF")
        self.replace_checkbox.stateChanged.connect(self.update_preview)
        main_layout.addWidget(self.replace_checkbox)

        # Saisie du préfixe et suffixe
        prefix_suffix_layout = QHBoxLayout()
        prefix_suffix_layout.addWidget(QLabel("Préfixe à ajouter :"))
        self.prefix_input = QLineEdit()
        self.prefix_input.textChanged.connect(self.update_preview)
        prefix_suffix_layout.addWidget(self.prefix_input)

        prefix_suffix_layout.addWidget(QLabel("Suffixe à ajouter :"))
        self.suffix_input = QLineEdit()
        self.suffix_input.textChanged.connect(self.update_preview)
        prefix_suffix_layout.addWidget(self.suffix_input)
        main_layout.addLayout(prefix_suffix_layout)

        # Champ nom personnalisé
        custom_layout = QHBoxLayout()
        custom_layout.addWidget(QLabel("Nom personnalisé :"))
        self.custom_name_input = QLineEdit()
        self.custom_name_input.setPlaceholderText("Laisser vide pour ne pas remplacer")
        self.custom_name_input.textChanged.connect(self.update_preview)
        custom_layout.addWidget(self.custom_name_input)
        main_layout.addLayout(custom_layout)

        # Listes côte à côte
        lists_layout = QHBoxLayout()
        self.files_list = QListWidget()
        lists_layout.addWidget(self.files_list)
        self.preview_list = QListWidget()
        lists_layout.addWidget(self.preview_list)
        main_layout.addLayout(lists_layout)

        # Boutons d'action
        buttons_layout = QHBoxLayout()
        self.rename_button = QPushButton("Valider le renommage")
        self.rename_button.clicked.connect(self.rename_files)
        buttons_layout.addWidget(self.rename_button)
        self.undo_button = QPushButton("Annuler le dernier renommage")
        self.undo_button.clicked.connect(self.undo_rename)
        self.undo_button.setEnabled(False)
        buttons_layout.addWidget(self.undo_button)
        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Sélectionner un dossier", os.path.expanduser("~"))
        if folder:
            self.folder = folder
            self.info_label.setText(f"Dossier sélectionné : {folder}")
            self.files_list.clear()
            self.preview_list.clear()
            self.filenames = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
            self.filenames.sort()  # <-- Ajoute ce tri ici
            for filename in self.filenames:
                self.files_list.addItem(filename)
            self.update_preview()

    def get_exif_info(self, filepath):
        date_str = ""
        model_str = ""
        try:
            with open(filepath, 'rb') as f:
                tags = exifread.process_file(f, stop_tag="UNDEF", details=False)
                # Date
                date_tag = tags.get("EXIF DateTimeOriginal") or tags.get("Image DateTime")
                if date_tag:
                    date_str = str(date_tag).replace(":", "-").replace(" ", "_")
                # Modèle appareil
                model_tag = tags.get("Image Model")
                if model_tag:
                    model_str = str(model_tag).replace(" ", "_")
        except Exception:
            pass
        return date_str, model_str

    def update_preview(self):
        prefix = self.prefix_input.text()
        suffix = self.suffix_input.text()
        custom_name = self.custom_name_input.text()
        use_date = self.date_checkbox.isChecked()
        use_model = self.model_checkbox.isChecked()
        replace_name = self.replace_checkbox.isChecked()
        self.preview_list.clear()
        base_names = []
        exts = []
        for idx, filename in enumerate(self.filenames):
            name, ext = os.path.splitext(filename)
            new_name = name
            date_str, model_str = "", ""
            if use_date or use_model:
                date_str, model_str = self.get_exif_info(os.path.join(self.folder, filename))
            custom_name = self.custom_name_input.text()
            if replace_name:
                # Ignore le nom personnalisé, ne prend que les infos EXIF
                parts = []
                if use_date and date_str:
                    parts.append(date_str)
                if use_model and model_str:
                    parts.append(model_str)
                # Si rien n'est coché, on garde le nom d'origine
                base = "_".join(parts) if parts else name
            else:
                # Utilise le nom personnalisé si présent, sinon le nom d'origine
                if custom_name:
                    base = custom_name
                    if len(self.filenames) > 1:
                        base = f"{base}_{idx+1:03d}"
                else:
                    base = name
                # Ajoute la date et/ou le matériel autour du nom personnalisé ou du nom d'origine
                if use_date and date_str:
                    base = f"{date_str}_{base}"
                if use_model and model_str:
                    base = f"{base}_{model_str}"
            new_name = f"{prefix}{base}{suffix}"
            base_names.append(new_name)
            exts.append(ext)

        # Compte les occurrences pour les doublons
        counts = collections.defaultdict(int)
        for i, base in enumerate(base_names):
            count = counts[base]
            if count == 0:
                final_name = f"{base}{exts[i]}"
            else:
                final_name = f"{base}-{count:03d}{exts[i]}"
            counts[base] += 1

            original = f"{os.path.splitext(self.filenames[i])[0]}{exts[i]}"
            item = QListWidgetItem(final_name)
            if final_name != original:
                item.setForeground(QBrush(QColor("red")))
            else:
                item.setForeground(QBrush(QColor("black")))
            self.preview_list.addItem(item)

    def rename_files(self):
        if not self.folder or not self.filenames:
            QMessageBox.warning(self, "Erreur", "Aucun dossier ou fichier sélectionné.")
            return
        prefix = self.prefix_input.text()
        suffix = self.suffix_input.text()
        custom_name = self.custom_name_input.text()
        use_date = self.date_checkbox.isChecked()
        use_model = self.model_checkbox.isChecked()
        replace_name = self.replace_checkbox.isChecked()
        if not prefix and not suffix and not use_date and not use_model and not custom_name:
            QMessageBox.warning(self, "Erreur", "Veuillez saisir un préfixe, un suffixe, un nom personnalisé ou choisir une option EXIF.")
            return

        base_names = []
        exts = []
        for idx, filename in enumerate(self.filenames):
            name, ext = os.path.splitext(filename)
            new_name = name
            date_str, model_str = "", ""
            if use_date or use_model:
                date_str, model_str = self.get_exif_info(os.path.join(self.folder, filename))
            custom_name = self.custom_name_input.text()
            if replace_name:
                # Ignore le nom personnalisé, ne prend que les infos EXIF
                parts = []
                if use_date and date_str:
                    parts.append(date_str)
                if use_model and model_str:
                    parts.append(model_str)
                # Si rien n'est coché, on garde le nom d'origine
                base = "_".join(parts) if parts else name
            else:
                # Utilise le nom personnalisé si présent, sinon le nom d'origine
                if custom_name:
                    base = custom_name
                    if len(self.filenames) > 1:
                        base = f"{base}_{idx+1:03d}"
                else:
                    base = name
                # Ajoute la date et/ou le matériel autour du nom personnalisé ou du nom d'origine
                if use_date and date_str:
                    base = f"{date_str}_{base}"
                if use_model and model_str:
                    base = f"{base}_{model_str}"
            new_name = f"{prefix}{base}{suffix}"
            base_names.append(new_name)
            exts.append(ext)

        counts = collections.defaultdict(int)
        new_names = []
        old_new_pairs = []
        for i, filename in enumerate(self.filenames):
            base = base_names[i]
            ext = exts[i]
            count = counts[base]
            if count == 0:
                final_name = f"{base}{ext}"
            else:
                final_name = f"{base}-{count:03d}{ext}"
            counts[base] += 1
            new_names.append(final_name)

            src = os.path.join(self.folder, filename)
            dst = os.path.join(self.folder, final_name)
            if filename != final_name:
                try:
                    os.rename(src, dst)
                    old_new_pairs.append((final_name, filename))
                except Exception as e:
                    QMessageBox.critical(self, "Erreur", f"Erreur lors du renommage de {filename} : {e}")
                    return
        self.last_renames = old_new_pairs
        self.undo_button.setEnabled(bool(self.last_renames))
        self.filenames = new_names
        self.files_list.clear()
        self.preview_list.clear()
        for filename in self.filenames:
            self.files_list.addItem(filename)
        self.update_preview()
        QMessageBox.information(self, "Succès", "Renommage effectué.")
        self.prefix_input.clear()
        self.suffix_input.clear()
        self.custom_name_input.clear()
        self.date_checkbox.setChecked(False)
        self.model_checkbox.setChecked(False)
        self.replace_checkbox.setChecked(False)

    def undo_rename(self):
        if not self.folder or not self.last_renames:
            return
        errors = []
        for new_name, old_name in self.last_renames:
            src = os.path.join(self.folder, new_name)
            dst = os.path.join(self.folder, old_name)
            try:
                os.rename(src, dst)
            except Exception as e:
                errors.append(f"{new_name} : {e}")
        # Rafraîchir la liste
        self.filenames = [f for f in os.listdir(self.folder) if os.path.isfile(os.path.join(self.folder, f))]
        self.files_list.clear()
        self.preview_list.clear()
        for filename in self.filenames:
            self.files_list.addItem(filename)
        self.update_preview()
        self.last_renames = []
        self.undo_button.setEnabled(False)
        if errors:
            QMessageBox.warning(self, "Erreur(s)", "\n".join(errors))
        else:
            QMessageBox.information(self, "Annulé", "Renommage annulé.")

    def fav_file_path(self):
        # Stocke les favoris à la racine du projet
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "favs.json")

    def load_favs(self):
        try:
            with open(self.fav_file_path(), "r") as f:
                favs = json.load(f)
                self.fav_combo.clear()
                self.fav_combo.addItems(favs)
        except Exception:
            self.fav_combo.clear()

    def save_favs(self):
        favs = [self.fav_combo.itemText(i) for i in range(self.fav_combo.count())]
        with open(self.fav_file_path(), "w") as f:
            json.dump(favs, f)

    def add_current_folder_to_fav(self):
        if self.folder and self.fav_combo.findText(self.folder) == -1:
            self.fav_combo.addItem(self.folder)
            self.save_favs()

    def remove_selected_fav(self):
        current_index = self.fav_combo.currentIndex()
        if current_index == -1:
            return
        folder = self.fav_combo.currentText()
        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Supprimer le dossier des favoris ?\n{folder}",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.fav_combo.removeItem(current_index)
            self.save_favs()

    def select_fav_folder(self):
        folder = self.fav_combo.currentText()
        if folder and os.path.isdir(folder):
            self.folder = folder
            self.info_label.setText(f"Dossier sélectionné : {folder}")
            self.files_list.clear()
            self.preview_list.clear()
            self.filenames = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
            self.filenames.sort()  # <-- Et ici aussi
            for filename in self.filenames:
                self.files_list.addItem(filename)
            self.update_preview()