// =============================================
// SPACE INVADERS - Paweł Goławski
// Lab 01: Gracz, ruch, init/update/draw
// Lab 02: Wrogowie, roj, animacja, strzelanie
// Lab 03: Kolizje AABB, Frontline AI, bunkry,
//         czasteczki, Mark&Sweep GC, UFO
// Lab 04: Maszyna stanow (FSM), reset, HUD,
//         pauza, High Score, Leaderboard
// =============================================

// ===================
// [Lab 03] Kolizja AABB - dedykowana funkcja
// sprawdzajaca nakladanie sie dwoch prostokatow
// ===================
overlap = function(a b)
  ax1 = a.x - a.w / 2
  ax2 = a.x + a.w / 2
  ay1 = a.y - a.h / 2
  ay2 = a.y + a.h / 2
  bx1 = b.x - b.w / 2
  bx2 = b.x + b.w / 2
  by1 = b.y - b.h / 2
  by2 = b.y + b.h / 2
  if ax2 < bx1 then return 0 end
  if ax1 > bx2 then return 0 end
  if ay2 < by1 then return 0 end
  if ay1 > by2 then return 0 end
  return 1
end

// ===================
// [Lab 03] Frontline AI - dla kazdej kolumny
// znajduje najnizszego zywego wroga
// (tylko oni moga strzelac)
// ===================
findFrontline = function()
  front = []
  for c = 0 to 6
    lowest = 999
    found = 0
    best = 0
    for e in enemies
      if not e.dead and e.ecol == c and e.y < lowest then
        lowest = e.y
        best = e
        found = 1
      end
    end
    if found then
      front.push(best)
    end
  end
  result = front
  return result
end

// ===================
// [Lab 03] System czasteczek - efekt eksplozji
// przy zniszczeniu wroga/bunkra/UFO
// ===================
spawnParticles = function(sx sy sc)
  for i = 0 to 11
    p = object end
    p.x = sx
    p.y = sy
    p.vx = -2 + random.next() * 4
    p.vy = -2 + random.next() * 4
    p.life = 20 + floor(random.next() * 20)
    p.dead = 0
    p.color = sc
    particles.push(p)
  end
end

// ===================
// [Lab 03] Garbage Collector: Mark & Sweep
// Zamiast removeAt() w petli - oznaczamy dead=1
// a potem filtrujemy tablice
// ===================
cleanup = function()
  tmp = []
  for b in player_bullets
    if not b.dead then tmp.push(b) end
  end
  player_bullets = tmp

  tmp = []
  for b in enemy_bullets
    if not b.dead then tmp.push(b) end
  end
  enemy_bullets = tmp

  tmp = []
  for e in enemies
    if not e.dead then tmp.push(e) end
  end
  enemies = tmp

  tmp = []
  for p in particles
    if not p.dead then tmp.push(p) end
  end
  particles = tmp

  tmp = []
  for bk in bunkers
    if not bk.dead then tmp.push(bk) end
  end
  bunkers = tmp
end

// ===================
// [Lab 03] Pomocnicza funkcja tworzaca
// tymczasowy prostokat do kolizji AABB
// (dla gracza i UFO ktore sa flat variables)
// ===================
makeRect = function(rx ry rw rh)
  r = object end
  r.x = rx
  r.y = ry
  r.w = rw
  r.h = rh
  tmp = r
  return tmp
end

// ===================
// [Lab 04] Odczyt klawisza A-Z / 0-9
// do wpisywania nazwy w leaderboardzie
// ===================
getKeyPressed = function()
  r = ""
  if keyboard.press.A then r = "A" end
  if keyboard.press.B then r = "B" end
  if keyboard.press.C then r = "C" end
  if keyboard.press.D then r = "D" end
  if keyboard.press.E then r = "E" end
  if keyboard.press.F then r = "F" end
  if keyboard.press.G then r = "G" end
  if keyboard.press.H then r = "H" end
  if keyboard.press.I then r = "I" end
  if keyboard.press.J then r = "J" end
  if keyboard.press.K then r = "K" end
  if keyboard.press.L then r = "L" end
  if keyboard.press.M then r = "M" end
  if keyboard.press.N then r = "N" end
  if keyboard.press.O then r = "O" end
  if keyboard.press.P then r = "P" end
  if keyboard.press.Q then r = "Q" end
  if keyboard.press.R then r = "R" end
  if keyboard.press.S then r = "S" end
  if keyboard.press.T then r = "T" end
  if keyboard.press.U then r = "U" end
  if keyboard.press.V then r = "V" end
  if keyboard.press.W then r = "W" end
  if keyboard.press.X then r = "X" end
  if keyboard.press.Y then r = "Y" end
  if keyboard.press.Z then r = "Z" end
  if keyboard.press["0"] then r = "0" end
  if keyboard.press["1"] then r = "1" end
  if keyboard.press["2"] then r = "2" end
  if keyboard.press["3"] then r = "3" end
  if keyboard.press["4"] then r = "4" end
  if keyboard.press["5"] then r = "5" end
  if keyboard.press["6"] then r = "6" end
  if keyboard.press["7"] then r = "7" end
  if keyboard.press["8"] then r = "8" end
  if keyboard.press["9"] then r = "9" end
  return r
end

// ===================
// [Lab 04] reset_game() - wydzielony kod
// inicjalizacji zmiennych rozgrywki
// Wywolywany w init() i przy restarcie (R)
// Czysci: gracza, pociski, wrogow, bunkry,
// czasteczki, UFO, gwiazdy
// ===================
reset_game = function()
  // [Lab 01] Gracz - pozycja, predkosc, zycia
  px = 0
  py = -80
  pspeed = 2
  lives = 3
  score = 0

  // [Lab 03] Pociski gracza (z limitem 3)
  player_bullets = []
  cooldown = 0
  // [Lab 02] Pociski wrogow
  enemy_bullets = []

  // [Lab 02] Wrogowie: siatka 5 rzedow x 7 kolumn
  enemies = []
  edir = 1
  espeed = 0.15
  // [Lab 02] Animacja klatkowa wrogow
  anim_timer = 0
  anim_frame = 0
  for row = 0 to 4
    for col = 0 to 6
      e = object end
      e.x = -90 + col * 20
      e.y = 70 - row * 16
      // [Lab 03] Hitbox do kolizji AABB
      e.w = 16
      e.h = 14
      // [Lab 03] Flaga dead dla Mark & Sweep
      e.dead = 0
      e.ecol = col
      e.type = "crab"
      if row < 2 then
        e.type = "octopus"
      end
      enemies.push(e)
    end
  end

  // [Lab 03] Bunkry: 4 oslony z HP
  bunkers = []
  for i = 0 to 3
    bk = object end
    bk.x = -60 + i * 40
    bk.y = -50
    bk.w = 22
    bk.h = 16
    bk.hp = 10
    bk.dead = 0
    bunkers.push(bk)
  end

  // [Lab 03] UFO - bonusowy wrog
  ufo_x = -130
  ufo_y = 92
  ufo_active = 0
  ufo_timer = 0
  ufo_anim = 0

  // [Lab 03] Czasteczki eksplozji
  particles = []
  // [Lab 02] Timer strzalow wroga
  shoot_timer = 0

  // [Lab 02] Gwiazdy (tlo dekoracyjne)
  stars = []
  for i = 0 to 59
    s = object end
    s.x = -100 + floor(random.next() * 200)
    s.y = -100 + floor(random.next() * 200)
    s.b = 50 + floor(random.next() * 200)
    stars.push(s)
  end
end

// ===================
// [Lab 04] Trwaly zapis High Score
// uzycie storage.get / storage.set
// ===================
loadHighScore = function()
  val = storage.get("hiscore")
  if val then
    highscore = val
  else
    highscore = 0
  end
end

saveHighScore = function()
  if score > highscore then
    highscore = score
    storage.set("hiscore" highscore)
  end
end

// ===================
// [Lab 04] Leaderboard - top 5 wynikow
// Dwie rownolegle tablice: lb_names + lb_scores
// Sortowanie bubble sort malejaco
// ===================
loadLeaderboard = function()
  sn = storage.get("lb_names")
  ss = storage.get("lb_scores")
  if sn and ss then
    lb_names = sn
    lb_scores = ss
  else
    lb_names = []
    lb_scores = []
  end
end

saveLeaderboard = function()
  lb_names.push(entry_name)
  lb_scores.push(score)
  // Bubble sort malejaco po wyniku
  for i = 0 to lb_scores.length - 2
    for j = 0 to lb_scores.length - 2 - i
      if lb_scores[j] < lb_scores[j + 1] then
        ts = lb_scores[j]
        lb_scores[j] = lb_scores[j + 1]
        lb_scores[j + 1] = ts
        tn = lb_names[j]
        lb_names[j] = lb_names[j + 1]
        lb_names[j + 1] = tn
      end
    end
  end
  // Zachowaj tylko top 5
  while lb_scores.length > 5
    lb_scores.removeAt(lb_scores.length - 1)
    lb_names.removeAt(lb_names.length - 1)
  end
  storage.set("lb_names" lb_names)
  storage.set("lb_scores" lb_scores)
end

// ===================
// [Lab 02] Rysowanie gwiazdek tla (wspolne)
// ===================
drawStars = function()
  for s in stars
    c = "rgb(" + s.b + "," + s.b + "," + s.b + ")"
    screen.fillRect(s.x s.y 1 1 c)
  end
end

// ===================
// [Lab 04] Rysowanie leaderboardu (wspolne)
// Wyswietla top 5: pozycja. NAZWA - wynik
// ===================
drawLeaderboard = function(base_y)
  if lb_scores.length > 0 then
    screen.drawText("--- TOP 5 ---" 0 base_y 8 "#FFFF00")
    for i = 0 to lb_scores.length - 1
      pos = i + 1
      line = pos + ". " + lb_names[i] + " - " + lb_scores[i]
      ty = base_y - 12 - i * 10
      screen.drawText(line 0 ty 7 "#CCCCCC")
    end
  else
    screen.drawText("BRAK WYNIKOW" 0 base_y 8 "#666666")
  end
end

// ===================
// [Lab 04] INIT - ladowanie danych i ustawienie
// poczatkowego stanu na MENU (delegaty FSM)
// ===================
init = function()
  // [Lab 04] Wczytanie trwalych danych
  loadHighScore()
  loadLeaderboard()
  // [Lab 04] Reset zmiennych rozgrywki
  reset_game()
  // [Lab 04] Zmienne ekranu wpisywania nazwy
  entry_name = ""
  entry_blink = 0
  end_type = "win"
  // [Lab 04] Maszyna stanow - delegaty funkcji
  // Zaczynamy od menu glownego
  current_update = update_menu
  current_draw = draw_menu
end

// ===================
// [Lab 04] Glowne update/draw - wywoluja
// aktualne delegaty (serce maszyny stanow)
// Zamiast if/else na stanach - zmienna
// wskazujaca na funkcje
// ===================
update = function()
  current_update()
end

draw = function()
  current_draw()
end

// ===================
// [Lab 04] STAN: MENU GLOWNE
// Oczekiwanie na SPACE -> przejscie do gry
// ===================
update_menu = function()
  if keyboard.press.SPACE then
    reset_game()
    current_update = update_game
    current_draw = draw_game
  end
end

draw_menu = function()
  screen.clear("rgb(5,5,20)")
  drawStars()

  screen.drawText("SPACE INVADERS" 0 55 18 "#33FF33")

  // [Lab 02] Dekoracja - sprite'y wrogow
  screen.drawSprite("crab_1" -30 30 20)
  screen.drawSprite("octopus_1" 0 30 20)
  screen.drawSprite("crab_2" 30 30 20)

  // [Lab 04] Wyswietlanie High Score
  hi_txt = "HI-SCORE: " + highscore
  screen.drawText(hi_txt 0 10 10 "#FFFF00")

  // [Lab 04] Wyswietlanie Leaderboardu
  drawLeaderboard(-8)

  screen.drawText("NACISNIJ SPACJE" 0 -85 10 "#FFFFFF")
end

// ===================
// [Lab 04] STAN: GRA (update_game)
// Cala logika rozgrywki przeniesiona
// z oryginalnego update()
// ===================
update_game = function()
  // [Lab 04] Pauza - ESC
  if keyboard.press.ESCAPE then
    current_update = update_pause
    current_draw = draw_pause
    return
  end

  // [Lab 01] Ruch gracza - polling klawiatury
  if keyboard.LEFT then
    px -= pspeed
  end
  if keyboard.RIGHT then
    px += pspeed
  end
  // [Lab 01] Clamping - gracz nie wychodzi poza ekran
  if px < -90 then px = -90 end
  if px > 90 then px = 90 end

  // [Lab 03] Strzal gracza (limit max 3 pociski)
  cooldown -= 1
  if keyboard.press.SPACE and cooldown <= 0 and player_bullets.length < 3 then
    b = object end
    b.x = px
    b.y = py + 10
    b.w = 4
    b.h = 10
    b.dead = 0
    player_bullets.push(b)
    cooldown = 15
  end

  // [Lab 02] Aktualizacja pociskow gracza
  for b in player_bullets
    b.y += 3.5
    if b.y > 105 then
      b.dead = 1
    end
  end

  // [Lab 02] Animacja klatkowa wrogow (2 klatki)
  anim_timer += 1
  if anim_timer >= 30 then
    anim_timer = 0
    anim_frame = 1 - anim_frame
  end

  // [Lab 02] Ruch roju wrogow (Hive Mind)
  // Caly roj porusza sie razem, zmiana kierunku
  // przy krawedzi + opadanie w dol
  need_drop = 0
  for e in enemies
    if not e.dead then
      if e.x + espeed * edir > 92 or e.x + espeed * edir < -92 then
        need_drop = 1
      end
    end
  end
  if need_drop then
    edir = -edir
    for e in enemies
      e.y -= 2
    end
  else
    for e in enemies
      if not e.dead then
        e.x += espeed * edir
      end
    end
  end

  // [Lab 03] Kolizja AABB: pociski gracza vs wrogowie
  for b in player_bullets
    if not b.dead then
      for e in enemies
        if not e.dead and not b.dead then
          if overlap(b e) then
            b.dead = 1
            e.dead = 1
            if e.type == "octopus" then
              score += 20
              spawnParticles(e.x e.y "#FF44FF")
            else
              score += 10
              spawnParticles(e.x e.y "#FF8800")
            end
          end
        end
      end
    end
  end

  // [Lab 03] Kolizja AABB: pociski gracza vs bunkry
  for b in player_bullets
    if not b.dead then
      for bk in bunkers
        if not bk.dead and not b.dead and overlap(b bk) then
          b.dead = 1
          bk.hp -= 1
          if bk.hp <= 0 then
            bk.dead = 1
            spawnParticles(bk.x bk.y "#448844")
          end
        end
      end
    end
  end

  // [Lab 03] Kolizja AABB: pociski gracza vs UFO
  if ufo_active then
    ufo_rect = makeRect(ufo_x ufo_y 20 14)
    for b in player_bullets
      if not b.dead then
        if overlap(b ufo_rect) then
          b.dead = 1
          ufo_active = 0
          score += 100
          spawnParticles(ufo_x ufo_y "#FF3333")
        end
      end
    end
  end

  // [Lab 04] Warunek zwyciestwa: brak zywych wrogow
  // -> zapis wyniku -> ekran wpisywania nazwy
  alive_count = 0
  for e in enemies
    if not e.dead then
      alive_count += 1
    end
  end
  if alive_count == 0 then
    saveHighScore()
    end_type = "win"
    entry_name = ""
    entry_blink = 0
    current_update = update_name_entry
    current_draw = draw_name_entry
    return
  end

  // [Lab 03] Przyspieszanie wrogow w miare eliminacji
  espeed = 0.15 + (35 - alive_count) * 0.008
  if espeed < 0.15 then espeed = 0.15 end

  // [Lab 03] Strzelanie wroga: Frontline AI
  // Tylko najnizszy wrog w kolumnie moze strzelac
  shoot_timer += 1
  if shoot_timer >= 60 then
    shoot_timer = 0
    front = findFrontline()
    if front.length > 0 then
      idx = floor(random.next() * front.length)
      shooter = front[idx]
      eb = object end
      eb.x = shooter.x
      eb.y = shooter.y - 8
      eb.w = 4
      eb.h = 10
      eb.dead = 0
      enemy_bullets.push(eb)
    end
  end

  // [Lab 02] Aktualizacja pociskow wroga
  for b in enemy_bullets
    b.y -= 2
    if b.y < -105 then
      b.dead = 1
    end
  end

  // [Lab 03] Kolizja AABB: pociski wroga vs gracz
  player_rect = makeRect(px py 20 16)
  for b in enemy_bullets
    if not b.dead then
      if overlap(b player_rect) then
        b.dead = 1
        lives -= 1
        // [Lab 04] Warunek przegranej: brak zyc
        if lives <= 0 then
          saveHighScore()
          end_type = "lose"
          entry_name = ""
          entry_blink = 0
          current_update = update_name_entry
          current_draw = draw_name_entry
          return
        end
      end
    end
  end

  // [Lab 03] Kolizja AABB: pociski wroga vs bunkry
  for b in enemy_bullets
    if not b.dead then
      for bk in bunkers
        if not bk.dead and not b.dead and overlap(b bk) then
          b.dead = 1
          bk.hp -= 1
          if bk.hp <= 0 then
            bk.dead = 1
            spawnParticles(bk.x bk.y "#448844")
          end
        end
      end
    end
  end

  // [Lab 04] Warunek przegranej: wrogowie dotarli
  // do linii gracza (y <= -70)
  for e in enemies
    if not e.dead and e.y <= -70 then
      saveHighScore()
      end_type = "lose"
      entry_name = ""
      entry_blink = 0
      current_update = update_name_entry
      current_draw = draw_name_entry
      return
    end
  end

  // [Lab 03] UFO - bonusowy wrog co ~600 klatek
  ufo_timer += 1
  ufo_anim += 1
  if not ufo_active and ufo_timer > 600 then
    ufo_active = 1
    ufo_x = -130
    ufo_timer = 0
  end
  if ufo_active then
    ufo_x += 0.7
    if ufo_x > 130 then
      ufo_active = 0
    end
  end

  // [Lab 03] Aktualizacja czasteczek eksplozji
  for p in particles
    if not p.dead then
      p.x += p.vx
      p.y += p.vy
      p.life -= 1
      if p.life <= 0 then
        p.dead = 1
      end
    end
  end

  // [Lab 03] Sprzatanie: Mark & Sweep GC
  cleanup()
end

// ===================
// [Lab 04] DRAW GAME - rysowanie rozgrywki
// Przeniesione z oryginalnego draw()
// ===================
draw_game = function()
  screen.clear("rgb(5,5,20)")
  // [Lab 02] Gwiazdy tla
  drawStars()

  // [Lab 01] Gracz - sprite
  screen.drawSprite("player" px py 20)

  // [Lab 02] Wrogowie - animacja 2-klatkowa
  for e in enemies
    if not e.dead then
      if e.type == "crab" then
        if anim_frame == 0 then
          screen.drawSprite("crab_1" e.x e.y 16)
        else
          screen.drawSprite("crab_2" e.x e.y 16)
        end
      else
        if anim_frame == 0 then
          screen.drawSprite("octopus_1" e.x e.y 16)
        else
          screen.drawSprite("octopus_2" e.x e.y 16)
        end
      end
    end
  end

  // [Lab 03] Bunkry - 3 stany wizualne (full/mid/low)
  for bk in bunkers
    if not bk.dead then
      if bk.hp > 6 then
        screen.drawSprite("bunker_full" bk.x bk.y 22)
      else
        if bk.hp > 3 then
          screen.drawSprite("bunker_mid" bk.x bk.y 22)
        else
          screen.drawSprite("bunker_low" bk.x bk.y 22)
        end
      end
    end
  end

  // [Lab 02] Pociski gracza
  for b in player_bullets
    screen.fillRect(b.x b.y 2 8 "#33FF33")
  end

  // [Lab 02] Pociski wroga
  for b in enemy_bullets
    screen.fillRect(b.x b.y 2 8 "#FF4444")
  end

  // [Lab 03] Czasteczki eksplozji
  for p in particles
    if not p.dead then
      screen.fillRect(p.x p.y 2 2 p.color)
    end
  end

  // [Lab 03] UFO - animacja 2-klatkowa
  if ufo_active then
    if floor(ufo_anim / 15) % 2 == 0 then
      screen.drawSprite("ufo_1" ufo_x ufo_y 20)
    else
      screen.drawSprite("ufo_2" ufo_x ufo_y 20)
    end
  end

  // [Lab 02] Linie graniczne
  screen.drawLine(-100 -88 100 -88 "#224422")
  screen.drawLine(-100 85 100 85 "#224422")

  // [Lab 04] HUD - interfejs uzytkownika
  drawUI()
end

// ===================
// [Lab 04] drawUI() - HUD rysowany na samym
// koncu draw_game() (Z-order: nad wszystkim)
// Wyswietla: wynik real-time, hi-score, zycia
// Zmienne tymczasowe unikaja parsowania
// "score -60" jako odejmowania
// ===================
drawUI = function()
  // Aktualny wynik - lewy gorny rog
  score_txt = "WYNIK: " + score
  score_x = -60
  screen.drawText(score_txt score_x 96 7 "#FFFFFF")
  // Hi-Score - srodek gory
  hi_txt = "HI: " + highscore
  screen.drawText(hi_txt 0 96 7 "#FFFF00")
  // Zycia - prawy gorny rog + ikony gracza
  lives_txt = "x" + lives
  screen.drawText(lives_txt 55 96 7 "#33FF33")
  for i = 0 to lives - 1
    lx = 65 + i * 12
    screen.drawSprite("player" lx 88 10)
  end
end

// ===================
// [Lab 04] STAN: PAUZA
// ESC wstrzymuje gre, ponowne ESC wznawia
// Rysuje zamrozony stan + ciemny overlay
// ===================
update_pause = function()
  if keyboard.press.ESCAPE then
    current_update = update_game
    current_draw = draw_game
  end
end

draw_pause = function()
  // Zamrozony stan gry pod spodem
  draw_game()
  // Polprzezroczysty overlay
  screen.fillRect(0 0 200 200 "rgba(0,0,0,0.6)")
  screen.drawText("PAUZA" 0 15 24 "#FFFFFF")
  screen.drawText("ESC - wznow gre" 0 -10 8 "#AAAAAA")
end

// ===================
// [Lab 04] STAN: WPISYWANIE NAZWY
// Po zakonczeniu gry (win/lose) gracz wpisuje
// nazwe z klawiatury (A-Z, 0-9, max 8 znakow)
// BACKSPACE kasuje, ENTER zatwierdza
// Wynik zapisywany do leaderboardu
// ===================
update_name_entry = function()
  entry_blink += 1

  // Odczyt klawisza z klawiatury
  k = getKeyPressed()
  if k != "" then
    if entry_name.length < 8 then
      entry_name = entry_name + k
    end
  end

  // BACKSPACE - usun ostatni znak
  if keyboard.press.BACKSPACE then
    if entry_name.length > 0 then
      entry_name = entry_name.substring(0 entry_name.length - 1)
    end
  end

  // ENTER - zatwierdz (min 1 znak)
  if keyboard.press.ENTER then
    if entry_name.length > 0 then
      saveLeaderboard()
      if end_type == "win" then
        current_update = update_win
        current_draw = draw_win
      else
        current_update = update_lose
        current_draw = draw_lose
      end
    end
  end
end

draw_name_entry = function()
  screen.clear("rgb(5,5,20)")
  drawStars()

  if end_type == "win" then
    screen.drawText("ZWYCIESTWO!" 0 70 16 "#33FF33")
  else
    screen.drawText("GAME OVER" 0 70 16 "#FF3333")
  end

  // Wynik koncowy
  end_score_txt = "Wynik: " + score
  screen.drawText(end_score_txt 0 52 12 "#FFFFFF")

  if score >= highscore and score > 0 then
    screen.drawText("NOWY REKORD!" 0 38 9 "#FFFF00")
  end

  // Instrukcja
  screen.drawText("WPISZ NAZWE (max 8 znakow)" 0 18 8 "#AAAAAA")

  // Aktualna nazwa z migajacym kursorem
  display_name = entry_name
  blink_on = floor(entry_blink / 20) % 2
  if entry_name.length < 8 then
    if blink_on then
      display_name = display_name + "_"
    else
      display_name = display_name + " "
    end
  end
  while display_name.length < 8
    display_name = display_name + " "
  end
  screen.drawText(display_name 0 0 16 "#FFFFFF")

  // Licznik znakow
  char_count = entry_name.length + "/8"
  screen.drawText(char_count 0 -18 7 "#888888")

  // Nawigacja
  screen.drawText("Klawiatura: A-Z  0-9" 0 -36 7 "#888888")
  screen.drawText("BACKSPACE - usun znak" 0 -46 7 "#888888")
  screen.drawText("ENTER - zatwierdz" 0 -56 7 "#33FF33")

  // Podglad dopuszczalnych znakow
  screen.drawText("A B C D E F G H I J K L M" 0 -72 5 "#555555")
  screen.drawText("N O P Q R S T U V W X Y Z" 0 -80 5 "#555555")
  screen.drawText("0 1 2 3 4 5 6 7 8 9" 0 -88 5 "#555555")
end

// ===================
// [Lab 04] STAN: WYGRANA
// Wyswietla wynik, leaderboard
// R - restart, ESC - menu
// ===================
update_win = function()
  // [Lab 03] Czasteczki nadal sie animuja
  for p in particles
    if not p.dead then
      p.x += p.vx
      p.y += p.vy
      p.life -= 1
      if p.life <= 0 then
        p.dead = 1
      end
    end
  end

  // [Lab 04] Restart lub powrot do menu
  if keyboard.press.R then
    reset_game()
    current_update = update_game
    current_draw = draw_game
  end
  if keyboard.press.ESCAPE then
    current_update = update_menu
    current_draw = draw_menu
  end
end

draw_win = function()
  screen.clear("rgb(5,5,20)")
  drawStars()

  // [Lab 03] Czasteczki
  for p in particles
    if not p.dead then
      screen.fillRect(p.x p.y 2 2 p.color)
    end
  end

  screen.drawText("ZWYCIESTWO!" 0 55 20 "#33FF33")
  win_score_txt = "Wynik: " + score
  screen.drawText(win_score_txt 0 32 12 "#FFFFFF")

  if score >= highscore and score > 0 then
    screen.drawText("NOWY REKORD!" 0 18 10 "#FFFF00")
  end

  // [Lab 04] Leaderboard
  drawLeaderboard(2)

  screen.drawText("R - zagraj ponownie" 0 -82 8 "#AAAAAA")
  screen.drawText("ESC - menu glowne" 0 -92 8 "#AAAAAA")
end

// ===================
// [Lab 04] STAN: PRZEGRANA
// Wyswietla wynik, leaderboard
// R - restart, ESC - menu
// ===================
update_lose = function()
  // [Lab 03] Czasteczki nadal sie animuja
  for p in particles
    if not p.dead then
      p.x += p.vx
      p.y += p.vy
      p.life -= 1
      if p.life <= 0 then
        p.dead = 1
      end
    end
  end

  // [Lab 04] Restart lub powrot do menu
  if keyboard.press.R then
    reset_game()
    current_update = update_game
    current_draw = draw_game
  end
  if keyboard.press.ESCAPE then
    current_update = update_menu
    current_draw = draw_menu
  end
end

draw_lose = function()
  screen.clear("rgb(5,5,20)")
  drawStars()

  // [Lab 03] Czasteczki
  for p in particles
    if not p.dead then
      screen.fillRect(p.x p.y 2 2 p.color)
    end
  end

  screen.drawText("GAME OVER" 0 55 20 "#FF3333")
  lose_score_txt = "Wynik: " + score
  screen.drawText(lose_score_txt 0 32 12 "#FFFFFF")

  if score >= highscore and score > 0 then
    screen.drawText("NOWY REKORD!" 0 18 10 "#FFFF00")
  end

  // [Lab 04] Leaderboard
  drawLeaderboard(2)

  screen.drawText("R - zagraj ponownie" 0 -82 8 "#AAAAAA")
  screen.drawText("ESC - menu glowne" 0 -92 8 "#AAAAAA")
end
