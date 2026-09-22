# --- Install ---
# 1. Set up the Python virtual environment for the DB manager app:
#      cd ~/git/kicad_db_gui
#      python3 -m venv venv
#      source venv/bin/activate
#      pip install -r requirements.txt
#      deactivate
#    (run.sh activates this venv automatically each time it's launched)
#
# 2. Symlink the launcher onto your PATH:
#      ln -s ~/git/kicad_db_gui/run.sh /opt/homebrew/bin/kicad-db
#      (Intel Macs: use /usr/local/bin/kicad-db instead)
#
# 3. Copy this plugin + icons into KiCad's plugin folder:
#      mkdir -p ~/Documents/KiCad/9.0/scripting/plugins/icons
#      cp kicad_db_manager_plugin.py ~/Documents/KiCad/10.0/scripting/plugins/
#      cp icon.png icon@2x.png ~/Documents/KiCad/10.0/scripting/plugins/icons/
#
# 4. In PCBNew: Tools -> External Plugins -> Refresh Plugins
#    (or restart KiCad)


import pcbnew
import subprocess
import os

class KiCadDBManagerPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "KiCad DB Manager"
        self.category = "Library Management"
        self.description = "Launch the PostgreSQL component library manager"
        self.show_toolbar_button = True
        self.icon_file_name = os.path.join(os.path.dirname(__file__), "icons", "kicad_db_gui_icon.png")

    def Run(self):
        subprocess.Popen(["/opt/homebrew/bin/kicad-db"])
        subprocess.Popen([script_path])

KiCadDBManagerPlugin().register()
