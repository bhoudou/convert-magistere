# 🔥 Convert-magistere

Outil de conversion et nettoyage de fichiers `.mbz` Moodle (Magistère-friendly).

## Fonctions principales :

- Convertit les activités `label` et `labellud` en `page`
- Nettoie les contenus HTML (`<intro>`, `<content>`) dans tous les modules
- Corrige les fichiers `files.xml`, `moodle_backup.xml` et `inforef.xml`
- Crée une nouvelle archive `.mbz` compatible avec Moodle
- Mode `.exe` disponible via PyInstaller

---

## 🚀 Utilisation

### Version `.exe` (Windows)

```bash
convert_magistere.exe [--input fichier.mbz] [--debug]
```

### Version Python

```bash
python convert_magistere.py --input fichier.mbz --debug
```

---

## ⚙️ Options

| Option       | Description                                        |
|--------------|----------------------------------------------------|
| `--input`    | Fichier `.mbz` à traiter (défaut : `cours.mbz`)     |
| `--debug`    | Garde le dossier `cours_decompresse` après traitement |

---

## 🏗 Génération du `.exe`

### Étapes :

```bash
pip install pyinstaller
pyinstaller --onefile convert_magistere.py
```

Le `.exe` se trouvera dans `dist/convert_magistere.exe`.

---

## 🛠 Dépendances

```bash
pip install beautifulsoup4 lxml
```

---

**Made with patience, café, et une pincée de Magistère.**