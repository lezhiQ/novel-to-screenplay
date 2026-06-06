const API_BASE = "";

const $ = (sel) => document.querySelector(sel);
const titleInput = $("#title");
const textArea = $("#novel-text");
const btnConvert = $("#btn-convert");
const btnYaml = $("#btn-export-yaml");
const btnJson = $("#btn-export-json");
const previewDiv = $("#screenplay-preview");
const yamlPre = $("#yaml-output");

let lastResult = null;

// API 设置
function getApiSettings() {
    return {
        api_key: $("#api-key").value.trim(),
        api_base: $("#api-base").value.trim(),
        model: $("#model-name").value.trim(),
    };
}

// 文件上传
const fileUpload = $("#file-upload");
const fileName = $("#file-name");

fileUpload.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const ext = file.name.split(".").pop().toLowerCase();
    fileName.textContent = file.name;

    if (ext === "txt") {
        // .txt 直接用 FileReader 读取
        const reader = new FileReader();
        reader.onload = () => {
            textArea.value = reader.result;
            // 自动提取标题（去掉扩展名）
            if (titleInput.value === "未命名作品") {
                titleInput.value = file.name.replace(/\.\w+$/, "");
            }
        };
        reader.readAsText(file, "utf-8");
    } else if (ext === "docx" || ext === "pdf") {
        // .docx/.pdf 上传到后端解析
        const formData = new FormData();
        formData.append("file", file);
        try {
            const res = await fetch(`${API_BASE}/api/upload`, {
                method: "POST",
                body: formData,
            });
            const data = await res.json();
            if (data.success) {
                textArea.value = data.text;
                if (titleInput.value === "未命名作品") {
                    titleInput.value = file.name.replace(/\.\w+$/, "");
                }
            } else {
                alert("文件解析失败: " + (data.detail || "未知错误"));
            }
        } catch (err) {
            alert("文件上传失败: " + err.message);
        }
    } else {
        alert("不支持的文件格式，请上传 .txt/.docx/.pdf 文件");
    }

    // 重置 input 以便重复选择同一文件
    fileUpload.value = "";
});

// Tab 切换
document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
        document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
        document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));
        tab.classList.add("active");
        $(`#${tab.dataset.tab}`).classList.add("active");
    });
});

// 转换按钮
btnConvert.addEventListener("click", async () => {
    const title = titleInput.value.trim();
    const text = textArea.value.trim();

    if (!text) {
        alert("请输入小说文本");
        return;
    }

    btnConvert.disabled = true;
    btnConvert.textContent = "转换中...";
    previewDiv.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>正在调用 AI 转换，请稍候...</p></div>';
    yamlPre.textContent = "";

    try {
        // 尝试流式接口
        const success = await convertStream(title, text);
        if (!success) {
            // 流式失败，回退到非流式
            await convertNonStream(title, text);
        }
    } catch (err) {
        previewDiv.innerHTML = `<p style="color:red;text-align:center;">错误: ${err.message}</p>`;
    } finally {
        btnConvert.disabled = false;
        btnConvert.textContent = "开始转换";
    }
});

// 流式转换（第1层：只显示原始文本）
async function convertStream(title, text) {
    try {
        const res = await fetch(`${API_BASE}/api/convert/stream`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title, text, ...getApiSettings() }),
        });

        if (!res.ok) {
            console.log("流式接口返回错误:", res.status);
            return false;
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let yamlContent = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() || "";

            for (const line of lines) {
                if (line.startsWith("data: ")) {
                    const data = line.slice(6);
                    try {
                        const parsed = JSON.parse(data);
                        if (parsed.done) {
                            // 流式完成，移除流式效果
                            yamlPre.classList.remove("streaming");
                            // 优先使用后端发来的结构化结果
                            if (parsed.result) {
                                lastResult = parsed.result;
                            } else {
                                // fallback：前端自行解析 YAML
                                lastResult = parseYamlSafe(yamlContent);
                            }
                            if (lastResult) {
                                renderPreview(lastResult);
                                renderYaml(lastResult);
                                btnYaml.disabled = false;
                                btnJson.disabled = false;
                                document.querySelector('.tab[data-tab="preview"]').click();
                            } else {
                                previewDiv.innerHTML = '<p style="color:#888;text-align:center;">YAML 解析失败，但原始内容已显示在右侧</p>';
                            }
                            return true;
                        } else if (parsed.chunk) {
                            // 实时显示原始 YAML 文本
                            yamlContent += parsed.chunk;
                            yamlPre.textContent = yamlContent;
                            // 添加流式效果
                            yamlPre.classList.add("streaming");
                            // 自动滚动到底部
                            yamlPre.scrollTop = yamlPre.scrollHeight;
                            // 切换到 YAML 标签页
                            document.querySelector('.tab[data-tab="yaml"]').click();
                        }
                    } catch (e) {
                        // 忽略解析错误
                    }
                }
            }
        }
        return true;
    } catch (err) {
        console.log("流式转换失败:", err);
        return false;
    }
}

// 非流式转换（fallback）
async function convertNonStream(title, text) {
    const res = await fetch(`${API_BASE}/api/convert`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, text, ...getApiSettings() }),
    });

    if (!res.ok) throw new Error(`请求失败: ${res.status}`);

    const data = await res.json();
    if (data.success) {
        lastResult = data.data;
        renderPreview(lastResult);
        renderYaml(lastResult);
        btnYaml.disabled = false;
        btnJson.disabled = false;
    } else {
        throw new Error("转换失败");
    }
}

// 安全的 YAML 解析（js-yaml 为主，正则 fallback）
function parseYamlSafe(yamlStr) {
    try {
        // 提取所有 ```yaml ... ``` 代码块（流式输出可能有多个）
        const blocks = [];
        const blockRegex = /```yaml\s*\n([\s\S]*?)```/g;
        let m;
        while ((m = blockRegex.exec(yamlStr)) !== null) {
            blocks.push(m[1].trim());
        }

        // 如果没有代码块标记，尝试直接解析整个内容
        if (blocks.length === 0) {
            blocks.push(yamlStr.trim());
        }

        // 解析每个代码块并合并场景
        const allScenes = [];
        let title = "";
        for (const block of blocks) {
            try {
                const result = jsyaml.load(block);
                if (result) {
                    if (result.title && !title) title = result.title;
                    if (result.scenes && Array.isArray(result.scenes)) {
                        allScenes.push(...result.scenes);
                    }
                }
            } catch (e) {
                console.warn("js-yaml 解析单个代码块失败:", e);
            }
        }

        // 重新编号场景
        allScenes.forEach((s, i) => { s.scene_id = i + 1; });

        if (allScenes.length > 0) {
            return { title: title || "剧本", scenes: allScenes };
        }

        // 所有代码块都解析失败，回退到正则
        return parseYamlFallback(yamlStr);
    } catch (e) {
        console.warn("js-yaml 解析失败，回退到正则解析:", e);
        return parseYamlFallback(yamlStr);
    }
}

// Fallback：正则解析（原有逻辑，支持 items 格式）
function parseYamlFallback(yamlStr) {
    try {
        let clean = yamlStr;
        const match = clean.match(/```yaml\s*\n([\s\S]*?)```/);
        if (match) {
            clean = match[1];
        }

        const result = { title: "", scenes: [] };

        const titleMatch = clean.match(/title:\s*["']?([^"'\n]+)["']?/);
        if (titleMatch) {
            result.title = titleMatch[1].trim();
        }

        const lines = clean.split('\n');
        let currentScene = null;
        let currentSection = null; // 'items', 'dialogues', 'actions'

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const trimmed = line.trim();

            if (!trimmed || trimmed.startsWith('#')) continue;

            if (trimmed.match(/^-?\s*scene_id:\s*(\d+)/)) {
                const sceneIdMatch = trimmed.match(/scene_id:\s*(\d+)/);
                if (sceneIdMatch) {
                    if (currentScene) result.scenes.push(currentScene);
                    currentScene = {
                        scene_id: parseInt(sceneIdMatch[1]),
                        location: "", time: "", description: "",
                        items: [], dialogues: [], actions: []
                    };
                    currentSection = null;
                }
                continue;
            }

            if (!currentScene) continue;

            if (trimmed.match(/^location:\s*/)) {
                currentScene.location = trimmed.replace(/^location:\s*["']?/, '').replace(/["']?$/, '').trim();
                currentSection = null;
            } else if (trimmed.match(/^time:\s*/)) {
                currentScene.time = trimmed.replace(/^time:\s*["']?/, '').replace(/["']?$/, '').trim();
                currentSection = null;
            } else if (trimmed.match(/^description:\s*/)) {
                currentScene.description = trimmed.replace(/^description:\s*["']?/, '').replace(/["']?$/, '').trim();
                currentSection = null;
            } else if (trimmed === 'items:') {
                currentSection = 'items';
            } else if (trimmed === 'dialogues:') {
                currentSection = 'dialogues';
            } else if (trimmed === 'actions:') {
                currentSection = 'actions';
            } else if (currentSection === 'items' && trimmed.startsWith('- type:')) {
                const typeMatch = trimmed.match(/type:\s*(\w+)/);
                if (typeMatch) {
                    const type = typeMatch[1];
                    if (type === 'dialogue') {
                        currentScene.items.push({ type: "dialogue", character: "", line: "", action: "" });
                    } else {
                        currentScene.items.push({ type: "action", character: "", action: "" });
                    }
                }
            } else if (currentSection === 'items' && currentScene.items.length > 0) {
                const last = currentScene.items[currentScene.items.length - 1];
                if (trimmed.match(/^character:\s*/)) {
                    last.character = trimmed.replace(/^character:\s*["']?/, '').replace(/["']?$/, '').trim();
                } else if (trimmed.match(/^line:\s*/)) {
                    last.line = trimmed.replace(/^line:\s*["']?/, '').replace(/["']?$/, '').trim();
                } else if (trimmed.match(/^action:\s*/)) {
                    last.action = trimmed.replace(/^action:\s*["']?/, '').replace(/["']?$/, '').trim();
                }
            } else if (currentSection === 'dialogues' && trimmed.startsWith('- character:')) {
                const charMatch = trimmed.match(/character:\s*["']?([^"'\n]+)["']?/);
                if (charMatch) {
                    currentScene.dialogues.push({ character: charMatch[1].trim(), line: "", action: "" });
                }
            } else if (currentSection === 'dialogues' && currentScene.dialogues.length > 0) {
                const last = currentScene.dialogues[currentScene.dialogues.length - 1];
                if (trimmed.match(/^line:\s*/)) {
                    last.line = trimmed.replace(/^line:\s*["']?/, '').replace(/["']?$/, '').trim();
                } else if (trimmed.match(/^action:\s*/)) {
                    last.action = trimmed.replace(/^action:\s*["']?/, '').replace(/["']?$/, '').trim();
                }
            } else if (currentSection === 'actions' && trimmed.startsWith('- character:')) {
                const charMatch = trimmed.match(/character:\s*["']?([^"'\n]+)["']?/);
                if (charMatch) {
                    currentScene.actions.push({ character: charMatch[1].trim(), action: "" });
                }
            } else if (currentSection === 'actions' && currentScene.actions.length > 0) {
                const last = currentScene.actions[currentScene.actions.length - 1];
                if (trimmed.match(/^action:\s*/)) {
                    last.action = trimmed.replace(/^action:\s*["']?/, '').replace(/["']?$/, '').trim();
                }
            }
        }

        if (currentScene) result.scenes.push(currentScene);

        return result.scenes.length > 0 ? result : null;
    } catch (e) {
        console.error("正则解析也失败:", e);
        return null;
    }
}

// 导出 YAML
btnYaml.addEventListener("click", () => {
    if (!lastResult) return;
    const yamlStr = toYamlString(lastResult);
    downloadFile(`${lastResult.title || "screenplay"}.yaml`, yamlStr, "text/yaml");
});

// 导出 JSON
btnJson.addEventListener("click", () => {
    if (!lastResult) return;
    const jsonStr = JSON.stringify(lastResult, null, 2);
    downloadFile(`${lastResult.title || "screenplay"}.json`, jsonStr, "application/json");
});

function renderPreview(data) {
    if (!data.scenes || data.scenes.length === 0) {
        previewDiv.innerHTML = '<p style="color:#888;text-align:center;">未生成任何场景</p>';
        return;
    }

    let html = `<h2 style="margin-bottom:1rem;">${data.title || "剧本"}</h2>`;
    for (const scene of data.scenes) {
        html += `<div class="scene-card">`;
        html += `<h3>场景 ${scene.scene_id}: ${scene.location || ""} ${scene.time ? "(" + scene.time + ")" : ""}</h3>`;
        if (scene.description) {
            html += `<p class="scene-action">${scene.description}</p>`;
        }

        // 优先使用 items 列表（按时间顺序排列）
        if (scene.items && scene.items.length > 0) {
            for (const item of scene.items) {
                if (item.type === "dialogue") {
                    html += `<div class="dialogue">`;
                    html += `<span class="character">${item.character}:</span>`;
                    html += `<span class="line">"${item.line}"</span>`;
                    if (item.action) html += `<span class="action"> (${item.action})</span>`;
                    html += `</div>`;
                } else {
                    html += `<p class="scene-action">[${item.character ? item.character + ": " : ""}${item.action}]</p>`;
                }
            }
        } else {
            // fallback：旧格式（actions + dialogues 分开）
            for (const a of (scene.actions || [])) {
                html += `<p class="scene-action">[${a.character ? a.character + ": " : ""}${a.action}]</p>`;
            }
            for (const d of (scene.dialogues || [])) {
                html += `<div class="dialogue">`;
                html += `<span class="character">${d.character}:</span>`;
                html += `<span class="line">"${d.line}"</span>`;
                if (d.action) html += `<span class="action"> (${d.action})</span>`;
                html += `</div>`;
            }
        }

        html += `</div>`;
    }
    previewDiv.innerHTML = html;
}

function renderYaml(data) {
    yamlPre.textContent = toYamlString(data);
}

function toYamlString(obj, indent = 0) {
    // 简易 YAML 序列化（避免引入库）
    const pad = "  ".repeat(indent);
    let out = "";
    if (Array.isArray(obj)) {
        for (const item of obj) {
            if (typeof item === "object" && item !== null) {
                out += `${pad}- `;
                const lines = toYamlString(item, indent + 1).split("\n").filter(Boolean);
                out += lines.join("\n" + pad + "  ") + "\n";
            } else {
                out += `${pad}- ${yamlVal(item)}\n`;
            }
        }
    } else if (typeof obj === "object" && obj !== null) {
        for (const [k, v] of Object.entries(obj)) {
            if (Array.isArray(v)) {
                out += `${pad}${k}:\n`;
                out += toYamlString(v, indent + 1);
            } else if (typeof v === "object" && v !== null) {
                out += `${pad}${k}:\n`;
                out += toYamlString(v, indent + 1);
            } else {
                out += `${pad}${k}: ${yamlVal(v)}\n`;
            }
        }
    }
    return out;
}

function yamlVal(v) {
    if (typeof v === "string") return `"${v.replace(/"/g, '\\"')}"`;
    return String(v);
}

function downloadFile(name, content, type) {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = name;
    a.click();
    URL.revokeObjectURL(url);
}
