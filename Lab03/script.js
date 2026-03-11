'use strict';

// ═══════════════════════════════════════════════════════
//  Klasa Particle (Cząsteczka)
//  Pojedynczy element fizyczny — nie wie o niczym poza sobą.
// ═══════════════════════════════════════════════════════
class Particle {
    /**
     * @param {number} x      – pozycja startowa X
     * @param {number} y      – pozycja startowa Y
     * @param {number} vx     – składowa prędkości X
     * @param {number} vy     – składowa prędkości Y
     * @param {number} hue    – barwa w modelu HSLA (0–360)
     * @param {number} decay  – szybkość zanikania alpha na klatkę
     */
    constructor(x, y, vx, vy, hue, decay = 0.015) {
        this.x = x;
        this.y = y;
        this.vx = vx;
        this.vy = vy;
        this.hue = hue;
        this.alpha = 1;
        this.decay = decay;
        this.active = true;
        this.radius = Math.random() * 2 + 1;
    }

    /**
     * Aktualizacja stanu cząsteczki w jednej klatce.
     * @param {number} gravity      – wartość przyspieszenia grawitacyjnego
     * @param {number} canvasHeight – wysokość elementu canvas (do kolizji z podłożem)
     */
    update(gravity, canvasHeight) {
        this.x += this.vx;
        this.y += this.vy;

        // Grawitacja
        this.vy += gravity;

        // Opór powietrza
        this.vx *= 0.98;
        this.vy *= 0.98;

        // Zanikanie
        this.alpha -= this.decay;
        if (this.alpha <= 0) {
            this.alpha = 0;
            this.active = false;
        }

        // Kolizja z podłożem – odbicie z tłumieniem
        if (this.y >= canvasHeight) {
            this.vy *= -0.6;
            this.y = canvasHeight;
        }
    }

    /**
     * Rysowanie cząsteczki na kontekście Canvas.
     * @param {CanvasRenderingContext2D} ctx
     */
    draw(ctx) {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fillStyle = `hsla(${this.hue}, 100%, 50%, ${this.alpha})`;
        ctx.fill();
    }

    /**
     * Resetowanie instancji (Object Pooling).
     * @param {number} x
     * @param {number} y
     * @param {number} vx
     * @param {number} vy
     * @param {number} hue
     * @param {number} decay
     */
    reset(x, y, vx, vy, hue, decay) {
        this.x = x;
        this.y = y;
        this.vx = vx;
        this.vy = vy;
        this.hue = hue;
        this.decay = decay;
        this.alpha = 1;
        this.active = true;
        this.radius = Math.random() * 2 + 1;
    }
}

// ═══════════════════════════════════════════════════════
//  Klasa Firework (Rakieta)
//  Zarządza sekwencją zdarzeń jednego fajerwerku.
// ═══════════════════════════════════════════════════════
class Firework {
    /**
     * @param {number} startX  – pozycja startowa X (dolna krawędź)
     * @param {number} startY  – pozycja startowa Y (dolna krawędź)
     * @param {number} targetX – cel X (miejsce kliknięcia)
     * @param {number} targetY – cel Y (miejsce kliknięcia)
     * @param {number} speed   – prędkość lotu rakiety
     * @param {number} particleCount – liczba cząsteczek eksplozji
     * @param {number} decay   – szybkość zanikania cząsteczek
     */
    constructor(startX, startY, targetX, targetY, speed = 8, particleCount = 120, decay = 0.015) {
        this.x = startX;
        this.y = startY;
        this.targetX = targetX;
        this.targetY = targetY;
        this.speed = speed;
        this.particleCount = particleCount;
        this.decay = decay;
        this.active = true;
        this.exploded = false;

        // Bazowy kolor (hue) — losowy dla każdego fajerwerku
        this.hue = Math.random() * 360;

        // Wektor prędkości — normalizowany i przemnożony przez speed
        const dx = targetX - startX;
        const dy = targetY - startY;
        const dist = Math.hypot(dx, dy) || 1;
        this.vx = (dx / dist) * this.speed;
        this.vy = (dy / dist) * this.speed;

        // Ślad rakiety
        this.trail = [];
        this.trailLength = 6;
    }

    /**
     * Aktualizacja stanu rakiety.
     */
    update() {
        this.trail.push({ x: this.x, y: this.y });
        if (this.trail.length > this.trailLength) {
            this.trail.shift();
        }

        this.x += this.vx;
        this.y += this.vy;

        // Sprawdź, czy rakieta dotarła do celu
        const dist = Math.hypot(this.targetX - this.x, this.targetY - this.y);
        if (dist < 5) {
            this.exploded = true;
            this.active = false;
        }
    }

    /**
     * Rysowanie rakiety (mały świecący punkt ze śladem).
     * @param {CanvasRenderingContext2D} ctx
     */
    draw(ctx) {
        for (let i = 0; i < this.trail.length; i++) {
            const t = this.trail[i];
            const a = (i / this.trail.length) * 0.5;
            ctx.beginPath();
            ctx.arc(t.x, t.y, 2, 0, Math.PI * 2);
            ctx.fillStyle = `hsla(${this.hue}, 100%, 70%, ${a})`;
            ctx.fill();
        }

        // Głowica
        ctx.beginPath();
        ctx.arc(this.x, this.y, 3, 0, Math.PI * 2);
        ctx.fillStyle = `hsla(${this.hue}, 100%, 80%, 1)`;
        ctx.fill();
    }

    /**
     * Generuje tablicę cząsteczek eksplozji.
     * @returns {Particle[]} tablica N cząsteczek
     */
    explode() {
        const particles = [];
        for (let i = 0; i < this.particleCount; i++) {
            const angle = Math.random() * Math.PI * 2;
            const speed = Math.random() * 5 + 1;
            const vx = Math.cos(angle) * speed;
            const vy = Math.sin(angle) * speed;
            const hue = this.hue + (Math.random() * 40 - 20);
            particles.push(new Particle(this.x, this.y, vx, vy, hue, this.decay));
        }
        return particles;
    }
}

// ═══════════════════════════════════════════════════════
//  Klasa FireworkShow (Menadżer)
//  Odpowiada za canvas, zdarzenia DOM i pętlę główną.
// ═══════════════════════════════════════════════════════
class FireworkShow {
    constructor(canvasId) {
        /** @type {HTMLCanvasElement} */
        this.canvas = document.getElementById(canvasId);
        /** @type {CanvasRenderingContext2D} */
        this.ctx = this.canvas.getContext('2d');

        // Kolekcje obiektów
        this.rockets = [];
        this.particles = [];

        // Parametry symulacji (domyślne)
        this.gravity = 0.06;
        this.particleCount = 120;
        this.rocketSpeed = 8;
        this.particleDecay = 0.015;

        // Opcje wizualne
        this.trailsEnabled = true;
        this.additiveBlend = true;

        // Automatyczny pokaz
        this.autoShowEnabled = true;
        this.autoTimer = 0;
        this.autoInterval = 90;

        // FPS
        this.frameCount = 0;
        this.fpsTime = performance.now();
        this.fps = 0;

        this._init();
    }

    /** Inicjalizacja rozmiaru, zdarzeń i kontrolek. */
    _init() {
        this._resize();
        window.addEventListener('resize', () => this._resize());

        // Kliknięcie na canvas — nowy fajerwerk
        this.canvas.addEventListener('click', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const targetX = e.clientX - rect.left;
            const targetY = e.clientY - rect.top;
            this._launchRocket(targetX, targetY);
        });

        // Podpięcie kontrolek
        this._bindSlider('slider-gravity',   'val-gravity',   v => { this.gravity = parseFloat(v); });
        this._bindSlider('slider-particles', 'val-particles', v => { this.particleCount = parseInt(v, 10); });
        this._bindSlider('slider-speed',     'val-speed',     v => { this.rocketSpeed = parseInt(v, 10); });
        this._bindSlider('slider-decay',     'val-decay',     v => { this.particleDecay = parseFloat(v); });

        this._bindToggle('toggle-auto',   v => { this.autoShowEnabled = v; });
        this._bindToggle('toggle-trails', v => { this.trailsEnabled = v; });
        this._bindToggle('toggle-blend',  v => { this.additiveBlend = v; });

        // Start pętli
        this._loop();
    }

    _resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    /**
     * @param {string} sliderId
     * @param {string} valId
     * @param {function(string):void} setter
     */
    _bindSlider(sliderId, valId, setter) {
        const slider = document.getElementById(sliderId);
        const valEl = document.getElementById(valId);
        slider.addEventListener('input', () => {
            valEl.textContent = slider.value;
            setter(slider.value);
        });
    }

    /**
     * @param {string} toggleId
     * @param {function(boolean):void} setter
     */
    _bindToggle(toggleId, setter) {
        const toggle = document.getElementById(toggleId);
        toggle.addEventListener('change', () => setter(toggle.checked));
    }

    /**
     * Tworzy nową rakietę lecącą do (targetX, targetY).
     * @param {number} targetX
     * @param {number} targetY
     */
    _launchRocket(targetX, targetY) {
        const startX = targetX;
        const startY = this.canvas.height;
        const rocket = new Firework(
            startX, startY, targetX, targetY,
            this.rocketSpeed, this.particleCount, this.particleDecay
        );
        this.rockets.push(rocket);
    }

    /** Automatyczne odpalanie rakiet w losowych pozycjach. */
    _autoLaunch() {
        if (!this.autoShowEnabled) return;

        this.autoTimer++;
        if (this.autoTimer >= this.autoInterval) {
            this.autoTimer = 0;
            this.autoInterval = Math.random() * 90 + 60;
            const targetX = Math.random() * this.canvas.width * 0.8 + this.canvas.width * 0.1;
            const targetY = Math.random() * this.canvas.height * 0.4 + this.canvas.height * 0.1;
            this._launchRocket(targetX, targetY);
        }
    }

    /** Główna pętla animacji (requestAnimationFrame). */
    _loop() {
        this._update();
        this._updateFps();
        requestAnimationFrame(() => this._loop());
    }

    _update() {
        const ctx = this.ctx;
        const W = this.canvas.width;
        const H = this.canvas.height;

        // Czyszczenie ekranu
        if (this.trailsEnabled) {
            ctx.globalCompositeOperation = 'source-over';
            ctx.fillStyle = 'rgba(0, 0, 0, 0.15)';
            ctx.fillRect(0, 0, W, H);
        } else {
            ctx.clearRect(0, 0, W, H);
            ctx.fillStyle = '#000';
            ctx.fillRect(0, 0, W, H);
        }

        // Addytywne blendowanie
        ctx.globalCompositeOperation = this.additiveBlend ? 'lighter' : 'source-over';

        // Aktualizacja rakiet
        for (let i = 0; i < this.rockets.length; i++) {
            const rocket = this.rockets[i];
            rocket.update();
            rocket.draw(ctx);

            if (rocket.exploded) {
                const newParticles = rocket.explode();
                this.particles.push(...newParticles);
            }
        }

        // Aktualizacja cząsteczek
        for (let i = 0; i < this.particles.length; i++) {
            const p = this.particles[i];
            p.update(this.gravity, H);
            p.draw(ctx);
        }

        // Usuwanie nieaktywnych obiektów
        this.rockets = this.rockets.filter(r => r.active);
        this.particles = this.particles.filter(p => p.active);

        // Automatyczny pokaz
        this._autoLaunch();

        // Reset composite operation
        ctx.globalCompositeOperation = 'source-over';
    }

    _updateFps() {
        this.frameCount++;
        const now = performance.now();
        if (now - this.fpsTime >= 1000) {
            this.fps = this.frameCount;
            this.frameCount = 0;
            this.fpsTime = now;
            document.getElementById('fps-counter').textContent =
                `FPS: ${this.fps} | Cząsteczki: ${this.particles.length} | Rakiety: ${this.rockets.length}`;
        }
    }
}

// Start aplikacji
void new FireworkShow('canvas');
