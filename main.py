from app.api.main import app
import uvicorn
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("peakstack.root")

if __name__ == "__main__":
    # Ensure frontend is built
    dist_path = "peakstack-ui/dist"
    if not os.path.exists(dist_path):
        logger.warning("Frontend build not found. API will work but UI will not be served.")
        logger.info("Run 'cd peakstack-ui && npm run build' to generate frontend assets.")
    
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting Peakstack SaaS Platform on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)