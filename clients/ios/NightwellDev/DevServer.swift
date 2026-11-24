import Foundation

/// Nightwell Dev can run on a home server or Railway. Never send the same bearer
/// token to a different server. Only HTTPS origins are accepted.
enum DevServer {
    static let homeOrigin = "https://dev.nightwell.fun"
    static let railwayOrigin = "https://nightwell-dev-web-production.up.railway.app"
    private static let preferencesKey = "nightwell.dev.server.origin"

    static var selectedOrigin: String {
        UserDefaults.standard.string(forKey: preferencesKey) ?? homeOrigin
    }

    static func validate(_ input: String) throws -> String {
        var raw = input.trimmingCharacters(in: .whitespacesAndNewlines)
        if !raw.contains("://") { raw = "https://" + raw }
        guard let parts = URLComponents(string: raw),
              parts.scheme?.lowercased() == "https",
              let host = parts.host, !host.isEmpty,
              parts.user == nil, parts.password == nil,
              parts.query == nil, parts.fragment == nil else {
            throw NetworkProblem(text: "Укажи адрес HTTPS-сервера, например https://dev.nightwell.fun")
        }
        let path = parts.path.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
        guard path.isEmpty || path == "api/v1" else {
            throw NetworkProblem(text: "Нужен адрес сайта без пути, либо с /api/v1/")
        }
        var origin = URLComponents()
        origin.scheme = "https"
        origin.host = host
        origin.port = parts.port
        guard let result = origin.url?.absoluteString.trimmingCharacters(in: CharacterSet(charactersIn: "/")),
              !result.isEmpty else {
            throw NetworkProblem(text: "Некорректный адрес сервера")
        }
        return result
    }

    static func save(_ origin: String) {
        UserDefaults.standard.set(origin, forKey: preferencesKey)
    }
}
