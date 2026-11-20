import Foundation
import Security
import SwiftUI

enum NightwellAPI {
    static let root = URL(string: "https://nightwell-dev-web-production.up.railway.app/api/v1/")!
}

struct NetworkProblem: LocalizedError {
    let text: String
    var errorDescription: String? { text }
}

enum SecureToken {
    private static let key = "fun.nightwell.dev.native-session"
    static func read() -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne,
        ]
        var result: CFTypeRef?
        guard SecItemCopyMatching(query as CFDictionary, &result) == errSecSuccess,
              let data = result as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }
    static func save(_ value: String?) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
        ]
        SecItemDelete(query as CFDictionary)
        guard let value else { return }
        let add: [String: Any] = query.merging([
            kSecValueData as String: Data(value.utf8),
            kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly,
        ]) { _, new in new }
        SecItemAdd(add as CFDictionary, nil)
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
    private var token: String?

    init() {
        token = SecureToken.read()
        signedIn = token != nil
        if signedIn { Task { await refresh() } }
    }

    private func url(_ path: String) -> URL {
        NightwellAPI.root.appendingPathComponent(path)
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
                SecureToken.save(nil)
                signedIn = false
            }
            let error = try? JSONDecoder().decode(APIErrorReply.self, from: data)
            throw NetworkProblem(text: error?.error ?? "Ошибка сервера: \(http.statusCode)")
        }
        return try JSONDecoder().decode(T.self, from: data)
    }

    func login(username: String, password: String) async {
        busy = true
        errorMessage = nil
        defer { busy = false }
        do {
            let reply: AuthReply = try await fetch("auth/login/", method: "POST", json: [
                "username": username, "password": password, "device_name": UIDevice.current.name,
            ])
            token = reply.token
            SecureToken.save(token)
            user = reply.user
            signedIn = true
            await refresh()
        } catch { errorMessage = error.localizedDescription }
    }

    func refresh() async {
        guard signedIn else { return }
        do {
            async let meRequest: MeReply = fetch("me/")
            async let projectRequest: ItemsReply<DevProject> = fetch("projects/")
            async let dashboardRequest: DashboardReply = fetch("dashboard/")
            async let postRequest: ItemsReply<DevPost> = fetch("posts/")
            async let taskRequest: ItemsReply<DevTask> = fetch("tasks/")
            async let fileRequest: ItemsReply<DevAsset> = fetch("files/")
            async let teamRequest: ItemsReply<APIUser> = fetch("team/")
            let (me, projs, home, p, t, f, users) = try await (
                meRequest, projectRequest, dashboardRequest, postRequest,
                taskRequest, fileRequest, teamRequest
            )
            user = me.user
            projects = projs.items
            dashboard = home
            posts = p.items
            tasks = t.items
            files = f.items
            team = users.items
            if currentProjectID == nil { currentProjectID = projects.first?.id }
            await loadBible()
            errorMessage = nil
        } catch { errorMessage = error.localizedDescription }
    }

    func loadBible() async {
        guard let currentProjectID else { return }
        do {
            bible = try await fetch("information/\(currentProjectID)/")
        } catch { errorMessage = error.localizedDescription }
    }

    func makePost(title: String, body: String, kind: String, status: String) async throws {
        guard let currentProjectID else { throw NetworkProblem(text: "Не выбран проект") }
        let _: ItemReply<DevPost> = try await fetch("posts/", method: "POST", json: [
            "project": currentProjectID, "title": title, "body": body,
            "kind": kind, "status": status, "pinned": false,
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
        var request = URLRequest(url: url(asset.download_path.replacingOccurrences(of: "/api/v1/", with: "")))
        request.setValue("Bearer " + (token ?? ""), forHTTPHeaderField: "Authorization")
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
            throw NetworkProblem(text: "Не удалось получить файл")
        }
        let name = URL(fileURLWithPath: asset.original_name).lastPathComponent
        let destination = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString + "-" + name)
        try data.write(to: destination)
        return destination
    }

    func logout() async {
        if signedIn {
            let _: [String: Bool]? = try? await fetch("auth/logout/", method: "POST")
        }
        token = nil
        SecureToken.save(nil)
        signedIn = false
        user = nil
        projects = []
        bible = nil
    }
}
