"use strict";

const byId = id => document.getElementById(id);
const canvas = byId("canvas");
const context = canvas.getContext("2d");
const cornerButtons = Array.from(document.querySelectorAll(".corner"));
const state = {
    frames: [],
    index: -1,
    photo: null,
    imageDigest: null,
    mode: "unlabelled",
    corners: [],
    landmarks: [],
    activeCorner: 0,
    pendingLandmark: null,
    dirty: false,
    saving: false,
    defaultOrder: "physical",
};
const instructions = {
    physical: "ابدأ بزاوية البورد الأقرب إلى A1. ثم زاوية A63، ثم J63، ثم J1. اضغط على الزوايا الخارجية للسطح العلوي واتبع أرقام الثقوب عند تدوير الصورة.",
    image: "ابدأ بالزاوية العلوية اليسرى في الصورة، ثم العلوية اليمنى، ثم السفلية اليمنى، ثم السفلية اليسرى. يفيد هذا الترتيب في تقييم اكتشاف الشكل بصرف النظر عن الاتجاه الفعلي للبورد.",
};

async function request(path, options) {
    const response = await fetch(path, options);
    const type = response.headers.get("content-type") || "";
    const data = type.includes("application/json") ? await response.json() : {};
    if (!response.ok)
        throw new Error(data.error || `HTTP ${response.status}`);
    return data;
}

function report(message, isError = false) {
    byId("issues").textContent = isError ? message : "";
    byId("status").textContent = isError ? "" : message;
}

function chooseCorner(index) {
    state.activeCorner = index;
    state.pendingLandmark = null;
    redraw();
}

function update(nextStatus) {
    state.dirty = true;
    report(nextStatus || "تغييرات بانتظار الحفظ.");
    redraw();
}

function drawSegment(a, b, scale) {
    context.beginPath();
    context.moveTo(...a);
    context.lineTo(...b);
    context.lineWidth = 3 * scale;
    context.strokeStyle = "#79f0cb";
    context.stroke();
}

function drawPoint(point, label, scale, color, selected) {
    context.beginPath();
    context.arc(point[0], point[1], (selected ? 8 : 5) * scale, 0, Math.PI * 2);
    context.lineWidth = 2 * scale;
    context.fillStyle = color;
    context.strokeStyle = "#142233";
    context.fill();
    context.stroke();
    context.font = `bold ${16 * scale}px system-ui`;
    context.textAlign = point[0] > canvas.width / 2 ? "right" : "left";
    const offset = (point[0] > canvas.width / 2 ? -12 : 12) * scale;
    const y = point[1] > 24 * scale ? point[1] - 7 * scale : point[1] + 22 * scale;
    context.lineWidth = 4 * scale;
    context.strokeText(label, point[0] + offset, y);
    context.fillText(label, point[0] + offset, y);
}

function redraw() {
    byId("instructions").textContent = instructions[byId("order").value];
    const disabled = !state.photo || state.saving;
    const noBoard = state.mode === "no-board";
    for (const [index, button] of cornerButtons.entries()) {
        button.disabled = disabled;
        button.setAttribute("aria-pressed", String(state.activeCorner === index && !state.pendingLandmark));
        button.title = state.corners[index] ? state.corners[index].join(", ") : "لم تحدد";
    }
    const selected = state.corners[state.activeCorner];
    byId("coordinates").textContent = noBoard ? "" : selected ? selected.join(", ") : "—";
    byId("previous").disabled = state.index < 1 || state.saving;
    byId("next").disabled = state.index < 0 || state.index >= state.frames.length - 1 || state.saving;
    byId("photo").disabled = state.saving;
    byId("no-board").disabled = disabled;
    byId("no-board").setAttribute("aria-pressed", String(noBoard));
    byId("remove-label").disabled = disabled;
    byId("clear-corner").disabled = disabled || !selected;
    byId("place-landmark").disabled = disabled || noBoard || state.corners.filter(Boolean).length !== 4;
    byId("remove-landmark").disabled = disabled || !byId("landmark-list").value;
    byId("save").disabled = disabled || !state.dirty;
    if (!state.photo)
        return;

    context.drawImage(state.photo, 0, 0);
    if (noBoard)
        return;

    const scale = canvas.width / Math.max(1, canvas.clientWidth);
    for (const [index, point] of state.corners.entries()) {
        const next = state.corners[(index + 1) % 4];
        if (point && next)
            drawSegment(point, next, scale);
    }
    for (const [index, point] of state.corners.entries()) {
        if (point)
            drawPoint(point, String(index + 1), scale, "#79f0cb", index === state.activeCorner);
    }
    for (const point of state.landmarks)
        drawPoint(point.pixel_px, point.id, scale, "#ffce8b", false);
}

function renderLandmarkList() {
    const list = byId("landmark-list");
    list.replaceChildren(new Option("اختر نقطة", ""));
    for (const point of state.landmarks)
        list.add(new Option(point.id, point.id));
}

async function loadPhoto(index) {
    if (state.saving || index === state.index || index < 0 || index >= state.frames.length)
        return;
    if (state.dirty && !window.confirm("هذه الصورة لها تغييرات غير محفوظة. هل تنتقل إلى صورة أخرى؟")) {
        byId("photo").value = state.index;
        return;
    }

    state.index = index;
    byId("photo").value = index;
    state.photo = null;
    state.imageDigest = null;
    state.dirty = false;
    state.pendingLandmark = null;
    state.activeCorner = 0;
    byId("landmark-id").value = "";
    byId("board-x").value = "";
    byId("board-z").value = "";
    const annotation = state.frames[index].annotation;
    state.mode = annotation ? annotation.corners_px ? "board" : "no-board" : "unlabelled";
    state.corners = structuredClone(annotation?.corners_px || [null, null, null, null]);
    state.landmarks = structuredClone(annotation?.landmarks || []);
    byId("order").value = annotation?.corner_order || state.defaultOrder;
    renderLandmarkList();
    report("جارٍ تحميل الصورة…");
    context.clearRect(0, 0, canvas.width, canvas.height);
    redraw();

    const photo = new Image();
    let imageDigest;
    let decodedUrl;
    try {
        const response = await fetch(`image/${index}`);
        if (!response.ok)
            throw new Error(`HTTP ${response.status}`);
        imageDigest = response.headers.get("X-Image-SHA256");
        decodedUrl = URL.createObjectURL(await response.blob());
        photo.src = decodedUrl;
        await photo.decode();
    } catch (error) {
        if (index === state.index)
            report(`تعذّر تحميل الصورة (${error.message}). افتح الرابط الكامل من مُشغّل الأداة.`, true);
        return;
    } finally {
        if (decodedUrl)
            URL.revokeObjectURL(decodedUrl);
    }
    if (index !== state.index)
        return;
    state.imageDigest = imageDigest;
    state.photo = photo;
    canvas.width = photo.naturalWidth;
    canvas.height = photo.naturalHeight;
    fitCanvas();
    if ((annotation?.width_px &&
        (annotation.width_px !== canvas.width || annotation.height_px !== canvas.height)) ||
        (annotation?.source?.sha256 && annotation.source.sha256 !== imageDigest)) {
        report("تختلف هذه الصورة عن الملف الذي وُسم سابقًا. استبعد الوسوم القديمة وأعد التأشير.", true);
    } else {
        const status = state.mode === "no-board" ? "صورة بلا بورد" :
            state.mode === "board" ? "صورة موسومة" : "صورة لم توسم بعد";
        report(`${status} • ${index + 1} / ${state.frames.length}`);
    }
    redraw();
}

function markPixel(event) {
    if (!state.photo || state.saving)
        return;

    const bounds = canvas.getBoundingClientRect();
    const x = (event.clientX - bounds.left) * canvas.width / bounds.width;
    const y = (event.clientY - bounds.top) * canvas.height / bounds.height;
    const position = [Math.round(x * 100) / 100, Math.round(y * 100) / 100];
    if (position[0] < 0 || position[0] >= canvas.width || position[1] < 0 || position[1] >= canvas.height)
        return;
    state.mode = "board";
    if (state.pendingLandmark) {
        const point = { ...state.pendingLandmark, pixel_px: position };
        const existing = state.landmarks.findIndex(item => item.id === point.id);
        if (existing < 0)
            state.landmarks.push(point);
        else
            state.landmarks[existing] = point;
        state.pendingLandmark = null;
        renderLandmarkList();
        byId("landmark-list").value = point.id;
    } else {
        state.corners[state.activeCorner] = position;
        const firstMissing = state.corners.findIndex(point => point == null);
        if (firstMissing >= 0)
            state.activeCorner = firstMissing;
    }
    update();
}

function beginLandmark() {
    const id = byId("landmark-id").value.trim();
    const board = [byId("board-x").valueAsNumber, byId("board-z").valueAsNumber];
    if (!id || !board.every(Number.isFinite)) {
        report("أدخل معرّف النقطة وإحداثيي X وZ أولًا.", true);
        return;
    }
    state.pendingLandmark = { id, board_mm: board };
    report("اضغط على موضع النقطة في الصورة.");
    redraw();
}

function selectLandmark() {
    const point = state.landmarks.find(item => item.id === byId("landmark-list").value);
    if (!point) {
        redraw();
        return;
    }
    byId("landmark-id").value = point.id;
    byId("board-x").value = point.board_mm[0];
    byId("board-z").value = point.board_mm[1];
    redraw();
}

function clearLabels(mode) {
    state.mode = mode;
    state.corners = [null, null, null, null];
    state.landmarks = [];
    state.activeCorner = 0;
    state.pendingLandmark = null;
    renderLandmarkList();
    update(mode === "no-board" ? "وُسمت الصورة بأنها بلا بورد. احفظ التغيير." : "استُبعدت الصورة. احفظ التغيير.");
}

async function save() {
    if (!state.photo || state.saving)
        return;
    if (state.mode === "board" && state.corners.some(point => point == null)) {
        report("حدّد الزوايا الأربع قبل الحفظ.", true);
        return;
    }

    const payload = state.mode === "unlabelled" ? { remove: true } : {
        corner_order: byId("order").value,
        image_sha256: state.imageDigest,
        width_px: canvas.width,
        height_px: canvas.height,
        no_board: state.mode === "no-board",
        corners_px: state.mode === "no-board" ? null : state.corners,
        landmarks: state.landmarks,
    };
    state.saving = true;
    redraw();
    try {
        const result = await request(`image/${state.index}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        state.frames[state.index].annotation = result.annotation;
        state.dirty = false;
        report("حُفظت البيانات.");
    } catch (error) {
        report(error.message, true);
    } finally {
        state.saving = false;
        redraw();
    }
}

async function initialize() {
    try {
        const data = await request("session.json");
        state.frames = data.images;
        state.defaultOrder = data.default_order;
        byId("session").textContent = `${data.session_id} / ${data.board_id}`;
        for (const [index, frame] of state.frames.entries())
            byId("photo").add(new Option(frame.path, index));
        await loadPhoto(0);
    } catch (error) {
        report(error.message, true);
    }
}

for (const [index, button] of cornerButtons.entries())
    button.addEventListener("click", () => chooseCorner(index));
byId("photo").addEventListener("change", event => loadPhoto(Number(event.target.value)));
byId("previous").addEventListener("click", () => loadPhoto(state.index - 1));
byId("next").addEventListener("click", () => loadPhoto(state.index + 1));
function fitCanvas() {
    const viewport = canvas.parentElement;
    const maxHeight = Number.parseFloat(getComputedStyle(viewport).maxHeight);
    const fitWidth = Math.min(viewport.clientWidth, maxHeight * canvas.width / canvas.height);
    canvas.style.width = `${fitWidth * Number(byId("zoom").value)}px`;
    canvas.style.marginInline = canvas.offsetWidth <= viewport.clientWidth ? "auto" : "0";
}

byId("zoom").addEventListener("change", () => {
    fitCanvas();
    redraw();
});
byId("order").addEventListener("change", () => {
    if (state.mode === "unlabelled")
        redraw();
    else
        update();
});
byId("clear-corner").addEventListener("click", () => {
    state.corners[state.activeCorner] = null;
    update();
});
byId("no-board").addEventListener("click", () => clearLabels("no-board"));
byId("remove-label").addEventListener("click", () => clearLabels("unlabelled"));
byId("place-landmark").addEventListener("click", beginLandmark);
byId("landmark-list").addEventListener("change", selectLandmark);
byId("remove-landmark").addEventListener("click", () => {
    state.landmarks = state.landmarks.filter(point => point.id !== byId("landmark-list").value);
    renderLandmarkList();
    update();
});
byId("save").addEventListener("click", save);
canvas.addEventListener("click", markPixel);
window.addEventListener("resize", () => {
    fitCanvas();
    redraw();
});
window.addEventListener("beforeunload", event => {
    if (state.dirty) {
        event.preventDefault();
        event.returnValue = "";
    }
});
window.addEventListener("keydown", event => {
    if (!state.photo || /INPUT|SELECT|TEXTAREA/.test(event.target.tagName))
        return;
    if (event.key >= "1" && event.key <= "4")
        chooseCorner(Number(event.key) - 1);
});
redraw();
initialize();
