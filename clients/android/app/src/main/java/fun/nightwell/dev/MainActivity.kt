package com.nightwell.dev

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.FileProvider
import kotlinx.coroutines.launch
import org.json.JSONObject

private val background = Color(0xFF090A0C)
private val glass = Color(0xFF1B1C20)
private val border = Color(0xFF34363B)
private val muted = Color(0xFFA3A6AE)
private val white = Color(0xFFF8F8FA)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            val backend = remember { DevBackend(applicationContext) }
            LaunchedEffect(Unit) { if (backend.token.isNotEmpty()) backend.refresh() }
            MaterialTheme(colorScheme = darkColorScheme(
                primary = white, onPrimary = background,
                secondary = Color(0xFFD5D7DC), background = background,
                surface = glass, onSurface = white, onBackground = white
            )) {
                if (backend.token.isEmpty()) Login(backend) else Workspace(backend)
            }
        }
    }
}

@Composable
private fun GlassCard(onClick: (() -> Unit)? = null, content: @Composable ColumnScope.() -> Unit) {
    val clickable = if (onClick == null) Modifier else Modifier.clickable(onClick = onClick)
    Column(
        Modifier.fillMaxWidth().then(clickable).border(1.dp, border, RoundedCornerShape(23.dp))
            .background(glass, RoundedCornerShape(23.dp)).padding(18.dp),
        content = content
    )
}

@Composable
private fun Header(label: String, caption: String) {
    Column(Modifier.fillMaxWidth().padding(bottom = 7.dp)) {
        Text(caption.uppercase(), fontSize = 10.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.5.sp, color = muted)
        Text(label, fontSize = 32.sp, fontWeight = FontWeight.Bold, letterSpacing = (-1.4).sp)
    }
}

@Composable
private fun Subtitle(text: String) {
    Text(text, fontSize = 13.sp, color = muted, lineHeight = 19.sp)
}

@Composable
private fun Login(client: DevBackend) {
    var username by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    val scope = rememberCoroutineScope()
    Column(
        Modifier.fillMaxSize().background(background).verticalScroll(rememberScrollState())
            .padding(horizontal = 24.dp).padding(top = 74.dp, bottom = 40.dp),
        verticalArrangement = Arrangement.spacedBy(19.dp)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(13.dp)) {
            Box(Modifier.size(45.dp).background(white, RoundedCornerShape(14.dp)), contentAlignment = Alignment.Center) {
                Text("N", fontSize = 27.sp, fontWeight = FontWeight.Black, color = background)
            }
            Column {
                Text("NIGHTWELL STUDIO", fontWeight = FontWeight.ExtraBold, fontSize = 15.sp, letterSpacing = 1.sp)
                Text("DEVELOPER SPACE", color = muted, fontSize = 10.sp, letterSpacing = 1.5.sp)
            }
        }
        Spacer(Modifier.height(38.dp))
        Text("Там, где\nсоздаются миры.", fontSize = 42.sp, fontWeight = FontWeight.Bold, lineHeight = 47.sp)
        Subtitle("Сюжет, задачи, заметки и материалы команды в одном закрытом пространстве.")
        Spacer(Modifier.height(10.dp))
        GlassCard {
            Text("ДОСТУП ПО ПРИГЛАШЕНИЮ", fontSize = 10.sp, letterSpacing = 1.6.sp, color = muted)
            Spacer(Modifier.height(10.dp))
            Text("С возвращением", fontSize = 23.sp, fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(18.dp))
            OutlinedTextField(username, { username = it }, label = { Text("Логин") }, singleLine = true,
                modifier = Modifier.fillMaxWidth())
            Spacer(Modifier.height(9.dp))
            OutlinedTextField(password, { password = it }, label = { Text("Пароль") },
                visualTransformation = PasswordVisualTransformation(), singleLine = true,
                modifier = Modifier.fillMaxWidth(), keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password))
            if (client.error.isNotBlank()) {
                Spacer(Modifier.height(9.dp))
                Text(client.error, color = Color(0xFFFFAA9D), fontSize = 12.sp)
            }
            Spacer(Modifier.height(16.dp))
            Button(
                onClick = { scope.launch { client.signIn(username, password) } },
                enabled = username.isNotBlank() && password.isNotBlank() && !client.busy,
                modifier = Modifier.fillMaxWidth().height(51.dp),
                shape = RoundedCornerShape(16.dp)
            ) { Text("Войти в пространство", fontWeight = FontWeight.Bold) }
        }
        Subtitle("Регистрация отключена. Доступ выдаёт администратор.")
    }
}

private enum class Tab(val label: String) {
    HOME("Главная"), INFO("Информация"), JOURNAL("Дневник"), TASKS("Задачи"), MORE("Ещё")
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun Workspace(client: DevBackend) {
    var tab by remember { mutableStateOf(Tab.HOME) }
    val scope = rememberCoroutineScope()
    val icons = mapOf(Tab.HOME to Icons.Default.Home, Tab.INFO to Icons.Default.Info,
        Tab.JOURNAL to Icons.Default.Article, Tab.TASKS to Icons.Default.Checklist,
        Tab.MORE to Icons.Default.MoreHoriz)
    Scaffold(
        containerColor = background,
        topBar = {
            TopAppBar(
                title = { Text("NIGHTWELL STUDIO  /  " + tab.label.uppercase(), fontSize = 11.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.1.sp) },
                actions = {
                    IconButton(onClick = { scope.launch { client.refresh() } }) {
                        Icon(Icons.Default.Refresh, contentDescription = "Обновить")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = background)
            )
        },
        bottomBar = {
            NavigationBar(containerColor = Color(0xFF202125), tonalElevation = 0.dp) {
                Tab.entries.forEach { item ->
                    NavigationBarItem(
                        selected = tab == item,
                        onClick = { tab = item },
                        icon = { Icon(icons[item] ?: Icons.Default.Home, contentDescription = item.label) },
                        label = { Text(item.label, fontSize = 10.sp) },
                        colors = NavigationBarItemDefaults.colors(
                            selectedIconColor = white, selectedTextColor = white,
                            indicatorColor = Color(0xFF43454B), unselectedIconColor = muted, unselectedTextColor = muted
                        )
                    )
                }
            }
        }
    ) { inset ->
        Column(Modifier.padding(inset).fillMaxSize()) {
            if (client.busy) LinearProgressIndicator(Modifier.fillMaxWidth())
            if (client.error.isNotBlank()) {
                Text(client.error, Modifier.fillMaxWidth().padding(10.dp),
                    color = Color(0xFFFFAD99), fontSize = 12.sp)
            }
            when (tab) {
                Tab.HOME -> Overview(client)
                Tab.INFO -> Information(client)
                Tab.JOURNAL -> Journal(client)
                Tab.TASKS -> Tasks(client)
                Tab.MORE -> More(client)
            }
        }
    }
}

@Composable
private fun Overview(client: DevBackend) {
    LazyColumn(contentPadding = PaddingValues(18.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
        item { Header("Твоя команда.", "NIGHTWELL STUDIO / WORKSPACE") }
        item {
            GlassCard {
                Text("СОЗДАВАЙТЕ МИРЫ ВМЕСТЕ", fontSize = 10.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.3.sp, color = muted)
                Spacer(Modifier.height(13.dp))
                Text("Все идеи.\nОдна история.", fontSize = 30.sp, lineHeight = 34.sp, fontWeight = FontWeight.Bold)
                Spacer(Modifier.height(12.dp))
                Subtitle("От первой заметки до последней главы игры.")
            }
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Box(Modifier.weight(1f)) { CountTile("Записи", client.counts.optInt("posts")) }
                Box(Modifier.weight(1f)) { CountTile("Задачи", client.counts.optInt("tasks")) }
            }
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Box(Modifier.weight(1f)) { CountTile("Файлы", client.counts.optInt("files")) }
                Box(Modifier.weight(1f)) { CountTile("Команда", client.counts.optInt("members")) }
            }
        }
        item { Text("Последние публикации", fontWeight = FontWeight.Bold, fontSize = 20.sp) }
        items(client.posts.take(6)) { post -> GlassCard {
            Text(post.optString("title"), fontWeight = FontWeight.SemiBold, fontSize = 15.sp)
            Spacer(Modifier.height(5.dp))
            Subtitle(post.optString("project") + " · " + post.optString("author"))
        } }
    }
}

@Composable
private fun CountTile(label: String, count: Int) {
    GlassCard {
        Subtitle(label)
        Spacer(Modifier.height(9.dp))
        Text(count.toString(), fontSize = 33.sp, fontWeight = FontWeight.Bold)
    }
}

@Composable
private fun Information(client: DevBackend) {
    val scope = rememberCoroutineScope()
    var expandedProjects by remember { mutableStateOf(false) }
    var infoEditor by remember { mutableStateOf(false) }
    var newEvent by remember { mutableStateOf(false) }
    var newCharacter by remember { mutableStateOf(false) }
    val current = client.info
    LazyColumn(contentPadding = PaddingValues(18.dp), verticalArrangement = Arrangement.spacedBy(13.dp)) {
        item { Header("Информация.", "GAME BIBLE / СЮЖЕТ И ВСЕЛЕННАЯ") }
        if (client.projects.isNotEmpty()) {
            item {
                Box {
                    OutlinedButton(onClick = { expandedProjects = true }) {
                        Icon(Icons.Default.Folder, null); Spacer(Modifier.width(8.dp))
                        Text(client.projects.firstOrNull { it.optInt("id") == client.selectedProject }?.optString("name") ?: "Проект")
                        Icon(Icons.Default.ArrowDropDown, null)
                    }
                    DropdownMenu(expandedProjects, { expandedProjects = false }) {
                        client.projects.forEach { project ->
                            DropdownMenuItem(text = { Text(project.optString("name")) }, onClick = {
                                expandedProjects = false
                                client.selectedProject = project.optInt("id")
                                scope.launch { client.loadBible() }
                            })
                        }
                    }
                }
            }
        }
        item {
            GlassCard {
                Subtitle("ИГРА / ЖАНР")
                Spacer(Modifier.height(8.dp))
                Text(current?.optString("title")?.takeIf { it.isNotBlank() }
                    ?: current?.optString("project") ?: "Проект", fontSize = 29.sp, fontWeight = FontWeight.Bold)
                Spacer(Modifier.height(9.dp))
                Subtitle(current?.optString("tagline") ?: "")
                Spacer(Modifier.height(10.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    InfoTag(current?.optString("genre")?.takeIf { it.isNotEmpty() } ?: "Жанр не указан")
                    InfoTag(current?.optString("development_status")?.takeIf { it.isNotEmpty() } ?: "В разработке")
                }
                if (client.role != "viewer") {
                    Spacer(Modifier.height(15.dp))
                    OutlinedButton(onClick = { infoEditor = true }) { Icon(Icons.Default.Edit, null); Spacer(Modifier.width(7.dp)); Text("Редактировать") }
                }
            }
        }
        item { InfoPanel("Сюжет", current?.optString("story"), "Сюжет пока не описан") }
        item { InfoPanel("Мир и сеттинг", current?.optString("setting"), "Сеттинг ещё не заполнен") }
        item { InfoPanel("Геймплей", current?.optString("gameplay"), "Пока нет описания механик") }
        item { InfoPanel("Лор", current?.optString("universe"), "Предыстория не добавлена") }
        item { InfoPanel("Темы и атмосфера", current?.optString("themes"), "Пока нет описания") }
        item { InfoPanel("Прочее", current?.optString("notes"), "Дополнительных заметок нет") }
        item { SectionHeader("События", client.role != "viewer") { newEvent = true } }
        if (client.storyEvents.length() == 0) item { Subtitle("Событий пока нет. Создайте первую главу.") }
        items(client.storyEvents.length()) { index ->
            val event = client.storyEvents.optJSONObject(index)
            var open by remember(event?.optInt("id")) { mutableStateOf(false) }
            if (event != null) {
                GlassCard(onClick = { open = !open }) {
                    Subtitle((event.optString("chapter").ifBlank { "Событие " + event.optInt("order") }) + " · " + event.optString("kind"))
                    Spacer(Modifier.height(5.dp))
                    Text(event.optString("title"), fontWeight = FontWeight.Bold, fontSize = 18.sp)
                    if (event.optBoolean("spoiler")) Text("Спойлер", color = Color(0xFFE9C189), fontSize = 11.sp)
                    if (open) {
                        Spacer(Modifier.height(10.dp))
                        Text(event.optString("summary"), fontSize = 13.sp)
                        Spacer(Modifier.height(6.dp))
                        Text(event.optString("description"), fontSize = 13.sp, color = muted)
                        Text(event.optString("consequences"), fontSize = 13.sp, color = muted)
                    } else if (event.optString("summary").isNotBlank()) {
                        Spacer(Modifier.height(7.dp))
                        Subtitle(event.optString("summary").take(120))
                    }
                }
            }
        }
        item { SectionHeader("Персонажи", client.role != "viewer") { newCharacter = true } }
        items(client.characters.length()) { index ->
            val character = client.characters.optJSONObject(index)
            if (character != null) GlassCard {
                Text(character.optString("name"), fontWeight = FontWeight.Bold, fontSize = 18.sp)
                Subtitle(character.optString("role"))
                if (character.optString("bio").isNotEmpty()) {
                    Spacer(Modifier.height(9.dp))
                    Text(character.optString("bio"), fontSize = 13.sp, color = muted)
                }
            }
        }
    }
    if (infoEditor) EditInfoDialog(client) { infoEditor = false }
    if (newEvent) AddEventDialog(client) { newEvent = false }
    if (newCharacter) AddCharacterDialog(client) { newCharacter = false }
}

@Composable
private fun InfoTag(text: String) {
    Text(text, color = white, fontSize = 11.sp, maxLines = 2,
        modifier = Modifier.background(Color(0xFF3A3B40), RoundedCornerShape(18.dp)).padding(9.dp))
}

@Composable
private fun InfoPanel(title: String, text: String?, empty: String) {
    GlassCard {
        Text(title, fontWeight = FontWeight.Bold, fontSize = 19.sp)
        Spacer(Modifier.height(10.dp))
        Text(text?.takeIf { it.isNotBlank() } ?: empty, color = muted, fontSize = 13.sp, lineHeight = 21.sp)
    }
}

@Composable
private fun SectionHeader(text: String, editable: Boolean, add: () -> Unit) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Text(text, fontWeight = FontWeight.Bold, fontSize = 22.sp, modifier = Modifier.weight(1f))
        if (editable) IconButton(onClick = add) { Icon(Icons.Default.Add, "Добавить") }
    }
}

@Composable
private fun EditInfoDialog(client: DevBackend, onClose: () -> Unit) {
    val scope = rememberCoroutineScope()
    var genre by remember { mutableStateOf(client.info?.optString("genre") ?: "") }
    var plot by remember { mutableStateOf(client.info?.optString("story") ?: "") }
    var setting by remember { mutableStateOf(client.info?.optString("setting") ?: "") }
    var gameplay by remember { mutableStateOf(client.info?.optString("gameplay") ?: "") }
    var err by remember { mutableStateOf("") }
    AlertDialog(onDismissRequest = onClose, title = { Text("Информация об игре") }, text = {
        Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            OutlinedTextField(genre, { genre = it }, label = { Text("Жанр") })
            OutlinedTextField(plot, { plot = it }, label = { Text("Сюжет") }, minLines = 4)
            OutlinedTextField(setting, { setting = it }, label = { Text("Мир и сеттинг") }, minLines = 3)
            OutlinedTextField(gameplay, { gameplay = it }, label = { Text("Геймплей") }, minLines = 3)
            if (err.isNotEmpty()) Text(err, color = Color(0xFFFFAF9E))
        }
    }, confirmButton = {
        TextButton(onClick = {
            scope.launch {
                runCatching { client.updateBible(mapOf("genre" to genre, "story" to plot, "setting" to setting, "gameplay" to gameplay)) }
                    .onSuccess { onClose() }.onFailure { err = it.message ?: "Ошибка сохранения" }
            }
        }) { Text("Сохранить") }
    }, dismissButton = { TextButton(onClick = onClose) { Text("Отмена") } })
}

@Composable
private fun AddEventDialog(client: DevBackend, onClose: () -> Unit) {
    val scope = rememberCoroutineScope()
    var title by remember { mutableStateOf("") }
    var chapter by remember { mutableStateOf("") }
    var summary by remember { mutableStateOf("") }
    var err by remember { mutableStateOf("") }
    AlertDialog(onDismissRequest = onClose, title = { Text("Новое событие") }, text = {
        Column(verticalArrangement = Arrangement.spacedBy(9.dp)) {
            OutlinedTextField(title, { title = it }, label = { Text("Название") })
            OutlinedTextField(chapter, { chapter = it }, label = { Text("Глава или акт") })
            OutlinedTextField(summary, { summary = it }, label = { Text("Содержание") }, minLines = 3)
            if (err.isNotEmpty()) Text(err, color = Color(0xFFFFAF9E))
        }
    }, confirmButton = {
        TextButton(enabled = title.isNotBlank(), onClick = {
            scope.launch {
                runCatching { client.addEvent(title, chapter, summary) }
                    .onSuccess { onClose() }.onFailure { err = it.message ?: "Ошибка сохранения" }
            }
        }) { Text("Добавить") }
    }, dismissButton = { TextButton(onClick = onClose) { Text("Отмена") } })
}

@Composable
private fun AddCharacterDialog(client: DevBackend, onClose: () -> Unit) {
    val scope = rememberCoroutineScope()
    var name by remember { mutableStateOf("") }
    var role by remember { mutableStateOf("") }
    var bio by remember { mutableStateOf("") }
    var err by remember { mutableStateOf("") }
    AlertDialog(onDismissRequest = onClose, title = { Text("Новый персонаж") }, text = {
        Column(verticalArrangement = Arrangement.spacedBy(9.dp)) {
            OutlinedTextField(name, { name = it }, label = { Text("Имя") })
            OutlinedTextField(role, { role = it }, label = { Text("Роль") })
            OutlinedTextField(bio, { bio = it }, label = { Text("Биография") }, minLines = 3)
            if (err.isNotEmpty()) Text(err, color = Color(0xFFFFAF9E))
        }
    }, confirmButton = {
        TextButton(enabled = name.isNotBlank(), onClick = {
            scope.launch {
                runCatching { client.addCharacter(name, role, bio) }
                    .onSuccess { onClose() }.onFailure { err = it.message ?: "Ошибка сохранения" }
            }
        }) { Text("Добавить") }
    }, dismissButton = { TextButton(onClick = onClose) { Text("Отмена") } })
}

@Composable
private fun Journal(client: DevBackend) {
    var docs by remember { mutableStateOf(false) }
    var editor by remember { mutableStateOf(false) }
    var selected by remember { mutableStateOf<JSONObject?>(null) }
    LazyColumn(contentPadding = PaddingValues(18.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item { Header("Дневник.", "ЗАПИСИ И ДОКУМЕНТАЦИЯ") }
        item {
            Row(verticalAlignment = Alignment.CenterVertically) {
                FilterChip(selected = !docs, onClick = { docs = false }, label = { Text("Записи") })
                Spacer(Modifier.width(8.dp))
                FilterChip(selected = docs, onClick = { docs = true }, label = { Text("Документация") })
                Spacer(Modifier.weight(1f))
                if (client.role != "viewer") IconButton(onClick = { editor = true }) { Icon(Icons.Default.Add, null) }
            }
        }
        items(client.posts.filter { (it.optString("kind") == "doc") == docs }) { post ->
            GlassCard(onClick = { selected = post }) {
                Subtitle(post.optString("kind").uppercase() + " · " + post.optString("project"))
                Spacer(Modifier.height(7.dp))
                Text(post.optString("title"), fontWeight = FontWeight.Bold, fontSize = 19.sp)
                Spacer(Modifier.height(7.dp))
                Subtitle(post.optString("body").take(165))
                Spacer(Modifier.height(9.dp))
                Subtitle(post.optString("author"))
            }
        }
    }
    if (editor) AddPostDialog(client) { editor = false }
    selected?.let { post -> AlertDialog(onDismissRequest = { selected = null },
        title = { Text(post.optString("title")) },
        text = { Column(Modifier.verticalScroll(rememberScrollState())) { Text(post.optString("body"), fontSize = 14.sp) } },
        confirmButton = { TextButton(onClick = { selected = null }) { Text("Закрыть") } }) }
}

@Composable
private fun AddPostDialog(client: DevBackend, onClose: () -> Unit) {
    val scope = rememberCoroutineScope()
    var title by remember { mutableStateOf("") }
    var body by remember { mutableStateOf("") }
    var kind by remember { mutableStateOf("note") }
    var err by remember { mutableStateOf("") }
    AlertDialog(onDismissRequest = onClose, title = { Text("Новая запись") }, text = {
        Column(verticalArrangement = Arrangement.spacedBy(9.dp)) {
            OutlinedTextField(title, { title = it }, label = { Text("Заголовок") })
            Row {
                FilterChip(selected = kind == "note", onClick = { kind = "note" }, label = { Text("Заметка") })
                Spacer(Modifier.width(8.dp))
                FilterChip(selected = kind == "doc", onClick = { kind = "doc" }, label = { Text("Документ") })
            }
            OutlinedTextField(body, { body = it }, label = { Text("Текст") }, minLines = 5)
            if (err.isNotBlank()) Text(err, color = Color(0xFFFFAD9C))
        }
    }, confirmButton = {
        TextButton(enabled = title.isNotBlank(), onClick = {
            scope.launch {
                runCatching { client.createPost(title, body, kind) }
                    .onSuccess { onClose() }.onFailure { err = it.message ?: "Ошибка" }
            }
        }) { Text("Опубликовать") }
    }, dismissButton = { TextButton(onClick = onClose) { Text("Отмена") } })
}

@Composable
private fun Tasks(client: DevBackend) {
    var editor by remember { mutableStateOf(false) }
    val groups = listOf("todo" to "К выполнению", "progress" to "В работе",
        "review" to "На проверке", "done" to "Готово")
    val scope = rememberCoroutineScope()
    LazyColumn(contentPadding = PaddingValues(18.dp), verticalArrangement = Arrangement.spacedBy(11.dp)) {
        item { Header("Задачи.", "ДОСКА РАЗРАБОТКИ") }
        item { if (client.role != "viewer") OutlinedButton(onClick = { editor = true }) {
            Icon(Icons.Default.Add, null); Spacer(Modifier.width(7.dp)); Text("Новая задача")
        } }
        groups.forEach { group ->
            item { Text(group.second, fontWeight = FontWeight.Bold, fontSize = 20.sp, modifier = Modifier.padding(top = 13.dp)) }
            items(client.tasks.filter { it.optString("status") == group.first }) { task ->
                GlassCard {
                    Text(task.optString("title"), fontWeight = FontWeight.Bold)
                    Spacer(Modifier.height(6.dp))
                    Subtitle(task.optString("description").ifBlank { task.optString("project") })
                    if (client.role != "viewer") {
                        var expanded by remember { mutableStateOf(false) }
                        Box {
                            TextButton(onClick = { expanded = true }) { Text("Статус ▾") }
                            DropdownMenu(expanded, { expanded = false }) {
                                groups.forEach { value ->
                                    DropdownMenuItem(text = { Text(value.second) }, onClick = {
                                        expanded = false
                                        scope.launch { runCatching { client.changeTaskStatus(task, value.first) } }
                                    })
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    if (editor) AddTaskDialog(client) { editor = false }
}

@Composable
private fun AddTaskDialog(client: DevBackend, onClose: () -> Unit) {
    val scope = rememberCoroutineScope()
    var title by remember { mutableStateOf("") }
    var description by remember { mutableStateOf("") }
    var err by remember { mutableStateOf("") }
    AlertDialog(onDismissRequest = onClose, title = { Text("Новая задача") }, text = {
        Column(verticalArrangement = Arrangement.spacedBy(9.dp)) {
            OutlinedTextField(title, { title = it }, label = { Text("Название") })
            OutlinedTextField(description, { description = it }, label = { Text("Описание") }, minLines = 4)
            if (err.isNotBlank()) Text(err, color = Color(0xFFFFAD9C))
        }
    }, confirmButton = {
        TextButton(enabled = title.isNotBlank(), onClick = {
            scope.launch {
                runCatching { client.createTask(title, description) }
                    .onSuccess { onClose() }.onFailure { err = it.message ?: "Ошибка" }
            }
        }) { Text("Создать") }
    }, dismissButton = { TextButton(onClick = onClose) { Text("Отмена") } })
}

@Composable
private fun More(client: DevBackend) {
    val scope = rememberCoroutineScope()
    val context = LocalContext.current
    var subsection by remember { mutableStateOf("") }
    var oldPassword by remember { mutableStateOf("") }
    var newPassword by remember { mutableStateOf("") }
    var localError by remember { mutableStateOf("") }
    val filePicker = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) scope.launch {
            runCatching { client.upload(uri) }.onFailure { localError = it.message ?: "Ошибка загрузки" }
        }
    }
    LazyColumn(contentPadding = PaddingValues(18.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item { Header(when (subsection) { "files" -> "Файлы."; "team" -> "Команда."; "password" -> "Пароль."; else -> "Ещё." }, "NIGHTWELL STUDIO / WORKSPACE") }
        if (subsection.isNotEmpty()) item { OutlinedButton(onClick = { subsection = "" }) {
            Icon(Icons.Default.ArrowBack, null); Text(" Назад")
        } }
        when (subsection) {
            "" -> {
                item { GlassCard(onClick = { subsection = "files" }) {
                    Text("Файлы", fontWeight = FontWeight.Bold); Subtitle("Закрытое хранилище")
                } }
                item { GlassCard(onClick = { subsection = "team" }) {
                    Text("Команда", fontWeight = FontWeight.Bold); Subtitle("Разработчики и роли")
                } }
                item { GlassCard(onClick = { subsection = "password" }) {
                    Text("Сменить пароль", fontWeight = FontWeight.Bold); Subtitle("Безопасность аккаунта")
                } }
                item { GlassCard {
                    Text("Аккаунт: " + client.username)
                    Subtitle("Роль: " + client.role)
                    Spacer(Modifier.height(12.dp))
                    OutlinedButton(onClick = { scope.launch { client.signOut() } }) { Text("Выйти") }
                } }
            }
            "files" -> {
                item { if (client.role != "viewer") OutlinedButton(onClick = { filePicker.launch(arrayOf("*/*")) }) {
                    Icon(Icons.Default.UploadFile, null); Spacer(Modifier.width(7.dp)); Text("Загрузить файл")
                } }
                items(client.files) { file ->
                    GlassCard(onClick = {
                        scope.launch {
                            runCatching {
                                val local = client.download(file)
                                val uri = FileProvider.getUriForFile(context, context.packageName + ".files", local)
                                val intent = Intent(Intent.ACTION_SEND).apply {
                                    type = "application/octet-stream"
                                    putExtra(Intent.EXTRA_STREAM, uri)
                                    addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                                }
                                context.startActivity(Intent.createChooser(intent, "Открыть файл"))
                            }.onFailure { localError = it.message ?: "Не удалось открыть файл" }
                        }
                    }) {
                        Text(file.optString("title"), fontWeight = FontWeight.Bold)
                        Subtitle(file.optString("original_name"))
                        Subtitle("Нажмите для скачивания")
                    }
                }
            }
            "team" -> items(client.team) { user -> GlassCard {
                Text(user.optString("name"), fontWeight = FontWeight.Bold)
                Subtitle(user.optString("role"))
            } }
            "password" -> {
                item { OutlinedTextField(oldPassword, { oldPassword = it },
                    label = { Text("Текущий пароль") }, visualTransformation = PasswordVisualTransformation(),
                    modifier = Modifier.fillMaxWidth()) }
                item { OutlinedTextField(newPassword, { newPassword = it },
                    label = { Text("Новый пароль") }, visualTransformation = PasswordVisualTransformation(),
                    modifier = Modifier.fillMaxWidth()) }
                item { Button(onClick = {
                    scope.launch {
                        runCatching { client.changePassword(oldPassword, newPassword) }
                            .onFailure { localError = it.message ?: "Ошибка" }
                    }
                }, enabled = oldPassword.isNotBlank() && newPassword.isNotBlank()) { Text("Изменить пароль") } }
            }
        }
        if (localError.isNotEmpty()) item { Text(localError, color = Color(0xFFFFAFA0), fontSize = 12.sp) }
    }
}
