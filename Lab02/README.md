# 🕐 Animowany Zegar Analogowy

Obiektowy zegar analogowy zaimplementowany w HTML5 Canvas z użyciem klas ES6.

## 📸 Zrzut ekranu

![Zegar Analogowy](screenshot.png)

## ✨ Funkcjonalności

### Podstawowe
- ✅ Wyświetlanie aktualnego czasu systemowego
- ✅ Płynny ruch wskazówek (z milisekundami)
- ✅ Trzy wskazówki: godzinowa, minutowa, sekundowa
- ✅ Różne grubości i kolory wskazówek

### Zaawansowane
- ✅ **Pauza (Spacja)** - zatrzymuje/wznawia zegar
- ✅ **Tarcza z cyframi** - godziny 1-12
- ✅ **Znaczniki** - kreski minutowe i godzinowe
- ✅ **Efekt Spirografu** - zanikający ślad sekundnika
- ✅ **Wyświetlacz cyfrowy** - aktualny czas

## 🏗️ Architektura (OOP)

Projekt wykorzystuje hierarchię klas ES6:

### Klasa `Hand`
Reprezentuje pojedynczą wskazówkę zegara:
```javascript
class Hand {
    constructor(length, width, color, hasCircle)
    draw(ctx, radius)
}
```

### Klasa `Clock`
Zarządza całym zegarem:
```javascript
class Clock {
    constructor(canvas)
    
    // Zarządzanie stanem
    togglePause()
    toggleTrailEffect()
    
    // Renderowanie
    render()
    drawFace()
    drawNumbers()
    drawTicks()
    drawHands(time)
    drawSingleHand(hand, angle)  // z użyciem save/restore
    drawCenterDot()
}
```

## 🎯 Kluczowe aspekty implementacji

### 1. Transformacje Canvas (save/restore)
```javascript
drawSingleHand(hand, angle) {
    ctx.save();                        // Zapisz stan
    ctx.translate(centerX, centerY);   // Przesuń do środka
    ctx.rotate(angle);                 // Obróć
    hand.draw(ctx, radius);            // Rysuj w pozycji "na 12"
    ctx.restore();                     // Przywróć stan
}
```

### 2. Płynny ruch wskazówek
```javascript
const smoothSeconds = seconds + milliseconds / 1000;
const smoothMinutes = minutes + smoothSeconds / 60;
const smoothHours = hours + smoothMinutes / 60;
```

### 3. Efekt Spirografu
Zamiast `clearRect()` używamy półprzezroczystego prostokąta:
```javascript
if (trailEffect) {
    ctx.fillStyle = 'rgba(26, 26, 46, 0.1)';
    ctx.fillRect(0, 0, width, height);
}
```

## 🚀 Uruchomienie

### Lokalnie
1. Sklonuj repozytorium
2. Otwórz `index.html` w przeglądarce

### GitHub Pages
🔗 [Link do działającego projektu](https://USERNAME.github.io/analog-clock/)

## 🎮 Sterowanie

| Klawisz/Przycisk | Akcja |
|------------------|-------|
| `Spacja` | Pauza / Wznowienie |
| Przycisk "Pauza" | Pauza / Wznowienie |
| Przycisk "Efekt Spirografu" | Włącz / Wyłącz efekt śladu |

## 📁 Struktura projektu

```
analog-clock/
├── index.html      # Strona HTML z canvasem
├── script.js       # Klasy Clock i Hand + logika
├── README.md       # Dokumentacja
└── screenshot.png  # Zrzut ekranu
```

## 🎨 Stylizacja wskazówek

| Wskazówka | Długość | Grubość | Kolor |
|-----------|---------|---------|-------|
| Godzinowa | 50% | 8px | Biały (#fff) |
| Minutowa | 70% | 5px | Różowy (#e94560) |
| Sekundowa | 85% | 2px | Zielony (#2ed573) |

## 📋 Kryteria oceny

- [x] ⭐ **3.0** - Zegar działa, pokazuje dobry czas, wskazówki się poruszają
- [x] ⭐ **4.0** - Poprawne `save/restore`, klasy ES6 (OOP)
- [x] ⭐ **5.0** - Pauza (Spacja), różne style wskazówek, tarcza z cyframi/kreskami

## 🔧 Technologie

- HTML5 Canvas
- JavaScript ES6 (Classes)
- CSS3 (Flexbox, Gradient, Animations)

## 👤 Autor
Paweł Goławski