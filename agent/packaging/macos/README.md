# macOS pkg Packaging (Outline)

1. Build the binary for darwin.
2. Place config in `/Library/Application Support/Eventsec/agent.yml`.
3. Install launchd plist `com.eventsec.agent.plist` in `/Library/LaunchDaemons`.

Unsigned pkg example:

```bash
pkgbuild --root payload --identifier com.eventsec.agent --version 1.0.0 eventsec-agent.pkg
```

For notarization, sign and notarize with Apple Developer ID certificates.
