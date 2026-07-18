const fileInput = document.getElementById("fileInput");
const preview = document.getElementById("preview");
const canvas = document.getElementById("overlay");

const ctx = canvas.getContext("2d");

const pointText = document.getElementById("pointText");
const pointStatus = document.getElementById("pointStatus");
const dots = document.querySelectorAll(".points-progress .dot");
const calibStage = document.getElementById("calibStage");
const fileName = document.getElementById("fileName");

const resetBtn = document.getElementById("resetBtn");
const saveBtn = document.getElementById("saveBtn");
const productInput = document.getElementById("productInput");
const productPreview = document.getElementById("productPreview");
const productName = document.getElementById("productName");
const measureBtn = document.getElementById("measureBtn");
const resultEl = document.getElementById("result");

function renderResult(html) {
    resultEl.innerHTML = html;
}

// Animate a number from 0 up to `target` for a lively result reveal.
// The final value is guaranteed to display even if requestAnimationFrame is
// throttled/paused (e.g. a background tab) or motion is reduced.
function animateNumber(el, target) {
    const fmt = function (v) {
        return v.toLocaleString(undefined, {
            minimumFractionDigits: 1,
            maximumFractionDigits: 1
        });
    };
    const finalText = fmt(target);

    const reduce = window.matchMedia &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (reduce || document.hidden) {
        el.textContent = finalText;
        return;
    }

    const duration = 750;
    const start = performance.now();
    function frame(now) {
        const t = Math.min(1, (now - start) / duration);
        const eased = 1 - Math.pow(1 - t, 3);
        el.textContent = t < 1 ? fmt(target * eased) : finalText;
        if (t < 1) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);

    // Safety net: guarantee the final value regardless of rAF behaviour.
    setTimeout(function () { el.textContent = finalText; }, duration + 120);
}

const RULER_SVG =
    '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" ' +
    'stroke="currentColor" stroke-width="2" stroke-linecap="round" ' +
    'stroke-linejoin="round"><path d="M3 8l13 13 5-5L8 3z"/>' +
    '<path d="M8 8l2 2M12 6l2 2M6 12l2 2"/></svg>';

function renderMeasurement(r) {
    let paper = "";
    if (r.paper_check) {
        const pc = r.paper_check;
        const ok = pc.error_pct <= 8;
        paper =
            '<div class="result-badge ' + (ok ? "ok" : "warn") + '">' +
            "✓ A4 reference " + (ok ? "verified" : "check") +
            ": measured " + pc.measured_cm2 + " cm² vs " + pc.expected_cm2 +
            " cm² expected (" + pc.error_pct + "% off)</div>";
    }

    renderResult(
        '<div class="result-show">' +
        '<div class="result-area"><span id="areaNum">0.0</span> ' +
            '<span class="u">cm²</span></div>' +
        '<div class="result-units">' +
            '<span class="chip chip-pia">' + r.area_pia + ' pía da</span>' +
            '<span class="chip">' + r.area_dm2 + ' dm²</span>' +
            '<span class="chip">' + r.area_m2 + ' m²</span>' +
            '<span class="chip">' + r.area_sqft + ' sq ft</span>' +
        '</div>' +
        '<div class="result-size">' + RULER_SVG +
            '<span>Detected size: <b>' + r.width_cm + ' × ' + r.height_cm +
            ' cm</b> <span class="result-mode">(' + r.detection_mode +
            ')</span></span></div>' +
        paper +
        '</div>'
    );

    animateNumber(document.getElementById("areaNum"), r.area_cm2);
}

// ---------------- Visualization tabs ----------------

const vizCard = document.getElementById("vizCard");
const vizTabs = document.getElementById("vizTabs");
const vizImage = document.getElementById("vizImage");
const vizSummary = document.getElementById("vizSummary");

let vizStages = null;

function showStage(stage) {
    if (!vizStages || !vizStages[stage]) return;
    vizImage.src = vizStages[stage];
    vizTabs.querySelectorAll(".tab").forEach(function (b) {
        b.classList.toggle("active", b.dataset.stage === stage);
    });
}

if (vizTabs) {
    vizTabs.addEventListener("click", function (e) {
        const btn = e.target.closest(".tab");
        if (btn) showStage(btn.dataset.stage);
    });
}

function tileChip(t) {
    const pct = t.coverage_pct;
    const g = Math.round(255 * pct / 100);
    const r = Math.round(255 * (1 - pct / 100));
    return '<span class="tile-chip" style="background:rgb(' + r + ',' + g +
        ',70)">#' + t.id + ' · ' + pct + '%</span>';
}

function renderViz(viz) {
    if (!viz) {
        vizCard.hidden = true;
        return;
    }
    vizStages = viz.stages;
    showStage("coverage");

    const s = viz.summary;
    vizSummary.innerHTML =
        '<div class="viz-stats"><b>' + s.tile_count + '</b> A4 sheets touch the ' +
        'leather · <b>' + s.full_tiles + '</b> fully covered · ≈ <b>' +
        s.equivalent_a4 + '</b> A4 equivalent</div>' +
        '<div class="tile-list">' + viz.tiles.map(tileChip).join("") + '</div>';

    vizCard.hidden = false;
}

let productFile = null;
console.log("productInput =", productInput);
productInput.addEventListener("change", function () {

    productFile = this.files[0];

    if (!productFile) return;

    productName.textContent = productFile.name;

    productPreview.src = URL.createObjectURL(productFile);

    productPreview.style.display = "block";

});

let points = [];
let selected = -1;

resetBtn.addEventListener("click", function () {

    points = [];
    selected = -1;

    draw();

});

fileInput.addEventListener("change", function(){

    const file = this.files[0];

    if(!file) return;

    fileName.textContent = file.name;

    preview.onload = function(){

        preview.style.display = "block";
        calibStage.classList.add("has-image");

        canvas.width = preview.clientWidth;
        canvas.height = preview.clientHeight;

        canvas.style.width = preview.clientWidth + "px";
        canvas.style.height = preview.clientHeight + "px";

        points = [];

        draw();

    };

    preview.src = URL.createObjectURL(file);

});
canvas.addEventListener("click", function(e){

    const rect = canvas.getBoundingClientRect();

    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const scaleX = preview.naturalWidth / preview.clientWidth;
    const scaleY = preview.naturalHeight / preview.clientHeight;

    if(selected!=-1){

        points[selected]={
            x:x*scaleX,
            y:y*scaleY
        };

        selected=-1;

        draw();

        return;

    }

    if(points.length>=4)
        return;

    points.push({

        x:x*scaleX,
        y:y*scaleY

    });

    draw();

});
function draw(){

    ctx.clearRect(0,0,canvas.width,canvas.height);

    const scaleX = preview.clientWidth / preview.naturalWidth;
    const scaleY = preview.clientHeight / preview.naturalHeight;

    for(let i=0;i<points.length;i++){

        const x=points[i].x*scaleX;
        const y=points[i].y*scaleY;

        ctx.beginPath();
        ctx.arc(x,y,12,0,Math.PI*2);

        ctx.fillStyle="red";
        ctx.fill();

        ctx.fillStyle="white";
        ctx.font="14px Arial";
        ctx.textAlign="center";
        ctx.textBaseline="middle";

        ctx.fillText(i+1,x,y);

    }

    // Drive the progress dots + status text.
    dots.forEach(function (d, i) {
        d.classList.toggle("filled", i < points.length);
    });

    if (pointStatus) {
        pointStatus.textContent = points.length + " / 4 corners" +
            (points.length === 4 ? " — ready to save" : "");
    }

    pointText.textContent = JSON.stringify(points, null, 2);

}
saveBtn.addEventListener("click", async function () {

    if (points.length != 4) {

        alert("Phải chọn đủ 4 điểm.");

        return;

    }

    try {

        const response = await fetch("/calibrate", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                points: points
            })

        });

        const result = await response.json();

        alert(result.message);

    }
    catch (err) {

        console.error(err);

        alert("Không kết nối được backend.");

    }

});
measureBtn.addEventListener("click", async function () {

    if (!productFile) {

        alert("Chọn ảnh sản phẩm trước.");

        return;

    }

    const formData = new FormData();

    formData.append("file", productFile);

    renderResult('<p class="result-hint">Measuring…</p>');

    vizCard.hidden = true;

    let result;
    try {
        const response = await fetch("/visualize", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            renderResult('<p class="result-error">Measurement failed: ' +
                (err.detail || response.status) + '</p>');
            return;
        }

        result = await response.json();
    } catch (err) {
        console.error(err);
        renderResult('<p class="result-error">Không kết nối được backend.</p>');
        return;
    }

    if (result.mode === "preview" || result.status === "preview_only") {
        renderResult(
            '<p class="result-hint">Preview only — no calibration is loaded on ' +
            'this deployment, so no real measurement was performed. Calibrate ' +
            'with an A4 sheet first (Save Calibration above).</p>'
        );
        return;
    }

    renderMeasurement(result.measurement);
    renderViz(result.visualization);

});