"""A throwaway Anki base folder for the journey test: one profile 'e2e' holding a copy of the demo collection, with
GuessWithAnki and the test driver (gp_e2e) installed. Never points at a real profile.

    python setup_base.py BASE DEMO_COLLECTION ADDON_DIR DRIVER_DIR"""
import shutil
import sys
from pathlib import Path

from aqt.profiles import ProfileManager

base, demo, addon, driver = (Path(x) for x in sys.argv[1:5])
if base.exists():
    shutil.rmtree(base)
base = ProfileManager.get_created_base_folder(str(base))
pm = ProfileManager(base)
pm.setupMeta()
pm.create("e2e")
pm.db.execute("update profiles set data = ? where name = '_global'", pm._pickle(dict(pm.meta, defaultLang="en_US")))
pm.db.commit()
(base / "e2e").mkdir(exist_ok=True)
shutil.copy(demo, base / "e2e" / "collection.anki2")
from anki.collection import Collection                    # (the demo studied 150 today: lift the day's new limit)
col = Collection(str(base / "e2e" / "collection.anki2"))
for conf in col.decks.all_config():
    conf["new"]["perDay"] = 9999
    col.decks.update_config(conf)
col.close()
shutil.copytree(addon, base / "addons21" / "guesswithanki", ignore=shutil.ignore_patterns("__pycache__", "user_files"))
shutil.copytree(driver, base / "addons21" / "gp_e2e", ignore=shutil.ignore_patterns("__pycache__"))
print(base)
