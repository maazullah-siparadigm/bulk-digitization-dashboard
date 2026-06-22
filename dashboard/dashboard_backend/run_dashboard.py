import os
from dotenv import load_dotenv
load_dotenv(override=True)


import uvicorn


if __name__ == "__main__":
    uvicorn.run(
            "dashboard_backend.dashboard_app_be:app",
            # host="0.0.0.0",
            reload=True,
        )