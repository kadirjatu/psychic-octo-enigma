const sessionId = crypto.randomUUID();
const headers = () => ({ "X-Session-ID": sessionId });
const fileInput = document.querySelector("#file-input");
const dropZone = document.querySelector("#drop-zone");
let activeUpload = null;
let activeJob = null;
let activeFile = null;
let uploadController = null;
let enhancedObjectUrl = null;
let originalObjectUrl = null;

async function api(path, options = {}) {
  const response = await fetch(path, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || "Request failed");
  return data;
}

async function initStatus() {
  const status = await api("/api/status");
  document.querySelector("#device").textContent =
    `${status.device.toUpperCase()}${status.cuda_available ? " / CUDA" : ""}`;
  document.querySelector("#tile-size").value = status.tile_size;
}

document.querySelector("#browse-button").addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", () => {
  if (fileInput.files[0]) startUpload(fileInput.files[0]);
});
["dragenter","dragover"].forEach(type => dropZone.addEventListener(type, event => {
  event.preventEvent?.();
  event.preventDefault();
  dropZone.classList.add("drag");
}));
["dragleave","drop"].forEach(type => dropZone.addEventListener(type, event => {
  event.preventDefault();
  dropZone.classList.remove("drag");
}));
dropZone.addEventListener("drop", event => {
  if (event.dataTransfer.files[0]) startUpload(event.dataTransfer.files[0]);
});

async function startUpload(file) {
  activeFile = file;
  document.querySelector("#upload-progress").classList.remove("hidden");
  dropZone.classList.add("hidden");
  const init = await api("/api/upload/init", {
    method:"POST", headers:{...headers(),"Content-Type":"application/json"},
    body:JSON.stringify({filename:file.name,total_size:file.size})
  });
  activeUpload = init.upload_id;
  const status = await api(`/api/upload/${activeUpload}/status`, {headers:headers()});
  const start = status.received || 0;
  const chunkSize = init.chunk_size;
  uploadController = new AbortController();
  try {
    for (let offset=start; offset<file.size; offset+=chunkSize) {
      const blob = file.slice(offset, Math.min(offset+chunkSize,file.size));
      const form = new FormData();
      form.append("upload_id", activeUpload);
      form.append("offset", String(offset));
      form.append("chunk", blob, "chunk");
      await fetch("/api/upload/chunk", {
        method:"POST", headers:headers(), body:form, signal:uploadController.signal
      }).then(async response => {
        const data=await response.json();
        if(!response.ok) throw new Error(data.detail || "Upload failed");
        const percent=Math.round(data.received/file.size*100);
        document.querySelector("#upload-percent").textContent=`${percent}%`;
        document.querySelector("#upload-bar").value=percent;
      });
    }
    const complete = await api("/api/upload/complete", {
      method:"POST", headers:{...headers(),"Content-Type":"application/json"},
      body:JSON.stringify({upload_id:activeUpload})
    });
    document.querySelector("#upload-progress").classList.add("hidden");
    document.querySelector("#video-info").classList.remove("hidden");
    document.querySelector("#video-info").innerHTML = `
      <h2>Video information</h2><div class="settings-grid">
      <label>Resolution<strong>${complete.info.width} × ${complete.info.height}</strong></label>
      <label>Duration<strong>${complete.info.duration.toFixed(2)} s</strong></label>
      <label>FPS<strong>${complete.info.fps.toFixed(3)}</strong></label>
      <label>File size<strong>${formatBytes(file.size)}</strong></label>
      <label>Audio<strong>${complete.info.has_audio ? "Yes" : "No"}</strong></label>
      <label>Enhanced target<strong>${complete.info.width*2} × ${complete.info.height*2}</strong></label></div>`;
    if (originalObjectUrl) URL.revokeObjectURL(originalObjectUrl);
    originalObjectUrl = await createObjectUrl(`/api/upload/${activeUpload}/preview`);
    document.querySelector("#original-video").src=originalObjectUrl;
    document.querySelector("#enhance-button").disabled=false;
  } catch (error) {
    if (error.name !== "AbortError") alert(error.message);
  }
}

function formatBytes(bytes) {
  if (!bytes) return "0 B";
  const units=["B","KB","MB","GB","TB"];
  const index=Math.min(Math.floor(Math.log(bytes)/Math.log(1024)),units.length-1);
  return `${(bytes/Math.pow(1024,index)).toFixed(index ? 1 : 0)} ${units[index]}`;
}

async function createObjectUrl(path) {
  const response=await fetch(path,{headers:headers()});
  if (!response.ok) {
    const data=await response.json().catch(()=>({}));
    throw new Error(data.detail || "Unable to open video");
  }
  return URL.createObjectURL(await response.blob());
}

document.querySelector("#download-button").addEventListener("click", async event => {
  event.preventDefault();
  try {
    const response=await fetch(`/api/download/${activeJob}`,{headers:headers()});
    if (!response.ok) {
      const data=await response.json().catch(()=>({}));
      throw new Error(data.detail || "Download failed");
    }
    const url=URL.createObjectURL(await response.blob());
    const link=document.createElement("a");
    link.href=url;
    link.download=`enhanced-${activeJob.slice(0,8)}.mp4`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
  } catch (error) {
    alert(error.message);
  }
});

document.querySelector("#cancel-upload").addEventListener("click", () => uploadController?.abort());
document.querySelector("#enhance-button").addEventListener("click", async () => {
  if (!activeUpload) return;
  const result = await api("/api/enhance", {
    method:"POST", headers:{...headers(),"Content-Type":"application/json"},
    body:JSON.stringify({upload_id:activeUpload,tile_size:Number(document.querySelector("#tile-size").value)})
  });
  activeJob=result.job_id;
  document.querySelector("#processing").classList.remove("hidden");
  pollJob();
});

async function pollJob() {
  try {
    const job=await api(`/api/jobs/${activeJob}`,{headers:headers()});
    document.querySelector("#stage").textContent=job.stage;
    document.querySelector("#job-percent").textContent=`${job.progress}%`;
    document.querySelector("#job-bar").value=job.progress;
    document.querySelector("#frame-progress").textContent=
      job.total_frames ? `${job.completed_frames} / ${job.total_frames} frames` : "";
    if(job.status==="Completed") await showResult();
    else if(job.status==="Failed") alert(job.error || "Processing failed");
    else if(job.status==="Cancelled") document.querySelector("#stage").textContent="Cancelled";
    else setTimeout(pollJob,1000);
  } catch(error) { alert(error.message); }
}

async function showResult() {
  const result=await api(`/api/jobs/${activeJob}/result`,{headers:headers()});
  document.querySelector("#results").classList.remove("hidden");
  if (enhancedObjectUrl) URL.revokeObjectURL(enhancedObjectUrl);
  enhancedObjectUrl = await createObjectUrl(`/api/download/${activeJob}`);
  document.querySelector("#enhanced-video").src=enhancedObjectUrl;
  document.querySelector("#download-button").href=`/api/download/${activeJob}`;
  document.querySelector("#download-button").setAttribute("download","enhanced.mp4");
  document.querySelector("#resolution-info").innerHTML=`
    <label>Enhanced resolution<strong>${result.result.width} × ${result.result.height}</strong></label>
    <label>Duration<strong>${result.result.duration.toFixed(2)} s</strong></label>
    <label>FPS<strong>${result.result.fps.toFixed(3)}</strong></label>`;
  document.querySelector("#processing").classList.add("hidden");
}

document.querySelector("#cancel-job").addEventListener("click", () =>
  api(`/api/jobs/${activeJob}/cancel`,{method:"POST",headers:headers()}).catch(error=>alert(error.message))
);

initStatus().catch(error => alert(error.message));
