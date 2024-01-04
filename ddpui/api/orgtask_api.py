import os
from pathlib import Path
from datetime import datetime
import yaml

from ninja import NinjaAPI
from ninja.errors import HttpError

from ninja.errors import ValidationError
from ninja.responses import Response
from pydantic.error_wrappers import ValidationError as PydanticValidationError

from ddpui import auth
from ddpui.ddpprefect import prefect_service
from ddpui.ddpairbyte import airbyte_service

from ddpui.ddpprefect import (
    DBTCORE,
    SHELLOPERATION,
    DBTCLIPROFILE,
    SECRET,
    AIRBYTECONNECTION,
    AIRBYTESERVER,
)
from ddpui.models.org import (
    OrgPrefectBlock,
    OrgWarehouse,
    OrgDataFlow,
    OrgDataFlowv1,
    OrgPrefectBlockv1,
)
from ddpui.models.org_user import OrgUser
from ddpui.models.tasks import Task, DataflowOrgTask, OrgTask, TaskLock
from ddpui.ddpprefect.schema import (
    PrefectAirbyteSync,
    PrefectDbtTaskSetup,
    PrefectDataFlowCreateSchema3,
    PrefectFlowRunSchema,
    PrefectDataFlowUpdateSchema3,
    PrefectSecretBlockCreate,
    PrefectShellTaskSetup,
    PrefectDataFlowCreateSchema4,
)

from ddpui.utils.custom_logger import CustomLogger
from ddpui.utils import secretsmanager
from ddpui.utils import timezone
from ddpui.utils.constants import (
    TASK_DBTRUN,
    TASK_GITPULL,
    TRANSFORM_TASKS_SEQ,
    AIRBYTE_SYNC_TIMEOUT,
)
from ddpui.utils.prefectlogs import parse_prefect_logs
from ddpui.utils.helpers import generate_hash_id

orgtaskapi = NinjaAPI(urls_namespace="orgtask")
# http://127.0.0.1:8000/api/docs


logger = CustomLogger("ddpui")


@orgtaskapi.exception_handler(ValidationError)
def ninja_validation_error_handler(request, exc):  # pylint: disable=unused-argument
    """
    Handle any ninja validation errors raised in the apis
    These are raised during request payload validation
    exc.errors is correct
    """
    return Response({"detail": exc.errors}, status=422)


@orgtaskapi.exception_handler(PydanticValidationError)
def pydantic_validation_error_handler(
    request, exc: PydanticValidationError
):  # pylint: disable=unused-argument
    """
    Handle any pydantic errors raised in the apis
    These are raised during response payload validation
    exc.errors() is correct
    """
    return Response({"detail": exc.errors()}, status=500)


@orgtaskapi.exception_handler(Exception)
def ninja_default_error_handler(
    request, exc: Exception  # skipcq PYL-W0613
):  # pylint: disable=unused-argument
    """Handle any other exception raised in the apis"""
    logger.info(exc)
    return Response({"detail": "something went wrong"}, status=500)


@orgtaskapi.post("transform/", auth=auth.CanManagePipelines())
def post_prefect_transformation_tasks(request):
    """
    - Create a git pull url secret block
    - Create a dbt cli profile block
    - Create dbt tasks
        - git pull
        - dbt deps
        - dbt clean
        - dbt run
        - dbt test
        - dbt docs generate
    """
    orguser: OrgUser = request.orguser
    if orguser.org.dbt is None:
        raise HttpError(400, "create a dbt workspace first")

    warehouse = OrgWarehouse.objects.filter(org=orguser.org).first()
    if warehouse is None:
        raise HttpError(400, "need to set up a warehouse first")
    credentials = secretsmanager.retrieve_warehouse_credentials(warehouse)

    if orguser.org.dbt.dbt_venv is None:
        orguser.org.dbt.dbt_venv = os.getenv("DBT_VENV")
        orguser.org.dbt.save()

    dbt_env_dir = Path(orguser.org.dbt.dbt_venv)
    if not dbt_env_dir.exists():
        raise HttpError(400, "create the dbt env first")

    dbt_binary = str(dbt_env_dir / "venv/bin/dbt")
    dbtrepodir = Path(os.getenv("CLIENTDBT_ROOT")) / orguser.org.slug / "dbtrepo"
    project_dir = str(dbtrepodir)
    dbt_project_filename = str(dbtrepodir / "dbt_project.yml")

    if not os.path.exists(dbt_project_filename):
        raise HttpError(400, dbt_project_filename + " is missing")

    # create a secret block to save the github endpoint url along with token
    try:
        gitrepo_access_token = secretsmanager.retrieve_github_token(orguser.org.dbt)
        gitrepo_url = orguser.org.dbt.gitrepo_url

        if gitrepo_access_token is not None and gitrepo_access_token != "":
            gitrepo_url = gitrepo_url.replace(
                "github.com", "oauth2:" + gitrepo_access_token + "@github.com"
            )

            # store the git oauth endpoint with token in a prefect secret block
            secret_block = PrefectSecretBlockCreate(
                block_name=f"{orguser.org.slug}-git-pull-url",
                secret=gitrepo_url,
            )
            block_response = prefect_service.create_secret_block(secret_block)

            # store secret block name block_response["block_name"] in orgdbt
            OrgPrefectBlockv1.objects.create(
                org=orguser.org,
                block_type=SECRET,
                block_id=block_response["block_id"],
                block_name=block_response["block_name"],
            )

    except Exception as error:
        logger.exception(error)
        raise HttpError(400, str(error)) from error

    with open(dbt_project_filename, "r", encoding="utf-8") as dbt_project_file:
        dbt_project = yaml.safe_load(dbt_project_file)
        if "profile" not in dbt_project:
            raise HttpError(400, "could not find 'profile:' in dbt_project.yml")

    profile_name = dbt_project["profile"]
    target = orguser.org.dbt.default_schema
    logger.info("profile_name=%s target=%s", profile_name, target)

    # get the dataset location if warehouse type is bigquery
    bqlocation = None
    if warehouse.wtype == "bigquery":
        destination = airbyte_service.get_destination(
            orguser.org.airbyte_workspace_id, warehouse.airbyte_destination_id
        )
        if destination.get("connectionConfiguration"):
            bqlocation = destination["connectionConfiguration"]["dataset_location"]

    # create a dbt cli profile block
    try:
        cli_block_name = f"{orguser.org.slug}-{profile_name}"
        cli_block_response = prefect_service.create_dbt_cli_profile_block(
            cli_block_name,
            profile_name,
            target,
            warehouse.wtype,
            bqlocation,
            credentials,
        )

        # save the cli profile block in django db
        OrgPrefectBlockv1.objects.create(
            org=orguser.org,
            block_type=DBTCLIPROFILE,
            block_id=cli_block_response["block_id"],
            block_name=cli_block_response["block_name"],
        )

    except Exception as error:
        logger.exception(error)
        raise HttpError(400, str(error)) from error

    # create org tasks for the transformation page
    for task in Task.objects.filter(type__in=["dbt", "git"]).all():
        org_task = OrgTask.objects.create(org=orguser.org, task=task)

        if task.slug == TASK_DBTRUN:
            # create deployment
            hash_code = generate_hash_id(8)
            deployment_name = f"manual-{orguser.org.slug}-{task.slug}-{hash_code}"
            dataflow = prefect_service.create_dataflow_v1(
                PrefectDataFlowCreateSchema3(
                    deployment_name=deployment_name,
                    flow_name=deployment_name,
                    orgslug=orguser.org.slug,
                    deployment_params={
                        "config": {
                            "tasks": [
                                {
                                    "slug": task.slug,
                                    "type": DBTCORE,
                                    "seq": 1,
                                    "commands": [
                                        f"{dbt_binary} {task.command} --target {target}"
                                    ],
                                    "env": {},
                                    "working_dir": project_dir,
                                    "profiles_dir": f"{project_dir}/profiles/",
                                    "project_dir": project_dir,
                                    "cli_profile_block": cli_block_response[
                                        "block_name"
                                    ],
                                    "cli_args": [],
                                }
                            ]
                        }
                    },
                )
            )

            # store deployment record in django db
            existing_dataflow = OrgDataFlowv1.objects.filter(
                deployment_id=dataflow["deployment"]["id"]
            ).first()
            if existing_dataflow:
                existing_dataflow.delete()

            new_dataflow = OrgDataFlowv1.objects.create(
                org=orguser.org,
                name=deployment_name,
                deployment_name=dataflow["deployment"]["name"],
                deployment_id=dataflow["deployment"]["id"],
                dataflow_type="manual",
            )

            DataflowOrgTask.objects.create(
                dataflow=new_dataflow,
                orgtask=org_task,
            )

    return {"success": 1}


@orgtaskapi.get("transform/", auth=auth.CanManagePipelines())
def get_prefect_transformation_tasks(request):
    """Fetch all dbt tasks for an org"""
    orguser: OrgUser = request.orguser

    org_tasks = []

    for org_task in (
        OrgTask.objects.filter(
            org=orguser.org,
            task__type__in=["git", "dbt"],
        )
        .order_by("task__id")
        .all()
    ):
        # check if task is locked
        lock = TaskLock.objects.filter(orgtask=org_task).first()

        org_tasks.append(
            {
                "label": org_task.task.label,
                "slug": org_task.task.slug,
                "id": org_task.id,
                "deploymentId": None,
                "lock": {
                    "lockedBy": lock.locked_by.user.email,
                    "lockedAt": lock.locked_at,
                }
                if lock
                else None,
            }
        )

        # fetch the manual deploymentId for the dbt run task
        if org_task.task.slug == TASK_DBTRUN:
            dataflow_orgtask = DataflowOrgTask.objects.filter(orgtask=org_task).first()
            org_tasks[-1]["deploymentId"] = (
                dataflow_orgtask.dataflow.deployment_id if dataflow_orgtask else None
            )

    return org_tasks


@orgtaskapi.delete("transform/", auth=auth.CanManagePipelines())
def delete_prefect_transformation_tasks(request):
    """delete tasks and related objects for an org"""
    orguser: OrgUser = request.orguser

    secret_block = OrgPrefectBlockv1.objects.filter(
        org=orguser.org,
        block_type=SECRET,
    ).first()
    if secret_block:
        logger.info("deleting secret block %s", secret_block.block_name)
        prefect_service.delete_secret_block(secret_block.block_id)
        secret_block.delete()

    cli_profile_block = OrgPrefectBlockv1.objects.filter(
        org=orguser.org,
        block_type=DBTCLIPROFILE,
    ).first()
    if cli_profile_block:
        logger.info("deleting cli profile block %s", cli_profile_block.block_name)
        prefect_service.delete_dbt_cli_profile_block(cli_profile_block.block_id)
        cli_profile_block.delete()

    org_tasks = OrgTask.objects.filter(org=orguser.org).all()

    for org_task in org_tasks:
        if org_task.task.slug == TASK_DBTRUN:
            dataflow_orgtask = DataflowOrgTask.objects.filter(orgtask=org_task).first()
            if dataflow_orgtask:
                # delete the manual deployment for this
                dataflow = dataflow_orgtask.dataflow
                logger.info("deleting manual deployment for dbt run")
                # do this in try catch because it can fail & throw error
                try:
                    prefect_service.delete_deployment_by_id(dataflow.deployment_id)
                except Exception:
                    pass
                logger.info("FINISHED deleting manual deployment for dbt run")
                logger.info("deleting OrgDataFlowv1")
                dataflow.delete()
                logger.info("deleting DataflowOrgTask")
                dataflow_orgtask.delete()

        logger.info("deleting org task %s", org_task.task.slug)
        org_task.delete()


@orgtaskapi.post("{orgtask_id}/run/", auth=auth.CanManagePipelines())
def post_run_prefect_org_task(request, orgtask_id):  # pylint: disable=unused-argument
    """
    Run dbt task & git pull in prefect. All tasks without a deployment.
    Basically short running tasks
    Can run
        - git pull
        - dbt deps
        - dbt clean
        - dbt test
    """
    orguser: OrgUser = request.orguser

    org_task = OrgTask.objects.filter(org=orguser.org, id=orgtask_id).first()

    if org_task is None:
        raise HttpError(400, "task not found")

    if org_task.task.type not in ["dbt", "git"]:
        raise HttpError(400, "task not supported")

    if orguser.org.dbt is None:
        raise HttpError(400, "dbt is not configured for this client")

    dbtrepodir = Path(os.getenv("CLIENTDBT_ROOT")) / orguser.org.slug / "dbtrepo"
    project_dir = str(dbtrepodir)

    # check if the task is locked
    task_lock = TaskLock.objects.filter(orgtask=org_task).first()
    if task_lock:
        raise HttpError(
            400, f"{task_lock.locked_by.user.email} is running this operation"
        )

    # lock the task
    task_lock = TaskLock.objects.create(orgtask=org_task, locked_by=orguser)

    if org_task.task.slug == TASK_GITPULL:
        shell_env = {"secret-git-pull-url-block": ""}

        gitpull_secret_block = OrgPrefectBlockv1.objects.filter(
            org=orguser.org, block_type=SECRET, block_name__contains="git-pull"
        ).first()

        if gitpull_secret_block is not None:
            shell_env["secret-git-pull-url-block"] = gitpull_secret_block.block_name

        payload = PrefectShellTaskSetup(
            commands=["git pull"],
            working_dir=project_dir,
            env=shell_env,
            slug=org_task.task.slug,
            type=SHELLOPERATION,
        )

        if payload.flow_name is None:
            payload.flow_name = f"{orguser.org.name}-gitpull"
        if payload.flow_run_name is None:
            now = timezone.as_ist(datetime.now())
            payload.flow_run_name = f"{now.isoformat()}"

        try:
            result = prefect_service.run_shell_task_sync(payload)
        except Exception as error:
            task_lock.delete()
            logger.exception(error)
            raise HttpError(
                400, f"failed to run the shell task {org_task.task.slug}"
            ) from error
    else:
        dbt_env_dir = Path(orguser.org.dbt.dbt_venv)
        if not dbt_env_dir.exists():
            raise HttpError(400, "create the dbt env first")

        dbt_binary = str(dbt_env_dir / "venv/bin/dbt")
        target = orguser.org.dbt.default_schema

        # fetch the cli profile block
        cli_profile_block = OrgPrefectBlockv1.objects.filter(
            org=orguser.org, block_type=DBTCLIPROFILE
        ).first()

        if cli_profile_block is None:
            raise HttpError(400, "dbt cli profile block not found")

        payload = PrefectDbtTaskSetup(
            slug=org_task.task.slug,
            commands=[f"{dbt_binary} {org_task.task.command} --target {target}"],
            env={},
            working_dir=project_dir,
            profiles_dir=f"{project_dir}/profiles/",
            project_dir=project_dir,
            cli_profile_block=cli_profile_block.block_name,
            cli_args=[],
            type=DBTCORE,
        )

        if payload.flow_name is None:
            payload.flow_name = f"{orguser.org.name}-{org_task.task.slug}"
        if payload.flow_run_name is None:
            now = timezone.as_ist(datetime.now())
            payload.flow_run_name = f"{now.isoformat()}"

        try:
            result = prefect_service.run_dbt_task_sync(payload)
        except Exception as error:
            task_lock.delete()
            logger.exception(error)
            raise HttpError(400, "failed to run dbt") from error

    # release the lock
    task_lock.delete()
    logger.info("released lock on task %s", org_task.task.slug)

    return result