# FaceMatch for Mac — visual app version

## Open it without Terminal

Double-click **FaceMatch** on the Desktop, or open **FaceMatch.app** in your user's
Applications folder (`~/Applications`). A FaceMatch window opens with the existing
visual overview, photo comparison, registration and people directory.

The app starts its own local recognition service automatically. No Terminal window,
command typing, browser tab or manually entered address is required. Choose a JPG
or PNG with the normal Mac file picker. Your current database and photographs stay
in the existing project locations; thresholds and reference images are unchanged.

Use **FaceMatch → Quit FaceMatch**, Command-Q, or close its last window to quit.
The app stops only the service it started. An existing browser-mode instance is
unaffected. If a photo is still being processed, you can wait or explicitly quit.
You can keep the icon in the Dock using the Dock's normal “Keep in Dock” option.

## If it cannot open

- If macOS requests Documents access, review the prompt: the project and private
  photographs are stored there. You decide whether to allow the request.
- If the project moved, use **Choose FaceMatch Folder…** on the recovery screen.
- If files are only in iCloud, download the project locally in Finder and retry.
- The verified recognition environment must still exist. This local app uses
  `~/.venvs/facematch-university`, falling back to the project's `.venv`.
  The existing setup instructions remain available for restoring that environment.
- First recognition may need model weights and internet access if the cache is empty.

The app remembers a folder you explicitly choose. It does not copy your photographs
into the app bundle, upload them to a new service, or modify existing enrollment
records just by opening. A nonpersistent web view avoids saving session browser
state between launches. Network navigation is restricted to its own loopback service.

## Scope of this version

This is a native-window **Mac desktop version**, built locally for this machine.
It wraps the existing web interface in Apple's WKWebView and manages the local
Python process. It is not a self-contained Python/runtime/weights distribution:
it still needs the project folder and installed environment on this Mac. Moving
it to another Mac requires the documented setup. It is locally ad-hoc signed,
not a notarized App Store release. No public publishing or remote push was performed.
The previous submission ZIP is preserved as the earlier verified snapshot.

## Source and rebuilding (developer instructions)

- `desktop/FaceMatch.swift`: native window, menus, file picker and service lifecycle.
- `desktop/MakeIcon.swift`: generated vector app icon.
- `scripts/build_mac_app.py`: compile, create the bundle, verify its local signature,
  and optionally install it with a Desktop shortcut.

On macOS with Apple Command Line Tools installed:

```bash
python3 scripts/build_mac_app.py --install --desktop-shortcut
```

Build outputs go under ignored `dist/`. Installation preserves an existing
FaceMatch.app as a timestamped previous-version app. An existing Desktop item of
the same name is not overwritten. Source files are suitable for Git; compiled
bundles, private data, environments and model weights are not source submissions.

## Verification

Native launch, directory loading/search, file-picker interaction, blank-image
rejection and owned-service shutdown are checked on this Mac before handover.
The existing application test suite remains a separate regression check; the new
native shell does not change recognition thresholds or evaluation metrics.

### Observed on 18 November 2026

- The installed app opens its own native window and automatically starts an owned
  loopback service on an available port. The five existing records load correctly.
- Directory filtering by ID works in the native window.
- The native JPG/PNG picker opens; selecting a generated blank PNG displays its
  preview and comparison rejects it with the expected no-face message.
- Command-Q stops that app's local service. Reopening the app starts a fresh service
  and reloads the same records. No other browser-mode server was running during the
  shutdown check, so coexistence shutdown was not separately exercised.
- Local code-signature verification and all 32 existing Python regression checks pass.
- No enrollment records, private photographs, thresholds or reference images were changed.

The native shell uses [Apple's WKWebView](https://developer.apple.com/documentation/webkit/wkwebview).
