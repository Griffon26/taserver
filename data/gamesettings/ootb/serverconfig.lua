-- TAMods-Server configuration can be placed in this file
-- You can read about the configuration language at: https://www.tamods.org/docs/doc_srv_api_overview.html

ServerSettings.Description = "My Custom OOTB Server"
ServerSettings.Motd = "This is my OOTB server"
-- ServerSettings.Password = "some-password"
ServerSettings.GameSettingMode = ServerSettings.GameSettingModes.OOTB

-- Basic Access Control, see https://www.tamods.org/docs/doc_srv_api_admin.html for more
-- Admin.Roles.add("admin", "somepasswordyouchoose", true)

ServerSettings.MutuallyExclusiveItems.add("Light", "BXT1", "Light", "Thrust Pack")
ServerSettings.MutuallyExclusiveItems.add("Light", "BXT1A", "Light", "Thrust Pack")
ServerSettings.MutuallyExclusiveItems.add("Light", "Phase Rifle", "Light", "Thrust Pack")
ServerSettings.MutuallyExclusiveItems.add("Light", "SAP20", "Light", "Thrust Pack")

ServerSettings.MutuallyExclusiveItems.add("Light", "BXT1", "Light", "Stealth Pack")
ServerSettings.MutuallyExclusiveItems.add("Light", "BXT1A", "Light", "Stealth Pack")
ServerSettings.MutuallyExclusiveItems.add("Light", "Phase Rifle", "Light", "Stealth Pack")
ServerSettings.MutuallyExclusiveItems.add("Light", "SAP20", "Light", "Stealth Pack")

ServerSettings.MutuallyExclusiveItems.add("Light", "BXT1", "Light", "Light Utility Pack")
ServerSettings.MutuallyExclusiveItems.add("Light", "BXT1A", "Light", "Light Utility Pack")
ServerSettings.MutuallyExclusiveItems.add("Light", "Phase Rifle", "Light", "Light Utility Pack")
ServerSettings.MutuallyExclusiveItems.add("Light", "SAP20", "Light", "Light Utility Pack")

-- Some other settings you might need, just uncomment those lines
-- If you need more settings, check the documentation at : https://www.tamods.org/docs/doc_srv_api_serverconfig.html

-- ServerSettings.WarmupTime = 60
-- ServerSettings.FriendlyFire = true
-- ServerSettings.CTFCapLimit = 7
-- ServerSettings.BannedItems.add("Light", "BXT1")


-- The default map rotation is: Katabatic, ArxNovena, DangerousCrossing, Crossfire, Drydock, Terminus, Sunstar
-- You can override the default map rotation by uncommenting any of the maps below.

-- ServerSettings.MapRotation.add(Maps.CTF.ArxNovena)
-- ServerSettings.MapRotation.add(Maps.CTF.BellaOmega)
-- ServerSettings.MapRotation.add(Maps.CTF.Blueshift)
-- ServerSettings.MapRotation.add(Maps.CTF.CanyonCrusade)
-- ServerSettings.MapRotation.add(Maps.CTF.Crossfire)
-- ServerSettings.MapRotation.add(Maps.CTF.DangerousCrossing)
-- ServerSettings.MapRotation.add(Maps.CTF.Drydock)
-- ServerSettings.MapRotation.add(Maps.CTF.Hellfire)
-- ServerSettings.MapRotation.add(Maps.CTF.IceCoaster)
-- ServerSettings.MapRotation.add(Maps.CTF.Katabatic)
-- ServerSettings.MapRotation.add(Maps.CTF.Perdition)
-- ServerSettings.MapRotation.add(Maps.CTF.Permafrost)
-- ServerSettings.MapRotation.add(Maps.CTF.Raindance)
-- ServerSettings.MapRotation.add(Maps.CTF.Stonehenge)
-- ServerSettings.MapRotation.add(Maps.CTF.Sunstar)
-- ServerSettings.MapRotation.add(Maps.CTF.Tartarus)
-- ServerSettings.MapRotation.add(Maps.CTF.TempleRuins)
-- ServerSettings.MapRotation.add(Maps.CTF.Terminus)
