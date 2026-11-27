from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import vk_updater


ACTIVITY = """\
.class public final Lcom/vk/music/screens/main/MainActivity;
.super Lcom/vkontakte/android/VKActivity;

.method public final onCreate(Landroid/os/Bundle;)V
    .locals 0

    invoke-super {p0, p1}, Lcom/vkontakte/android/VKActivity;->onCreate(Landroid/os/Bundle;)V

    return-void
.end method

.method public final onResume()V
    .locals 0

    invoke-super {p0}, Lcom/vkontakte/android/VKActivity;->onResume()V

    return-void
.end method
"""


class UpdaterInjectionTest(unittest.TestCase):
    def test_injects_on_create_and_resume_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            path = work / vk_updater.MAIN_ACTIVITY
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(ACTIVITY, encoding="utf-8")
            vk_updater.install_call(work)
            vk_updater.install_call(work)
            text = path.read_text(encoding="utf-8")
            self.assertEqual(2, text.count("Lcom/vk/music/updater/UpdateChecker;->check"))
            self.assertEqual(1, text.split(".method public final onCreate")[1].split(".end method")[0].count("UpdateChecker;->check"))
            self.assertEqual(1, text.split(".method public final onResume")[1].split(".end method")[0].count("UpdateChecker;->check"))


if __name__ == "__main__":
    unittest.main()
