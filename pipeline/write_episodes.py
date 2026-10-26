"""Step 3: write the three remote episodes with Muse Wonder."""
import json

from paths import CONTENT
from quest_common import EPISODES, ask

episodes = ask(EPISODES).get("episodes", [])
(CONTENT / "episodes.lt.json").write_text(json.dumps({"episodes": episodes}, ensure_ascii=False, indent=2), encoding="utf-8")
print(len(episodes), "episodes")
