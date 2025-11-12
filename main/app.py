from __future__ import annotations

import os

import uvicorn


def run():
    port = int(os.environ.get("PORT", "5000"))
    uvicorn.run(
        "BGLApp_Refactor.api.server:app",
        host=os.environ.get("HOST", "0.0.0.0"),
        port=port,
        reload=os.environ.get("UVICORN_RELOAD", "1") == "1",
    )


if __name__ == "__main__":
    run()
