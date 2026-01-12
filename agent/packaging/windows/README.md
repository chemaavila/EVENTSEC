# Windows MSI Packaging (Outline)

Use WiX Toolset to build an MSI that installs:
- `eventsec-agent.exe` into `Program Files\Eventsec\`
- config into `ProgramData\Eventsec\agent.yml`
- service registration (StartType=auto)

Example WiX snippet (outline only):

```xml
<ServiceInstall Id="EventsecAgentService"
    Name="EventsecAgent"
    DisplayName="EVENTSEC Agent"
    Description="EVENTSEC endpoint telemetry agent"
    Start="auto"
    Type="ownProcess"
    ErrorControl="normal" />
```

Ensure admin consent during install. Uninstall removes service and files.
