import os
from app import create_app
from dotenv import load_dotenv

load_dotenv()

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(debug=bool(os.getenv("IS_DEBUG")),
            port=port, host='0.0.0.0', threaded=True)
