import sounddevice as sd
import soundfile as sf
import tempfile
import os
import openai

def enregistrer_audio(duree: int = 8, sample_rate: int = 16000) -> str:
    print(f"Enregistrement {duree}s...")
    audio = sd.rec(int(duree * sample_rate), samplerate=sample_rate, channels=1, dtype="float32")
    sd.wait()
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    sf.write(tmp.name, audio, sample_rate)
    return tmp.name

def transcrire(client: openai.OpenAI, fichier_audio: str) -> str:
    try:
        with open(fichier_audio, "rb") as f:
            return client.audio.transcriptions.create(
                model="whisper-1", file=f, language="fr"
            ).text
    finally:
        if os.path.exists(fichier_audio):
            os.unlink(fichier_audio)