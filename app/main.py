import os

import uvicorn
from app.api.server import get_application

app = get_application()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=os.getenv("ENVIRONMENT", "development") == "development")
