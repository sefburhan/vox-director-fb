"""Narration for the 23-minute film: one wav + word timings per beat. Skips beats already done.

HF_HUB_CACHE=.../models/hf uv run --python 3.12 --with mlx-audio --with 'misaki[en]' --with mlx-whisper --with soundfile python vo_long.py [beat_id ...]
Re-voice one beat: delete vo/<id>.wav (or pass its id) and run again.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
VO = HERE / "vo"
VO.mkdir(exist_ok=True)
VOICE, SPEED = "af_heart", 1.0

# pronunciation guide from the script (misaki phonemes); longest keys first
PRON = {
    "Reko Diq": "/ɹˈAkO dˈɪk/", "Balochistan": "/bəlˈOʧɪstˌɑn/", "Balochi": "/bəlˈOʧi/", "Baloch": "/bəlˈOʧ/",
    "Chagai": "/ʧˈɑɡi/", "Nok Kundi": "/nˈOk kˈʌndi/", "Quetta": "/kwˈɛtə/", "Ras Koh": "/ɹˈɑs kˈO/",
    "Saindak": "/sˈAndʌk/", "Tanjeel": "/tænʤˈil/", "Gwadar": "/ɡwˈɑdəɹ/", "Zahedan": "/zɑhɛdˈɑn/",
    "Qasim": "/kˈɑsɪm/", "Raisani": "/ɹɑisˈɑni/", "Mubarakmand": "/mubˈɑɹəkmʌnd/", "Tethyan": "/tˈɛθiən/",
    "Tethys": "/tˈɛθɪs/", "Antofagasta": "/ˌæntOfəɡˈæstə/", "ICSID": "/ˈɪksɪd/", "EXIM": "/ˈɛksɪm/",
    "Fluor": "/flˈɔɹ/", "Bandial": "/bˈʌndiˌɑl/", "Mengal": "/mˈɛŋɡəl/", "Iftikhar": "/ɪftɪkˈɑɹ/",
    "Shehbaz": "/ʃɛhbˈɑz/", "Munir": "/munˈiɹ/", "Manara": "/mənˈɑɹə/",
}
SPELL = {"OGDCL": "O G D C L", "PPL": "P P L", "GHPL": "G H P L", "PIA": "P I A", "IFC": "I F C", "IMF": "I M F",
         "BHP": "B H P", "Hôtel Scribe": "Hotel Scribe", "BNP-M": "B N P M"}


def prep(text):
    for k, v in SPELL.items():
        text = text.replace(k, v)
    keys = sorted(PRON, key=len, reverse=True)
    pat = re.compile(r"(?<![\[\w])(" + "|".join(re.escape(k) for k in keys) + r")(?![\w\]])")
    text = pat.sub(lambda m: f"[{m.group(1)}]({PRON[m.group(1)]})", text)
    return text.replace("“", '"').replace("”", '"').replace("’", "'")


def main():
    from mlx_audio.tts.utils import load_model
    import mlx_whisper
    chapters = json.load(open(HERE / "script.json"))
    only = set(sys.argv[1:])
    tts = None
    for ch in chapters:
        for r in ch["rows"]:
            wav, js = VO / f"{r['id']}.wav", VO / f"{r['id']}.json"
            if (only and r["id"] not in only) or (not only and wav.exists() and js.exists()):
                continue
            if tts is None:
                tts = load_model("mlx-community/Kokoro-82M-bf16")
            text = prep(r["vo"])
            a = np.concatenate([np.array(x.audio) for x in tts.generate(text=text, voice=VOICE, speed=SPEED, lang_code="a")])
            sf.write(wav, a, 24000)
            res = mlx_whisper.transcribe(str(wav), path_or_hf_repo="mlx-community/whisper-small-mlx", word_timestamps=True, language="en")
            words = [dict(word=w["word"], start=w["start"], end=w["end"]) for s in res["segments"] for w in s["words"]]
            json.dump(dict(text=res["text"], words=words, dur=len(a) / 24000), open(js, "w"))
            print(f"{r['id']} {len(a) / 24000:5.1f}s  {res['text'].strip()[:80]}", flush=True)


if __name__ == "__main__":
    main()
