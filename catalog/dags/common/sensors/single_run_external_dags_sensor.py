import os
from collections.abc import Iterable

from airflow.exceptions import AirflowException
from airflow.models import DagBag, DagModel, DagRun, TaskInstance
from airflow.sensors.base import BaseSensorOperator
from airflow.utils.session import provide_session
from airflow.utils.state import State


class SingleRunExternalDAGsSensor(BaseSensorOperator):
    """
    Sensor for ensuring only one DAG runs at a time.

    Waits for a list of related DAGs, each assumed to have a similar Sensor,
    to not be running. A related DAG is considered to be 'running' if it is
    itself in the running state, and its corresponding wait task completed
    successfully. It looks for a task with the same `task_id` in each of the
    provided external DAGs.

    :param external_dag_ids: A list of dag_ids that you want to wait for
    :param check_existence: Set to `True` to check if the external DAGs exist,
    and immediately cease waiting if not (default value: False).
    :param allow_concurrent_runs: Used to force the Sensor to pass, even
    if there are concurrent runs.
    """

    def __init__(
        self,
        *,
        external_dag_ids: Iterable[str],
        check_existence: bool = False,
        allow_concurrent_runs: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.external_dag_ids = external_dag_ids
        self.check_existence = check_existence
        self.allow_concurrent_runs = allow_concurrent_runs

        # Used to ensure some checks are only evaluated on the first poke
        self._has_checked_params = False

    @provide_session
    def poke(self, context, session=None):
        self.log.info(
            "Poking for DAGs %s ...",
            self.external_dag_ids,
        )

        if not self._has_checked_params:
            if self.allow_concurrent_runs:
                self.log.info(
                    "`allow_concurrent_runs` is enabled. Returning without"
                    " checking for running DAGs."
                )
                return True

            if self.check_existence:
                self._check_for_existence(session=session)

            # Only check DAG existence and `allow_concurrent_runs`
            # on the first execution.
            self._has_checked_params = True

        count_running = self.get_count(session)

        self.log.info("%s DAGs are in the running state", count_running)
        return count_running == 0

    def _check_for_existence(self, session) -> None:
        for dag_id in self.external_dag_ids:
            dag_to_wait = (
                session.query(DagModel).filter(DagModel.dag_id == dag_id).first()
            )

            if not dag_to_wait:
                raise AirflowException(f"The external DAG {dag_id} does not exist.")

            if not os.path.exists(dag_to_wait.fileloc):
                raise AirflowException(f"The external DAG {dag_id} was deleted.")

            refreshed_dag_info = DagBag(dag_to_wait.fileloc).get_dag(dag_id)
            if not refreshed_dag_info.has_task(self.task_id):
                raise AirflowException(
                    f"The external DAG {dag_id} does not have a task "
                    f"with id {self.task_id}."
                )

    def get_count(self, session) -> int:
        # Get the count of running DAGs. A DAG is considered 'running' if
        # the DAG itself is in the running state, and if its instance of
        # the Sensor task has completed successfully.
        return (
            session.query(DagRun)
            .filter(
                DagRun.dag_id.in_(self.external_dag_ids),
                DagRun.state == State.RUNNING,
            )
            .join(TaskInstance, TaskInstance.run_id == DagRun.run_id)
            .filter(
                TaskInstance.task_id == self.task_id,
                TaskInstance.state == State.SUCCESS,
            )
            .count()
        )
