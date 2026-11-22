using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using Microsoft.UI.Xaml.Media.Animation;
using Microsoft.UI;
using Microsoft.UI.Text;
using Microsoft.UI.Xaml.Controls.Primitives;
using System.Diagnostics;
using System.Text.Json.Nodes;
using Windows.Storage.Pickers;

namespace NightwellDev;

public sealed partial class MainWindow : Window
{
    private readonly Backend api = new();
    private readonly SolidColorBrush foreground = new(Colors.White);
    private readonly SolidColorBrush secondary = new(ColorHelper.FromArgb(255, 167, 171, 181));
    private readonly SolidColorBrush panel = new(ColorHelper.FromArgb(255, 29, 30, 35));
    private readonly SolidColorBrush stroke = new(ColorHelper.FromArgb(255, 65, 67, 72));
    private string page = "home";

    public MainWindow()
    {
        InitializeComponent();
        Title = "Nightwell Dev · Nightwell Studio";
        LoginRoot.Loaded += async (_, _) =>
        {
            if (!api.SignedIn) return;
            try
            {
                await api.RefreshAsync();
                EnterWorkspace();
            }
            catch { await api.SignOutAsync(false); }
        };
    }

    private static string Value(JsonNode? item, string name)
        => item?[name]?.ToString() ?? "";

    private static IEnumerable<JsonNode> Each(JsonArray source)
        => source.Where(x => x != null).Select(x => x!);

    private TextBlock Text(string value, double size = 14, bool bold = false, bool muted = false)
    {
        return new TextBlock {
            Text = value, FontSize = size, FontWeight = bold ? FontWeights.SemiBold : FontWeights.Normal,
            Foreground = muted ? secondary : foreground, TextWrapping = TextWrapping.Wrap,
            IsTextSelectionEnabled = true,
        };
    }

    private Border Card(params UIElement[] elements)
    {
        var content = new StackPanel { Spacing = 10 };
        foreach (var element in elements) content.Children.Add(element);
        return new Border {
            Background = panel, BorderBrush = stroke, BorderThickness = new Thickness(1),
            CornerRadius = new CornerRadius(22), Padding = new Thickness(21),
            MinWidth = 280, Child = content,
        };
    }

    private Button Action(string label, Action callback)
    {
        var button = new Button { Content = label, Padding = new Thickness(16, 10, 16, 10),
            CornerRadius = new CornerRadius(13), Background = new SolidColorBrush(ColorHelper.FromArgb(255, 239, 240, 244)),
            Foreground = new SolidColorBrush(ColorHelper.FromArgb(255, 16, 17, 19)) };
        button.Click += (_, _) => callback();
        return button;
    }

    private void Header(string title, string eyebrow)
    {
        ContentPanel.Children.Add(Text(eyebrow.ToUpperInvariant(), 11, true, true));
        ContentPanel.Children.Add(Text(title, 36, true));
    }

    private void EnterWorkspace()
    {
        LoginRoot.Visibility = Visibility.Collapsed;
        MainNav.Visibility = Visibility.Visible;
        MainNav.SelectedItem = MainNav.MenuItems[0];
        Render();
    }

    private async void LoginClicked(object sender, RoutedEventArgs e)
    {
        LoginButton.IsEnabled = false;
        LoginError.Text = "";
        try
        {
            await api.SignInAsync(UsernameInput.Text.Trim(), PasswordInput.Password);
            await api.RefreshAsync();
            PasswordInput.Password = "";
            EnterWorkspace();
        }
        catch (Exception ex) { LoginError.Text = ex.Message; }
        finally { LoginButton.IsEnabled = true; }
    }

    private void NavigationChanged(NavigationView sender, NavigationViewSelectionChangedEventArgs e)
    {
        if (e.SelectedItem is NavigationViewItem item && item.Tag is string tag)
        {
            page = tag;
            Render();
        }
    }

    private async Task Refresh()
    {
        try { await api.RefreshAsync(); Render(); }
        catch (Exception ex) { await ShowError(ex.Message); }
    }

    private async Task ShowError(string message)
    {
        await new ContentDialog {
            XamlRoot = Content.XamlRoot, Title = "Nightwell Dev",
            Content = message, CloseButtonText = "ОК",
        }.ShowAsync();
    }

    private void Render()
    {
        ContentPanel.Children.Clear();
        var bar = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 12 };
        bar.Children.Add(Action("↻  Обновить", () => _ = Refresh()));
        ContentPanel.Children.Add(bar);
        switch (page)
        {
            case "home": RenderHome(); break;
            case "info": RenderInfo(); break;
            case "journal": RenderPosts(false); break;
            case "docs": RenderPosts(true); break;
            case "tasks": RenderTasks(); break;
            case "files": RenderFiles(); break;
            case "team": RenderTeam(); break;
            case "account": RenderAccount(); break;
            default: RenderHome(); break;
        }
    }

    private void RenderHome()
    {
        Header("Твоя команда.", "NIGHTWELL STUDIO / РАБОЧЕЕ ПРОСТРАНСТВО");
        ContentPanel.Children.Add(Card(
            Text("СОЗДАВАЙТЕ МИРЫ ВМЕСТЕ", 11, true, true),
            Text("Все идеи. Одна история.", 30, true),
            Text("Документируйте прогресс, распределяйте задачи и стройте мир игры.", 14, false, true)
        ));
        var grid = new Grid { ColumnSpacing = 13, RowSpacing = 13 };
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        var cards = new [] {
            ("Публикации", Value(api.Counts, "posts")),
            ("Активные задачи", Value(api.Counts, "tasks")),
            ("Файлы", Value(api.Counts, "files")),
            ("Команда", Value(api.Counts, "members")),
        };
        for (var i = 0; i < cards.Length; i++)
        {
            var cell = Card(Text(cards[i].Item1, 12, false, true), Text(cards[i].Item2, 37, true));
            Grid.SetRow(cell, i / 2);
            Grid.SetColumn(cell, i % 2);
            grid.Children.Add(cell);
        }
        ContentPanel.Children.Add(grid);
        ContentPanel.Children.Add(Text("Последние записи", 23, true));
        foreach (var post in Each(api.Posts).Take(6))
        {
            var button = Action("Открыть ↗", () => RenderArticle(post));
            ContentPanel.Children.Add(Card(Text(Value(post, "title"), 17, true),
                Text(Value(post, "project") + " · " + Value(post, "author"), 12, false, true), button));
        }
    }

    private void RenderArticle(JsonNode post)
    {
        ContentPanel.Children.Clear();
        ContentPanel.Children.Add(Action("← Назад", Render));
        Header(Value(post, "title"), Value(post, "kind"));
        ContentPanel.Children.Add(Card(
            Text(Value(post, "author") + " · " + Value(post, "project"), 12, false, true),
            Text(Value(post, "body"), 15)));
    }

    private void RenderInfo()
    {
        Header("Информация.", "GAME BIBLE / ИГРА И ВСЕЛЕННАЯ");
        var chooser = new ComboBox { MinWidth = 240, PlaceholderText = "Проект" };
        var selected = 0;
        var index = 0;
        foreach (var project in Each(api.Projects))
        {
            var id = project["id"]?.GetValue<int>() ?? 0;
            chooser.Items.Add(new ComboBoxItem { Content = Value(project, "name"), Tag = id });
            if (id == api.ProjectId) selected = index;
            index++;
        }
        chooser.SelectedIndex = selected;
        chooser.SelectionChanged += async (_, _) =>
        {
            if (chooser.SelectedItem is not ComboBoxItem item || item.Tag is not int id || api.ProjectId == id) return;
            api.ProjectId = id;
            try { await api.RefreshInformationAsync(); Render(); }
            catch (Exception ex) { await ShowError(ex.Message); }
        };
        ContentPanel.Children.Add(chooser);
        var info = api.GameInfo;
        var title = Value(info, "title");
        if (string.IsNullOrEmpty(title)) title = Value(info, "project");
        var block = Card(
            Text("ОБ ИГРЕ", 11, true, true), Text(title, 30, true),
            Text(Value(info, "tagline"), 14, false, true),
            Text("Жанр: " + Empty(Value(info, "genre")) + "     |     Движок: " + Empty(Value(info, "engine")), 13),
            Text("Платформы: " + Empty(Value(info, "platforms")) + "     |     Стадия: " + Empty(Value(info, "development_status")), 13)
        );
        if (api.Role != "viewer")
            ((StackPanel)block.Child).Children.Add(Action("✎  Редактировать", () => _ = EditInfo()));
        ContentPanel.Children.Add(block);
        ContentPanel.Children.Add(Card(Text("Сюжет", 21, true), Text(Empty(Value(info, "story")), 14)));
        ContentPanel.Children.Add(Card(Text("Мир и сеттинг", 21, true), Text(Empty(Value(info, "setting")), 14)));
        ContentPanel.Children.Add(Card(Text("Геймплей", 21, true), Text(Empty(Value(info, "gameplay")), 14)));
        ContentPanel.Children.Add(Card(Text("Лор и предыстория", 21, true), Text(Empty(Value(info, "universe")), 14)));
        ContentPanel.Children.Add(Card(Text("Темы и атмосфера", 21, true), Text(Empty(Value(info, "themes")), 14)));
        ContentPanel.Children.Add(Card(Text("Прочее", 21, true), Text(Empty(Value(info, "notes")), 14)));
        ContentPanel.Children.Add(Text("События и хронология", 24, true));
        if (api.Role != "viewer") ContentPanel.Children.Add(Action("＋ Новое событие", () => _ = AddEvent()));
        foreach (var item in Each(api.Events))
        {
            var details = new StackPanel { Spacing = 10 };
            details.Children.Add(Text(Value(item, "chapter") + " · №" + Value(item, "order"), 12, true, true));
            details.Children.Add(Text(Value(item, "title"), 19, true));
            details.Children.Add(Text(Value(item, "summary"), 13));
            var extra = new Expander { Header = "Подробности" };
            extra.Content = new StackPanel { Spacing = 8, Children = {
                Text(Value(item, "description"), 13),
                Text("Место: " + Value(item, "location"), 13, false, true),
                Text("Участники: " + Value(item, "participants"), 13, false, true),
                Text("Последствия: " + Value(item, "consequences"), 13),
            } };
            details.Children.Add(extra);
            ContentPanel.Children.Add(new Border {
                Child = details, BorderBrush = stroke, Background = panel, BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(20), Padding = new Thickness(19)
            });
        }
        ContentPanel.Children.Add(Text("Персонажи", 24, true));
        if (api.Role != "viewer") ContentPanel.Children.Add(Action("＋ Новый персонаж", () => _ = AddCharacter()));
        foreach (var person in Each(api.Characters))
        {
            ContentPanel.Children.Add(Card(Text(Value(person, "name"), 19, true),
                Text(Value(person, "role") + " · " + Value(person, "faction"), 12, false, true),
                Text(Value(person, "bio"), 14)));
        }
    }

    private static string Empty(string text) => string.IsNullOrWhiteSpace(text) ? "Пока не заполнено" : text;

    private async Task<Dictionary<string, string>?> EditFields(string title, params (string Name, string Value)[] fields)
    {
        var stack = new StackPanel { Spacing = 13, MaxHeight = 480 };
        var inputs = new Dictionary<string, TextBox>();
        foreach (var field in fields)
        {
            var input = new TextBox {
                Header = field.Name, Text = field.Value, TextWrapping = TextWrapping.Wrap,
                AcceptsReturn = field.Name is "story" or "setting" or "gameplay" or "summary" or "bio" or "description",
                MinWidth = 380,
            };
            inputs[field.Name] = input;
            stack.Children.Add(input);
        }
        var dialog = new ContentDialog {
            Title = title, Content = new ScrollViewer { Content = stack, MaxHeight = 480 },
            XamlRoot = Content.XamlRoot, PrimaryButtonText = "Сохранить", CloseButtonText = "Отмена",
        };
        var result = await dialog.ShowAsync();
        return result == ContentDialogResult.Primary ? inputs.ToDictionary(x => x.Key, x => x.Value.Text) : null;
    }

    private async Task EditInfo()
    {
        var info = api.GameInfo;
        var values = await EditFields("Информация об игре",
            ("title", Value(info, "title")), ("genre", Value(info, "genre")),
            ("tagline", Value(info, "tagline")), ("story", Value(info, "story")),
            ("setting", Value(info, "setting")), ("gameplay", Value(info, "gameplay")),
            ("universe", Value(info, "universe")), ("themes", Value(info, "themes")),
            ("engine", Value(info, "engine")), ("platforms", Value(info, "platforms")),
            ("development_status", Value(info, "development_status")),
            ("audience", Value(info, "audience")), ("notes", Value(info, "notes")));
        if (values == null) return;
        try { await api.SaveInfoAsync(values); Render(); }
        catch (Exception ex) { await ShowError(ex.Message); }
    }

    private async Task AddEvent()
    {
        var values = await EditFields("Новое сюжетное событие",
            ("title", ""), ("chapter", ""), ("summary", ""));
        if (values == null || string.IsNullOrWhiteSpace(values["title"])) return;
        try { await api.AddEventAsync(values["title"], values["chapter"], values["summary"]); Render(); }
        catch (Exception ex) { await ShowError(ex.Message); }
    }

    private async Task AddCharacter()
    {
        var values = await EditFields("Новый персонаж",
            ("name", ""), ("role", ""), ("bio", ""));
        if (values == null || string.IsNullOrWhiteSpace(values["name"])) return;
        try { await api.AddCharacterAsync(values["name"], values["role"], values["bio"]); Render(); }
        catch (Exception ex) { await ShowError(ex.Message); }
    }

    private void RenderPosts(bool docs)
    {
        Header(docs ? "Документация." : "Дневник.", docs ? "БАЗА ЗНАНИЙ" : "ЗАМЕТКИ И ОБНОВЛЕНИЯ");
        if (api.Role != "viewer") ContentPanel.Children.Add(Action("＋ Новая запись", () => _ = AddPost(docs)));
        foreach (var post in Each(api.Posts).Where(p => (Value(p, "kind") == "doc") == docs))
        {
            var button = Action("Читать ↗", () => RenderArticle(post));
            ContentPanel.Children.Add(Card(
                Text(Value(post, "kind").ToUpperInvariant() + " · " + Value(post, "project"), 11, true, true),
                Text(Value(post, "title"), 20, true),
                Text(Value(post, "body").Length > 240 ? Value(post, "body")[..240] + "…" : Value(post, "body"), 13, false, true),
                button));
        }
    }

    private async Task AddPost(bool docs)
    {
        var values = await EditFields("Новая публикация", ("title", ""), ("body", ""));
        if (values == null || string.IsNullOrWhiteSpace(values["title"])) return;
        try { await api.AddPostAsync(values["title"], values["body"], docs ? "doc" : "note"); Render(); }
        catch (Exception ex) { await ShowError(ex.Message); }
    }

    private void RenderTasks()
    {
        Header("Задачи.", "ПЛАН РАЗРАБОТКИ");
        if (api.Role != "viewer") ContentPanel.Children.Add(Action("＋ Новая задача", () => _ = AddTask()));
        foreach (var (status, title) in new [] {
            ("todo", "К выполнению"), ("progress", "В работе"),
            ("review", "На проверке"), ("done", "Готово")
        })
        {
            ContentPanel.Children.Add(Text(title, 23, true));
            foreach (var task in Each(api.Tasks).Where(x => Value(x, "status") == status))
            {
                var card = Card(Text(Value(task, "title"), 17, true),
                    Text(Empty(Value(task, "description")), 13, false, true),
                    Text(Value(task, "project") + " · " + Value(task, "priority"), 12, false, true));
                if (api.Role != "viewer")
                {
                    var combo = new ComboBox { PlaceholderText = "Статус", MinWidth = 200 };
                    foreach (var choice in new [] { ("todo","К выполнению"), ("progress","В работе"),
                        ("review","На проверке"), ("done","Готово")})
                    {
                        combo.Items.Add(new ComboBoxItem { Tag = choice.Item1, Content = choice.Item2 });
                    }
                    combo.SelectionChanged += async (_, _) =>
                    {
                        if (combo.SelectedItem is not ComboBoxItem selected || selected.Tag is not string next || next == Value(task, "status")) return;
                        try { await api.UpdateTaskAsync(task, next); Render(); }
                        catch (Exception ex) { await ShowError(ex.Message); }
                    };
                    ((StackPanel)card.Child).Children.Add(combo);
                }
                ContentPanel.Children.Add(card);
            }
        }
    }

    private async Task AddTask()
    {
        var values = await EditFields("Новая задача", ("title", ""), ("description", ""));
        if (values == null || string.IsNullOrWhiteSpace(values["title"])) return;
        try { await api.AddTaskAsync(values["title"], values["description"]); Render(); }
        catch (Exception ex) { await ShowError(ex.Message); }
    }

    private void RenderFiles()
    {
        Header("Файлы.", "ЗАКРЫТОЕ ХРАНИЛИЩЕ");
        if (api.Role != "viewer") ContentPanel.Children.Add(Action("＋ Загрузить файл", () => _ = Upload()));
        foreach (var file in Each(api.Files))
        {
            var current = file;
            ContentPanel.Children.Add(Card(
                Text(Value(file, "title"), 17, true),
                Text(Value(file, "original_name") + " · " + Value(file, "uploader"), 12, false, true),
                Action("Скачать", () => _ = Download(current))
            ));
        }
    }

    private async Task Upload()
    {
        try
        {
            var picker = new FileOpenPicker();
            picker.FileTypeFilter.Add("*");
            WinRT.Interop.InitializeWithWindow.Initialize(picker, WinRT.Interop.WindowNative.GetWindowHandle(this));
            var selected = await picker.PickSingleFileAsync();
            if (selected != null) { await api.UploadAsync(selected.Path); Render(); }
        }
        catch (Exception ex) { await ShowError(ex.Message); }
    }

    private async Task Download(JsonNode file)
    {
        try
        {
            var saved = await api.DownloadAsync(file);
            Process.Start(new ProcessStartInfo("explorer.exe", "/select,\"" + saved + "\"") { UseShellExecute = true });
        }
        catch (Exception ex) { await ShowError(ex.Message); }
    }

    private void RenderTeam()
    {
        Header("Команда.", "РАЗРАБОТЧИКИ И РОЛИ");
        foreach (var person in Each(api.Team))
            ContentPanel.Children.Add(Card(Text(Value(person, "name"), 17, true),
                Text(Value(person, "username") + " · " + Value(person, "role"), 12, false, true)));
    }

    private void RenderAccount()
    {
        Header("Аккаунт.", "NIGHTWELL STUDIO / БЕЗОПАСНОСТЬ");
        ContentPanel.Children.Add(Card(
            Text("Пользователь: " + api.Username, 18, true),
            Text("Роль: " + api.Role, 13, false, true),
            Action("Сменить пароль", () => _ = ChangePassword()),
            Action("Выйти", () => _ = Logout())
        ));
    }

    private async Task ChangePassword()
    {
        var values = await EditFields("Смена пароля", ("old_password", ""), ("new_password", ""));
        if (values == null) return;
        try
        {
            await api.ChangePasswordAsync(values["old_password"], values["new_password"]);
            MainNav.Visibility = Visibility.Collapsed;
            LoginRoot.Visibility = Visibility.Visible;
            await ShowError("Пароль обновлён. Войдите с новым паролем.");
        }
        catch (Exception ex) { await ShowError(ex.Message); }
    }

    private async Task Logout()
    {
        await api.SignOutAsync();
        MainNav.Visibility = Visibility.Collapsed;
        LoginRoot.Visibility = Visibility.Visible;
    }
}
