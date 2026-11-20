package fun.nightwell.dev

import android.content.Context
import android.net.Uri
import android.provider.OpenableColumns
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import okio.BufferedSink
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.IOException
import java.util.concurrent.TimeUnit

const val API_BASE = "https://nightwell-dev-web-production.up.railway.app/api/v1/"

class DevBackend(private val context: Context) {
    private val client = OkHttpClient.Builder().connectTimeout(15, TimeUnit.SECONDS).readTimeout(40, TimeUnit.SECONDS).build()
    private val masterKey = MasterKey.Builder(context).setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build()
    private val prefs = EncryptedSharedPreferences.create(
        context, "nightwell_dev_secure", masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )
    var token by mutableStateOf(prefs.getString("access_token", "") ?: "")
        private set
    var username by mutableStateOf("")
        private set
    var role by mutableStateOf("")
        private set
    var busy by mutableStateOf(false)
        private set
    var error by mutableStateOf("")
        private set
    var selectedProject by mutableStateOf(0)
    var info by mutableStateOf<JSONObject?>(null)
        private set
    var storyEvents by mutableStateOf(JSONArray())
        private set
    var characters by mutableStateOf(JSONArray())
        private set
    var counts by mutableStateOf(JSONObject())
        private set
    val projects = mutableStateListOf<JSONObject>()
    val posts = mutableStateListOf<JSONObject>()
    val tasks = mutableStateListOf<JSONObject>()
    val files = mutableStateListOf<JSONObject>()
    val team = mutableStateListOf<JSONObject>()

    private fun request(path: String, method: String, body: RequestBody?, auth: Boolean): Request {
        val builder = Request.Builder().url(API_BASE + path).header("Accept", "application/json")
        if (auth && token.isNotEmpty()) builder.header("Authorization", "Bearer " + token)
        return builder.method(method, body).build()
    }

    private suspend fun call(path: String, method: String = "GET", body: JSONObject? = null, auth: Boolean = true): JSONObject =
        withContext(Dispatchers.IO) {
            val payload = body?.toString()?.toRequestBody("application/json; charset=utf-8".toMediaType())
            client.newCall(request(path, method, payload, auth)).execute().use { response ->
                val json = runCatching { JSONObject(response.body?.string() ?: "") }.getOrElse { JSONObject() }
                if (!response.isSuccessful) throw IOException(json.optString("error", "HTTP " + response.code))
                json
            }
        }

    private fun array(result: JSONObject): List<JSONObject> {
        val arr = result.optJSONArray("items") ?: JSONArray()
        return (0 until arr.length()).mapNotNull { arr.optJSONObject(it) }
    }

    private fun replace(dst: MutableList<JSONObject>, items: List<JSONObject>) {
        dst.clear()
        dst.addAll(items)
    }

    suspend fun signIn(user: String, password: String) {
        busy = true
        error = ""
        try {
            val reply = call("auth/login/", "POST", JSONObject().put("username", user)
                .put("password", password).put("device_name", "Android"), false)
            token = reply.getString("token")
            prefs.edit().putString("access_token", token).apply()
            username = reply.getJSONObject("user").getString("username")
            role = reply.getJSONObject("user").getString("role")
            refresh()
        } catch (t: Exception) { error = t.message ?: "Ошибка входа" }
        finally { busy = false }
    }

    suspend fun refresh() {
        if (token.isEmpty()) return
        busy = true
        try {
            val me = call("me/").getJSONObject("user")
            username = me.optString("username")
            role = me.optString("role")
            val p = array(call("projects/"))
            replace(projects, p)
            if (selectedProject == 0) selectedProject = p.firstOrNull()?.optInt("id") ?: 0
            counts = call("dashboard/").optJSONObject("counts") ?: JSONObject()
            replace(posts, array(call("posts/")))
            replace(tasks, array(call("tasks/")))
            replace(files, array(call("files/")))
            replace(team, array(call("team/")))
            loadBible()
            error = ""
        } catch (t: Exception) {
            error = t.message ?: "Не удалось загрузить данные"
            if (error.contains("Сессия истекла") || error.contains("Требуется вход")) signOut(true)
        }
        finally { busy = false }
    }

    suspend fun loadBible() {
        if (selectedProject == 0) return
        try {
            val bible = call("information/" + selectedProject + "/")
            info = bible.optJSONObject("info")
            storyEvents = bible.optJSONArray("events") ?: JSONArray()
            characters = bible.optJSONArray("characters") ?: JSONArray()
        } catch (t: Exception) { error = t.message ?: "Ошибка загрузки информации" }
    }

    suspend fun updateBible(values: Map<String, String>) {
        val merged = JSONObject(info?.toString() ?: "{}")
        for ((key, value) in values) merged.put(key, value)
        call("information/" + selectedProject + "/", "PUT", merged)
        loadBible()
    }

    suspend fun addEvent(title: String, chapter: String, summary: String) {
        call("information/" + selectedProject + "/events/", "POST", JSONObject()
            .put("title", title).put("chapter", chapter).put("summary", summary)
            .put("kind", "main").put("order", storyEvents.length() + 1))
        loadBible()
    }

    suspend fun addCharacter(name: String, role: String, bio: String) {
        call("information/" + selectedProject + "/characters/", "POST", JSONObject()
            .put("name", name).put("role", role).put("bio", bio).put("order", 1))
        loadBible()
    }

    suspend fun createPost(title: String, body: String, kind: String) {
        call("posts/", "POST", JSONObject().put("project", selectedProject)
            .put("title", title).put("body", body).put("kind", kind)
            .put("status", "published").put("pinned", false))
        replace(posts, array(call("posts/")))
    }

    suspend fun createTask(title: String, description: String) {
        call("tasks/", "POST", JSONObject().put("project", selectedProject)
            .put("title", title).put("description", description)
            .put("status", "todo").put("priority", "normal"))
        replace(tasks, array(call("tasks/")))
    }

    suspend fun changeTaskStatus(task: JSONObject, status: String) {
        val input = JSONObject().put("project", task.getInt("project_id"))
            .put("title", task.getString("title")).put("description", task.optString("description"))
            .put("priority", task.optString("priority")).put("status", status)
            .put("assignee", task.optInt("assignee_id").takeIf { it > 0 } ?: "")
            .put("due_date", task.optString("due_date").takeUnless { it == "null" } ?: "")
        call("tasks/" + task.getInt("id") + "/", "PATCH", input)
        replace(tasks, array(call("tasks/")))
    }

    suspend fun download(asset: JSONObject): File = withContext(Dispatchers.IO) {
        val path = asset.getString("download_path").removePrefix("/api/v1/")
        client.newCall(request(path, "GET", null, true)).execute().use { response ->
            if (!response.isSuccessful) throw IOException("Не удалось скачать файл")
            val name = asset.getString("original_name").substringAfterLast('/').substringAfterLast('\\')
            val file = File(context.cacheDir, System.currentTimeMillis().toString() + "-" + name)
            response.body?.byteStream()?.use { input ->
                file.outputStream().use { output -> input.copyTo(output) }
            } ?: throw IOException("Пустой файл")
            file
        }
    }

    suspend fun upload(uri: Uri) = withContext(Dispatchers.IO) {
        if (selectedProject == 0) throw IOException("Проект не выбран")
        var name = "material.bin"
        context.contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use { cursor ->
            if (cursor.moveToFirst()) name = cursor.getString(0)
        }
        val content = object : RequestBody() {
            override fun contentType() = (context.contentResolver.getType(uri) ?: "application/octet-stream").toMediaType()
            override fun writeTo(sink: BufferedSink) {
                context.contentResolver.openInputStream(uri)?.use { input ->
                    val buffer = ByteArray(8192)
                    while (true) {
                        val amount = input.read(buffer)
                        if (amount == -1) break
                        sink.write(buffer, 0, amount)
                    }
                } ?: throw IOException("Файл недоступен")
            }
        }
        val multipart = MultipartBody.Builder().setType(MultipartBody.FORM)
            .addFormDataPart("project", selectedProject.toString())
            .addFormDataPart("title", name).addFormDataPart("description", "")
            .addFormDataPart("file", name, content).build()
        client.newCall(request("files/", "POST", multipart, true)).execute().use {
            if (!it.isSuccessful) throw IOException("Ошибка загрузки: " + it.code)
        }
        val updated = array(call("files/"))
        withContext(Dispatchers.Main) { replace(files, updated) }
    }

    suspend fun changePassword(old: String, fresh: String) {
        call("auth/password/", "POST", JSONObject().put("old_password", old).put("new_password", fresh))
        signOut(localOnly = true)
    }

    suspend fun signOut(localOnly: Boolean = false) {
        if (!localOnly && token.isNotEmpty()) runCatching { call("auth/logout/", "POST", JSONObject()) }
        token = ""
        username = ""
        role = ""
        prefs.edit().remove("access_token").apply()
        info = null
        projects.clear(); posts.clear(); tasks.clear(); files.clear(); team.clear()
    }
}
