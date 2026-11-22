import Foundation
import SwiftUI

// The player website has its own public editorial model. Never copy GameInfo,
// story events, characters or other private Nightwell Dev material into it.
struct AshfallPage: Codable {
    var is_published: Bool
    var title: String
    var eyebrow: String
    var tagline: String
    var introduction: String
    var story_teaser: String
    var world_description: String
    var feature_lines: String
    var genre: String
    var platforms: String
    var development_status: String
    var release_window: String
    var hero_image_url: String
    var trailer_url: String
    var screenshots: String
    var wishlist_url: String
    var community_url: String
    var telegram_url: String
    var contact_email: String
}

struct AshfallNews: Codable, Identifiable {
    let id: Int
    var title: String
    var summary: String
    var content: String
    var is_published: Bool
    let date: String
}

struct AshfallReply: Decodable {
    var page: AshfallPage
    var news: [AshfallNews]
    var can_write: Bool
}

struct AshfallNewsReply: Decodable {
    let item: AshfallNews
}

@MainActor
extension DevStore {
    func loadAshfallSite() async throws -> AshfallReply {
        try await fetch("player-site/")
    }

    func saveAshfallSite(_ page: AshfallPage) async throws {
        let data = try JSONEncoder().encode(page)
        guard let values = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw NetworkProblem(text: "Не удалось подготовить данные сайта")
        }
        let _: AshfallReply = try await fetch("player-site/", method: "PUT", json: values)
    }

    func saveAshfallNews(
        existingID: Int?,
        title: String,
        summary: String,
        content: String,
        isPublished: Bool
    ) async throws {
        let path = existingID.map { "player-site/news/\($0)/" } ?? "player-site/news/"
        let method = existingID == nil ? "POST" : "PATCH"
        let _: AshfallNewsReply = try await fetch(path, method: method, json: [
            "title": title, "summary": summary, "content": content,
            "is_published": isPublished,
        ])
    }
}

struct AshfallSiteScreen: View {
    @EnvironmentObject private var store: DevStore
    @State private var snapshot: AshfallReply?
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var showPageEditor = false
    @State private var showNewNews = false
    @State private var editingNews: AshfallNews?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                HeaderLabel(title: "Сайт ASHFALL.", caption: "NIGHTWELL STUDIO / ДЛЯ ИГРОКОВ")
                GlassCard {
                    VStack(alignment: .leading, spacing: 12) {
                        Label("Публичная информация", systemImage: "globe").font(.headline)
                        Text("Здесь только одобренный контент для игроков. Сюжетные документы, задачи и файлы команды остаются закрытыми.")
                            .font(.subheadline).foregroundStyle(.secondary)
                        Link(destination: URL(string: "https://afl.nightwell.fun/")!) {
                            Label("Открыть afl.nightwell.fun", systemImage: "arrow.up.right.square")
                        }
                        Link(destination: URL(string: "https://opoaal080-eng.github.io/Game-Dev/ashfall/")!) {
                            Label("Открыть GitHub Pages", systemImage: "arrow.up.right.square")
                        }.font(.footnote)
                    }
                }

                if let site = snapshot {
                    GlassCard {
                        VStack(alignment: .leading, spacing: 12) {
                            HStack {
                                Label(site.page.is_published ? "Опубликовано" : "Черновик",
                                      systemImage: site.page.is_published ? "checkmark.circle.fill" : "eye.slash")
                                    .font(.caption.bold())
                                    .foregroundStyle(site.page.is_published ? .green : .orange)
                                Spacer()
                                Text("ASHFALL").font(.caption2.bold()).foregroundStyle(.secondary)
                            }
                            Text(site.page.title).font(.title2.bold())
                            if !site.page.tagline.isEmpty {
                                Text(site.page.tagline).foregroundStyle(.secondary)
                            }
                            Text("Жанр: " + (site.page.genre.isEmpty ? "не указан" : site.page.genre))
                                .font(.subheadline)
                            Text("Платформы: " + (site.page.platforms.isEmpty ? "не объявлены" : site.page.platforms))
                                .font(.subheadline)
                            if site.can_write {
                                Button {
                                    showPageEditor = true
                                } label: {
                                    Label("Редактировать информацию и медиа", systemImage: "square.and.pencil")
                                        .font(.subheadline.bold())
                                }
                                .buttonStyle(.bordered)
                            }
                        }
                    }

                    HStack {
                        Text("Новости").font(.title2.bold())
                        Spacer()
                        if site.can_write {
                            Button {
                                showNewNews = true
                            } label: {
                                Label("Добавить", systemImage: "plus")
                            }.font(.subheadline.bold())
                        }
                    }
                    if site.news.isEmpty {
                        GlassCard {
                            Text("Пока нет новостей. Можно создать черновик и опубликовать его позже.")
                                .font(.subheadline).foregroundStyle(.secondary)
                        }
                    }
                    ForEach(site.news) { news in
                        GlassCard {
                            VStack(alignment: .leading, spacing: 11) {
                                HStack {
                                    Label(news.is_published ? "Опубликовано" : "Черновик",
                                          systemImage: news.is_published ? "checkmark.circle" : "pencil.circle")
                                        .font(.caption.bold())
                                        .foregroundStyle(news.is_published ? .green : .orange)
                                    Spacer()
                                    Text(news.date).font(.caption2).foregroundStyle(.secondary)
                                }
                                Text(news.title).font(.headline)
                                if !news.summary.isEmpty {
                                    Text(news.summary).font(.subheadline).foregroundStyle(.secondary)
                                }
                                if site.can_write {
                                    Button("Редактировать новость") {
                                        editingNews = news
                                    }.font(.subheadline.bold())
                                }
                            }
                        }
                    }
                    Text("Публикация сохраняется на сервере Nightwell Dev. Игрокам показываются только опубликованные материалы. GitHub Pages обновляет резервную копию по расписанию.")
                        .font(.footnote).foregroundStyle(.secondary)
                } else if isLoading {
                    ProgressView("Загружаем публикации ASHFALL…")
                        .frame(maxWidth: .infinity, alignment: .center)
                        .padding(22)
                }

                if let errorMessage {
                    Notice(text: errorMessage)
                    Button("Повторить загрузку") { Task { await reload() } }
                        .font(.subheadline.bold())
                }
            }
            .padding(18)
        }
        .background(Color(red: 0.035, green: 0.039, blue: 0.047))
        .navigationTitle("Сайт ASHFALL")
        .refreshable { await reload() }
        .task { if snapshot == nil { await reload() } }
        .sheet(isPresented: $showPageEditor) {
            if let page = snapshot?.page {
                AshfallPageEditor(page: page) { await reload() }
            }
        }
        .sheet(isPresented: $showNewNews) {
            AshfallNewsEditor(news: nil) { await reload() }
        }
        .sheet(item: $editingNews) { news in
            AshfallNewsEditor(news: news) { await reload() }
        }
    }

    private func reload() async {
        guard !isLoading else { return }
        isLoading = true
        defer { isLoading = false }
        do {
            snapshot = try await store.loadAshfallSite()
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

struct AshfallPageEditor: View {
    @EnvironmentObject private var store: DevStore
    @Environment(\.dismiss) private var dismiss
    @State private var page: AshfallPage
    @State private var saving = false
    @State private var errorMessage: String?
    let onSaved: () async -> Void

    init(page: AshfallPage, onSaved: @escaping () async -> Void) {
        _page = State(initialValue: page)
        self.onSaved = onSaved
    }

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    Toggle("Показывать сайт игрокам", isOn: $page.is_published)
                    Text(page.is_published
                         ? "После сохранения новые данные будут доступны в публичном API."
                         : "Черновик: контент страницы скрыт от игроков.")
                        .font(.footnote).foregroundStyle(.secondary)
                } header: { Text("Публикация") }

                Section("Название и анонс") {
                    TextField("Название игры", text: $page.title)
                    TextField("Надпись над названием", text: $page.eyebrow)
                    TextField("Слоган", text: $page.tagline)
                    TextField("Жанр", text: $page.genre)
                    TextField("Платформы", text: $page.platforms)
                    TextField("Стадия разработки", text: $page.development_status)
                    TextField("Период релиза", text: $page.release_window)
                }
                Section("Описание для игроков") {
                    multiline("Об игре", text: $page.introduction)
                    multiline("Завязка без спойлеров", text: $page.story_teaser)
                    multiline("Мир игры", text: $page.world_description)
                    multiline("Особенности, по одной на строку", text: $page.feature_lines)
                }
                Section("Медиа") {
                    TextField("Ссылка на обложку, HTTPS", text: $page.hero_image_url)
                        .textInputAutocapitalization(.never).keyboardType(.URL)
                    TextField("Ссылка на трейлер, HTTPS", text: $page.trailer_url)
                        .textInputAutocapitalization(.never).keyboardType(.URL)
                    multiline("Скриншоты, по одной HTTPS-ссылке на строку", text: $page.screenshots)
                }
                Section("Ссылки и контакты") {
                    TextField("Страница игры", text: $page.wishlist_url)
                        .textInputAutocapitalization(.never).keyboardType(.URL)
                    TextField("Сообщество", text: $page.community_url)
                        .textInputAutocapitalization(.never).keyboardType(.URL)
                    TextField("Telegram", text: $page.telegram_url)
                        .textInputAutocapitalization(.never).keyboardType(.URL)
                    TextField("Email", text: $page.contact_email)
                        .textInputAutocapitalization(.never).keyboardType(.emailAddress)
                }
                if let errorMessage {
                    Section { Notice(text: errorMessage) }
                }
            }
            .navigationTitle("Редактор ASHFALL")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Закрыть") { dismiss() }.disabled(saving)
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Сохранить") { Task { await save() } }
                        .disabled(saving || page.title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }
            }
        }
    }

    private func multiline(_ title: String, text: Binding<String>) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title).font(.footnote).foregroundStyle(.secondary)
            TextEditor(text: text).frame(minHeight: 95)
        }
    }

    private func save() async {
        saving = true
        defer { saving = false }
        do {
            try await store.saveAshfallSite(page)
            await onSaved()
            dismiss()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

struct AshfallNewsEditor: View {
    @EnvironmentObject private var store: DevStore
    @Environment(\.dismiss) private var dismiss
    private let existingID: Int?
    private let onSaved: () async -> Void
    @State private var title: String
    @State private var summary: String
    @State private var content: String
    @State private var isPublished: Bool
    @State private var saving = false
    @State private var errorMessage: String?

    init(news: AshfallNews?, onSaved: @escaping () async -> Void) {
        existingID = news?.id
        self.onSaved = onSaved
        _title = State(initialValue: news?.title ?? "")
        _summary = State(initialValue: news?.summary ?? "")
        _content = State(initialValue: news?.content ?? "")
        _isPublished = State(initialValue: news?.is_published ?? false)
    }

    var body: some View {
        NavigationStack {
            Form {
                Section("Содержание") {
                    TextField("Заголовок", text: $title)
                    TextField("Краткое описание", text: $summary)
                    VStack(alignment: .leading, spacing: 7) {
                        Text("Полный текст").font(.footnote).foregroundStyle(.secondary)
                        TextEditor(text: $content).frame(minHeight: 190)
                    }
                }
                Section("Публикация") {
                    Toggle("Показать игрокам", isOn: $isPublished)
                    Text("Черновики видны только в Nightwell Dev.")
                        .font(.footnote).foregroundStyle(.secondary)
                }
                if let errorMessage {
                    Section { Notice(text: errorMessage) }
                }
            }
            .navigationTitle(existingID == nil ? "Новая новость" : "Изменить новость")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Закрыть") { dismiss() }.disabled(saving)
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Сохранить") { Task { await save() } }
                        .disabled(saving || title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }
            }
        }
    }

    private func save() async {
        saving = true
        defer { saving = false }
        do {
            try await store.saveAshfallNews(
                existingID: existingID, title: title,
                summary: summary, content: content, isPublished: isPublished
            )
            await onSaved()
            dismiss()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
