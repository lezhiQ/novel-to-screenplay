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
    previewDiv.innerHTML = '<p style="color:#888;text-align:center;">正在调用 AI 转换，请稍候...</p>';
    yamlPre.textContent = "";

    try {
        // 使用非流式接口（简单可靠）
        const res = await fetch(`${API_BASE}/api/convert`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title, text }),
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
    } catch (err) {
        previewDiv.innerHTML = `<p style="color:red;text-align:center;">错误: ${err.message}</p>`;
    } finally {
        btnConvert.disabled = false;
        btnConvert.textContent = "开始转换";
    }
});

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
        if (scene.actions) {
            for (const a of scene.actions) {
                html += `<p class="scene-action">[${a.character ? a.character + ": " : ""}${a.action}]</p>`;
            }
        }
        if (scene.dialogues) {
            for (const d of scene.dialogues) {
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
