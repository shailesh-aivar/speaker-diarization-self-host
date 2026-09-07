import io
import os
import threading

import torch
import torchaudio
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse

app = FastAPI(title="Speaker Diarization API")

pipeline = None
load_error: str | None = None
_load_lock = threading.Lock()


def _hf_token() -> str | None:
    return os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")


def load_pipeline() -> None:
    global pipeline, load_error
    try:
        from pyannote.audio import Pipeline

        token = _hf_token()
        if not token:
            load_error = "HF_TOKEN (or HUGGINGFACE_HUB_TOKEN) is not set"
            return
        loaded = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=token,
        )
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        loaded.to(device)
        with _load_lock:
            pipeline = loaded
            load_error = None
    except Exception as exc:
        load_error = str(exc)


@app.on_event("startup")
def on_startup() -> None:
    threading.Thread(target=load_pipeline, daemon=True).start()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> JSONResponse:
    if pipeline is not None:
        return JSONResponse({"status": "ready"})
    status = 503
    body = {"status": "error" if load_error else "loading"}
    if load_error:
        body["detail"] = load_error
    return JSONResponse(body, status_code=status)


@app.post("/diarize")
async def diarize(
    file: UploadFile = File(...),
    num_speakers: int | None = Query(None),
    min_speakers: int | None = Query(None),
    max_speakers: int | None = Query(None),
):
    if pipeline is None:
        raise HTTPException(
            status_code=503,
            detail=load_error or "pipeline still loading",
        )

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="empty file")

    waveform, sample_rate = torchaudio.load(io.BytesIO(contents))
    kwargs = {}
    if num_speakers is not None:
        kwargs["num_speakers"] = num_speakers
    if min_speakers is not None:
        kwargs["min_speakers"] = min_speakers
    if max_speakers is not None:
        kwargs["max_speakers"] = max_speakers

    diarization = pipeline(
        {"waveform": waveform, "sample_rate": sample_rate},
        **kwargs,
    )

    segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append(
            {
                "start": round(turn.start, 3),
                "end": round(turn.end, 3),
                "speaker": speaker,
            }
        )
    return JSONResponse({"segments": segments})
