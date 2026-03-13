from engine_cli.domain import ServerInstance, TaskRun


class ServerInstanceLifecycleService:
    """Thin stub for server lifecycle orchestration."""

    def validate(self, server: ServerInstance) -> ServerInstance:
        raise NotImplementedError("Server validation is not implemented yet.")

    def start(self, server: ServerInstance) -> TaskRun:
        raise NotImplementedError("Server start is not implemented yet.")

    def stop(self, server: ServerInstance) -> TaskRun:
        raise NotImplementedError("Server stop is not implemented yet.")
