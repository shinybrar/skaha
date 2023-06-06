"""Skaha Headless Session."""
from asyncio import get_event_loop
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import root_validator
from requests.exceptions import HTTPError
from requests.models import Response

from skaha.client import SkahaClient
from skaha.models import CreateSpec, FetchSpec
from skaha.utils import convert, logs
from skaha.utils.threaded import scale

log = logs.get_logger(__name__)


class Session(SkahaClient):
    """Skaha Session Client."""

    @root_validator
    def set_server(cls, values: Dict[str, Any]):
        """Sets the server path after validation."""
        values["server"] = f"{values['server']}/{values['version']}/session"
        log.debug(f'Server set to {values["server"]}')
        return values

    def fetch(
        self,
        kind: Optional[str] = None,
        status: Optional[str] = None,
        view: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """List open sessions for the user.

        Args:
            kind (str, optional): Session kind. Defaults to None.
            status (str, optional): Session status. Defaults to None.
            view (str, optional): Session view level. Defaults to None.

        Notes:
            By default, only the calling user's sessions are listed. If views is
            set to 'all', all user sessions are listed (with limited information).

        Returns:
            list: Sessions information.

        Examples:
            >>> from skaha.session import Session
            >>> session = Session()
            >>> session.fetch(kind="notebook")
            [{'id': 'ikvp1jtp',
              'userid': 'username',
              'image': 'images.canfar.net/image/label:latest',
              'type': 'notebook',
              'status': 'Running',
              'name': 'example-notebook',
              'startTime': '2222-12-14T02:24:06Z',
              'connectURL': 'https://skaha.example.com/ikvp1jtp',
              'requestedRAM': '16G',
              'requestedCPUCores': '2',
              'requestedGPUCores': '<none>',
              'coresInUse': '0m',
              'ramInUse': '101Mi'}]
            >>> session.fetch(kind="desktop", view="all")
            [{'userid': 'bmajor',
              'type': 'desktop',
              'status': 'Running',
              'startTime': '2222-12-07T05:45:58Z'},
              ...]
        """
        specification: FetchSpec = FetchSpec(kind=kind, status=status, view=view)
        parameters = specification.dict(exclude_none=True)
        log.debug(parameters)
        response: Response = self.session.get(url=self.server, params=parameters)  # type: ignore # noqa: E501
        response.raise_for_status()
        return response.json()

    def stats(self) -> Dict[str, Any]:
        """Get statistics for the entire skaha cluster.

        Returns:
            Dict[str, Any]: Cluster statistics.

        Examples:
            >>> from skaha.session import Session
            >>> session = Session()
            >>> session.stats()
            {'instances': {'session': 88, 'desktopApp': 30, 'headless': 0, 'total': 118},
             'cores': {'requestedCPUCores': 377,
             'coresAvailable': 960,
             'maxCores': {'cores': 32, 'withRam': '147Gi'}},
             'ram': {'maxRAM': {'ram': '226Gi', 'withCores': 32}}}
        """
        parameters = {"view": "stats"}
        log.debug(parameters)
        response: Response = self.session.get(url=self.server, params=parameters)  # type: ignore # noqa: E501
        response.raise_for_status()
        return response.json()

    def info(self, id: Union[List[str], str]) -> List[Dict[str, Any]]:
        """Get information about session[s].

        Args:
            id (Union[List[str], str]): Session ID[s].

        Returns:
            Dict[str, Any]: Session information.

        Examples:
            >>> session.info(session_id="hjko98yghj")
            >>> session.info(id=["hjko98yghj", "ikvp1jtp"])
        """
        # Convert id to list if it is a string
        if isinstance(id, str):
            id = [id]
        parameters: Dict[str, str] = {"view": "event"}
        arguments: List[Any] = []
        for value in id:
            arguments.append({"url": self.server + "/" + value, "params": parameters})
        loop = get_event_loop()
        results = loop.run_until_complete(scale(self.session.get, arguments))
        responses: List[Dict[str, Any]] = []
        for response in results:
            try:
                response.raise_for_status()
                responses.append(response.json())
            except HTTPError as err:
                log.error(err)
        return responses

    def logs(self, id: Union[List[str], str]) -> Dict[str, str]:
        """Get logs from a session[s].

        Args:
            id (Union[List[str], str]): Session ID[s].

        Returns:
            Dict[str, str]: Logs in text/plain format.

        Examples:
            >>> session.logs(id="hjko98yghj")
            >>> session.logs(id=["hjko98yghj", "ikvp1jtp"])
        """
        if isinstance(id, str):
            id = [id]
        parameters: Dict[str, str] = {"view": "logs"}
        arguments: List[Any] = []
        for value in id:
            arguments.append({"url": self.server + "/" + value, "params": parameters})
        loop = get_event_loop()
        results = loop.run_until_complete(scale(self.session.get, arguments))
        responses: Dict[str, str] = {}
        for index, identity in enumerate(id):
            responses[identity] = ""
            try:
                results[index].raise_for_status()
                responses[identity] = results[index].text
            except HTTPError as err:
                log.error(err)
        return responses

    def create(
        self,
        name: str,
        image: str,
        cores: int = 2,
        ram: int = 4,
        kind: str = "headless",
        gpu: Optional[int] = None,
        cmd: Optional[str] = None,
        args: Optional[str] = None,
        env: Dict[str, Any] = {},
        replicas: int = 1,
    ) -> List[str]:
        """Launch a skaha session.

        Args:
            name (str): A unique name for the session.
            image (str): Container image to use for the session.
            cores (int, optional): Number of cores. Defaults to 2.
            ram (int, optional): Amount of RAM (GB). Defaults to 4.
            kind (str, optional): Type of skaha session. Defaults to "headless".
            cmd (Optional[str], optional): Command to run. Defaults to None.
            args (Optional[str], optional): Arguments to the command. Defaults to None.
            env (Optional[Dict[str, Any]], optional): Environment variables to inject.
                Defaults to None.
            replicas (int, optional): Number of sessions to launch. Defaults to 1.

        Notes:
            The name of the session suffixed with the replica number. eg. test-1, test-2
            Each container will have the following environment variables injected:
                * REPLICA_ID - The replica number
                * REPLICA_COUNT - The total number of replicas

        Returns:
            List[str]: A list of session IDs for the launched sessions.

        Examples:
            >>> session.create(
                    name="test",
                    image='images.canfar.net/skaha/terminal:1.1.1',
                    cores=2,
                    ram=8,
                    kind="headless",
                    cmd="env",
                    env={"TEST": "test"},
                    replicas=2,
                )
            >>> ["hjko98yghj", "ikvp1jtp"]
        """
        specification: CreateSpec = CreateSpec(
            name=name,
            image=image,
            cores=cores,
            ram=ram,
            kind=kind,
            gpu=gpu,
            cmd=cmd,
            args=args,
            env=env,
            replicas=replicas,
        )
        data: Dict[str, Any] = specification.dict(exclude_none=True)
        log.info(f"Creating {replicas} session(s) with parameters:")
        log.info(data)
        payload: List[Tuple[str, Any]] = []
        arguments: List[Any] = []
        for replica in range(replicas):
            data["name"] = name + "-" + str(replica + 1)
            data["env"].update({"REPLICA_ID": str(replica + 1)})
            data["env"].update({"REPLICA_COUNT": str(replicas)})
            log.debug(f"Replica Data: {data}")
            payload = convert.dict_to_tuples(data)
            arguments.append({"url": self.server, "params": payload})
        loop = get_event_loop()
        results = loop.run_until_complete(scale(self.session.post, arguments))
        responses: List[str] = []
        for response in results:
            try:
                response.raise_for_status()
                responses.append(response.text.rstrip("\r\n"))
            except HTTPError as err:
                log.error(err)
        return responses

    def destroy(self, id: Union[str, List[str]]) -> Dict[str, bool]:
        """Destroy skaha session[s].

        Args:
            id (Union[str, List[str]]): Session ID[s].

        Returns:
            Dict[str, bool]: A dictionary of session IDs
            and a bool indicating if the session was destroyed.

        Examples:
            >>> session.destroy(id="hjko98yghj")
            >>> session.destroy(id=["hjko98yghj", "ikvp1jtp"])
        """
        if isinstance(id, str):
            id = [id]
        arguments: List[Any] = []
        for value in id:
            arguments.append({"url": self.server + "/" + value})
        loop = get_event_loop()
        results = loop.run_until_complete(scale(self.session.delete, arguments))
        responses: Dict[str, bool] = {}
        for index, identity in enumerate(id):
            try:
                results[index].raise_for_status()
                responses[identity] = True
            except HTTPError as err:
                log.error(err)
                responses[identity] = False
        return responses
