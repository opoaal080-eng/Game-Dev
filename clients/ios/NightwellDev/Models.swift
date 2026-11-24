import Foundation

struct APIUser: Codable, Identifiable {
    let id: Int
    let username: String
    let name: String
    let role: String
    let can_write: Bool
    let job_title: String?
}
struct AuthReply: Decodable { let token: String; let user: APIUser }
struct MeReply: Decodable { let user: APIUser }
struct CountSummary: Decodable { let posts: Int; let tasks: Int; let files: Int; let members: Int }
struct DashboardReply: Decodable {
    let counts: CountSummary
    let latest_posts: [DevPost]
    let active_tasks: [DevTask]
    let projects: [DevProject]
}
struct ItemReply<T: Decodable>: Decodable { let item: T }
struct ItemsReply<T: Decodable>: Decodable { let items: [T] }
struct DevProject: Codable, Identifiable, Hashable {
    let id: Int
    let name: String
    let slug: String
    let description: String
}
struct DevPost: Codable, Identifiable {
    let id: Int
    let project_id: Int
    let project: String
    let title: String
    let body: String
    let kind: String
    let status: String
    let pinned: Bool
    let author: String
    let author_id: Int
    let updated_at: String
    let content_mode: String?
    let code_language: String?
}
struct DevTask: Codable, Identifiable {
    let id: Int
    let project_id: Int
    let project: String
    let title: String
    let description: String
    let status: String
    let priority: String
    let assignee: String?
    let assignee_id: Int?
    let created_by_id: Int
    let due_date: String?
}
struct DevAsset: Codable, Identifiable {
    let id: Int
    let project_id: Int
    let title: String
    let original_name: String
    let description: String
    let size: Int
    let uploader: String
    let download_path: String
}
struct GameInfo: Codable {
    let project_id: Int
    let project: String
    let title: String
    let genre: String
    let tagline: String
    let setting: String
    let story: String
    let gameplay: String
    let themes: String
    let universe: String
    let platforms: String
    let engine: String
    let development_status: String
    let audience: String
    let notes: String
}
struct StoryEvent: Codable, Identifiable {
    let id: Int
    let project_id: Int
    let chapter: String
    let title: String
    let kind: String
    let order: Int
    let timeline: String
    let location: String
    let participants: String
    let summary: String
    let description: String
    let consequences: String
    let spoiler: Bool
}
struct StoryCharacter: Codable, Identifiable {
    let id: Int
    let project_id: Int
    let name: String
    let role: String
    let faction: String
    let bio: String
    let motivation: String
    let notes: String
    let order: Int
}
struct BibleReply: Decodable {
    let info: GameInfo
    let events: [StoryEvent]
    let characters: [StoryCharacter]
}
struct APIErrorReply: Decodable { let error: String }
