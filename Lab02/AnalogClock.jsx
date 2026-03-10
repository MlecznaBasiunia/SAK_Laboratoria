import { useState, useEffect, useRef, useCallback } from 'react';

class Hand {
  constructor(length, width, color, hasCircle = false) {
    this.length = length;
    this.width = width;
    this.color = color;
    this.hasCircle = hasCircle;
  }

  draw(ctx, radius) {
    const handLength = radius * this.length;
    const tailLength = radius * 0.1;

    ctx.beginPath();
    ctx.lineWidth = this.width;
    ctx.lineCap = 'round';
    ctx.strokeStyle = this.color;
    ctx.moveTo(0, tailLength);
    ctx.lineTo(0, -handLength);
    ctx.stroke();

    if (this.hasCircle) {
      ctx.beginPath();
      ctx.fillStyle = this.color;
      ctx.arc(0, -handLength + 10, 4, 0, Math.PI * 2);
      ctx.fill();
    }
  }
}

class Clock {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.centerX = canvas.width / 2;
    this.centerY = canvas.height / 2;
    this.radius = Math.min(this.centerX, this.centerY) - 20;

    this.hourHand = new Hand(0.5, 8, '#1a2533');
    this.minuteHand = new Hand(0.7, 4, '#2c3e50');
    this.secondHand = new Hand(0.85, 1.5, '#c0392b');
  }

  render(trailEffect = false) {
    const now = new Date();
    const ctx = this.ctx;

    if (trailEffect) {
      ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
      ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    } else {
      ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }

    this.drawFace(trailEffect);
    this.drawNumbers();
    this.drawTicks();
    this.drawHands(now);
    this.drawCenterDot();

    return now;
  }

  drawFace(trailEffect = false) {
    const ctx = this.ctx;

    if (!trailEffect) {
      ctx.beginPath();
      ctx.arc(this.centerX, this.centerY, this.radius, 0, Math.PI * 2);
      ctx.fillStyle = '#ffffff';
      ctx.fill();
    }

    ctx.beginPath();
    ctx.arc(this.centerX, this.centerY, this.radius, 0, Math.PI * 2);
    ctx.strokeStyle = '#2c3e50';
    ctx.lineWidth = 3;
    ctx.stroke();
  }

  drawNumbers() {
    const ctx = this.ctx;
    ctx.font = 'bold 18px sans-serif';
    ctx.fillStyle = '#2c3e50';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    for (let num = 1; num <= 12; num++) {
      const angle = (num * 30 - 90) * (Math.PI / 180);
      const x = this.centerX + Math.cos(angle) * (this.radius - 30);
      const y = this.centerY + Math.sin(angle) * (this.radius - 30);
      ctx.fillText(num.toString(), x, y);
    }
  }

  drawTicks() {
    const ctx = this.ctx;

    for (let i = 0; i < 60; i++) {
      const angle = (i * 6 - 90) * (Math.PI / 180);
      const isHour = i % 5 === 0;
      const outerRadius = this.radius - 8;
      const innerRadius = isHour ? this.radius - 20 : this.radius - 14;

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
    const hours = time.getHours() % 12;
    const minutes = time.getMinutes();
    const seconds = time.getSeconds();
    const milliseconds = time.getMilliseconds();

    const smoothSeconds = seconds + milliseconds / 1000;
    const smoothMinutes = minutes + smoothSeconds / 60;
    const smoothHours = hours + smoothMinutes / 60;

    const hourAngle = (smoothHours * 30) * (Math.PI / 180);
    const minuteAngle = (smoothMinutes * 6) * (Math.PI / 180);
    const secondAngle = (smoothSeconds * 6) * (Math.PI / 180);

    this.drawSingleHand(this.hourHand, hourAngle);
    this.drawSingleHand(this.minuteHand, minuteAngle);
    this.drawSingleHand(this.secondHand, secondAngle);
  }

  drawSingleHand(hand, angle) {
    const ctx = this.ctx;
    ctx.save();
    ctx.translate(this.centerX, this.centerY);
    ctx.rotate(angle);
    hand.draw(ctx, this.radius);
    ctx.restore();
  }

  drawCenterDot() {
    const ctx = this.ctx;

    ctx.beginPath();
    ctx.arc(this.centerX, this.centerY, 8, 0, Math.PI * 2);
    ctx.fillStyle = '#c0392b';
    ctx.fill();

    ctx.beginPath();
    ctx.arc(this.centerX, this.centerY, 3, 0, Math.PI * 2);
    ctx.fillStyle = '#ffffff';
    ctx.fill();
  }
}

export default function AnalogClock() {
  const canvasRef = useRef(null);
  const clockRef = useRef(null);
  const animationRef = useRef(null);
  const tubesCanvasRef = useRef(null);
  const tubesAppRef = useRef(null);

  const [isPaused, setIsPaused] = useState(false);
  const [trailEffect, setTrailEffect] = useState(false);
  const [digitalTime, setDigitalTime] = useState('00:00:00');
  const [tubesEnabled, setTubesEnabled] = useState(false);

  const animate = useCallback(() => {
    if (clockRef.current && !isPaused) {
      const now = clockRef.current.render(trailEffect);
      const hours = now.getHours().toString().padStart(2, '0');
      const minutes = now.getMinutes().toString().padStart(2, '0');
      const seconds = now.getSeconds().toString().padStart(2, '0');
      setDigitalTime(`${hours}:${minutes}:${seconds}`);
      animationRef.current = requestAnimationFrame(animate);
    }
  }, [isPaused, trailEffect]);

  useEffect(() => {
    if (canvasRef.current) {
      clockRef.current = new Clock(canvasRef.current);
      animate();
    }
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!isPaused) {
      animate();
    }
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isPaused, trailEffect, animate]);

  useEffect(() => {
    const handleKeydown = (e) => {
      if (e.code === 'Space') {
        e.preventDefault();
        setIsPaused(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleKeydown);
    return () => window.removeEventListener('keydown', handleKeydown);
  }, []);

  useEffect(() => {
    const canvas = tubesCanvasRef.current;
    if (!canvas) return;

    if (tubesEnabled) {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;

      if (!tubesAppRef.current) {
        import('https://cdn.jsdelivr.net/npm/threejs-components@0.0.19/build/cursors/tubes1.min.js')
          .then(({ default: TubesCursor }) => {
            tubesAppRef.current = TubesCursor(canvas, {
              tubes: {
                colors: ['#069804', '#ac43d7', '#96a72a'],
                lights: {
                  intensity: 200,
                  colors: ['#7c0c91', '#0175d1', '#00ff75', '#9f512a'],
                },
              },
            });
          });
      }
    }
  }, [tubesEnabled]);

  function randomColors(count) {
    return new Array(count).fill(0).map(
      () => '#' + Math.floor(Math.random() * 16777215).toString(16).padStart(6, '0')
    );
  }

  function handleBodyClick() {
    if (!tubesAppRef.current || !tubesEnabled) return;
    tubesAppRef.current.tubes.setColors(randomColors(3));
    tubesAppRef.current.tubes.setLightsColors(randomColors(4));
  }

  const containerStyle = {
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    background: '#eef0f3',
    fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
  };

  const cardStyle = {
    textAlign: 'center',
    background: '#ffffff',
    padding: '40px',
    borderRadius: '6px',
    boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
  };

  const statusStyle = {
    marginTop: '10px',
    padding: '4px 14px',
    borderRadius: '3px',
    fontWeight: '600',
    fontSize: '0.72rem',
    letterSpacing: '1.5px',
    display: 'inline-block',
    background: isPaused ? '#fce4ec' : '#e8f5e9',
    color: isPaused ? '#c62828' : '#2e7d32',
    border: isPaused ? '1px solid #ef9a9a' : '1px solid #a5d6a7',
  };

  const btnBaseStyle = {
    padding: '7px 18px',
    border: '1px solid #d0d5dd',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.82rem',
    fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
    background: '#ffffff',
    color: '#1a2533',
  };

  const btnPauseStyle = {
    ...btnBaseStyle,
    background: '#1a2533',
    color: '#ffffff',
    borderColor: '#1a2533',
  };

  return (
    <div style={containerStyle} onClick={handleBodyClick}>
      <canvas
        ref={tubesCanvasRef}
        style={{
          position: 'fixed', top: 0, left: 0,
          width: '100%', height: '100%',
          zIndex: 2,
          display: tubesEnabled ? 'block' : 'none',
          pointerEvents: 'none',
          mixBlendMode: 'difference',
        }}
      />
      <div style={{ ...cardStyle, position: 'relative', zIndex: 1 }}>
        <h1 style={{ color: '#1a2533', marginBottom: '24px', fontSize: '1.1rem', fontWeight: '600', letterSpacing: '1px', textTransform: 'uppercase' }}>
          Zegar Analogowy
        </h1>

        <canvas
          ref={canvasRef}
          width={400}
          height={400}
          style={{ borderRadius: '50%', display: 'block', margin: '0 auto' }}
        />

        <div style={{ marginTop: '18px', fontSize: '1.4rem', color: '#1a2533', fontFamily: "'Courier New', monospace", letterSpacing: '3px' }}>
          {digitalTime}
        </div>

        <div style={statusStyle}>
          {isPaused ? 'NIE DZIAŁA' : 'DZIAŁA'}
        </div>

        <div style={{ marginTop: '16px', display: 'flex', gap: '8px', justifyContent: 'center' }}>
          <button onClick={() => setIsPaused(prev => !prev)} style={btnPauseStyle}>
            {isPaused ? 'Wznów (Spacja)' : 'Pauza (Spacja)'}
          </button>

          <button onClick={() => setTrailEffect(prev => !prev)} style={btnBaseStyle}>
            Spirograf: {trailEffect ? 'WŁ' : 'WYŁ'}
          </button>

          <button onClick={(e) => { e.stopPropagation(); setTubesEnabled(prev => !prev); }} style={btnBaseStyle}>
            Kursor 3D: {tubesEnabled ? 'WŁ' : 'WYŁ'}
          </button>
        </div>

        <p style={{ marginTop: '14px', color: '#6b7280', fontSize: '0.78rem' }}>
          Naciśnij <strong>Spację</strong> aby zatrzymać / wznowić
        </p>
      </div>
    </div>
  );
}
