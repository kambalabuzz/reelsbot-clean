import threading

from fastapi import FastAPI

from queue_worker import main as worker_main


app = FastAPI()


def worker_wrapper():
    try:
        worker_main()
    except Exception as e:
        print(f"FATAL: Worker thread crashed: {e}", flush=True)
        import traceback
        traceback.print_exc()

@app.on_event("startup")
def start_worker() -> None:
    thread = threading.Thread(target=worker_wrapper, daemon=True)
    thread.start()
    print("Worker thread started", flush=True)


@app.get("/")
def root() -> dict:
    return {"status": "ok"}


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}
