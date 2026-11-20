import SwiftUI

private enum Palette {
    static let background = Color(red: 0.035, green: 0.039, blue: 0.047)
    static let foreground = Color.white
    static let muted = Color(white: 0.65)
    static let tile = Color.white.opacity(0.065)
    static let border = Color.white.opacity(0.14)
}

struct GlassCard<Content: View>: View {
    let content: Content
    init(@ViewBuilder content: () -> Content) { self.content = content() }
    var body: some View {
        content.padding(18).frame(maxWidth: .infinity, alignment: .leading)
            .background(Palette.tile, in: RoundedRectangle(cornerRadius: 24, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 24).strokeBorder(Palette.border, lineWidth: 0.8))
    }
}

struct HeaderLabel: View {
    let title: String
    let caption: String
    var body: some View {
        VStack(alignment: .leading, spacing: 5) {
            Text(caption.uppercased())
                .font(.system(size: 10, weight: .bold, design: .rounded))
                .tracking(1.5).foregroundStyle(Palette.muted)
                .lineLimit(1).minimumScaleFactor(0.7)
            Text(title)
                .font(.system(size: 31, weight: .bold, design: .rounded))
                .tracking(-1.2).lineLimit(2).minimumScaleFactor(0.85)
        }.frame(maxWidth: .infinity, alignment: .leading)
    }
}

struct QuietButton: View {
    let title: String
    let symbol: String
    let action: () -> Void
    var body: some View {
        Button(action: action) { Label(title, systemImage: symbol).font(.system(size: 13, weight: .semibold)).foregroundStyle(.white).padding(12)
            .background(.white.opacity(0.10), in: Capsule()) }
    }
}

struct Notice: View {
    let text: String
    var body: some View {
        Text(text).font(.footnote).foregroundStyle(.orange).padding(12)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(.orange.opacity(0.10), in: RoundedRectangle(cornerRadius: 12))
    }
}

@main
struct NightwellDevApp: App {
    @StateObject private var store = DevStore()
    var body: some Scene {
        WindowGroup {
            ZStack {
                // Keep the canvas edge-to-edge; the views still respect the notch and home indicator.
                Palette.background.ignoresSafeArea()
                Group {
                    if store.signedIn { AppTabs() } else { LoginScreen() }
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .environmentObject(store)
            .preferredColorScheme(.dark)
            .tint(.white)
        }
    }
}

struct LoginScreen: View {
    @EnvironmentObject var store: DevStore
    @State private var username = ""
    @State private var password = ""
    var body: some View {
        GeometryReader { proxy in
            ScrollView {
                VStack(alignment: .leading, spacing: 22) {
                    HStack(spacing: 13) {
                        Text("N").font(.system(size: 27, weight: .black, design: .rounded))
                            .foregroundStyle(.black).frame(width: 46, height: 46).background(.white, in: RoundedRectangle(cornerRadius: 15))
                        VStack(alignment: .leading, spacing: 2) {
                            Text("NIGHTWELL").font(.system(size: 16, weight: .heavy)).tracking(2)
                            Text("DEVELOPER SPACE").font(.system(size: 9, weight: .medium)).tracking(1.8).foregroundStyle(Palette.muted)
                        }
                    }
                    Spacer(minLength: 38)
                    Text("Там, где\nсоздаются миры.")
                        .font(.system(size: 43, weight: .bold, design: .rounded)).tracking(-2)
                        .fixedSize(horizontal: false, vertical: true)
                    Text("Заметки, задачи, сюжет и файлы твоей команды в одном месте.")
                        .foregroundStyle(Palette.muted)
                    GlassCard {
                        VStack(alignment: .leading, spacing: 17) {
                            Label("Закрытый доступ", systemImage: "lock.shield").font(.system(size: 12, weight: .semibold)).foregroundStyle(Palette.muted)
                            Text("Вход в Nightwell Dev").font(.title2.bold())
                            TextField("Логин", text: $username).textInputAutocapitalization(.never).autocorrectionDisabled()
                                .textContentType(.username).padding(15).background(.white.opacity(0.07), in: RoundedRectangle(cornerRadius: 14))
                            SecureField("Пароль", text: $password).textContentType(.password).padding(15)
                                .background(.white.opacity(0.07), in: RoundedRectangle(cornerRadius: 14))
                            if let error = store.errorMessage { Notice(text: error) }
                            Button {
                                Task { await store.login(username: username, password: password) }
                            } label: {
                                HStack { Text("Войти"); Spacer(); Image(systemName: "arrow.right") }
                                    .font(.system(size: 15, weight: .bold)).foregroundStyle(.black)
                                    .padding(17).background(.white, in: RoundedRectangle(cornerRadius: 16))
                            }.disabled(username.isEmpty || password.isEmpty || store.busy)
                        }
                    }
                    Text("Регистрация отключена. Доступ выдаёт администратор.")
                        .font(.footnote).foregroundStyle(Palette.muted)
                    Spacer(minLength: 20)
                }
                .padding(24)
                .frame(minHeight: proxy.size.height, alignment: .topLeading)
            }
        }.background(Palette.background)
    }
}

struct AppTabs: View {
    var body: some View {
        // Short labels avoid colliding in the native iOS floating tab bar.
        // Every destination retains its full title in the navigation bar.
        TabView {
            NavigationStack { OverviewScreen() }
                .tabItem { Label("Главная", systemImage: "house.fill") }
            NavigationStack { GameInformationScreen() }
                .tabItem { Label("Инфо", systemImage: "info.circle.fill") }
            NavigationStack { JournalScreen() }
                .tabItem { Label("Дневник", systemImage: "book.pages") }
            NavigationStack { TasksScreen() }
                .tabItem { Label("Задачи", systemImage: "checklist") }
            NavigationStack { MoreScreen() }
                .tabItem { Label("Ещё", systemImage: "square.grid.2x2.fill") }
        }
        .toolbarBackground(.ultraThinMaterial, for: .tabBar)
    }
}

struct OverviewScreen: View {
    @EnvironmentObject var store: DevStore
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                HeaderLabel(title: "Твоя команда.", caption: "NIGHTWELL / РАБОЧЕЕ ПРОСТРАНСТВО")
                GlassCard {
                    VStack(alignment: .leading, spacing: 16) {
                        Text("СОЗДАВАЙТЕ МИРЫ ВМЕСТЕ").font(.caption2.bold()).tracking(1.5).foregroundStyle(Palette.muted)
                        Text("Все идеи.\nОдна история.").font(.system(size: 31, weight: .bold)).tracking(-1)
                        Text("От первых заметок до последней главы проекта.").font(.subheadline).foregroundStyle(Palette.muted)
                    }
                }
                if let counts = store.dashboard?.counts {
                    LazyVGrid(columns: [.init(.flexible()), .init(.flexible())], spacing: 12) {
                        countCard("Записи", counts.posts, "doc.text")
                        countCard("Задачи", counts.tasks, "checkmark.circle")
                        countCard("Файлы", counts.files, "folder")
                        countCard("Команда", counts.members, "person.2")
                    }
                }
                Text("Последние записи").font(.title3.bold()).padding(.top, 6)
                ForEach(store.dashboard?.latest_posts ?? []) { post in
                    NavigationLink { PostDetailsScreen(post: post) } label: {
                        GlassCard {
                            VStack(alignment: .leading, spacing: 7) {
                                Text(post.title).font(.headline).foregroundStyle(.white)
                                Text(post.project + " · " + post.author).font(.caption).foregroundStyle(Palette.muted)
                            }
                        }
                    }
                }
                Text("Активные задачи").font(.title3.bold())
                ForEach(store.dashboard?.active_tasks ?? []) { task in
                    GlassCard {
                        Text(task.title).font(.headline)
                        Text(task.project + " · " + task.status).font(.caption).foregroundStyle(Palette.muted)
                    }
                }
            }.padding(18)
        }
        .background(Palette.background)
        .navigationTitle("Обзор")
        .refreshable { await store.refresh() }
    }
    private func countCard(_ label: String, _ value: Int, _ icon: String) -> some View {
        GlassCard {
            HStack { Text(label).font(.caption).foregroundStyle(Palette.muted); Spacer(); Image(systemName: icon).foregroundStyle(Palette.muted) }
            Text("\(value)").font(.system(size: 35, weight: .bold, design: .rounded)).padding(.top, 11)
        }
    }
}

struct GameInformationScreen: View {
    @EnvironmentObject var store: DevStore
    @State private var showEdit = false
    @State private var showEvent = false
    @State private var showCharacter = false
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                HeaderLabel(title: "Информация.", caption: "GAME BIBLE / СЮЖЕТ И ВСЕЛЕННАЯ")
                if !store.projects.isEmpty {
                    Picker("Проект", selection: Binding(get: { store.currentProjectID ?? store.projects[0].id }, set: { store.currentProjectID = $0; Task { await store.loadBible() } })) {
                        ForEach(store.projects) { project in Text(project.name).tag(project.id) }
                    }.pickerStyle(.menu).padding(12).background(.white.opacity(0.07), in: RoundedRectangle(cornerRadius: 17))
                }
                if let info = store.bible?.info {
                    GlassCard {
                        VStack(alignment: .leading, spacing: 11) {
                            Text("ИГРА").font(.caption2.bold()).tracking(2).foregroundStyle(Palette.muted)
                            Text(info.title.isEmpty ? info.project : info.title).font(.system(size: 30, weight: .bold)).tracking(-1)
                            if !info.tagline.isEmpty { Text(info.tagline).foregroundStyle(Palette.muted) }
                            HStack(spacing: 9) {
                                infoPill(info.genre, fallback: "Жанр не указан")
                                infoPill(info.development_status, fallback: "В разработке")
                            }
                            if store.user?.can_write == true {
                                QuietButton(title: "Редактировать", symbol: "square.and.pencil") { showEdit = true }
                            }
                        }
                    }
                    infoSection("Сюжет", text: info.story, icon: "book.closed", fallback: "Сюжет пока не заполнен")
                    infoSection("Мир и сеттинг", text: info.setting, icon: "globe.europe.africa", fallback: "Нет описания мира")
                    infoSection("Геймплей", text: info.gameplay, icon: "gamecontroller", fallback: "Механики будут добавлены")
                    infoSection("Лор", text: info.universe, icon: "sparkles", fallback: "Нет предыстории")
                    infoSection("Атмосфера", text: info.themes, icon: "moon.stars", fallback: "Не указана")
                    infoSection("Прочее", text: info.notes, icon: "note.text", fallback: "Дополнительные детали пока не заполнены")
                    HStack {
                        Text("События").font(.title2.bold())
                        Spacer()
                        if store.user?.can_write == true {
                            QuietButton(title: "Добавить", symbol: "plus") { showEvent = true }
                        }
                    }.padding(.top, 7)
                    if store.bible?.events.isEmpty ?? true {
                        GlassCard { Text("Добавьте первую главу или событие.").foregroundStyle(Palette.muted) }
                    }
                    ForEach(store.bible?.events ?? []) { event in
                        DisclosureGroup {
                            VStack(alignment: .leading, spacing: 10) {
                                if !event.summary.isEmpty { Text(event.summary) }
                                if !event.location.isEmpty { Text("Место: " + event.location).foregroundStyle(Palette.muted) }
                                if !event.participants.isEmpty { Text("Участники: " + event.participants).foregroundStyle(Palette.muted) }
                                if !event.description.isEmpty { Text(event.description) }
                                if !event.consequences.isEmpty { Text("Последствия: " + event.consequences) }
                            }.font(.subheadline).padding(.top, 9)
                        } label: {
                            VStack(alignment: .leading, spacing: 6) {
                                Text(event.chapter.isEmpty ? "Событие \(event.order)" : event.chapter).font(.caption).foregroundStyle(Palette.muted)
                                Text(event.title).font(.headline)
                                if event.spoiler { Label("Спойлер", systemImage: "eye.slash").font(.caption).foregroundStyle(.orange) }
                            }
                        }.padding(17)
                            .background(Palette.tile, in: RoundedRectangle(cornerRadius: 21))
                    }
                    HStack {
                        Text("Персонажи").font(.title2.bold())
                        Spacer()
                        if store.user?.can_write == true {
                            QuietButton(title: "Добавить", symbol: "plus") { showCharacter = true }
                        }
                    }.padding(.top, 7)
                    ForEach(store.bible?.characters ?? []) { c in
                        GlassCard {
                            HStack(spacing: 12) {
                                Text(String(c.name.prefix(1)).uppercased()).font(.title2.bold())
                                    .frame(width: 48, height: 48).background(.white.opacity(0.12), in: RoundedRectangle(cornerRadius: 15))
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(c.name).font(.headline)
                                    Text(c.role.isEmpty ? "Персонаж" : c.role).font(.caption).foregroundStyle(Palette.muted)
                                }
                            }
                            if !c.bio.isEmpty { Text(c.bio).font(.subheadline).foregroundStyle(Palette.muted).padding(.top, 9) }
                        }
                    }
                } else {
                    GlassCard { Text("Информация загружается...").foregroundStyle(Palette.muted) }
                }
                if let error = store.errorMessage { Notice(text: error) }
            }.padding(18)
        }
        .background(Palette.background)
        .navigationTitle("Информация")
        .refreshable { await store.loadBible() }
        .sheet(isPresented: $showEdit) { if let info = store.bible?.info { BibleEditor(info: info) } }
        .sheet(isPresented: $showEvent) { EventEditor() }
        .sheet(isPresented: $showCharacter) { CharacterEditor() }
    }
    private func infoPill(_ text: String, fallback: String) -> some View {
        Text(text.isEmpty ? fallback : text).font(.caption).lineLimit(1).padding(10)
            .background(.white.opacity(0.12), in: Capsule())
    }
    private func infoSection(_ title: String, text: String, icon: String, fallback: String) -> some View {
        GlassCard {
            Label(title, systemImage: icon).font(.title3.bold())
            Text(text.isEmpty ? fallback : text)
                .font(.subheadline).foregroundStyle(text.isEmpty ? Palette.muted : Palette.foreground)
                .padding(.top, 6).textSelection(.enabled)
        }
    }
}

struct BibleEditor: View {
    @EnvironmentObject var store: DevStore
    @Environment(\.dismiss) private var dismiss
    @State private var fields: [String: String]
    @State private var message: String?
    private let names: [(String, String, Bool)] = [
        ("title", "Название игры", false), ("genre", "Жанр", false),
        ("tagline", "Короткое описание", false), ("setting", "Мир и сеттинг", true),
        ("story", "Сюжет", true), ("gameplay", "Геймплей", true),
        ("themes", "Темы и атмосфера", true), ("universe", "Лор", true),
        ("platforms", "Платформы", false), ("engine", "Движок", false),
        ("development_status", "Статус разработки", false),
        ("audience", "Аудитория", false), ("notes", "Прочее", true),
    ]
    init(info: GameInfo) {
        _fields = State(initialValue: [
            "title":info.title,"genre":info.genre,"tagline":info.tagline,"setting":info.setting,
            "story":info.story,"gameplay":info.gameplay,"themes":info.themes,"universe":info.universe,
            "platforms":info.platforms,"engine":info.engine,"development_status":info.development_status,
            "audience":info.audience,"notes":info.notes,
        ])
    }
    var body: some View {
        NavigationStack {
            Form {
                ForEach(names.indices, id: \.self) { index in
                    let item = names[index]
                    Section(item.1) {
                        if item.2 {
                            TextEditor(text: binding(item.0)).frame(minHeight: 94)
                        } else {
                            TextField(item.1, text: binding(item.0))
                        }
                    }
                }
                if let message { Text(message).foregroundStyle(.orange) }
            }
            .navigationTitle("Об игре").navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Закрыть") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Сохранить") {
                        Task {
                            do { try await store.updateBible(fields); dismiss() }
                            catch { message = error.localizedDescription }
                        }
                    }
                }
            }
        }
    }
    private func binding(_ key: String) -> Binding<String> {
        Binding(get: { fields[key] ?? "" }, set: { fields[key] = $0 })
    }
}

struct EventEditor: View {
    @EnvironmentObject var store: DevStore
    @Environment(\.dismiss) private var dismiss
    @State private var title = ""
    @State private var chapter = ""
    @State private var summary = ""
    @State private var order = 1
    @State private var message: String?
    var body: some View {
        NavigationStack {
            Form {
                TextField("Название события", text: $title)
                TextField("Глава или акт", text: $chapter)
                Stepper("Порядок: \(order)", value: $order, in: 1...9999)
                Section("Описание") { TextEditor(text: $summary).frame(minHeight: 130) }
                if let message { Text(message).foregroundStyle(.orange) }
            }
            .navigationTitle("Новое событие").navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Закрыть") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Добавить") {
                        Task {
                            do { try await store.addEvent(chapter: chapter, title: title, order: order, summary: summary); dismiss() }
                            catch { message = error.localizedDescription }
                        }
                    }.disabled(title.isEmpty)
                }
            }
        }
    }
}

struct CharacterEditor: View {
    @EnvironmentObject var store: DevStore
    @Environment(\.dismiss) private var dismiss
    @State private var name = ""
    @State private var role = ""
    @State private var bio = ""
    @State private var message: String?
    var body: some View {
        NavigationStack {
            Form {
                TextField("Имя", text: $name)
                TextField("Роль", text: $role)
                Section("Биография") { TextEditor(text: $bio).frame(minHeight: 130) }
                if let message { Text(message).foregroundStyle(.orange) }
            }
            .navigationTitle("Новый персонаж").navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Закрыть") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Добавить") {
                        Task {
                            do { try await store.addCharacter(name: name, role: role, bio: bio); dismiss() }
                            catch { message = error.localizedDescription }
                        }
                    }.disabled(name.isEmpty)
                }
            }
        }
    }
}

struct JournalScreen: View {
    @EnvironmentObject var store: DevStore
    @State private var mode = 0
    @State private var showEditor = false
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                HeaderLabel(title: "Дневник.", caption: "ЗАМЕТКИ И ДОКУМЕНТАЦИЯ")
                Picker("Раздел", selection: $mode) {
                    Text("Записи").tag(0)
                    Text("Документация").tag(1)
                }.pickerStyle(.segmented)
                ForEach(store.posts.filter { mode == 1 ? $0.kind == "doc" : $0.kind != "doc" }) { post in
                    NavigationLink { PostDetailsScreen(post: post) } label: {
                        GlassCard {
                            Text(post.kind.uppercased()).font(.caption2.bold()).tracking(1.5).foregroundStyle(Palette.muted)
                            Text(post.title).font(.title3.bold()).foregroundStyle(.white).padding(.top, 6)
                            Text(post.body).font(.subheadline).foregroundStyle(Palette.muted).lineLimit(3).padding(.top, 3)
                            HStack { Text(post.author); Spacer(); Text(post.project) }
                                .font(.caption).foregroundStyle(Palette.muted).padding(.top, 10)
                        }
                    }
                }
            }.padding(18)
        }
        .navigationTitle("Дневник")
        .background(Palette.background)
        .toolbar { if store.user?.can_write == true {
            ToolbarItem(placement: .topBarTrailing) { Button { showEditor = true } label: { Image(systemName: "plus") } }
        }}
        .sheet(isPresented: $showEditor) { PostEditor() }
        .refreshable { await store.refresh() }
    }
}

struct PostDetailsScreen: View {
    let post: DevPost
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 17) {
                Text(post.kind.uppercased()).font(.caption2.bold()).tracking(1.4).foregroundStyle(Palette.muted)
                Text(post.title).font(.largeTitle.bold())
                Text(post.project + " · " + post.author).font(.caption).foregroundStyle(Palette.muted)
                GlassCard { Text(post.body).font(.body).textSelection(.enabled) }
            }.padding(18)
        }.navigationTitle("Публикация").background(Palette.background)
    }
}

struct PostEditor: View {
    @EnvironmentObject var store: DevStore
    @Environment(\.dismiss) private var dismiss
    @State private var title = ""
    @State private var postBody = ""
    @State private var kind = "note"
    @State private var status = "published"
    @State private var message: String?
    var body: some View {
        NavigationStack {
            Form {
                TextField("Название записи", text: $title)
                Picker("Тип", selection: $kind) {
                    Text("Заметка").tag("note")
                    Text("Документ").tag("doc")
                    Text("Дневник").tag("devlog")
                    Text("Решение").tag("decision")
                }
                Picker("Статус", selection: $status) { Text("Опубликовано").tag("published"); Text("Черновик").tag("draft") }
                Section("Содержание") { TextEditor(text: $postBody).frame(minHeight: 200) }
                if let message { Text(message).foregroundStyle(.orange) }
            }.navigationTitle("Новая запись")
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) { Button("Отмена") { dismiss() } }
                    ToolbarItem(placement: .confirmationAction) { Button("Сохранить") {
                        Task {
                            do { try await store.makePost(title: title, body: postBody, kind: kind, status: status); dismiss() }
                            catch { message = error.localizedDescription }
                        }
                    }.disabled(title.isEmpty) }
                }
        }
    }
}

struct TasksScreen: View {
    @EnvironmentObject var store: DevStore
    @State private var showEditor = false
    private func statusLabel(_ value: String) -> String {
        switch value {
        case "todo": return "К выполнению"
        case "progress": return "В работе"
        case "review": return "На проверке"
        default: return "Готово"
        }
    }
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 17) {
                HeaderLabel(title: "Задачи.", caption: "ДОСКА РАЗРАБОТКИ")
                ForEach(["todo", "progress", "review", "done"], id: \.self) { code in
                    Text(statusLabel(code)).font(.title3.bold()).padding(.top, 5)
                    ForEach(store.tasks.filter { $0.status == code }) { task in
                        GlassCard {
                            VStack(alignment: .leading, spacing: 9) {
                                Text(task.title).font(.headline)
                                Text(task.description.isEmpty ? task.project : task.description)
                                    .font(.subheadline).foregroundStyle(Palette.muted).lineLimit(3)
                                HStack {
                                    Text(task.priority.uppercased()).font(.caption2.bold()).foregroundStyle(Palette.muted)
                                    Spacer()
                                    if store.user?.can_write == true &&
                                        (store.user?.role == "admin" || store.user?.id == task.created_by_id || store.user?.id == task.assignee_id) {
                                        Menu {
                                            ForEach(["todo", "progress", "review", "done"], id: \.self) { value in
                                                Button(statusLabel(value)) { Task { try? await store.updateTask(task, status: value) } }
                                            }
                                        } label: {
                                            Label("Статус", systemImage: "chevron.down").font(.caption)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }.padding(18)
        }.background(Palette.background).navigationTitle("Задачи")
            .toolbar { if store.user?.can_write == true {
                ToolbarItem(placement: .topBarTrailing) { Button { showEditor = true } label: { Image(systemName: "plus") } }
            }}
            .sheet(isPresented: $showEditor) { TaskEditor() }
            .refreshable { await store.refresh() }
    }
}

struct TaskEditor: View {
    @EnvironmentObject var store: DevStore
    @Environment(\.dismiss) private var dismiss
    @State private var title = ""
    @State private var description = ""
    @State private var priority = "normal"
    @State private var message: String?
    var body: some View {
        NavigationStack {
            Form {
                TextField("Задача", text: $title)
                Section("Описание") { TextEditor(text: $description).frame(minHeight: 140) }
                Picker("Приоритет", selection: $priority) {
                    Text("Низкий").tag("low")
                    Text("Обычный").tag("normal")
                    Text("Высокий").tag("high")
                    Text("Срочно").tag("critical")
                }
                if let message { Text(message).foregroundStyle(.orange) }
            }.navigationTitle("Новая задача")
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) { Button("Отмена") { dismiss() } }
                    ToolbarItem(placement: .confirmationAction) { Button("Создать") {
                        Task {
                            do { try await store.makeTask(title: title, description: description, priority: priority); dismiss() }
                            catch { message = error.localizedDescription }
                        }
                    }.disabled(title.isEmpty) }
                }
        }
    }
}

struct MoreScreen: View {
    @EnvironmentObject var store: DevStore
    var body: some View {
        List {
            Section("Проект") {
                NavigationLink { FilesScreen() } label: { Label("Файлы", systemImage: "folder.fill") }
                NavigationLink { TeamScreen() } label: { Label("Команда", systemImage: "person.2.fill") }
            }
            Section("Аккаунт") {
                HStack { Label("Пользователь", systemImage: "person.crop.circle"); Spacer(); Text(store.user?.username ?? "").foregroundStyle(Palette.muted) }
                NavigationLink { PasswordScreen() } label: { Label("Сменить пароль", systemImage: "lock.rotation") }
                Button(role: .destructive) { Task { await store.logout() } } label: { Label("Выйти", systemImage: "rectangle.portrait.and.arrow.right") }
            }
            Section { Text("Nightwell Dev · Native SwiftUI").font(.footnote).foregroundStyle(Palette.muted) }
        }.navigationTitle("Ещё").scrollContentBackground(.hidden).background(Palette.background)
    }
}

struct FilesScreen: View {
    @EnvironmentObject var store: DevStore
    @State private var selectedFile: URL?
    @State private var message: String?
    var body: some View {
        ScrollView {
            VStack(spacing: 12) {
                ForEach(store.files) { asset in
                    GlassCard {
                        HStack(spacing: 13) {
                            Image(systemName: "doc.fill").font(.title2)
                            VStack(alignment: .leading, spacing: 5) {
                                Text(asset.title).font(.headline)
                                Text(asset.original_name).font(.caption).foregroundStyle(Palette.muted)
                            }
                            Spacer()
                            Button {
                                Task {
                                    do { selectedFile = try await store.download(asset) }
                                    catch { message = error.localizedDescription }
                                }
                            } label: { Image(systemName: "square.and.arrow.down").padding(9) }
                        }
                    }
                }
                if let message { Notice(text: message) }
                if let selectedFile {
                    ShareLink(item: selectedFile) { Label("Поделиться скачанным файлом", systemImage: "square.and.arrow.up") }
                }
            }.padding(18)
        }.navigationTitle("Файлы").background(Palette.background)
            .refreshable { await store.refresh() }
    }
}

struct TeamScreen: View {
    @EnvironmentObject var store: DevStore
    var body: some View {
        ScrollView {
            LazyVStack(spacing: 12) {
                ForEach(store.team) { person in
                    GlassCard {
                        HStack(spacing: 13) {
                            Text(String(person.username.prefix(1)).uppercased())
                                .font(.title2.bold()).frame(width: 50, height: 50)
                                .background(.white.opacity(0.12), in: RoundedRectangle(cornerRadius: 17))
                            VStack(alignment: .leading, spacing: 5) {
                                Text(person.name).font(.headline)
                                Text(person.role == "admin" ? "Администратор" : person.role == "developer" ? "Разработчик" : "Наблюдатель")
                                    .font(.caption).foregroundStyle(Palette.muted)
                            }
                        }
                    }
                }
            }.padding(18)
        }.navigationTitle("Команда").background(Palette.background)
    }
}

struct PasswordScreen: View {
    @EnvironmentObject var store: DevStore
    @State private var old = ""
    @State private var new = ""
    @State private var message: String?
    var body: some View {
        Form {
            SecureField("Текущий пароль", text: $old)
            SecureField("Новый пароль", text: $new)
            Text("Используйте уникальный пароль не короче 12 символов. После смены войдите снова.")
                .font(.footnote).foregroundStyle(Palette.muted)
            Button("Сменить пароль") {
                Task {
                    do {
                        let _: [String: Bool] = try await store.fetch("auth/password/", method: "POST", json: ["old_password":old, "new_password":new])
                        await store.logout()
                    } catch { message = error.localizedDescription }
                }
            }.disabled(old.isEmpty || new.isEmpty)
            if let message { Notice(text: message) }
        }.navigationTitle("Безопасность").scrollContentBackground(.hidden).background(Palette.background)
    }
}
