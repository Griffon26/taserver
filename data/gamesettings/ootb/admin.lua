local commands = {
    {
        name      = "NextMap",
        arguments = {
            {"MapId", Admin.Command.ArgumentType.Int},
        },
        func      = function (player, role, MapId)
            if Admin.Game.NextMap(MapId) then
                Admin.SendConsoleMessageToPlayer(player, "Set next map to " .. MapId)
            else
                Admin.SendConsoleMessageToPlayer(player, "Failed to set next map to " .. MapId)
            end
            
        end,
    },
    {
        name      = "StartMap",
        arguments = {},
        func      = function (player, role)
            Admin.Game.StartMap()
            Admin.SendConsoleMessageToPlayer(player, "Map started")
        end,
    },
    {
        name      = "EndMap",
        arguments = {},
        func      = function (player, role)
            Admin.Game.EndMap()
            Admin.SendConsoleMessageToPlayer(player, "Map ended")
        end,
    },
}

function doSetupRoles(roles)
    for cmdIdx, command in pairs(commands) do
        Admin.Command.define(command.name, command.arguments, command.func)
    end
    
    for roleIdx, role in pairs(roles) do
        Admin.Roles.add(role.name, role.password, role.canLua)
        for cmdIdx, cmdName in pairs(role.commands) do
            Admin.Roles.addAllowedCommand(role.name, cmdName)
        end
    end
end