import os
import tarfile
import shutil
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import re
import time
import html

MBZ_FILE = "cours.mbz"
DEST_DIR = "cours_decompresse"
ACTIVITIES_DIR = os.path.join(DEST_DIR, "activities")
BACKUP_XML = os.path.join(DEST_DIR, "moodle_backup.xml")
ARCHIVE_INDEX = os.path.join(DEST_DIR, ".ARCHIVE_INDEX")

def transform_activity_generic(activity_path, modulename):
    xml_file = os.path.join(ACTIVITIES_DIR, activity_path, f"{modulename}.xml")
    if not os.path.exists(xml_file):
        print(f"⚠️ Fichier XML manquant pour {activity_path}")
        return False

    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        modified = False

        for tag in ["intro", "content"]:
            node = root.find(f".//{tag}")
            if node is not None and node.text : #and "<table" in node.text:
                original = node.text
                cleaned = clean_html(original, escape_output=False)
                if cleaned != original:
                    node.text = cleaned
                    modified = True
                    print(f"✅ {activity_path} → nettoyé <{tag}>")
                else: 
                    print(f"❌  {activity_path} → pas nettoyé <{tag}>")

        if modified:
            tree.write(xml_file, encoding="utf-8", xml_declaration=True)

        return modified

    except Exception as e:
        print(f"❌ Erreur XML dans {activity_path}: {e}")
        return False


def extract_mbz():
    with tarfile.open(MBZ_FILE, "r:*") as tar:
        tar.extractall(DEST_DIR)
    print(f"[✓] Archive extraite dans {DEST_DIR}/")

def clean_html(content, escape_output=True):
    decoded = html.unescape(content)
    soup = BeautifulSoup(decoded, "html.parser")

    # 🔁 Remplacement des <table> par <p> + <br> avec contenu préservé
    for table in soup.find_all("table"):
        paragraph = soup.new_tag("p")
        for row in table.find_all("tr"):
            row_html_parts = []
            for cell in row.find_all(["td", "th"]):
                cell_content = "".join(str(c) for c in cell.contents)
                row_html_parts.append(cell_content)
            line_html = "&nbsp;".join(row_html_parts)
            paragraph.append(BeautifulSoup(line_html + "<br>", "html.parser"))
        table.replace_with(paragraph)

    # 🔧 Supprimer les styles de couleur (mais garder les balises utiles)
    for tag in soup.find_all():
        if 'style' in tag.attrs:
            style = tag['style']
            if 'color:' in style:
                del tag.attrs['style']
        if 'color' in tag.attrs:
            del tag.attrs['color']

    # 💡 Déballer les <span> pour éviter les styles résiduels
    for span in soup.find_all("span"):
        span.unwrap()

    # 🧼 Échapper uniquement si utilisé dans un <content> XML (page)
    if escape_output:
        return html.escape(str(soup))
    else:
        return str(soup)

    
def patch_files_xml(xml_path):
    print(f"🔧 Patch de {xml_path} ...")
    with open(xml_path, "r", encoding="utf-8") as f:
        xml_data = f.read()

    replaced = xml_data
    replaced = replaced.replace("<component>mod_label</component>", "<component>mod_page</component>")
    replaced = replaced.replace("<component>mod_labellud</component>", "<component>mod_page</component>")
    replaced = replaced.replace("<filearea>intro</filearea>", "<filearea>content</filearea>")

    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(replaced)

    print("✅ files.xml patché : composants et fileareas corrigés.")





import subprocess
import os

def repack_mbz(source_dir="cours_decompresse", output_file="cours_modifie.mbz"):
    print(f"[📦] Recompression avec 7-Zip (Windows) en {output_file}...")

    # Chemin vers 7z.exe (adapter si besoin)
    seven_zip_path = r"C:\Program Files\7-Zip\7z.exe"

    if not os.path.exists(seven_zip_path):
        print(f"❌ ERREUR : 7z.exe introuvable à : {seven_zip_path}")
        return

    temp_tar = os.path.abspath("cours_temp.tar")
    output_mbz = os.path.abspath(output_file)

    # Étape 1 : créer un TAR à la racine
    cmd_tar = [seven_zip_path, "a", "-ttar", temp_tar, "."]
    print("➡️ Création .tar...")
    result_tar = subprocess.run(cmd_tar, cwd=source_dir, capture_output=True)

    if result_tar.returncode != 0:
        print("❌ Erreur création TAR :", result_tar.stderr.decode("cp1252", errors="replace"))
        return

    # Étape 2 : gzip du TAR
    cmd_gzip = [seven_zip_path, "a", "-tgzip", output_mbz, temp_tar]
    print("➡️ Compression .gz...")
    result_gz = subprocess.run(cmd_gzip, capture_output=True)

    if result_gz.returncode != 0:
        print("❌ Erreur compression GZ :", result_gz.stderr.decode("cp1252", errors="replace"))
        return

    # Nettoyage
    if os.path.exists(temp_tar):
        os.remove(temp_tar)

    print(f"✅ Archive Moodle générée avec succès : {output_mbz}")







def transform_activity(activity_path, modulename):
    activity_id = re.search(r'_(\d+)', activity_path).group(1)
    new_name = f"page_{activity_id}"
    new_path = os.path.join(ACTIVITIES_DIR, new_name)
    os.makedirs(new_path, exist_ok=True)

    xml_file = os.path.join(ACTIVITIES_DIR, activity_path, f"{modulename}.xml")
    tree = ET.parse(xml_file)
    root = tree.getroot()
    id = root.attrib.get("id")
    moduleid = root.attrib.get("moduleid")
    contextid = root.attrib.get("contextid")
    activity_node = root.find(f"./{modulename}")
    name = activity_node.findtext("name")
    intro_html = activity_node.findtext("intro", "")

    content_html = clean_html(intro_html, escape_output=True)

    # Créer page.xml
    page_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<activity id="{id}" moduleid="{moduleid}" modulename="page" contextid="{contextid}">
<page id="{id}">
<name>{html.escape(name)}</name>
<intro></intro>
<introformat>1</introformat>
<content>{content_html}</content>
<contentformat>1</contentformat>
<legacyfiles>0</legacyfiles>
<legacyfileslast>$@NULL@$</legacyfileslast>
<display>5</display>
<displayoptions>a:2:{{s:10:"printintro";s:1:"0";s:17:"printlastmodified";s:1:"0";}}</displayoptions>
<revision>1</revision>
<timemodified>1744563744</timemodified>
</page>
</activity>
"""
    with open(os.path.join(new_path, "page.xml"), "w", encoding="utf-8") as f:
        f.write(page_xml)

    # Copie des fichiers vides nécessaires
    empty_files = ["calendar.xml", "filters.xml", "grades.xml", "grade_history.xml", "roles.xml"]
    for filename in empty_files:
        content = f"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<{filename.split('.')[0]}></{filename.split('.')[0]}>"
        with open(os.path.join(new_path, filename), "w", encoding="utf-8") as f:
            f.write(content)

    # Modifier module.xml d'origine pour mettre <modulename>page</modulename>
    original_module_path = os.path.join(ACTIVITIES_DIR, activity_path, "module.xml")
    module_tree = ET.parse(original_module_path)
    module_root = module_tree.getroot()

    modname_node = module_root.find("modulename")
    if modname_node is not None:
        modname_node.text = "page"

    module_tree.write(os.path.join(new_path, "module.xml"), encoding="UTF-8", xml_declaration=True)

    shutil.rmtree(os.path.join(ACTIVITIES_DIR, activity_path))
    # print(f"[✓] Activité {activity_path} convertie en {new_name}")
    return (activity_id, moduleid, contextid, name)


def update_backup_xml(modules):
    tree = ET.parse(BACKUP_XML)
    root = tree.getroot()

    for activity_id, moduleid, contextid, name in modules:
        for activity in root.findall(".//activity"):
            if activity.findtext("moduleid") == moduleid:
                activity.find("modulename").text = "page"
                activity.find("title").text = name
                activity.find("directory").text = f"activities/page_{activity_id}"

        for setting in root.findall(".//setting"):
            activity = setting.findtext("activity")
            if activity in [f"label_{moduleid}", f"labellud_{moduleid}"]:
                setting.find("activity").text = f"page_{moduleid}"
                setting.find("name").text = setting.find("name").text.replace("label_", "page_").replace("labellud_", "page_")

    tree.write(BACKUP_XML, encoding="utf-8", xml_declaration=False)

    with open(BACKUP_XML, 'r', encoding='utf-8') as file:
        content = file.read()

    new_content = '<?xml version="1.0" encoding="UTF-8"?>\n' + content

    with open(BACKUP_XML, 'w', encoding='utf-8') as file:
        file.write(new_content)

    print("[✓] moodle_backup.xml mis à jour")


def update_archive_index(base_dir=DEST_DIR):
    entries = []
    entries.append("Moodle archive file index. Count: 0\n")

    for root, dirs, files in os.walk(base_dir):
        rel_root = os.path.relpath(root, base_dir).replace("\\", "/")
        if rel_root == ".":
            rel_root = ""

        if rel_root:
            entries.append(f"{rel_root}/\td\t0\t?\n")

        for f in files:
            path = os.path.join(root, f)
            rel_path = os.path.relpath(path, base_dir).replace("\\", "/")
            size = os.path.getsize(path)
            mtime = int(os.path.getmtime(path))
            entries.append(f"{rel_path}\tf\t{size}\t{mtime}\n")

    count = len(entries) - 1
    entries[0] = f"Moodle archive file index. Count: {count}\n"

    with open(ARCHIVE_INDEX, "w", encoding="utf-8") as f:
        f.writelines(entries)

    print("[✓] .ARCHIVE_INDEX entièrement régénéré (chemins normalisés)")

def generate_inforef_for_pages(activities_path, files_xml_path):
    print("📎 (Méthode robuste BS4/lxml) Génération des inforef.xml pour les activités page...")

    if not os.path.exists(files_xml_path):
        print(f"❌ Fichier introuvable : {files_xml_path}")
        return

    # Lecture brute du fichier files.xml
    with open(files_xml_path, "r", encoding="utf-8") as f:
        files_content = f.read()
    
    # Afficher une partie du contenu pour déboguer
    # print(f"DEBUG: Extrait de files.xml: {files_content[:500]}...")
    
    # Utiliser BeautifulSoup pour le parsing
    files_soup = BeautifulSoup(files_content, "lxml-xml")
    
    # Extraction directe des éléments file et contextid
    files_by_context = {}
    file_elements = files_soup.find_all("file")
    print(f"🔎 Nombre total de <file> trouvés : {len(file_elements)}")
    
    for file_element in file_elements:
        # Extraction directe du texte des éléments
        file_id = file_element.get('id')
        contextid_element = file_element.find('contextid')
        
        if file_id and contextid_element and contextid_element.text:
            contextid = contextid_element.text.strip()
            # print(f"DEBUG: Fichier ID={file_id}, ContextID={contextid}")
            
            if contextid not in files_by_context:
                files_by_context[contextid] = []
            files_by_context[contextid].append(file_id)
    
    # print(f"DEBUG: ContextIDs trouvés dans files.xml: {list(files_by_context.keys())}")

    # Traitement des activités
    for folder in os.listdir(activities_path):
        if not folder.startswith("page_"):
            continue

        activity_folder = os.path.join(activities_path, folder)
        page_xml_path = os.path.join(activity_folder, "page.xml")
        if not os.path.exists(page_xml_path):
            continue

        with open(page_xml_path, "r", encoding="utf-8") as f:
            page_content = f.read()
        
        # Extraction du contextid avec BeautifulSoup
        page_soup = BeautifulSoup(page_content, "lxml-xml")
        activity_element = page_soup.find("activity")
        
        if not activity_element:
            print(f"⚠️ Pas de tag 'activity' trouvé dans {folder}")
            continue
            
        contextid = activity_element.get("contextid", "").strip()
        # print(f"DEBUG: Activity folder={folder}, ContextID={contextid}")
        
        # Conversion explicit pour être sûr
        contextid_str = str(contextid)
        # print(f"🔬 Comparaison : activity contextid='{contextid_str}' (type: {type(contextid_str)}) vs disponibles : {list(files_by_context.keys())}")
        
        # Tentative avec contextid et contextid_str
        file_ids = files_by_context.get(contextid_str, [])
        if not file_ids:
            # Essai avec conversion inverse (au cas où)
            try:
                contextid_int = int(contextid)
                file_ids = files_by_context.get(str(contextid_int), [])
            except:
                pass
        
        # print(f"📄 {folder} — contextid={contextid_str} — fichiers liés : {len(file_ids)}")
        
        # Générer inforef.xml
        inforef_root = ET.Element("inforef")
        fileref = ET.SubElement(inforef_root, "fileref")
        for fid in file_ids:
            file_el = ET.SubElement(fileref, "file")
            ET.SubElement(file_el, "id").text = str(fid)
        
        inforef_tree = ET.ElementTree(inforef_root)
        inforef_path = os.path.join(activity_folder, "inforef.xml")
        inforef_tree.write(inforef_path, encoding="utf-8", xml_declaration=True)
        
        # print(f"✅ inforef.xml généré pour {folder} ({len(file_ids)} fichier(s))")


import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Convertisseur Moodle MBZ (label ➜ page + nettoyage)")
    parser.add_argument("--input", type=str, default="cours.mbz", help="Fichier MBZ à traiter (défaut : cours.mbz)")
    parser.add_argument("--debug", action="store_true", help="Ne pas supprimer le dossier 'cours_decompresse'")
    return parser.parse_args()

def main():
    args = parse_args()
    global MBZ_FILE, DEST_DIR, ACTIVITIES_DIR, BACKUP_XML, ARCHIVE_INDEX
    MBZ_FILE = args.input
    DEST_DIR = "cours_decompresse"
    ACTIVITIES_DIR = os.path.join(DEST_DIR, "activities")
    BACKUP_XML = os.path.join(DEST_DIR, "moodle_backup.xml")
    ARCHIVE_INDEX = os.path.join(DEST_DIR, ".ARCHIVE_INDEX")

    if not os.path.exists(MBZ_FILE):
        print(f"❌ Fichier introuvable : {MBZ_FILE}")
        return

    extract_mbz()
    modules_to_update = []
    files_xml_path = os.path.join(DEST_DIR, "files.xml")

    for dirname in os.listdir(ACTIVITIES_DIR):
        if dirname.startswith("label_") or dirname.startswith("labellud_"):
            modulename = dirname.split("_")[0]
            try:
                mod_info = transform_activity(dirname, modulename)
                modules_to_update.append(mod_info)
            except Exception as e:
                print(f"[!] Erreur avec {dirname} : {e}")

    update_backup_xml(modules_to_update)

    for dirname in os.listdir(ACTIVITIES_DIR):
        # print(f"{dirname}")
        if "_" not in dirname:
            continue
        modulename = dirname.split("_")[0]
        # print(f"{modulename}")
        if modulename in ["label", "labellud"]:
            continue
        transform_activity_generic(dirname, modulename)

    if os.path.exists(files_xml_path):
        patch_files_xml(files_xml_path)
        generate_inforef_for_pages(ACTIVITIES_DIR, files_xml_path)
    else:
        print("⚠️ Aucun fichier files.xml trouvé.")

    update_archive_index()
    repack_mbz()

    if not args.debug:
        print("🧹 Nettoyage du dossier temporaire...")
        shutil.rmtree(DEST_DIR, ignore_errors=True)

if __name__ == "__main__":
    main()
