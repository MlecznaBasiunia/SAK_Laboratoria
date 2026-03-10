// klasa dla jednej wskazówki zegara
// zamiast pisać 3 razy ten sam kod dla godzinowej, minutowej i sekundowej,
// robimy jedną klasę i tworzymy 3 obiekty z różnymi parametrami
class Hand {
    // length - jaka część promienia (0.5 = połowa tarczy, 0.85 = prawie cała)
    // width - grubość linii w pikselach
    // color - kolor jako string hex
    // hasCircle - opcjonalna kuleczka na końcu (tylko sekundnik ją ma)
    constructor(length, width, color, hasCircle = false) {
        this.length = length;
        this.width = width;
        this.color = color;
        this.hasCircle = hasCircle;
    }

    // ta metoda zakłada, że układ współrzędnych jest już przesunięty do środka zegara
    // i obrócony pod właściwy kąt - robi to drawSingleHand() przed wywołaniem tej metody
    draw(ctx, radius) {
        const handLength = radius * this.length;
        const tailLength = radius * 0.1; // mały ogonek za środkiem

        ctx.beginPath();
        ctx.lineWidth = this.width;
        ctx.lineCap = 'round'; // zaokrąglone końce wyglądają lepiej niż kwadratowe
        ctx.strokeStyle = this.color;

        // rysujemy pionowo - od ogonka (dodatni Y = w dół) do końca (ujemny Y = w górę)
        // dlaczego pionowo? bo układ jest już obrócony, więc "góra" to właściwy kierunek
        ctx.moveTo(0, tailLength);
        ctx.lineTo(0, -handLength);
        ctx.stroke();

        // sekundnik ma kuleczkę blisko końca - czysto estetyczne
        if (this.hasCircle) {
            ctx.beginPath();
            ctx.fillStyle = this.color;
            ctx.arc(0, -handLength + 10, 4, 0, Math.PI * 2);
            ctx.fill();
        }
    }
}

// główna klasa zarządzająca całym zegarem
class Clock {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d'); // kontekst 2D do rysowania
        this.centerX = canvas.width / 2;   // środek canvasa
        this.centerY = canvas.height / 2;
        this.radius = Math.min(this.centerX, this.centerY) - 20; // -20 żeby nie wychodził za krawędź

        // stan zegara
        this.isPaused = false;
        this.trailEffect = false;
        this.animationId = null; // id z requestAnimationFrame, potrzebne do zatrzymania

        // tworzymy 3 wskazówki z różnymi parametrami - to właśnie po to jest klasa Hand
        this.hourHand   = new Hand(0.5,  8,   '#1a2533'); // krótka i gruba
        this.minuteHand = new Hand(0.7,  4,   '#2c3e50'); // średnia
        this.secondHand = new Hand(0.85, 1.5, '#c0392b'); // długa, cienka, czerwona

        // bind() sprawia że 'this' w tych metodach zawsze wskazuje na obiekt Clock
        // bez tego po przekazaniu do addEventListener 'this' byłoby undefined
        this.handleKeydown = this.handleKeydown.bind(this);
        this.animate = this.animate.bind(this);

        this.setupEventListeners();
        this.start();
    }

    setupEventListeners() {
        document.addEventListener('keydown', this.handleKeydown);
    }

    handleKeydown(event) {
        if (event.code === 'Space') {
            event.preventDefault(); // żeby spacja nie scrollowała strony
            this.togglePause();
        }
    }

    togglePause() {
        this.isPaused = !this.isPaused; // przełącz stan
        this.updateStatusDisplay();

        if (!this.isPaused) {
            // wznowienie - startujemy animację od nowa
            // zegar pokazuje aktualny czas systemowy, nie kontynuuje od momentu zatrzymania
            this.animate();
        }
    }

    toggleTrailEffect() {
        this.trailEffect = !this.trailEffect;
    }

    updateStatusDisplay() {
        const statusEl = document.getElementById('status');
        const pauseBtn = document.getElementById('pauseBtn');

        if (this.isPaused) {
            statusEl.textContent = 'PAUZA';
            statusEl.className = 'status paused';
            pauseBtn.textContent = 'Wznów (Spacja)';
        } else {
            statusEl.textContent = 'DZIAŁA';
            statusEl.className = 'status running';
            pauseBtn.textContent = 'Pauza (Spacja)';
        }
    }

    start() {
        this.animate();
    }

    // pętla animacji - wywołuje sama siebie przez requestAnimationFrame
    // przeglądarka synchronizuje to z odświeżaniem monitora (zwykle 60 razy/s)
    // to lepsze niż setInterval bo nie marnuje zasobów gdy karta nie jest widoczna
    animate() {
        if (this.isPaused) {
            return; // po prostu nie rysujemy - wskazówki stoją w miejscu
        }

        this.render();
        this.animationId = requestAnimationFrame(this.animate);
    }

    render() {
        const now = new Date(); // aktualny czas systemowy

        if (this.trailEffect) {
            // efekt spirografu z labki: zamiast czyścić, nakładamy półprzezroczystą warstwę
            // każda klatka trochę przykrywa poprzednią, ale nie całkowicie - ślad powoli zanika
            this.ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        } else {
            // normalne czyszczenie - canvas przezroczysty przed rysowaniem nowej klatki
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        }

        // rysujemy wszystkie elementy zegara od tyłu do przodu
        this.drawFace();
        this.drawNumbers();
        this.drawTicks();
        this.drawHands(now);
        this.drawCenterDot(); // centralny punkt na wierzchu, żeby wskazówki "wychodziły" ze środka
        this.updateDigitalTime(now);
    }

    drawFace() {
        const ctx = this.ctx;

        if (!this.trailEffect) {
            // w trybie normalnym: pełne białe koło jako tło tarczy
            // w trybie spirografu pomijamy to - gdybyśmy to rysowali, białe koło
            // wymazywałoby ślad wskazówki w każdej klatce
            ctx.beginPath();
            ctx.arc(this.centerX, this.centerY, this.radius, 0, Math.PI * 2);
            ctx.fillStyle = '#ffffff';
            ctx.fill();
        }

        // obramowanie rysujemy zawsze - widoczne w obu trybach
        ctx.beginPath();
        ctx.arc(this.centerX, this.centerY, this.radius, 0, Math.PI * 2);
        ctx.strokeStyle = '#2c3e50';
        ctx.lineWidth = 3;
        ctx.stroke();
    }

    drawNumbers() {
        const ctx = this.ctx;

        ctx.font = 'bold 18px Segoe UI';
        ctx.fillStyle = '#2c3e50';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        for (let num = 1; num <= 12; num++) {
            // każda godzina to 30 stopni (360/12)
            // odejmujemy 90 bo canvas ma 0 stopni na godzinie 3, my chcemy na 12
            const angle = (num * 30 - 90) * (Math.PI / 180); // stopnie na radiany
            const x = this.centerX + Math.cos(angle) * (this.radius - 30);
            const y = this.centerY + Math.sin(angle) * (this.radius - 30);
            ctx.fillText(num.toString(), x, y);
        }
    }

    drawTicks() {
        const ctx = this.ctx;

        // 60 kresek - jedna na każdą minutę/sekundę
        for (let i = 0; i < 60; i++) {
            const angle = (i * 6 - 90) * (Math.PI / 180); // 360/60 = 6 stopni na kreskę
            const isHour = i % 5 === 0; // co 5 kreska to znacznik godziny (grubsza i dłuższa)

            const outerRadius = this.radius - 8;
            const innerRadius = isHour ? this.radius - 20 : this.radius - 14; // godzinowe dłuższe

            // punkt zewnętrzny i wewnętrzny kreski (rysujemy od brzegu do środka)
            const x1 = this.centerX + Math.cos(angle) * outerRadius;
            const y1 = this.centerY + Math.sin(angle) * outerRadius;
            const x2 = this.centerX + Math.cos(angle) * innerRadius;
            const y2 = this.centerY + Math.sin(angle) * innerRadius;

            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.strokeStyle = isHour ? '#2c3e50' : '#9aa3ae';
            ctx.lineWidth = isHour ? 2 : 1;
            ctx.stroke();
        }
    }

    drawHands(time) {
        const hours = time.getHours() % 12; // 0-11, bo zegar 12-godzinny
        const minutes = time.getMinutes();
        const seconds = time.getSeconds();
        const milliseconds = time.getMilliseconds();

        // płynny ruch: dodajemy ułamki z mniejszych jednostek
        // np. sekundnik o 14.5s jest w połowie między 14 a 15 sekundą
        // bez tego wskazówki "skakałyby" zamiast płynnie się poruszać
        const smoothSeconds = seconds + milliseconds / 1000;
        const smoothMinutes = minutes + smoothSeconds / 60;
        const smoothHours   = hours   + smoothMinutes / 60;

        // przeliczamy czas na kąty obrotu
        // godzinowa: 360/12 = 30 stopni na godzinę
        // minutowa i sekundowa: 360/60 = 6 stopni na minutę/sekundę
        const hourAngle   = (smoothHours   * 30) * (Math.PI / 180);
        const minuteAngle = (smoothMinutes * 6)  * (Math.PI / 180);
        const secondAngle = (smoothSeconds * 6)  * (Math.PI / 180);

        this.drawSingleHand(this.hourHand,   hourAngle);
        this.drawSingleHand(this.minuteHand, minuteAngle);
        this.drawSingleHand(this.secondHand, secondAngle);
    }

    drawSingleHand(hand, angle) {
        const ctx = this.ctx;

        // kluczowy trick z labki: save/restore + translate + rotate
        // save() - zapisuje cały stan kontekstu (transformacje, kolory, itp.)
        ctx.save();

        // przesuwa układ współrzędnych do środka zegara
        // teraz (0,0) to środek tarczy
        ctx.translate(this.centerX, this.centerY);

        // obraca układ współrzędnych o dany kąt
        // dzięki temu Hand.draw() zawsze rysuje "w górę" (do -Y)
        // a my po prostu obracamy cały świat zamiast liczyć nową pozycję
        ctx.rotate(angle);

        hand.draw(ctx, this.radius);

        // restore() - przywraca stan sprzed save()
        // obrót tej wskazówki nie wpływa na następną - każda ma swój własny kąt
        ctx.restore();
    }

    drawCenterDot() {
        const ctx = this.ctx;

        // czerwony krążek na zewnątrz
        ctx.beginPath();
        ctx.arc(this.centerX, this.centerY, 8, 0, Math.PI * 2);
        ctx.fillStyle = '#c0392b';
        ctx.fill();

        // biały punkcik w środku - czysto estetyczne, wygląda profesjonalnie
        ctx.beginPath();
        ctx.arc(this.centerX, this.centerY, 3, 0, Math.PI * 2);
        ctx.fillStyle = '#ffffff';
        ctx.fill();
    }

    updateDigitalTime(time) {
        const digitalEl = document.getElementById('digitalTime');
        if (digitalEl) {
            // padStart(2, '0') dodaje zero z przodu jeśli liczba jest jednocyfrowa
            // np. 9 -> "09", 12 -> "12"
            const hours   = time.getHours().toString().padStart(2, '0');
            const minutes = time.getMinutes().toString().padStart(2, '0');
            const seconds = time.getSeconds().toString().padStart(2, '0');
            digitalEl.textContent = `${hours}:${minutes}:${seconds}`;
        }
    }

    // sprzątanie po sobie - zatrzymujemy animację i usuwamy event listenery
    // przydatne np. gdy komponent jest usuwany z DOM
    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        document.removeEventListener('keydown', this.handleKeydown);
    }
}

// czekamy aż DOM się załaduje zanim cokolwiek robimy
// bez tego getElementById zwróciłoby null bo elementy jeszcze nie istnieją
document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('clockCanvas');
    const clock = new Clock(canvas); // tworzy zegar i od razu startuje animację

    document.getElementById('pauseBtn').addEventListener('click', () => {
        clock.togglePause();
    });

    const trailBtn = document.getElementById('trailBtn');
    trailBtn.addEventListener('click', () => {
        clock.toggleTrailEffect();
        // aktualizujemy tekst przycisku żeby pokazywał aktualny stan
        trailBtn.textContent = clock.trailEffect
            ? 'Spirograf: WŁ'
            : 'Spirograf: WYŁ';
    });
});
