from src.tools.generator import main
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


if __name__ == "__main__":
    main(region="oklahoma_city")
