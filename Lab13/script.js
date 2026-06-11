import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const MODEL_PATH = './biomech_13.glb';
const KOLOR_TLA = 0x050810;
const PREDKOSC_OBROTU = 0.08;
const PULSACJA_AMPLITUDA = 0.08;
const PULSACJA_CZESTOSC = 1.2;

const statusEl = document.getElementById('status');
const statsEl = document.getElementById('stats');

const canvas = document.getElementById('scene');
const renderer = new THREE.WebGLRenderer({
    canvas: canvas,
    antialias: true,
    powerPreference: 'high-performance'
});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;

const scene = new THREE.Scene();
scene.background = new THREE.Color(KOLOR_TLA);
scene.fog = new THREE.Fog(KOLOR_TLA, 12, 40);

const camera = new THREE.PerspectiveCamera(
    45,
    window.innerWidth / window.innerHeight,
    0.1,
    100
);
camera.position.set(6, 4, 8);
camera.lookAt(0, 1.5, 0);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.minDistance = 3;
controls.maxDistance = 25;
controls.target.set(0, 1.5, 0);
controls.maxPolarAngle = Math.PI * 0.95;

const ambient = new THREE.AmbientLight(0x445566, 0.6);
scene.add(ambient);

const keyLight = new THREE.DirectionalLight(0xfff0d8, 2.2);
keyLight.position.set(5, 7, 4);
keyLight.name = 'Key_Light';
scene.add(keyLight);

const fillLight = new THREE.DirectionalLight(0x9bb8ff, 0.8);
fillLight.position.set(-6, 3, 2);
fillLight.name = 'Fill_Light';
scene.add(fillLight);

const rimLight = new THREE.DirectionalLight(0x55ddee, 1.5);
rimLight.position.set(0, 4, -6);
rimLight.name = 'Rim_Light';
scene.add(rimLight);

const akcentLight = new THREE.PointLight(0xff8844, 1.2, 8, 1.5);
akcentLight.position.set(2.5, 1.5, 1.5);
scene.add(akcentLight);

const clock = new THREE.Clock();

let model = null;
let pakMesh = null;
let pakBaseScale = null;

function wycentruj_kamere(obj) {
    const box = new THREE.Box3().setFromObject(obj);
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z);

    const fov = camera.fov * Math.PI / 180;
    const dystans = Math.abs(maxDim / Math.tan(fov / 2)) * 1.4;

    camera.position.set(
        center.x + dystans * 0.6,
        center.y + maxDim * 0.4,
        center.z + dystans * 0.8
    );

    controls.target.copy(center);
    controls.update();

    camera.near = Math.max(0.01, maxDim / 100);
    camera.far = dystans * 10;
    camera.updateProjectionMatrix();

    return { center, size, maxDim };
}

function policz_i_zapisz_mesh_e(root) {
    let licznikMesh = 0;
    let licznikMaterials = 0;
    const materialy = new Set();
    const nazwy = [];

    root.traverse((obj) => {
        if (obj.isMesh) {
            licznikMesh++;
            nazwy.push(obj.name);
            const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
            mats.forEach(m => { if (m) materialy.add(m.uuid); });

            if (!pakMesh && obj.name.toLowerCase().includes('pak')) {
                pakMesh = obj;
                pakBaseScale = obj.scale.clone();
                console.log(`[Lab 13] Znaleziono pąk do pulsacji: "${obj.name}"`);
            }
        }
    });

    licznikMaterials = materialy.size;
    console.log(`[Lab 13] Wczytano ${licznikMesh} mesh-y, ${licznikMaterials} materiałów`);
    console.log('[Lab 13] Nazwy obiektów:', nazwy);

    return { licznikMesh, licznikMaterials };
}

async function wczytaj_model() {
    const loader = new GLTFLoader();
    try {
        statusEl.textContent = 'Pobieram biomech_13.glb...';
        const gltf = await loader.loadAsync(MODEL_PATH);
        model = gltf.scene;
        scene.add(model);

        const { licznikMesh, licznikMaterials } = policz_i_zapisz_mesh_e(model);
        const wymiary = wycentruj_kamere(model);

        statusEl.textContent = 'Model wczytany';
        statusEl.classList.add('status');
        statsEl.innerHTML = `
            Mesh-e: ${licznikMesh}<br>
            Materiały: ${licznikMaterials}<br>
            Wymiary: ${wymiary.size.x.toFixed(1)} × ${wymiary.size.y.toFixed(1)} × ${wymiary.size.z.toFixed(1)}<br>
            ${pakMesh ? 'Pąk pulsuje · model rotuje' : 'Model rotuje'}
        `;
    } catch (error) {
        console.error('[Lab 13] Błąd ładowania:', error);
        statusEl.classList.remove('status');
        statusEl.classList.add('error');
        statusEl.innerHTML = `Błąd ładowania modelu:<br>${error.message}`;
        statsEl.innerHTML = `
            Sprawdź:<br>
            • plik biomech_13.glb w folderze lab13/<br>
            • używasz Live Server (nie file://)<br>
            • Network tab w DevTools
        `;
    }
}

function on_resize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
}

window.addEventListener('resize', on_resize);

function animate() {
    requestAnimationFrame(animate);

    const delta = clock.getDelta();
    const elapsed = clock.getElapsedTime();

    if (model) {
        model.rotation.y += PREDKOSC_OBROTU * delta;
    }

    if (pakMesh && pakBaseScale) {
        const puls = 1.0 + Math.sin(elapsed * PULSACJA_CZESTOSC) * PULSACJA_AMPLITUDA;
        pakMesh.scale.set(
            pakBaseScale.x * puls,
            pakBaseScale.y * puls,
            pakBaseScale.z * puls
        );
    }

    akcentLight.intensity = 1.2 + Math.sin(elapsed * 0.8) * 0.3;

    controls.update();
    renderer.render(scene, camera);
}

wczytaj_model();
animate();