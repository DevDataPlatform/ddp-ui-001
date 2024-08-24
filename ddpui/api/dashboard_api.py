from ninja import NinjaAPI
from ninja.errors import ValidationError

from ninja.responses import Response
from pydantic.error_wrappers import ValidationError as PydanticValidationError
from django.forms import model_to_dict
from django.db.models import Prefetch

# dependencies
from ddpui import auth

# models
from ddpui.models.org import OrgDataFlowv1
from ddpui.models.tasks import DataflowOrgTask, TaskLock, OrgTask
from ddpui.auth import has_permission
from ddpui.ddpprefect import prefect_service

dashboardapi = NinjaAPI(urls_namespace="dashboard")


@dashboardapi.exception_handler(ValidationError)
def ninja_validation_error_handler(request, exc):  # pylint: disable=unused-argument
    """
    Handle any ninja validation errors raised in the apis
    These are raised during request payload validation
    exc.errors is correct
    """
    return Response({"detail": exc.errors}, status=422)


@dashboardapi.exception_handler(PydanticValidationError)
def pydantic_validation_error_handler(
    request, exc: PydanticValidationError
):  # pylint: disable=unused-argument
    """
    Handle any pydantic errors raised in the apis
    These are raised during response payload validation
    exc.errors() is correct
    """
    return Response({"detail": exc.errors()}, status=500)


@dashboardapi.exception_handler(Exception)
def ninja_default_error_handler(
    request, exc: Exception  # skipcq PYL-W0613
):  # pylint: disable=unused-argument
    """Handle any other exception raised in the apis"""
    return Response({"detail": "something went wrong"}, status=500)


@dashboardapi.get("/v1", auth=auth.CustomAuthMiddleware())
@has_permission(["can_view_dashboard"])
def get_dashboard_v1(request):
    """Fetch all flows/pipelines created in an organization"""
    orguser = request.orguser

    org_data_flows = OrgDataFlowv1.objects.filter(
        org=orguser.org, dataflow_type="orchestrate"
    )

    dataflow_ids = org_data_flows.values_list("id", flat=True)
    all_dataflow_orgtasks = DataflowOrgTask.objects.filter(
        dataflow_id__in=dataflow_ids
    ).select_related("orgtask")

    all_org_task_ids = all_dataflow_orgtasks.values_list("orgtask_id", flat=True)
    all_org_task_locks = TaskLock.objects.filter(orgtask_id__in=all_org_task_ids)

    deployment_ids = [flow.deployment_id for flow in org_data_flows]
    all_runs = prefect_service.get_flow_runs_by_deployment_id_v1(
        deployment_ids=deployment_ids, limit=50, offset=0
    )

    res = []

    # fetch 50 (default limit) flow runs for each flow
    for flow in org_data_flows:
        # if there is one there will typically be several - a sync,
        # a git-run, a git-test... we return the userinfo only for the first one
        dataflow_orgtasks = [
            dfot for dfot in all_dataflow_orgtasks if dfot.dataflow_id == flow.id
        ]

        org_tasks: list[OrgTask] = [
            dataflow_orgtask.orgtask for dataflow_orgtask in dataflow_orgtasks
        ]
        orgtask_ids = [org_task.id for org_task in org_tasks]

        lock = None
        all_locks = [
            lock for lock in all_org_task_locks if lock.orgtask_id in orgtask_ids
        ]
        if len(all_locks) > 0:
            lock = all_locks[0]

        res.append(
            {
                "name": flow.name,
                "deploymentId": flow.deployment_id,
                "cron": flow.cron,
                "deploymentName": flow.deployment_name,
                "runs": [
                    run
                    for run in all_runs
                    if run["deployment_id"] == flow.deployment_id
                ],
                "lock": (
                    {
                        "lockedBy": lock.locked_by.user.email,
                        "lockedAt": lock.locked_at,
                    }
                    if lock
                    else None
                ),
            }
        )

    # we might add more stuff here , system logs etc.
    return res
