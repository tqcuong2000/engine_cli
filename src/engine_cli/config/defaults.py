DEFAULT_SETTINGS: dict[str, object] = {
    "default_agent_profiles": {
        "base": "base-default",
        "server": "server-default",
        "datapack": "datapack-default",
    },
    "agent_profiles": [
        {
            "agent_profile_id": "base-default",
            "name": "Base Assistant",
            "mode": "base",
            "agent_kind": "system_assistant",
        },
        {
            "agent_profile_id": "server-default",
            "name": "Server Ops",
            "mode": "server",
            "agent_kind": "server_ops",
        },
        {
            "agent_profile_id": "datapack-default",
            "name": "Datapack Dev",
            "mode": "datapack",
            "agent_kind": "datapack_dev",
        },
    ],
}
