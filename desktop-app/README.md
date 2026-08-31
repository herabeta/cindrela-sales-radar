# Cindrela Sales Radar — Standalone Foundation

This folder is the separate desktop-app foundation for the existing Cindrela Sales Radar web application.

## Safety rule
The production web app remains at the repository root. This desktop foundation is intentionally isolated under `desktop-app/` and is developed on the `standalone-foundation` branch first.

## Local Windows target
Recommended local working folder:

`C:\Cindrela\Sales-Radar-Desktop\`

## Current foundation

- Electron desktop shell
- Existing root `index.html` loaded inside a secure BrowserWindow
- External links opened through the OS browser
- Context isolation enabled
- Node integration disabled
- A local JSON database foundation stored in Electron `userData`
- IPC bridge prepared for future lead/deal/settings persistence
- Windows NSIS packaging configuration prepared

## Next phases

1. Build and install a local development copy on Windows.
2. Run the existing web workflows inside the desktop shell.
3. Migrate shared lead/pipeline storage to the local database bridge without changing business behavior.
4. Add contact intelligence and email/follow-up services behind secure APIs.
5. Add backup/export and update flow.
6. Build and test the final Windows installer.
