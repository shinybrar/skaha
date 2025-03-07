"""Skaha Headless Session."""

import asyncio
from typing import Any, Dict, List, Optional, Tuple, Union

from httpx import HTTPError, Response

from skaha.client import SkahaClient
from skaha.models import KINDS, STATUS, VIEW
from skaha.utils import build, logs

log = logs.get_logger(__name__)


class Session(SkahaClient):
    """Skaha Session Management Client.

    This class provides methods to manage sessions in the Skaha system,
    including fetching session details, creating new sessions,
    retrieving logs, and destroying existing sessions.

    Args:
        SkahaClient (SkahaClient): Base HTTP client for making API requests.

    Examples:
        >>> from skaha.session import Session
        >>> session = Session(
                timeout=120,
                concurrency=100, # <--- Has no effect on the sync client
                loglevel=40,
            )
    """

    def fetch(
        self,
        kind: Optional[KINDS] = None,
        status: Optional[STATUS] = None,
        view: Optional[VIEW] = None,
    ) -> List[Dict[str, str]]:
        """List open sessions for the user.

        Args:
            kind (Optional[KINDS], optional): Session kind. Defaults to None.
            status (Optional[STATUS], optional): Session status. Defaults to None.
            view (Optional[VIEW], optional): Session view level. Defaults to None.

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
        """
        parameters: Dict[str, Any] = build.fetch_parameters(kind, status, view)
        response: Response = self.client.get(url="session", params=parameters)
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
            {'instances': {
             'session': 88, 'desktopApp': 30, 'headless': 0, 'total': 118},
             'cores': {'requestedCPUCores': 377,
             'coresAvailable': 960,
             'maxCores': {'cores': 32, 'withRam': '147Gi'}},
             'ram': {'maxRAM': {'ram': '226Gi', 'withCores': 32}}}
        """
        parameters = {"view": "stats"}
        response: Response = self.client.get("session", params=parameters)
        response.raise_for_status()
        return response.json()

    def info(self, ids: Union[List[str], str]) -> List[Dict[str, Any]]:
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
        if isinstance(ids, str):
            ids = [ids]
        parameters: Dict[str, str] = {"view": "event"}
        results: List[Dict[str, Any]] = []
        for value in ids:
            try:
                response: Response = self.client.get(
                    url=f"session/{value}", params=parameters
                ).raise_for_status()
                results.append(response.json())
            except HTTPError as err:
                log.error(err)
        return results

    def logs(
        self, ids: Union[List[str], str], verbose: bool = False
    ) -> Optional[Dict[str, str]]:
        """Get logs from a session[s].

        Args:
            ids (Union[List[str], str]): Session ID[s].
            verbose (bool, optional): Print logs to stdout. Defaults to False.

        Returns:
            Dict[str, str]: Logs in text/plain format.

        Examples:
            >>> session.logs(id="hjko98yghj")
            >>> session.logs(id=["hjko98yghj", "ikvp1jtp"])
        """
        if isinstance(ids, str):
            ids = [ids]
        parameters: Dict[str, str] = {"view": "logs"}
        results: Dict[str, str] = {}

        for value in ids:
            try:
                response: Response = self.client.get(
                    url=f"session/{value}", params=parameters
                ).raise_for_status()
                results[value] = response.text
            except HTTPError as err:
                log.error(err)

        if verbose:
            for key, value in results.items():
                log.info("Session ID: %s\n", key)
                logs.stdout(value)
            return None

        return results

    def create(
        self,
        name: str,
        image: str,
        cores: int = 2,
        ram: int = 4,
        kind: KINDS = "headless",
        gpu: Optional[int] = None,
        cmd: Optional[str] = None,
        args: Optional[str] = None,
        env: Optional[Dict[str, Any]] = None,
        replicas: int = 1,
    ) -> List[str]:
        """Launch a skaha session.

        Args:
            name (str): A unique name for the session.
            image (str): Container image to use for the session.
            cores (int, optional): Number of cores. Defaults to 2.
            ram (int, optional): Amount of RAM (GB). Defaults to 4.
            kind (str, optional): Type of skaha session. Defaults to "headless".
            gpu (Optional[int], optional): Number of GPUs. Defaults to None.
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
            >>> from skaha.session import Session
            >>> session = Session()
            >>> session.create(
                    name="test",
                    image='images.canfar.net/skaha/terminal:1.1.1',
                    cores=2,
                    ram=8,
                    gpu=1,
                    kind="headless",
                    cmd="env",
                    env={"TEST": "test"},
                    replicas=2,
                )
            >>> ["hjko98yghj", "ikvp1jtp"]
        """
        payloads = build.create_parameters(
            name, image, cores, ram, kind, gpu, cmd, args, env, replicas
        )
        results: List[str] = []
        log.info("Creating %d %s session[s].", replicas, kind)
        for payload in payloads:
            try:
                response: Response = self.client.post(url="session", params=payload)
                response.raise_for_status()
                results.append(response.text.rstrip("\r\n"))
            except HTTPError as err:
                log.error(err)
        return results

    def destroy(self, ids: Union[str, List[str]]) -> Dict[str, bool]:
        """Destroy skaha session[s].

        Args:
            ids (Union[str, List[str]]): Session ID[s].

        Returns:
            Dict[str, bool]: A dictionary of session IDs
            and a bool indicating if the session was destroyed.

        Examples:
            >>> from skaha.session import Session
            >>> session = Session()
            >>> session.destroy(id="hjko98yghj")
            >>> session.destroy(id=["hjko98yghj", "ikvp1jtp"])
        """
        if isinstance(ids, str):
            ids = [ids]
        results: Dict[str, bool] = {}
        for value in ids:
            try:
                response: Response = self.client.delete(url=f"session/{value}")
                response.raise_for_status()
                results[value] = True
            except HTTPError as err:
                log.error(err)
                results[value] = False
        return results

    def destroy_with(
        self, prefix: str, kind: KINDS = "headless", status: STATUS = "Succeeded"
    ) -> Dict[str, bool]:
        """Destroy skaha session[s] matching search criteria.

        Args:
            prefix (str): Prefix to match in the session name.
            kind (KINDS): Type of skaha session. Defaults to "headless".
            status (STATUS): Status of the session. Defaults to "Succeeded".


        Returns:
            Dict[str, bool]: A dictionary of session IDs
            and a bool indicating if the session was destroyed.

        Notes:
            The prefix is case-sensitive.
            This method is useful for destroying multiple sessions at once.

        Examples:
            >>> from skaha.session import Session
            >>> session = Session()
            >>> session.destroy_with(prefix="test")
            >>> session.destroy_with(prefix="test", kind="desktop")
            >>> session.destroy_with(prefix="test", kind="headless", status="Running")

        """
        sessions = self.fetch(kind=kind, status=status)
        ids: List[str] = []
        for session in sessions:
            if session["name"].startswith(prefix):
                ids.append(session["id"])
        return self.destroy(ids)


class AsyncSession(SkahaClient):
    """Asynchronous Skaha Session Management Client.

    This class provides methods to manage sessions in the Skaha system,
    including fetching session details, creating new sessions,
    retrieving logs, and destroying existing sessions.

    Args:
        SkahaClient (SkahaClient): Base HTTP client for making API requests.

    Examples:
        >>> from skaha.session import AsyncSession
        >>> session = AsyncSession(
                server="https://skaha.example.com",
                version="v1",
                token="token",
                timeout=30,
                concurrency=100,
                loglevel=40,
            )
    """

    async def fetch(
        self,
        kind: Optional[KINDS] = None,
        status: Optional[STATUS] = None,
        view: Optional[VIEW] = None,
    ) -> List[Dict[str, str]]:
        """List open sessions for the user.

        Args:
            kind (Optional[KINDS], optional): Session kind. Defaults to None.
            status (Optional[STATUS], optional): Session status. Defaults to None.
            view (Optional[VIEW], optional): Session view level. Defaults to None.

        Notes:
            By default, only the calling user's sessions are listed. If views is
            set to 'all', all user sessions are listed (with limited information).

        Returns:
            list: Sessions information.

        Examples:
            >>> from skaha.session import AsyncSession
            >>> session = AsyncSession()
            >>> await session.fetch(kind="notebook")
            [{'id': 'vl91sfzz',
            'userid': 'brars',
            'runAsUID': '166169204',
            'runAsGID': '166169204',
            'supplementalGroups': [34241,
            34337,
            35124,
            36227,
            1902365706,
            1454823273,
            1025424273],
            'appid': '<none>',
            'image': 'images-rc.canfar.net/skaha/skaha-notebook:22.09-test',
            'type': 'notebook',
            'status': 'Running',
            'name': 'notebook1',
            'startTime': '2025-03-05T21:48:29Z',
            'expiryTime': '2025-03-09T21:48:29Z',
            'connectURL': 'https://canfar.net/session/notebook/some/url',
            'requestedRAM': '8G',
            'requestedCPUCores': '2',
            'requestedGPUCores': '0',
            'ramInUse': '<none>',
            'gpuRAMInUse': '<none>',
            'cpuCoresInUse': '<none>',
            'gpuUtilization': '<none>'}]
        """
        parameters: Dict[str, Any] = build.fetch_parameters(kind, status, view)
        response: Response = await self.asynclient.get(url="session", params=parameters)
        response.raise_for_status()
        return response.json()

    async def stats(self) -> Dict[str, Any]:
        """Get statistics for the entire skaha cluster.

        Returns:
            Dict[str, Any]: Cluster statistics.

        Examples:
            >>> from skaha.session import AsyncSession
            >>> session = AsyncSession()
            >>> await session.stats()
            {'instances': {
             'session': 88, 'desktopApp': 30, 'headless': 0, 'total': 118},
             'cores': {'requestedCPUCores': 377,
             'coresAvailable': 960,
             'maxCores': {'cores': 32, 'withRam': '147Gi'}},
             'ram': {'maxRAM': {'ram': '226Gi', 'withCores': 32}}}
        """
        parameters = {"view": "stats"}
        response: Response = await self.asynclient.get("session", params=parameters)
        response.raise_for_status()
        return response.json()

    async def info(self, ids: Union[List[str], str]) -> List[Dict[str, Any]]:
        """Get information about session[s].

        Args:
            id (Union[List[str], str]): Session ID[s].

        Returns:
            Dict[str, Any]: Session information.

        Examples:
            >>> from skaha.session import AsyncSession
            >>> session = AsyncSession()
            >>> await session.info(session_id="hjko98yghj")
            >>> await session.info(id=["hjko98yghj", "ikvp1jtp"])
        """
        # Convert id to list if it is a string
        if isinstance(ids, str):
            ids = [ids]
        parameters: Dict[str, str] = {"view": "event"}
        results: List[Dict[str, Any]] = []
        tasks: List[Any] = []
        semaphore: asyncio.Semaphore = asyncio.Semaphore(self.concurrency)

        async def bounded(value: str) -> Dict[str, Any]:
            async with semaphore:
                response = await self.asynclient.get(
                    url=f"session/{value}", params=parameters
                )
                response.raise_for_status()
                return response.json()

        tasks = [bounded(value) for value in ids]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        for reply in responses:
            if isinstance(reply, Exception):
                log.error(reply)
            elif isinstance(reply, dict):
                results.append(reply)  # type: ignore
        return results

    async def logs(
        self, ids: Union[List[str], str], verbose: bool = False
    ) -> Optional[Dict[str, str]]:
        """Get logs from a session[s].

        Args:
            ids (Union[List[str], str]): Session ID[s].
            verbose (bool, optional): Print logs to stdout. Defaults to False.

        Returns:
            Dict[str, str]: Logs in text/plain format.

        Examples:
            >>> from skaha.session import AsyncSession
            >>> session = AsyncSession()
            >>> await session.logs(id="hjko98yghj")
            >>> await session.logs(id=["hjko98yghj", "ikvp1jtp"])
        """
        if isinstance(ids, str):
            ids = [ids]
        parameters: Dict[str, str] = {"view": "logs"}
        results: Dict[str, str] = {}

        semaphore: asyncio.Semaphore = asyncio.Semaphore(self.concurrency)
        tasks: List[Any] = []

        async def bounded(value: str) -> Tuple[str, str]:
            async with semaphore:
                response = await self.asynclient.get(
                    url=f"session/{value}", params=parameters
                )
                response.raise_for_status()
                return value, response.text

        tasks = [bounded(value) for value in ids]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        for reply in responses:
            if isinstance(reply, Exception):
                log.error(reply)
            elif isinstance(reply, tuple):
                results[reply[0]] = reply[1]

        # Print logs to stdout if verbose is set to True
        if verbose:
            for key, value in results.items():
                log.info("Session ID: %s\n", key)
                logs.stdout(value)
                return None
        return results

    async def create(
        self,
        name: str,
        image: str,
        cores: int = 2,
        ram: int = 4,
        kind: KINDS = "headless",
        gpu: Optional[int] = None,
        cmd: Optional[str] = None,
        args: Optional[str] = None,
        env: Optional[Dict[str, Any]] = None,
        replicas: int = 1,
    ) -> List[str]:
        """Launch a skaha session.

        Args:
            name (str): A unique name for the session.
            image (str): Container image to use for the session.
            cores (int, optional): Number of cores. Defaults to 2.
            ram (int, optional): Amount of RAM (GB). Defaults to 4.
            kind (str, optional): Type of skaha session. Defaults to "headless".
            gpu (Optional[int], optional): Number of GPUs. Defaults to None.
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
            >>> from skaha.session import AsyncSession
            >>> session = AsyncSession()
            >>> session.create(
                    name="test",
                    image='images.canfar.net/skaha/terminal:1.1.1',
                    cores=2,
                    ram=8,
                    gpu=1,
                    kind="headless",
                    cmd="env",
                    env={"TEST": "test"},
                    replicas=2,
                )
            >>> ["hjko98yghj", "ikvp1jtp"]
        """
        payloads: List[List[Tuple[str, Any]]] = build.create_parameters(
            name, image, cores, ram, kind, gpu, cmd, args, env, replicas
        )
        results: List[str] = []
        tasks: List[Any] = []
        semaphore: asyncio.Semaphore = asyncio.Semaphore(self.concurrency)

        async def bounded(parameters: List[Tuple[str, Any]]) -> Any:
            async with semaphore:
                response = await self.asynclient.post(url="session", params=parameters)
                response.raise_for_status()
                return response.text.rstrip("\r\n")

        for payload in payloads:
            tasks.append(bounded(payload))

        log.info("Creating {replicas} {kind} session[s].")
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        for reply in responses:
            if isinstance(reply, Exception):
                log.error(reply)
            elif isinstance(reply, str):
                results.append(reply)
        return results

    async def destroy(self, ids: Union[str, List[str]]) -> Dict[str, bool]:
        """Destroy skaha session[s].

        Args:
            ids (Union[str, List[str]]): Session ID[s].

        Returns:
            Dict[str, bool]: A dictionary of session IDs
            and a bool indicating if the session was destroyed.

        Examples:
            >>> from skaha.session import AsyncSession
            >>> session = AsyncSession()
            >>> await session.destroy(id="hjko98yghj")
            >>> await session.destroy(id=["hjko98yghj", "ikvp1jtp"])
        """
        if isinstance(ids, str):
            ids = [ids]
        results: Dict[str, bool] = {}
        semaphore: asyncio.Semaphore = asyncio.Semaphore(self.concurrency)
        tasks: List[Any] = []

        async def bounded(value: str) -> Tuple[str, bool]:
            async with semaphore:
                try:
                    response = await self.asynclient.delete(url=f"session/{value}")
                    response.raise_for_status()
                    return value, True
                except HTTPError as err:
                    log.error(err)
                    return value, False

        tasks = [bounded(value) for value in ids]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        for reply in responses:
            if isinstance(reply, tuple):
                results[reply[0]] = reply[1]
        return results

    async def destroy_with(
        self, prefix: str, kind: KINDS = "headless", status: STATUS = "Succeeded"
    ) -> Dict[str, bool]:
        """Destroy skaha session[s] matching search criteria.

        Args:
            prefix (str): Prefix to match in the session name.
            kind (KINDS): Type of skaha session. Defaults to "headless".
            status (STATUS): Status of the session. Defaults to "Succeeded".


        Returns:
            Dict[str, bool]: A dictionary of session IDs
            and a bool indicating if the session was destroyed.

        Notes:
            The prefix is case-sensitive.
            This method is useful for destroying multiple sessions at once.

        Examples:
            >>> from skaha.session import AsyncSession
            >>> session = AsyncSession()
            >>> await session.destroy_with(prefix="test")
            >>> await session.destroy_with(prefix="test", kind="desktop")
            >>> await session.destroy_with(prefix="car", kind="carta", status="Running")

        """
        ids: List[str] = []
        for session in await self.fetch(kind=kind, status=status):
            if session["name"].startswith(prefix):
                ids.append(session["id"])
        return await self.destroy(ids)
