import AppKit
import WebKit
import UniformTypeIdentifiers

@MainActor
final class AppDelegate: NSObject, NSApplicationDelegate, WKNavigationDelegate, WKUIDelegate, WKScriptMessageHandler {
    private var window: NSWindow!
    private var web: WKWebView!
    private var cover: NSView!
    private var titleLabel: NSTextField!
    private var detailLabel: NSTextField!
    private var spinner: NSProgressIndicator!
    private var retryButton: NSButton!
    private var chooseButton: NSButton!
    private var backend: Process?
    private var outputBuffer = ""
    private var errorText = ""
    private var origin: URL?
    private var startupTimer: Timer?
    private var quitting = false
    private var processing = false
    private var startupID = UUID()

    func applicationDidFinishLaunching(_ notification: Notification) {
        makeMenu()
        makeWindow()
        NSApp.activate(ignoringOtherApps: true)
        startWorkspace()
    }

    private func makeMenu() {
        let menu = NSMenu()
        let appItem = NSMenuItem(); menu.addItem(appItem)
        let appMenu = NSMenu(); appItem.submenu = appMenu
        let about = NSMenuItem(title: "About FaceMatch", action: #selector(showAbout), keyEquivalent: "")
        about.target = self; appMenu.addItem(about)
        appMenu.addItem(.separator())
        appMenu.addItem(withTitle: "Hide FaceMatch", action: #selector(NSApplication.hide(_:)), keyEquivalent: "h")
        appMenu.addItem(.separator())
        appMenu.addItem(withTitle: "Quit FaceMatch", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        let editItem = NSMenuItem(); menu.addItem(editItem)
        let editMenu = NSMenu(title: "Edit"); editItem.submenu = editMenu
        for (title, selector, key) in [("Undo", Selector(("undo:")), "z"), ("Cut", #selector(NSText.cut(_:)), "x"), ("Copy", #selector(NSText.copy(_:)), "c"), ("Paste", #selector(NSText.paste(_:)), "v"), ("Select All", #selector(NSText.selectAll(_:)), "a")] {
            editMenu.addItem(withTitle: title, action: selector, keyEquivalent: key)
        }
        let viewItem = NSMenuItem(); menu.addItem(viewItem)
        let viewMenu = NSMenu(title: "View"); viewItem.submenu = viewMenu
        let home = NSMenuItem(title: "Home", action: #selector(goHome), keyEquivalent: "1"); home.target = self; viewMenu.addItem(home)
        let reload = NSMenuItem(title: "Reload", action: #selector(reloadPage), keyEquivalent: "r"); reload.target = self; viewMenu.addItem(reload)
        NSApp.mainMenu = menu
    }

    private func makeWindow() {
        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 1200, height: 850), styleMask: [.titled, .closable, .miniaturizable, .resizable], backing: .buffered, defer: false)
        window.title = "FaceMatch"
        window.minSize = NSSize(width: 820, height: 620)
        window.center()
        window.isReleasedWhenClosed = false
        let root = NSView(); window.contentView = root
        let config = WKWebViewConfiguration()
        config.websiteDataStore = .nonPersistent()
        config.userContentController.add(self, name: "faceMatchActivity")
        // Observe only our own controls to avoid quitting in the middle of enrollment.
        let activityScript = """
        document.addEventListener('DOMContentLoaded', () => {
          let last = false;
          const check = () => {
            const busy = ['recognize-submit','register-submit'].some(id => {
              const text = document.getElementById(id)?.textContent || '';
              return text.startsWith('Comparing') || text.startsWith('Registering');
            });
            if (busy !== last) { last = busy; window.webkit.messageHandlers.faceMatchActivity.postMessage(busy); }
          };
          new MutationObserver(check).observe(document.body, {childList:true,subtree:true,characterData:true});
          check();
        });
        """
        config.userContentController.addUserScript(WKUserScript(source: activityScript, injectionTime: .atDocumentStart, forMainFrameOnly: true))
        web = WKWebView(frame: .zero, configuration: config)
        web.navigationDelegate = self; web.uiDelegate = self
        web.translatesAutoresizingMaskIntoConstraints = false
        root.addSubview(web)
        NSLayoutConstraint.activate([web.leadingAnchor.constraint(equalTo: root.leadingAnchor), web.trailingAnchor.constraint(equalTo: root.trailingAnchor), web.topAnchor.constraint(equalTo: root.topAnchor), web.bottomAnchor.constraint(equalTo: root.bottomAnchor)])
        cover = NSView(); cover.translatesAutoresizingMaskIntoConstraints = false
        cover.wantsLayer = true; cover.layer?.backgroundColor = NSColor.windowBackgroundColor.cgColor
        root.addSubview(cover)
        NSLayoutConstraint.activate([cover.leadingAnchor.constraint(equalTo: root.leadingAnchor), cover.trailingAnchor.constraint(equalTo: root.trailingAnchor), cover.topAnchor.constraint(equalTo: root.topAnchor), cover.bottomAnchor.constraint(equalTo: root.bottomAnchor)])
        spinner = NSProgressIndicator(); spinner.style = .spinning; spinner.controlSize = .large
        titleLabel = NSTextField(labelWithString: "Opening FaceMatch…"); titleLabel.font = .systemFont(ofSize: 29, weight: .semibold)
        detailLabel = NSTextField(wrappingLabelWithString: "Your photographs stay on this Mac.")
        detailLabel.font = .systemFont(ofSize: 15); detailLabel.textColor = .secondaryLabelColor; detailLabel.alignment = .center
        detailLabel.preferredMaxLayoutWidth = 480
        retryButton = NSButton(title: "Try Again", target: self, action: #selector(retry)); retryButton.bezelStyle = .rounded; retryButton.isHidden = true
        chooseButton = NSButton(title: "Choose FaceMatch Folder…", target: self, action: #selector(chooseProject)); chooseButton.bezelStyle = .rounded; chooseButton.isHidden = true
        let stack = NSStackView(views: [spinner, titleLabel, detailLabel, retryButton, chooseButton]); stack.orientation = .vertical; stack.spacing = 20; stack.translatesAutoresizingMaskIntoConstraints = false
        cover.addSubview(stack)
        NSLayoutConstraint.activate([stack.centerXAnchor.constraint(equalTo: cover.centerXAnchor), stack.centerYAnchor.constraint(equalTo: cover.centerYAnchor), stack.widthAnchor.constraint(lessThanOrEqualToConstant: 520), stack.leadingAnchor.constraint(greaterThanOrEqualTo: cover.leadingAnchor, constant: 30)])
        window.makeKeyAndOrderFront(nil)
    }

    private func projectFolder() -> URL? {
        let candidates = [UserDefaults.standard.string(forKey: "FaceMatchProjectFolder"), Bundle.main.object(forInfoDictionaryKey: "FaceMatchProjectPath") as? String, "~/Documents/FaceMatch"].compactMap { $0 }
        return candidates.map { URL(fileURLWithPath: ($0 as NSString).expandingTildeInPath) }.first {
            FileManager.default.fileExists(atPath: $0.appendingPathComponent("app/ui.py").path)
        }
    }

    private func startWorkspace() {
        stopBackend()
        quitting = false; processing = false; origin = nil; outputBuffer = ""; errorText = ""
        startupID = UUID(); let attempt = startupID
        cover.isHidden = false; titleLabel.stringValue = "Opening FaceMatch…"
        detailLabel.stringValue = "Your photographs stay on this Mac."
        retryButton.isHidden = true; chooseButton.isHidden = true; spinner.startAnimation(nil)
        guard let project = projectFolder() else {
            showFailure("Choose the FaceMatch project folder to open your workspace."); return
        }
        let home = FileManager.default.homeDirectoryForCurrentUser
        var candidates: [URL] = []
        if let custom = ProcessInfo.processInfo.environment["FACEMATCH_PYTHON"] { candidates.append(URL(fileURLWithPath: custom)) }
        candidates += [home.appendingPathComponent(".venvs/facematch-university/bin/python"), project.appendingPathComponent(".venv/bin/python")]
        guard let python = candidates.first(where: { FileManager.default.isExecutableFile(atPath: $0.path) }) else {
            showFailure("The FaceMatch recognition environment is missing. Restore the project’s verified environment, then choose Try Again."); return
        }
        let process = Process(); process.executableURL = python
        process.arguments = ["-B", "-u", project.appendingPathComponent("app/ui.py").path, "--port", "0", "--no-browser"]
        process.currentDirectoryURL = project
        var env = ProcessInfo.processInfo.environment
        // Keep the same private records as the existing project by default.
        if env["FACEMATCH_DATA_DIR"] == nil { env["FACEMATCH_DATA_DIR"] = project.path }
        env["PYTHONUNBUFFERED"] = "1"; env["PYTHONDONTWRITEBYTECODE"] = "1"
        process.environment = env
        let out = Pipe(); let errors = Pipe(); process.standardOutput = out; process.standardError = errors
        out.fileHandleForReading.readabilityHandler = { [weak self] handle in
            let data = handle.availableData
            if data.isEmpty { handle.readabilityHandler = nil; return }
            let value = String(decoding: data, as: UTF8.self)
            DispatchQueue.main.async { guard let self = self, self.startupID == attempt else { return }; self.receive(value) }
        }
        errors.fileHandleForReading.readabilityHandler = { [weak self] handle in
            let data = handle.availableData
            if data.isEmpty { handle.readabilityHandler = nil; return }
            let value = String(decoding: data, as: UTF8.self)
            DispatchQueue.main.async { guard let self = self, self.startupID == attempt else { return }; self.errorText = String((self.errorText + value).suffix(2000)) }
        }
        process.terminationHandler = { [weak self] finished in
            DispatchQueue.main.async {
                guard let self = self, self.backend === finished, !self.quitting else { return }
                self.showFailure("FaceMatch could not stay open. Check that the project and its recognition files are downloaded on this Mac, then try again.")
            }
        }
        backend = process
        do { try process.run() }
        catch { showFailure("FaceMatch could not open its recognition service. Choose your project folder and try again."); return }
        startupTimer = Timer.scheduledTimer(withTimeInterval: 60, repeats: false) { [weak self] _ in
            DispatchQueue.main.async {
                guard let self = self, self.startupID == attempt, self.origin == nil else { return }
                self.stopBackend()
                self.showFailure("Some project files may still be in iCloud. In Finder, download the FaceMatch folder locally, then try again.")
            }
        }
    }

    private func receive(_ text: String) {
        outputBuffer += text
        while let range = outputBuffer.range(of: "\n") {
            let line = String(outputBuffer[..<range.lowerBound]); outputBuffer.removeSubrange(..<range.upperBound)
            let prefix = "FaceMatch is running at "
            if line.hasPrefix(prefix), let url = URL(string: String(line.dropFirst(prefix.count))), url.scheme == "http", url.host == "127.0.0.1", let port = url.port, port > 0 {
                origin = url; startupTimer?.invalidate(); web.load(URLRequest(url: url))
            }
        }
        outputBuffer = String(outputBuffer.suffix(4000))
    }

    private func showFailure(_ detail: String) {
        startupTimer?.invalidate(); spinner.stopAnimation(nil); cover.isHidden = false
        titleLabel.stringValue = "Let’s reopen your workspace"
        detailLabel.stringValue = detail; retryButton.isHidden = false; chooseButton.isHidden = false
    }

    private func stopBackend() {
        startupTimer?.invalidate()
        guard let process = backend else { return }
        backend = nil
        if process.isRunning {
            process.interrupt()
            for _ in 0..<20 { if !process.isRunning { break }; Thread.sleep(forTimeInterval: 0.05) }
            if process.isRunning { process.terminate() }
        }
    }

    @objc private func retry() { startWorkspace() }
    @objc private func chooseProject() {
        let picker = NSOpenPanel(); picker.title = "Choose your FaceMatch project folder"; picker.canChooseFiles = false; picker.canChooseDirectories = true; picker.allowsMultipleSelection = false
        if picker.runModal() == .OK, let url = picker.url {
            guard FileManager.default.fileExists(atPath: url.appendingPathComponent("app/ui.py").path) else {
                showFailure("That folder does not contain the FaceMatch application. Please choose your project folder."); return
            }
            UserDefaults.standard.set(url.path, forKey: "FaceMatchProjectFolder"); startWorkspace()
        }
    }
    @objc private func goHome() { if let url = origin { web.load(URLRequest(url: url)) } }
    @objc private func reloadPage() { web.reload() }
    @objc private func showAbout() {
        NSApp.orderFrontStandardAboutPanel(options: [.applicationName: "FaceMatch", .applicationVersion: "1.1", .credits: NSAttributedString(string: "Local academic face-comparison prototype.\nPossible matches are not proof of identity.")])
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) { cover.isHidden = true; spinner.stopAnimation(nil) }
    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) { showFailure("The workspace could not open. Choose Try Again to reconnect.") }
    func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        guard let url = navigationAction.request.url else { decisionHandler(.cancel); return }
        if url.absoluteString == "about:blank" || (url.scheme == origin?.scheme && url.host == origin?.host && url.port == origin?.port) { decisionHandler(.allow) }
        else { decisionHandler(.cancel) }
    }
    func webView(_ webView: WKWebView, runOpenPanelWith parameters: WKOpenPanelParameters, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping ([URL]?) -> Void) {
        let picker = NSOpenPanel(); picker.allowedContentTypes = [.jpeg, .png]; picker.canChooseDirectories = false; picker.canChooseFiles = true; picker.allowsMultipleSelection = false
        picker.beginSheetModal(for: window) { result in completionHandler(result == .OK ? picker.urls : nil) }
    }
    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        guard message.frameInfo.isMainFrame, message.frameInfo.securityOrigin.host == "127.0.0.1", message.frameInfo.securityOrigin.port == origin?.port else { return }
        if let value = message.body as? Bool { processing = value }
    }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
    func applicationShouldTerminate(_ sender: NSApplication) -> NSApplication.TerminateReply {
        if processing {
            let alert = NSAlert(); alert.messageText = "A photograph is still being processed"
            alert.informativeText = "Wait for the result before closing FaceMatch. Quitting now interrupts this operation."
            alert.addButton(withTitle: "Keep FaceMatch Open"); alert.addButton(withTitle: "Quit Anyway")
            if alert.runModal() == .alertFirstButtonReturn { return .terminateCancel }
        }
        quitting = true; stopBackend(); return .terminateNow
    }
}

@main
struct FaceMatchMain {
    @MainActor static func main() {
        let application = NSApplication.shared
        let delegate = AppDelegate()
        application.delegate = delegate
        application.setActivationPolicy(.regular)
        withExtendedLifetime(delegate) { application.run() }
    }
}
