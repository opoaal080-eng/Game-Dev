import Foundation
import Security
import SwiftUI
import CryptoKit

enum NightwellAPI {
    static var root: URL { URL(string: DevServer.selectedOrigin + "/api/v1/")! }
}

struct NetworkProblem: LocalizedError {
    let text: String
    var errorDescription: String? { text }
}

enum SecureToken {
    private static let legacyKey = "fun.nightwell.dev.native-session"

    private static func key(for origin: String) -> String {
        let hash = SHA256.hash(data: Data(origin.utf8))
        let digest = hash.map { String(format: "%02x", $0) }.joined()
        return legacyKey + "." + String(digest.prefix(24))
    }

    private static func read(account: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: account,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]
        var value: CFTypeRef?
        guard SecItemCopyMatching(query as CFDictionary, &value) == errSecSuccess,
              let data = value as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }

    private static func remove(account: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: account
        ]
        SecItemDelete(query as CFDictionary)
    }

    static func read(for origin: String) -> String? {
        if let result = read(account: key(for: origin)) { return result }
        // Upgrade pre-v0.4 credentials only for their original Railway origin.
        if origin == DevServer.railwayOrigin, let legacy = read(account: legacyKey) {
            save(legacy, for: origin)
            remove(account: legacyKey)
            return legacy
        }
        return nil
    }

    static func save(_ value: String?, for origin: String) {
        let account = key(for: origin)
        remove(account: account)
        guard let value else { return }
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: account,
            kSecValueData as String: Data(value.utf8),
            kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
        ]
        SecItemAdd(query as CFDictionary, nil)
    }
}
@MainActor
final class DevStore: ObservableObject {
    @Published var signedIn = false
    @Published var user: APIUser?
    @Published var projects: [DevProject] = []
    @Published var dashboard: DashboardReply?
    @Published var posts: [DevPost] = []
    @Published var tasks: [DevTask] = []
    @Published var files: [DevAsset] = []
    @Published var team: [APIUser] = []
    @Published var bible: BibleReply?
    @Published var currentProjectID: Int?
    @Published var busy = false
    @Published var errorMessage: String?
    @Published var sectionErrors: [String: String] = [:]
    @Published var serverOrigin: String
    private var token: String?

    init() {
        let savedOrigin = DevServer.selectedOrigin
        serverOrigin = savedOrigin
        token = SecureToken.read(for: savedOrigin)
        signedIn = token != nil
        if signedIn { Task { await refresh() } }
    }

    private func url(_ path: String) -> URL {
        // URL.appendingPathComponent can escape embedded slashes in API paths.
        URL(string: serverOrigin + "/api/v1/" + path)!
    }

    func configureServer(_ address: String) throws {
        let normalized = try DevServer.validate(address)
        guard normalized != serverOrigin else { return }
        // Credentials are never reused across hosts.
        token = nil
        signedIn = false
        user = nil
        projects = []
        dashboard = nil
        posts = []
        tasks = []
        files = []
        team = []
        bible = nil
        currentProjectID = nil
        sectionErrors = [:]
        errorMessage = nil
        serverOrigin = normalized
        DevServer.save(normalized)
    }

    func fetch<T: Decodable>(_ path: String, method: String = "GET", json: [String: Any]? = nil) async throws -> T {
        var request = URLRequest(url: url(path))
        request.httpMethod = method
        request.timeoutInterval = 25
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        if let token { request.setValue("Bearer " + token, forHTTPHeaderField: "Authorization") }
        if let json {
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = try JSONSerialization.data(withJSONObject: json)
        }
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else { throw NetworkProblem(text: "Нет ответа от сервера") }
        guard (200..<300).contains(http.statusCode) else {
            if http.statusCode == 401 && path != "auth/login/" {
                token = nil
                SecureToken.save(nil, for: serverOrigin)
                signedIn = false
            }
            let error = try? JSONDecoder().decode(APIErrorReply.self, from: data)
            throw NetworkProblem(text: error?.error ?? "Ошибка сервера: \(http.statusCode)")
        }
        return try JSONDecoder().decode(T.self, from: data)
    }

    func login(username: String, password: String, serverAddress: String) async {
        busy = true
        errorMessage = nil
        defer { busy = false }
        do {
            try configureServer(serverAddress)
            let reply: AuthReply = try await fetch("auth/login/", method: "POST", json: [
                "username": username, "password": password, "device_name": UIDevice.current.name,
            ])
            token = reply.token
            SecureToken.save(token, for: serverOrigin)
            user = reply.user
            signedIn = true
            await refresh()
        } catch { errorMessage = error.localizedDescription }
    }

    private func attempt<T: Decodable>(_ path: String, as type: T.Type) async -> Result<T, Error> {
        do { return .success(try await fetch(path)) }
        catch { return .failure(error) }
    }

    func refresh() async {
        guard signedIn else { return }
        // Independent results: a failed request must not hide documents, files or tasks.
        async let meCall = attempt("me/", as: MeReply.self)
        async let projectsCall = attempt("projects/", as: ItemsReply<DevProject>.self)
        async let dashboardCall = attempt("dashboard/", as: DashboardReply.self)
        async let postsCall = attempt("posts/", as: ItemsReply<DevPost>.self)
        async let tasksCall = attempt("tasks/", as: ItemsReply<DevTask>.self)
        async let filesCall = attempt("files/", as: ItemsReply<DevAsset>.self)
        async let teamCall = attempt("team/", as: ItemsReply<APIUser>.self)

        let (me, projs, home, p, t, f, members) = await (
            meCall, projectsCall, dashboardCall, postsCall,
            tasksCall, filesCall, teamCall
        )
        guard signedIn else { return }
        var failures: [String: String] = [:]
        switch me {
        case .success(let reply): user = reply.user
        case .failure(let error): failures["Аккаунт"] = error.localizedDescription
        }
        switch projs {
        case .success(let reply):
            projects = reply.items
            if !projects.contains(where: { $0.id == currentProjectID }) {
                currentProjectID = projects.first?.id
                bible = nil
            }
        case .failure(let error): failures["Проекты"] = error.localizedDescription
        }
        switch home {
        case .success(let reply): dashboard = reply
        case .failure(let error): failures["Главная"] = error.localizedDescription
        }
        switch p {
        case .success(let reply): posts = reply.items
        case .failure(let error): failures["Документация"] = error.localizedDescription
        }
        switch t {
        case .success(let reply): tasks = reply.items
        case .failure(let error): failures["Задачи"] = error.localizedDescription
        }
        switch f {
        case .success(let reply): files = reply.items
        case .failure(let error): failures["Файлы"] = error.localizedDescription
        }
        switch members {
        case .success(let reply): team = reply.items
        case .failure(let error): failures["Команда"] = error.localizedDescription
        }
        sectionErrors = failures
        if currentProjectID != nil { await loadBible() }
        if !failures.isEmpty {
            errorMessage = "Не удалось загрузить: " + failures.keys.sorted().joined(separator: ", ")
        } else if sectionErrors["Информация"] == nil {
            errorMessage = nil
        }
    }

    func loadBible() async {
        guard let currentProjectID else { return }
        do {
            bible = try await fetch("information/\(currentProjectID)/")
            sectionErrors.removeValue(forKey: "Информация")
        } catch {
            sectionErrors["Информация"] = error.localizedDescription
            errorMessage = "Информация: " + error.localizedDescription
        }
    }

    func makePost(title: String, body: String, kind: String, status: String,
                  contentMode: String = "markdown", codeLanguage: String = "") async throws {
        guard let currentProjectID else { throw NetworkProblem(text: "Не выбран проект") }
        let _: ItemReply<DevPost> = try await fetch("posts/", method: "POST", json: [
            "project": currentProjectID, "title": title, "body": body,
            "kind": kind, "status": status, "pinned": false,
            "content_mode": contentMode, "code_language": codeLanguage,
        ])
        await refresh()
    }

    func makeTask(title: String, description: String, priority: String) async throws {
        guard let currentProjectID else { throw NetworkProblem(text: "Не выбран проект") }
        let _: ItemReply<DevTask> = try await fetch("tasks/", method: "POST", json: [
            "project": currentProjectID, "title": title, "description": description,
            "status": "todo", "priority": priority,
        ])
        await refresh()
    }

    func updateTask(_ task: DevTask, status: String) async throws {
        let _: ItemReply<DevTask> = try await fetch("tasks/\(task.id)/", method: "PATCH", json: [
            "project": task.project_id, "title": task.title, "description": task.description,
            "status": status, "priority": task.priority, "assignee": task.assignee_id as Any? ?? "",
            "due_date": task.due_date ?? "",
        ])
        await refresh()
    }

    func updateBible(_ dictionary: [String: String]) async throws {
        guard let currentProjectID else { throw NetworkProblem(text: "Не выбран проект") }
        let _: BibleReply = try await fetch("information/\(currentProjectID)/", method: "PUT", json: dictionary)
        await loadBible()
    }

    func addEvent(chapter: String, title: String, order: Int, summary: String) async throws {
        guard let currentProjectID else { throw NetworkProblem(text: "Не выбран проект") }
        let _: ItemReply<StoryEvent> = try await fetch("information/\(currentProjectID)/events/", method: "POST", json: [
            "chapter": chapter, "title": title, "order": order, "summary": summary, "kind": "main",
        ])
        await loadBible()
    }

    func addCharacter(name: String, role: String, bio: String) async throws {
        guard let currentProjectID else { throw NetworkProblem(text: "Не выбран проект") }
        let _: ItemReply<StoryCharacter> = try await fetch("information/\(currentProjectID)/characters/", method: "POST", json: [
            "name": name, "role": role, "bio": bio, "order": 1,
        ])
        await loadBible()
    }

    func download(_ asset: DevAsset) async throws -> URL {
        var request = URLRequest(url: url("files/\(asset.id)/download/"))
        request.timeoutInterval = 120
        request.setValue("Bearer " + (token ?? ""), forHTTPHeaderField: "Authorization")
        // Download directly to disk; 100 MB attachments must not be buffered in RAM.
        let (temporary, response) = try await URLSession.shared.download(for: request)
        guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
            throw NetworkProblem(text: "Не удалось скачать файл с \(serverOrigin)")
        }
        let name = URL(fileURLWithPath: asset.original_name).lastPathComponent
        let destination = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString + "-" + name)
        try FileManager.default.moveItem(at: temporary, to: destination)
        return destination
    }

    func uploadFile(at originalURL: URL) async throws {
        guard let currentProjectID else { throw NetworkProblem(text: "Не выбран проект") }
        let accessGranted = originalURL.startAccessingSecurityScopedResource()
        defer { if accessGranted { originalURL.stopAccessingSecurityScopedResource() } }
        let attributes = try FileManager.default.attributesOfItem(atPath: originalURL.path)
        if let size = attributes[.size] as? NSNumber, size.int64Value > 100 * 1024 * 1024 {
            throw NetworkProblem(text: "Максимальный размер файла 100 МБ")
        }
        let filename = originalURL.lastPathComponent
        let safeName = filename.replacingOccurrences(of: "\r", with: "_")
            .replacingOccurrences(of: "\n", with: "_")
            .replacingOccurrences(of: "\"", with: "_")
        let boundary = "NightwellDev-" + UUID().uuidString
        let multipart = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString + ".multipart")
        FileManager.default.createFile(atPath: multipart.path, contents: nil)
        defer { try? FileManager.default.removeItem(at: multipart) }
        let output = try FileHandle(forWritingTo: multipart)
        defer { try? output.close() }
        func write(_ value: String) throws {
            try output.write(contentsOf: Data(value.utf8))
        }
        try write("--\(boundary)\r\nContent-Disposition: form-data; name=\"project\"\r\n\r\n\(currentProjectID)\r\n")
        try write("--\(boundary)\r\nContent-Disposition: form-data; name=\"title\"\r\n\r\n\(String(filename.prefix(180)))\r\n")
        try write("--\(boundary)\r\nContent-Disposition: form-data; name=\"description\"\r\n\r\n\r\n")
        try write("--\(boundary)\r\nContent-Disposition: form-data; name=\"file\"; filename=\"\(safeName)\"\r\nContent-Type: application/octet-stream\r\n\r\n")
        let input = try FileHandle(forReadingFrom: originalURL)
        defer { try? input.close() }
        while let chunk = try input.read(upToCount: 1024 * 1024), !chunk.isEmpty {
            try output.write(contentsOf: chunk)
        }
        try write("\r\n--\(boundary)--\r\n")
        try output.close()
        var request = URLRequest(url: url("files/"))
        request.httpMethod = "POST"
        request.timeoutInterval = 180
        request.setValue("Bearer " + (token ?? ""), forHTTPHeaderField: "Authorization")
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        let (data, response) = try await URLSession.shared.upload(for: request, fromFile: multipart)
        guard let http = response as? HTTPURLResponse else {
            throw NetworkProblem(text: "Сервер не ответил")
        }
        guard (200..<300).contains(http.statusCode) else {
            let error = try? JSONDecoder().decode(APIErrorReply.self, from: data)
            throw NetworkProblem(text: error?.error ?? "Ошибка загрузки файла: \(http.statusCode)")
        }
        let reply = try JSONDecoder().decode(ItemReply<DevAsset>.self, from: data)
        files.insert(reply.item, at: 0)
        await refresh()
    }

    func logout() async {
        if signedIn {
            let _: [String: Bool]? = try? await fetch("auth/logout/", method: "POST")
        }
        token = nil
        SecureToken.save(nil, for: serverOrigin)
        signedIn = false
        user = nil
        projects = []
        dashboard = nil
        posts = []
        tasks = []
        files = []
        team = []
        bible = nil
        currentProjectID = nil
        sectionErrors = [:]
        errorMessage = nil
    }
}
