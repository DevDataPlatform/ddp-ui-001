from dotenv import load_dotenv
from django.core.management.base import BaseCommand

from ddpui.models.org import Org, OrgWarehouse
from ddpui.utils.secretsmanager import save_superset_usage_dashboard_credentials

from ddpui.utils.custom_logger import CustomLogger

logger = CustomLogger("ddpui")

load_dotenv()


class Command(BaseCommand):
    """
    This script populates the DataflowBlock table
    """

    help = "Writes the DataflowBlock table"

    def add_arguments(self, parser):  # skipcq: PYL-R0201
        parser.add_argument("--org", required=True)
        parser.add_argument("--username", required=True)
        parser.add_argument("--first-name", required=True)
        parser.add_argument("--last-name", required=True)
        parser.add_argument("--password", required=True)

    def handle(self, *args, **options):
        """adds credentials to secrets manager"""
        org = Org.objects.filter(slug=options["org"]).first()
        if not org:
            logger.error("org not found")
            return
        warehouse = OrgWarehouse.objects.filter(org=org).first()
        if not warehouse:
            logger.error("warehouse not found")
            return

        secret_id = save_superset_usage_dashboard_credentials(
            warehouse,
            {
                "username": options["username"],
                "first_name": options["first_name"],
                "last_name": options["last_name"],
                "password": options["password"],
            },
        )
        warehouse.superset_creds = secret_id
        warehouse.save()
        logger.info("credentials saved")