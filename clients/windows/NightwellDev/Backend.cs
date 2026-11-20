using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json.Nodes;
using Windows.Security.Credentials;

namespace NightwellDev;

internal sealed class Backend
{
    private const string BaseUrl = "https://nightwell-dev-web-production.up.railway.app/api/v1/";
    private const string VaultResource = "fun.nightwell.dev.native";
    private readonly HttpClient http = new() { BaseAddress = new Uri(BaseUrl), Timeout = TimeSpan.FromSeconds(35) };
    private string? token;
    public string Username { get; private set; } = "";
    public string Role { get; private set; } = "";
    public int ProjectId { get; set; }
    public JsonArray Projects { get; private set; } = new();
    public JsonObject Counts { get; private set; } = new();
    public JsonArray Posts { get; private set; } = new();
    public JsonArray Tasks { get; private set; } = new();
    public JsonArray Files { get; private set; } = new();
    public JsonArray Team { get; private set; } = new();
    public JsonObject GameInfo { get; private set; } = new();
    public JsonArray Events { get; private set; } = new();
    public JsonArray Characters { get; private set; } = new();
    public bool SignedIn => !string.IsNullOrEmpty(token);

    public Backend()
    {
        try
        {
            var vault = new PasswordVault();
            var entry = vault.Retrieve(VaultResource, "session");
            entry.RetrievePassword();
            token = entry.Password;
        }
        catch { /* No prior session or credential vault unavailable */ }
    }

    private HttpRequestMessage Make(string path, HttpMethod method, HttpContent? content = null)
    {
        var request = new HttpRequestMessage(method, path);
        request.Headers.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));
        if (token != null) request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
        request.Content = content;
        return request;
    }

    private async Task<HttpResponseMessage> SendAsync(string path, HttpMethod method, HttpContent? content = null)
    {
        using var request = Make(path, method, content);
        var response = await http.SendAsync(request);
        if (!response.IsSuccessStatusCode)
        {
            var data = await response.Content.ReadAsStringAsync();
            response.Dispose();
            try { throw new InvalidOperationException(JsonNode.Parse(data)?["error"]?.ToString() ?? "Ошибка сервера"); }
            catch (System.Text.Json.JsonException) { throw new InvalidOperationException("HTTP " + (int)response.StatusCode); }
        }
        return response;
    }

    private async Task<JsonObject> JsonAsync(string path, HttpMethod method, JsonObject? body = null)
    {
        HttpContent? content = body == null ? null : new StringContent(body.ToJsonString(), Encoding.UTF8, "application/json");
        using var response = await SendAsync(path, method, content);
        var text = await response.Content.ReadAsStringAsync();
        return JsonNode.Parse(text)?.AsObject() ?? new JsonObject();
    }

    public Task<JsonObject> GetAsync(string path) => JsonAsync(path, HttpMethod.Get);
    public Task<JsonObject> PostAsync(string path, JsonObject json) => JsonAsync(path, HttpMethod.Post, json);
    public Task<JsonObject> PutAsync(string path, JsonObject json) => JsonAsync(path, HttpMethod.Put, json);
    public Task<JsonObject> PatchAsync(string path, JsonObject json) => JsonAsync(path, HttpMethod.Patch, json);

    public async Task SignInAsync(string username, string password)
    {
        var auth = await PostAsync("auth/login/", new JsonObject
        {
            ["username"] = username, ["password"] = password, ["device_name"] = Environment.MachineName + " Windows",
        });
        token = auth["token"]?.ToString() ?? throw new InvalidOperationException("Сервер не вернул токен");
        Username = auth["user"]?["username"]?.ToString() ?? username;
        Role = auth["user"]?["role"]?.ToString() ?? "viewer";
        try
        {
            var vault = new PasswordVault();
            foreach (var previous in vault.FindAllByResource(VaultResource)) vault.Remove(previous);
            vault.Add(new PasswordCredential(VaultResource, "session", token));
        }
        catch { /* Windows credential storage is optional; session remains in memory */ }
    }

    public async Task RefreshAsync()
    {
        var me = await GetAsync("me/");
        Username = me["user"]?["username"]?.ToString() ?? Username;
        Role = me["user"]?["role"]?.ToString() ?? Role;
        Projects = (await GetAsync("projects/"))["items"]?.AsArray() ?? new();
        if (ProjectId == 0) ProjectId = Projects.FirstOrDefault()?["id"]?.GetValue<int>() ?? 0;
        Counts = (await GetAsync("dashboard/"))["counts"]?.AsObject() ?? new();
        Posts = (await GetAsync("posts/"))["items"]?.AsArray() ?? new();
        Tasks = (await GetAsync("tasks/"))["items"]?.AsArray() ?? new();
        Files = (await GetAsync("files/"))["items"]?.AsArray() ?? new();
        Team = (await GetAsync("team/"))["items"]?.AsArray() ?? new();
        await RefreshInformationAsync();
    }

    public async Task RefreshInformationAsync()
    {
        if (ProjectId == 0) return;
        var bible = await GetAsync("information/" + ProjectId + "/");
        GameInfo = bible["info"]?.AsObject() ?? new();
        Events = bible["events"]?.AsArray() ?? new();
        Characters = bible["characters"]?.AsArray() ?? new();
    }

    public async Task SaveInfoAsync(IDictionary<string, string> values)
    {
        var result = (JsonObject)GameInfo.DeepClone();
        foreach (var kv in values) result[kv.Key] = kv.Value;
        await PutAsync("information/" + ProjectId + "/", result);
        await RefreshInformationAsync();
    }

    public async Task AddEventAsync(string name, string chapter, string summary)
    {
        await PostAsync("information/" + ProjectId + "/events/", new JsonObject {
            ["title"] = name, ["chapter"] = chapter, ["summary"] = summary,
            ["kind"] = "main", ["order"] = Events.Count + 1,
        });
        await RefreshInformationAsync();
    }

    public async Task AddCharacterAsync(string name, string role, string bio)
    {
        await PostAsync("information/" + ProjectId + "/characters/", new JsonObject {
            ["name"] = name, ["role"] = role, ["bio"] = bio, ["order"] = 1,
        });
        await RefreshInformationAsync();
    }

    public async Task AddPostAsync(string title, string body, string kind)
    {
        await PostAsync("posts/", new JsonObject {
            ["project"] = ProjectId, ["title"] = title, ["body"] = body,
            ["kind"] = kind, ["status"] = "published", ["pinned"] = false,
        });
        Posts = (await GetAsync("posts/"))["items"]?.AsArray() ?? new();
    }

    public async Task AddTaskAsync(string title, string description)
    {
        await PostAsync("tasks/", new JsonObject {
            ["project"] = ProjectId, ["title"] = title, ["description"] = description,
            ["status"] = "todo", ["priority"] = "normal",
        });
        Tasks = (await GetAsync("tasks/"))["items"]?.AsArray() ?? new();
    }

    public async Task UpdateTaskAsync(JsonNode task, string status)
    {
        var content = new JsonObject {
            ["project"] = task["project_id"]?.GetValue<int>() ?? ProjectId,
            ["title"] = task["title"]?.ToString() ?? "",
            ["description"] = task["description"]?.ToString() ?? "",
            ["status"] = status,
            ["priority"] = task["priority"]?.ToString() ?? "normal",
            ["assignee"] = task["assignee_id"]?.GetValue<int>(),
            ["due_date"] = task["due_date"]?.ToString() ?? "",
        };
        await PatchAsync("tasks/" + task["id"]?.GetValue<int>() + "/", content);
        Tasks = (await GetAsync("tasks/"))["items"]?.AsArray() ?? new();
    }

    public async Task<string> DownloadAsync(JsonNode file)
    {
        var path = file["download_path"]?.ToString()?.Replace("/api/v1/", "") ?? "";
        using var response = await SendAsync(path, HttpMethod.Get);
        var name = Path.GetFileName(file["original_name"]?.ToString() ?? "download");
        var folder = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "Nightwell Dev", "Downloads");
        Directory.CreateDirectory(folder);
        var destination = Path.Combine(folder, Guid.NewGuid().ToString("N")[..7] + "-" + name);
        await using var stream = File.Create(destination);
        await response.Content.CopyToAsync(stream);
        return destination;
    }

    public async Task UploadAsync(string path)
    {
        using var content = new MultipartFormDataContent();
        content.Add(new StringContent(ProjectId.ToString()), "project");
        content.Add(new StringContent(Path.GetFileName(path)), "title");
        content.Add(new StringContent(""), "description");
        await using var input = File.OpenRead(path);
        using var fileContent = new StreamContent(input);
        content.Add(fileContent, "file", Path.GetFileName(path));
        using var response = await SendAsync("files/", HttpMethod.Post, content);
        Files = (await GetAsync("files/"))["items"]?.AsArray() ?? new();
    }

    public async Task ChangePasswordAsync(string old, string fresh)
    {
        await PostAsync("auth/password/", new JsonObject { ["old_password"] = old, ["new_password"] = fresh });
        await SignOutAsync(false);
    }

    public async Task SignOutAsync(bool contactServer = true)
    {
        if (contactServer && SignedIn)
            try { await PostAsync("auth/logout/", new JsonObject()); } catch { }
        token = null;
        Username = "";
        Role = "";
        try
        {
            var vault = new PasswordVault();
            foreach (var entry in vault.FindAllByResource(VaultResource)) vault.Remove(entry);
        }
        catch { }
    }
}
