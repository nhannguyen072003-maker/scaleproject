const fileInput = document.getElementById("fileInput");
const preview = document.getElementById("preview");
const canvas = document.getElementById("overlay");

const ctx = canvas.getContext("2d");

const pointText = document.getElementById("pointText");

const resetBtn = document.getElementById("resetBtn");
const saveBtn = document.getElementById("saveBtn");
const productInput = document.getElementById("productInput");
const productPreview = document.getElementById("productPreview");
const measureBtn = document.getElementById("measureBtn");
const resultText = document.getElementById("resultText");

let productFile = null;
console.log("productInput =", productInput);
productInput.addEventListener("change", function () {

    productFile = this.files[0];

    if (!productFile) return;

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

    preview.onload = function(){

        preview.style.display = "block";

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

    pointText.textContent=
        JSON.stringify(points,null,2);

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

    const response = await fetch("/measure", {

        method: "POST",

        body: formData

    });

    const result = await response.json();
    let message = result.message || "Measurement unavailable.";

    if (result.mode === "preview" || result.status === "preview_only") {
        const area = result.result?.area_cm2 ?? result.area_cm2 ?? 0;
        message = `Measurement completed. Preview area: ${area.toFixed(2)} cm²`;
    }

    resultText.textContent = message;
    alert(message);

});