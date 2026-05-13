"""Networking module for Asteroids on Steroids multiplayer.

Architecture
────────────
- **Host** runs the authoritative game loop. Clients send inputs, host
  broadcasts the full game snapshot every tick.
- **TCP** (port 5556) carries the reliable game-state stream between
  host and each connected client.
- **UDP broadcast** (port 5555) is used only for LAN discovery —
  the host periodically announces itself so that clients on the same
  subnet can find it without typing an IP.
- Messages are length-prefixed JSON (4-byte big-endian length + UTF-8
  JSON payload).  Kept intentionally simple for a university project.

Lobby flow
──────────
1. Client connects, sends {"type":"join","name":"..."}
2. Server replies {"type":"accept","name":"HostName","config":{...}}
3. Client enters lobby state.  Server periodically broadcasts
   {"type":"lobby","players":[{name,ready},...]} to all clients.
4. Client sends {"type":"ready"} to toggle ready.
5. Host can force-start or wait for all ready.
6. Server sends {"type":"game_start"} → everyone enters playing.
"""

import json
import socket
import struct
import threading
import time
import traceback

# ── Ports ──
DISCOVERY_PORT = 5555
GAME_PORT = 5556
DISCOVERY_MAGIC = b"ASTMULTI"
BROADCAST_INTERVAL = 1.0  # seconds between discovery beacons
DEFAULT_MAX_CLIENTS = 3   # default max players (besides host)

# ── Message helpers ──

def _send_msg(sock, obj):
    """Send a length-prefixed JSON message on *sock*.  Returns False on error."""
    try:
        data = json.dumps(obj, separators=(',', ':')).encode('utf-8')
        header = struct.pack('>I', len(data))
        sock.sendall(header + data)
        return True
    except (OSError, BrokenPipeError):
        return False


def _recv_msg(sock, timeout=None):
    """Receive one length-prefixed JSON message.  Returns dict or None."""
    if timeout is not None:
        sock.settimeout(timeout)
    try:
        raw_len = _recvall(sock, 4)
        if raw_len is None:
            return None
        msg_len = struct.unpack('>I', raw_len)[0]
        if msg_len > 2_000_000:  # sanity cap (larger for full state)
            return None
        raw = _recvall(sock, msg_len)
        if raw is None:
            return None
        return json.loads(raw.decode('utf-8'))
    except (OSError, json.JSONDecodeError, struct.error):
        return None


def _recvall(sock, n):
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf.extend(chunk)
    return bytes(buf)


def get_local_ip():
    """Best-effort LAN IP of this machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# ══════════════════════════════════════════════
#  GameServer — runs on the host
# ══════════════════════════════════════════════

class GameServer:
    def __init__(self, player_name="Host", port=GAME_PORT, max_clients=DEFAULT_MAX_CLIENTS,
                 server_config=None):
        self.player_name = player_name
        self.running = False
        self.clients = []       # list of (socket, addr, name)
        self.client_inputs = {} # addr_str -> latest input dict
        self.client_ready = {}  # addr_str -> bool
        self.client_colors = {} # addr_str -> [r, g, b]
        self.client_skins = {}  # addr_str -> int (skin index)
        self._lock = threading.Lock()
        self._tcp_sock = None
        self._disc_sock = None
        self._threads = []
        self.local_ip = get_local_ip()
        self.port = port
        self.max_clients = max_clients
        self.server_config = server_config or {}  # game rules sent to clients
        self.status = "idle"    # idle / waiting / lobby / playing / error
        self.status_msg = ""
        self.game_started = False  # set True when host starts the game

    def start(self):
        """Start listening for connections + broadcasting discovery."""
        try:
            self._tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._tcp_sock.bind(('', self.port))
            self._tcp_sock.listen(self.max_clients + 1)
            self._tcp_sock.settimeout(1.0)
            self.running = True
            self.status = "waiting"
            self.status_msg = f"Waiting on {self.local_ip}:{self.port}"

            t1 = threading.Thread(target=self._accept_loop, daemon=True)
            t1.start()
            self._threads.append(t1)

            t2 = threading.Thread(target=self._discovery_loop, daemon=True)
            t2.start()
            self._threads.append(t2)
        except OSError as e:
            self.status = "error"
            self.status_msg = f"Port {self.port} in use"
            self.running = False

    def stop(self):
        self.running = False
        with self._lock:
            for sock, _, _ in self.clients:
                try:
                    sock.close()
                except OSError:
                    pass
            self.clients.clear()
            self.client_inputs.clear()
            self.client_ready.clear()
            self.client_colors.clear()
            self.client_skins.clear()
        if self._tcp_sock:
            try:
                self._tcp_sock.close()
            except OSError:
                pass
        if self._disc_sock:
            try:
                self._disc_sock.close()
            except OSError:
                pass
        self.status = "idle"
        self.game_started = False

    @property
    def client_count(self):
        with self._lock:
            return len(self.clients)

    def get_client_names(self):
        """Return list of (name, ready) tuples for all connected clients."""
        with self._lock:
            result = []
            for sock, addr, name in self.clients:
                addr_str = f"{addr[0]}:{addr[1]}"
                ready = self.client_ready.get(addr_str, False)
                result.append((name, ready))
            return result

    def get_first_client_color(self):
        """Return the ship color of the first connected client."""
        with self._lock:
            for sock, addr, name in self.clients:
                addr_str = f"{addr[0]}:{addr[1]}"
                return self.client_colors.get(addr_str, [255, 255, 255])
        return [255, 255, 255]

    def get_first_client_skin(self):
        """Return the ship skin index of the first connected client."""
        with self._lock:
            for sock, addr, name in self.clients:
                addr_str = f"{addr[0]}:{addr[1]}"
                return self.client_skins.get(addr_str, 0)
        return 0

    def get_lobby_info(self):
        """Return lobby player list for broadcast."""
        with self._lock:
            players = [{"name": self.player_name, "ready": True, "host": True}]
            for sock, addr, name in self.clients:
                addr_str = f"{addr[0]}:{addr[1]}"
                ready = self.client_ready.get(addr_str, False)
                players.append({"name": name, "ready": ready, "host": False})
            return players

    def all_ready(self):
        """Check if all connected clients are ready."""
        with self._lock:
            if not self.clients:
                return False
            return all(self.client_ready.get(f"{a[0]}:{a[1]}", False)
                       for _, a, _ in self.clients)

    def get_ready_count(self):
        """Number of ready clients."""
        with self._lock:
            return sum(1 for _, a, _ in self.clients
                       if self.client_ready.get(f"{a[0]}:{a[1]}", False))

    def start_game(self):
        """Host triggers game start — notify all ready clients."""
        self.game_started = True
        self.status = "playing"
        with self._lock:
            kick_list = []
            for sock, addr, name in self.clients:
                addr_str = f"{addr[0]}:{addr[1]}"
                if self.client_ready.get(addr_str, False):
                    _send_msg(sock, {"type": "game_start"})
                else:
                    # Kick not-ready players
                    _send_msg(sock, {"type": "kick", "reason": "not_ready"})
                    kick_list.append((sock, addr, name))
            for entry in kick_list:
                try:
                    entry[0].close()
                except OSError:
                    pass
                self.clients.remove(entry)
                addr_str = f"{entry[1][0]}:{entry[1][1]}"
                self.client_inputs.pop(addr_str, None)
                self.client_ready.pop(addr_str, None)
                self.client_colors.pop(addr_str, None)
                self.client_skins.pop(addr_str, None)

    def broadcast_lobby(self):
        """Send lobby state to all connected clients."""
        info = self.get_lobby_info()
        with self._lock:
            dead = []
            for sock, addr, name in self.clients:
                ok = _send_msg(sock, {"type": "lobby", "players": info})
                if not ok:
                    dead.append((sock, addr, name))
            for entry in dead:
                try:
                    entry[0].close()
                except OSError:
                    pass
                self.clients.remove(entry)
                addr_str = f"{entry[1][0]}:{entry[1][1]}"
                self.client_inputs.pop(addr_str, None)
                self.client_ready.pop(addr_str, None)
                self.client_colors.pop(addr_str, None)
                self.client_skins.pop(addr_str, None)

    # ── accept loop ──

    def _accept_loop(self):
        while self.running:
            try:
                conn, addr = self._tcp_sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            # Handshake — expect {"type":"join","name":"..."}
            msg = _recv_msg(conn, timeout=5.0)
            if not msg or msg.get('type') != 'join':
                conn.close()
                continue

            name = msg.get('name', 'Player')[:16]
            client_color = msg.get('color', [255, 255, 255])
            client_skin = msg.get('skin', 0)
            with self._lock:
                if len(self.clients) >= self.max_clients:
                    _send_msg(conn, {"type": "reject", "reason": "full"})
                    conn.close()
                    continue
                if self.game_started:
                    _send_msg(conn, {"type": "reject", "reason": "game_in_progress"})
                    conn.close()
                    continue
                _send_msg(conn, {"type": "accept", "name": self.player_name,
                                 "config": self.server_config})
                self.clients.append((conn, addr, name))
                addr_str = f"{addr[0]}:{addr[1]}"
                self.client_inputs[addr_str] = {}
                self.client_ready[addr_str] = False
                self.client_colors[addr_str] = client_color
                self.client_skins[addr_str] = client_skin
                if self.status == "waiting":
                    self.status = "lobby"
                self.status_msg = f"{len(self.clients)} player(s) in lobby"

            # Spawn a reader thread for this client
            t = threading.Thread(target=self._client_reader,
                                 args=(conn, addr, name), daemon=True)
            t.start()
            self._threads.append(t)

    def _client_reader(self, conn, addr, name):
        addr_str = f"{addr[0]}:{addr[1]}"
        while self.running:
            msg = _recv_msg(conn, timeout=2.0)
            if msg is None:
                # Check if it's just a timeout (no data) vs disconnect
                try:
                    conn.getpeername()
                    continue
                except OSError:
                    break
            if msg.get('type') == 'input':
                with self._lock:
                    self.client_inputs[addr_str] = msg.get('data', {})
            elif msg.get('type') == 'ready':
                with self._lock:
                    self.client_ready[addr_str] = not self.client_ready.get(addr_str, False)
            elif msg.get('type') == 'leave':
                break

        # Client disconnected
        with self._lock:
            self.clients = [(s, a, n) for s, a, n in self.clients
                            if f"{a[0]}:{a[1]}" != addr_str]
            self.client_inputs.pop(addr_str, None)
            self.client_ready.pop(addr_str, None)
            self.client_colors.pop(addr_str, None)
            if not self.clients:
                self.status = "waiting"
                self.status_msg = f"Waiting on {self.local_ip}:{self.port}"
            else:
                self.status_msg = f"{len(self.clients)} player(s) in lobby"
        try:
            conn.close()
        except OSError:
            pass

    # ── discovery beacon ──

    def _discovery_loop(self):
        try:
            self._disc_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._disc_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        except OSError:
            return

        while self.running:
            try:
                beacon = {
                    "magic": DISCOVERY_MAGIC.decode(),
                    "name": self.player_name,
                    "ip": self.local_ip,
                    "port": self.port,
                    "players": self.client_count,
                    "max": self.max_clients + 1,
                }
                data = json.dumps(beacon).encode('utf-8')
                self._disc_sock.sendto(data, ('<broadcast>', DISCOVERY_PORT))
            except OSError:
                pass
            time.sleep(BROADCAST_INTERVAL)

    # ── broadcast state to clients ──

    def broadcast_state(self, state_dict):
        """Send snapshot to every connected client.  Called from game loop."""
        with self._lock:
            dead = []
            for sock, addr, name in self.clients:
                ok = _send_msg(sock, {"type": "state", "data": state_dict})
                if not ok:
                    dead.append((sock, addr, name))
            for entry in dead:
                try:
                    entry[0].close()
                except OSError:
                    pass
                self.clients.remove(entry)
                addr = entry[1]
                self.client_inputs.pop(f"{addr[0]}:{addr[1]}", None)
                self.client_ready.pop(f"{addr[0]}:{addr[1]}", None)
                self.client_colors.pop(f"{addr[0]}:{addr[1]}", None)
                self.client_skins.pop(f"{addr[0]}:{addr[1]}", None)
            if not self.clients and dead:
                self.status = "waiting"
                self.status_msg = f"Waiting on {self.local_ip}:{self.port}"

    def get_client_input(self):
        """Return the latest input dict from the first client."""
        with self._lock:
            for v in self.client_inputs.values():
                return dict(v)
        return {}


# ══════════════════════════════════════════════
#  GameClient — runs on the joining player
# ══════════════════════════════════════════════

class GameClient:
    def __init__(self, player_name="Player", ship_color=(255, 255, 255), ship_skin=0):
        self.player_name = player_name
        self.ship_color = ship_color
        self.ship_skin = ship_skin
        self.connected = False
        self.host_name = ""
        self.server_config = {}
        self.status = "idle"
        self.status_msg = ""
        self._sock = None
        self._lock = threading.Lock()
        self._latest_state = None
        self._reader_thread = None
        # Lobby
        self.lobby_players = []   # list of {"name":..,"ready":..,"host":..}
        self.game_started = False
        self.is_ready = False

    def connect(self, host_ip, port=GAME_PORT):
        """Try to connect to a host.  Blocking, call from a thread or wrap."""
        self.status = "connecting"
        self.status_msg = f"Connecting to {host_ip}:{port}..."
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(5.0)
            self._sock.connect((host_ip, port))
            _send_msg(self._sock, {"type": "join", "name": self.player_name,
                                   "color": list(self.ship_color),
                                   "skin": self.ship_skin})
            resp = _recv_msg(self._sock, timeout=5.0)
            if resp is None or resp.get('type') != 'accept':
                reason = resp.get('reason', 'rejected') if resp else 'timeout'
                self.status = "error"
                self.status_msg = f"Rejected: {reason}"
                self._sock.close()
                self._sock = None
                return False
            self.host_name = resp.get('name', 'Host')
            self.server_config = resp.get('config', {})
            self.connected = True
            self.status = "lobby"
            self.status_msg = f"In lobby - {self.host_name}'s game"
            self.game_started = False
            self.is_ready = False
            self._sock.settimeout(2.0)

            self._reader_thread = threading.Thread(
                target=self._reader_loop, daemon=True)
            self._reader_thread.start()
            return True
        except (OSError, socket.timeout) as e:
            self.status = "error"
            self.status_msg = f"Failed: {e}"
            if self._sock:
                try:
                    self._sock.close()
                except OSError:
                    pass
                self._sock = None
            return False

    def disconnect(self):
        self.connected = False
        if self._sock:
            try:
                _send_msg(self._sock, {"type": "leave"})
            except OSError:
                pass
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None
        self.status = "idle"
        self.status_msg = ""
        self.game_started = False
        self.is_ready = False

    def toggle_ready(self):
        """Toggle ready state and notify server."""
        if not self.connected or not self._sock:
            return
        self.is_ready = not self.is_ready
        _send_msg(self._sock, {"type": "ready"})

    def send_input(self, input_dict):
        """Send local player input to host."""
        if not self.connected or not self._sock:
            return
        ok = _send_msg(self._sock, {"type": "input", "data": input_dict})
        if not ok:
            self.connected = False
            self.status = "error"
            self.status_msg = "Connection lost"

    def get_state(self):
        """Return latest game-state snapshot from host (or None)."""
        with self._lock:
            s = self._latest_state
            self._latest_state = None
            return s

    def _reader_loop(self):
        while self.connected:
            msg = _recv_msg(self._sock, timeout=2.0)
            if msg is None:
                try:
                    if self._sock:
                        self._sock.getpeername()
                except OSError:
                    self.connected = False
                    self.status = "error"
                    self.status_msg = "Connection lost"
                    break
                continue
            mtype = msg.get('type')
            if mtype == 'state':
                with self._lock:
                    self._latest_state = msg.get('data')
            elif mtype == 'lobby':
                with self._lock:
                    self.lobby_players = msg.get('players', [])
            elif mtype == 'game_start':
                self.game_started = True
                self.status = "playing"
                self.status_msg = "Game starting!"
            elif mtype == 'kick':
                self.connected = False
                self.status = "error"
                reason = msg.get('reason', 'kicked')
                self.status_msg = f"Kicked: {reason}"
                break


# ══════════════════════════════════════════════
#  LAN Discovery Scanner
# ══════════════════════════════════════════════

class LANScanner:
    """Listens for host discovery beacons on the LAN."""

    def __init__(self):
        self.servers = {}   # ip:port -> {name, ip, port, players, max, last_seen}
        self._lock = threading.Lock()
        self._running = False
        self._sock = None
        self._thread = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        except Exception:
            pass
        try:
            self._sock.bind(('', DISCOVERY_PORT))
        except OSError:
            # Port already in use (we might be hosting)
            self._running = False
            return
        self._sock.settimeout(1.0)
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass

    def get_servers(self):
        """Return list of visible servers, pruning stale ones (>5s)."""
        now = time.time()
        with self._lock:
            stale = [k for k, v in self.servers.items()
                     if now - v['last_seen'] > 5.0]
            for k in stale:
                del self.servers[k]
            return list(self.servers.values())

    def _listen(self):
        while self._running:
            try:
                data, addr = self._sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                break
            try:
                info = json.loads(data.decode('utf-8'))
                if info.get('magic') != DISCOVERY_MAGIC.decode():
                    continue
                key = f"{info['ip']}:{info['port']}"
                entry = {
                    'name': info.get('name', '?'),
                    'ip': info['ip'],
                    'port': info['port'],
                    'players': info.get('players', 0),
                    'max': info.get('max', 2),
                    'last_seen': time.time(),
                }
                with self._lock:
                    self.servers[key] = entry
            except (json.JSONDecodeError, KeyError):
                continue
