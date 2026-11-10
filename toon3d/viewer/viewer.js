import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { VRMLoaderPlugin, VRMUtils } from "@pixiv/three-vrm";

const canvas = document.querySelector("#canvas");
const stage = document.querySelector("#stage");
const statusEl = document.querySelector("#status");

const renderer = new THREE.WebGLRenderer({
  canvas,
  alpha: true,
  antialias: true,
  powerPreference: "high-performance",
});
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.NoToneMapping;
renderer.setClearColor(0x000000, 0);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(30, window.innerWidth / window.innerHeight, 0.05, 100);
camera.position.set(0, 1.18, 3.35);

const controls = new OrbitControls(camera, canvas);
controls.target.set(0, 0.82, 0);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.enablePan = false;
controls.minDistance = 1.4;
controls.maxDistance = 8;
controls.minPolarAngle = Math.PI * 0.22;
controls.maxPolarAngle = Math.PI * 0.62;
controls.update();

scene.add(new THREE.HemisphereLight(0xffffff, 0x29314a, 1.4));
const key = new THREE.DirectionalLight(0xffffff, 2.0);
key.position.set(2.2, 4.0, 3.2);
scene.add(key);
const fill = new THREE.DirectionalLight(0xbcd4ff, 0.7);
fill.position.set(-3.0, 2.2, 1.5);
scene.add(fill);
const rim = new THREE.DirectionalLight(0x9fd0ff, 0.8);
rim.position.set(-1.0, 3.0, -3.0);
scene.add(rim);

// Soft contact shadow card.
const shadowCanvas = document.createElement("canvas");
shadowCanvas.width = shadowCanvas.height = 256;
const ctx = shadowCanvas.getContext("2d");
const grad = ctx.createRadialGradient(128, 128, 20, 128, 128, 124);
grad.addColorStop(0, "rgba(0,0,0,.36)");
grad.addColorStop(0.55, "rgba(0,0,0,.16)");
grad.addColorStop(1, "rgba(0,0,0,0)");
ctx.fillStyle = grad;
ctx.fillRect(0, 0, 256, 256);
const shadowTex = new THREE.CanvasTexture(shadowCanvas);
const shadow = new THREE.Mesh(
  new THREE.PlaneGeometry(1.7, 1.7),
  new THREE.MeshBasicMaterial({ map: shadowTex, transparent: true, depthWrite: false })
);
shadow.rotation.x = -Math.PI / 2;
shadow.position.y = 0.002;
scene.add(shadow);

const clock = new THREE.Clock();
let vrm = null;
let mixer = null;
let idleAction = null;
let oneShot = null;
let currentModel = "";
let head = null;
let neck = null;
let baseHeadY = 0;
let baseNeckY = 0;
let shakeStart = -1;
let blinkUntil = 0;
let transparent = false;

function setStatus(text) {
  statusEl.textContent = text;
}

function disposeCurrent() {
  if (mixer) {
    mixer.stopAllAction();
    mixer = null;
  }
  if (vrm) {
    scene.remove(vrm.scene);
    VRMUtils.deepDispose(vrm.scene);
    vrm = null;
  }
  head = null;
  neck = null;
  idleAction = null;
  oneShot = null;
}

function findExpression(name) {
  if (!vrm?.expressionManager) return null;
  const manager = vrm.expressionManager;
  for (const candidate of [name, name.toLowerCase(), name[0].toUpperCase() + name.slice(1)]) {
    if (manager.getExpression(candidate)) return candidate;
  }
  return null;
}

function playOneShot(name) {
  if (!mixer || !vrm) return;
  const clip = vrm.scene.userData.__clips?.find((c) => c.name === name);
  if (!clip) {
    setStatus(`这个模型没有 ${name} 动作。\n它只有：${(vrm.scene.userData.__clips || []).map((c) => c.name).join(" / ") || "无内置动作"}`);
    return;
  }
  if (oneShot) oneShot.stop();
  oneShot = mixer.clipAction(clip);
  oneShot.reset();
  oneShot.setLoop(THREE.LoopOnce, 1);
  oneShot.clampWhenFinished = true;
  if (idleAction) oneShot.crossFadeFrom(idleAction, 0.2, false);
  oneShot.play();
}

function doBlink() {
  blinkUntil = performance.now() + 130;
}

function loadModel(url, label) {
  setStatus(`加载 ${label || url} …`);
  const loader = new GLTFLoader();
  loader.register((parser) => new VRMLoaderPlugin(parser));
  loader.load(
    url,
    (gltf) => {
      disposeCurrent();
      const model = gltf.userData.vrm;
      if (!model) {
        setStatus("这个文件不是 VRM（或 VRM 扩展没有加载成功）。");
        return;
      }
      vrm = model;
      currentModel = label || url;
      VRMUtils.removeUnnecessaryVertices(gltf.scene);
      VRMUtils.combineSkeletons(gltf.scene);
      if (vrm.meta?.metaVersion === "0") VRMUtils.rotateVRM0(vrm);
      // Let the model's embedded bone animations drive the raw bones; otherwise
      // VRMHumanoid.update() overwrites them with the normalized T-pose.
      if (vrm.humanoid) vrm.humanoid.autoUpdateHumanBones = false;

      const junk = [];
      gltf.scene.traverse((obj) => {
        if (obj.name && obj.name.startsWith("Icosphere")) junk.push(obj);
        if (obj.isMesh || obj.isSkinnedMesh) {
          obj.frustumCulled = false;
        }
      });
      for (const obj of junk) obj.parent?.remove(obj);
      scene.add(gltf.scene);
      gltf.scene.userData.__clips = gltf.animations || [];

      // Size the camera from the model's bounds.
      const box = new THREE.Box3().setFromObject(gltf.scene);
      const size = box.getSize(new THREE.Vector3());
      const center = box.getCenter(new THREE.Vector3());
      controls.target.set(center.x, center.y, center.z);
      camera.position.set(center.x, center.y, center.z + Math.max(2.4, size.y * 2.6));
      camera.near = 0.01;
      camera.far = 100;
      camera.updateProjectionMatrix();
      controls.update();
      shadow.scale.setScalar(Math.max(0.8, size.x * 1.6));
      shadow.position.set(center.x, box.min.y + 0.002, center.z);

      head = vrm.humanoid?.getRawBoneNode?.("head") || vrm.humanoid?.getNormalizedBoneNode?.("head") || null;
      neck = vrm.humanoid?.getRawBoneNode?.("neck") || vrm.humanoid?.getNormalizedBoneNode?.("neck") || null;
      baseHeadY = head?.rotation.y || 0;
      baseNeckY = neck?.rotation.y || 0;

      mixer = gltf.animations?.length ? new THREE.AnimationMixer(gltf.scene) : null;
      if (mixer) {
        const idle = gltf.animations.find((clip) => /idle/i.test(clip.name)) || gltf.animations[0];
        if (idle) {
          idleAction = mixer.clipAction(idle);
          idleAction.play();
        }
        window.__viewer.mixer = mixer;
        window.__viewer.idleAction = idleAction;
        mixer.addEventListener("finished", (event) => {
          if (event.action === oneShot && idleAction) {
            idleAction.reset().fadeIn(0.2).play();
          }
        });
      }

      const bones = vrm.humanoid ? Object.keys(vrm.humanoid.humanBones || {}).length : 0;
      const expressions = vrm.expressionManager?.expressions?.length || 0;
      const clips = gltf.animations?.map((clip) => clip.name).join(" / ") || "无内置动作";
      setStatus(
        `已加载：${currentModel}\n骨骼：${bones || "?"} · 表情：${expressions || "?"}\n动作：${clips}\n\n拖动旋转，滚轮缩放。`
      );
      window.__viewer.loaded = true;
      window.__viewer.error = "";
      window.__viewer.clips = gltf.animations?.map((clip) => clip.name) || [];
    },
    undefined,
    (error) => {
      console.error(error);
      setStatus(`加载失败：${url}\n${error?.message || error}`);
      window.__viewer.loaded = false;
      window.__viewer.error = String(error?.message || error);
    }
  );
}

function animate() {
  requestAnimationFrame(animate);
  const delta = Math.min(clock.getDelta(), 0.05);
  if (mixer) mixer.update(delta);

  if (vrm) {
    const now = performance.now();
    if (shakeStart >= 0) {
      const t = (now - shakeStart) / 1000;
      if (t < 6) {
        const envelope = Math.min(1, t / 0.45) * Math.min(1, (6 - t) / 0.55);
        const yaw = Math.sin(t * Math.PI * 2 * 0.82) * THREE.MathUtils.degToRad(14) * envelope;
        if (head) head.rotation.y = baseHeadY + yaw;
        if (neck) neck.rotation.y = baseNeckY + yaw * 0.32;
      } else {
        if (head) head.rotation.y = baseHeadY;
        if (neck) neck.rotation.y = baseNeckY;
        shakeStart = -1;
      }
    }

    const blinkName = findExpression("blink");
    if (blinkName && vrm.expressionManager) {
      vrm.expressionManager.setValue(blinkName, now < blinkUntil ? 1 : 0);
    }

    vrm.update(delta);
  }

  controls.update();
  renderer.render(scene, camera);
}

window.__viewer = {
  loaded: false,
  error: "",
  clips: [],
  load: loadModel,
  shake: () => { shakeStart = performance.now(); },
  blink: doBlink,
  scene,
  camera,
  renderer,
  THREE,
  get vrm() { return vrm; },
};

document.querySelector("#shake").addEventListener("click", () => {
  shakeStart = performance.now();
});
document.querySelector("#blink").addEventListener("click", doBlink);
document.querySelector("#wave").addEventListener("click", () => playOneShot("HappyWave"));
document.querySelector("#reset").addEventListener("click", () => {
  if (!vrm) return;
  const box = new THREE.Box3().setFromObject(vrm.scene);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  controls.target.set(center.x, center.y, center.z);
  camera.position.set(center.x, center.y, center.z + Math.max(2.4, size.y * 2.6));
  controls.update();
});
document.querySelector("#transparent").addEventListener("click", () => {
  transparent = !transparent;
  document.body.classList.toggle("transparent", transparent);
  stage.classList.toggle("transparent", transparent);
  renderer.setClearAlpha(transparent ? 0 : 1);
  if (!transparent) renderer.setClearColor(0x0e1119, 1);
});
document.querySelector("#file").addEventListener("change", (event) => {
  const file = event.target.files?.[0];
  if (!file) return;
  const url = URL.createObjectURL(file);
  loadModel(url, file.name);
});

window.addEventListener("resize", () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

animate();

// Try the local reference model first; fall back to the CC0 sample.
loadModel("./models/BlueFish-StarLite.vrm", "BlueFish-StarLite.vrm（本地参考）");
