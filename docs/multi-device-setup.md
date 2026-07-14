> **NOTA rename (13 Lug 2026):** il progetto si chiama ora **wadachi** (ex Engram).
> Il server MCP si registra come `wadachi`, il package Python è `wadachi`
> (`from wadachi.store import ...`), l'entry point è `venv/bin/wadachi`
> (con alias legacy `venv/bin/engram`). I **path su disco restano invariati**:
> repo in `/Volumes/ExtremeSSD/engram/`, brain in `/Volumes/ExtremeSSD/engram-brain/`.

# Engram multi-device — usare lo stesso "cervello" su più Mac

> Obiettivo: un **unico brain** condiviso tra Mac Mini e MacBook Air (ed eventuali
> altre macchine), portato fisicamente dall'SSD esterno. Sicuro, veloce, senza
> rischio di corruzione del database.

---

## 0 · TL;DR (checklist)

```
[ ] 1. Sul Mac che HA i dati (Mini): copia ~/.engram  ->  /Volumes/ExtremeSSD/engram-brain
[ ] 2. Su OGNI Mac: esegui  scripts/setup-device.sh   (crea venv locale + registra MCP)
[ ] 3. Su OGNI Mac: riavvia Claude Code
[ ] 4. Verifica:  in una sessione chiama il tool  brain_status  /  list_projects
[ ] 5. (consigliato) Versiona i markdown del brain con git  +  backup periodico di brain.db
```

Regola d'oro: **un solo Mac alla volta** usa il brain (quello a cui è collegato
l'SSD). Niente uso simultaneo, niente cloud-sync del database.

---

## 1 · Modello mentale: tre cose distinte

Engram è fatto di tre componenti che vanno trattati **diversamente**:

| Componente | Cos'è | Dove vive | Condiviso? |
|---|---|---|---|
| **Codice** | il programma (`engram/*.py`) | `/Volumes/ExtremeSSD/engram` | **Sì** — sull'SSD, uguale per tutti |
| **Dati** (il "brain") | `brain.db` + i markdown delle memorie | `BRAIN_DIR` | **Sì** — sull'SSD, uguale per tutti |
| **Ambiente** (venv) | interprete Python + dipendenze installate | locale a ogni Mac | **No** — uno per macchina |

Il punto che genera quasi tutti i problemi: **il venv non è portabile**. Un virtualenv
ha "cotto" dentro di sé il percorso assoluto dell'interprete Python e dei binari
compilati per quella specifica architettura/versione. Spostarlo su un altro Mac (o
aggiornare Python) lo rompe — è *esattamente* il motivo per cui il `venv/` storico
sull'SSD oggi è inservibile (punta a un `python3.14` che non esiste più).

> **Conseguenza progettuale:** condividiamo **codice + dati** sull'SSD, ma ogni Mac
> ha il **suo venv locale**, ricreabile in pochi secondi con lo script di setup.

Come engram trova i dati (`engram/server.py:25`):

```python
brain_dir = os.environ.get("BRAIN_DIR", os.path.expanduser("~/.engram"))
store = MemoryStore(brain_dir)
```

Se **non** imposti `BRAIN_DIR`, ogni macchina usa `~/.engram` **locale** → cervelli
separati e vuoti. Tutta l'infrastruttura qui sotto serve a forzare `BRAIN_DIR` sullo
**stesso** percorso dell'SSD su ogni Mac.

---

## 2 · Strategia di storage: brain sull'SSD

`BRAIN_DIR = /Volumes/ExtremeSSD/engram-brain`

Perché l'SSD e non il cloud:

- **SQLite + sync cloud (iCloud/OneDrive/Dropbox) = rischio corruzione.** Questi
  servizi sincronizzano il file a blocchi e possono sovrascriverlo mentre engram ci
  scrive, o fonderlo male se due Mac toccano il DB ravvicinati. È un anti-pattern noto.
- L'SSD lo **sposti fisicamente**: per costruzione un solo Mac alla volta lo monta →
  accesso **serializzato**, zero conflitti. È il modello più semplice e robusto.
- Su macOS un volume chiamato `ExtremeSSD` monta sempre su `/Volumes/ExtremeSSD`:
  il percorso è **identico** su ogni Mac → la config MCP è copia-incolla.

> Vuoi davvero la disponibilità "sempre, senza SSD"? È possibile ma è un livello di
> complessità superiore (sync con lock): vedi §9 "Evoluzioni avanzate". Per ora l'SSD
> è la scelta giusta: massima affidabilità, minima complessità.

---

## 3 · Migrazione: portare i dati del Mini sull'SSD

I dati attuali stanno nella home del Mac Mini (`~/.engram` **del Mini**). Vanno copiati
una volta sola sull'SSD. **Sul Mac Mini, con l'SSD collegato:**

```bash
# copia incrementale di brain.db + tutti i markdown
rsync -av --progress ~/.engram/ /Volumes/ExtremeSSD/engram-brain/
```

Verifica che sia arrivato tutto:

```bash
ls -la /Volumes/ExtremeSSD/engram-brain
BRAIN_DIR=/Volumes/ExtremeSSD/engram-brain /Volumes/ExtremeSSD/engram/scripts/with-venv.sh \
  python -c "from engram.store import MemoryStore as M; s=M(); \
  print('progetti:', [p['name'] for p in s.list_projects()]); \
  print('memorie:', len(s.list_memories()))"
```

> Se sul MacBook Air era stato creato un `~/.engram` vuoto per errore, eliminalo per
> non confonderti — **non** è la fonte dei dati:
> ```bash
> rm -rf ~/.engram      # solo se vuoto / non è la fonte autoritativa
> ```

---

## 4 · Setup di ogni macchina (automatico)

Sull'SSD c'è uno script che fa tutto: crea il venv **locale** alla macchina, installa
le dipendenze (incluso il motore semantico) e registra il server MCP in Claude Code con
il `BRAIN_DIR` corretto.

```bash
/Volumes/ExtremeSSD/engram/scripts/setup-device.sh
```

Poi **riavvia Claude Code**. Da quel momento, in ogni sessione, avrai i tool
`get_context`, `recall`, `store_memory`, `store_decision`, ecc.

Cosa fa lo script, in breve:

1. controlla che l'SSD sia montato e che il brain condiviso esista;
2. crea/aggiorna un venv **per-macchina** in `~/.local/share/engram/venv`
   (con `uv` se presente — molto più veloce — altrimenti `python3 -m venv`);
3. installa engram in modalità editable con l'extra semantico:
   `pip install -e "/Volumes/ExtremeSSD/engram[semantic]"`;
4. registra il server MCP a livello utente:
   ```bash
   claude mcp add engram --scope user \
     --env BRAIN_DIR=/Volumes/ExtremeSSD/engram-brain \
     -- ~/.local/share/engram/venv/bin/python /Volumes/ExtremeSSD/engram/engram/server.py
   ```
5. esegue una verifica d'import e stampa i progetti trovati.

### Setup manuale (se preferisci capire ogni passo)

```bash
SSD=/Volumes/ExtremeSSD
VENV=$HOME/.local/share/engram/venv

# 1. venv locale (NON sull'SSD)
uv venv "$VENV" --python 3.13                 # oppure: python3 -m venv "$VENV"
uv pip install --python "$VENV/bin/python" -e "$SSD/engram[semantic]"

# 2. registra il server MCP (scope user = vale per tutte le sessioni)
claude mcp remove engram --scope user 2>/dev/null || true
claude mcp add engram --scope user \
  --env BRAIN_DIR="$SSD/engram-brain" \
  -- "$VENV/bin/python" "$SSD/engram/engram/server.py"

# 3. controlla
claude mcp list
```

> **Prima volta che usi la ricerca semantica:** `fastembed` scarica il modello
> `BAAI/bge-small-en-v1.5` (~200 MB) e lo mette in cache **locale** alla macchina.
> Succede una volta per Mac. Nessuna chiamata cloud dopo.

---

## 5 · Pulizia del venv rotto storico

Il vecchio `venv/` nella root del repo sull'SSD è inservibile e fuorviante. Rimuovilo e
tienilo fuori dal versionamento:

```bash
rm -rf /Volumes/ExtremeSSD/engram/venv
```

Aggiungi a `.gitignore` del repo (se usi git):

```
venv/
.venv/
*.egg-info/
__pycache__/
```

I venv non vanno **mai** committati né messi sull'SSD condiviso: si rigenerano con lo
script di setup su ciascuna macchina.

---

## 6 · Integrità e sicurezza dei dati

- **Single-writer per costruzione.** Solo il Mac con l'SSD collegato scrive. Non
  collegare l'SSD a due Mac contemporaneamente (es. via condivisione/Thunderbolt
  target) mentre engram è attivo.
- **Espelli sempre l'SSD prima di scollegarlo** (`diskutil eject ExtremeSSD` o dal
  Finder), così SQLite chiude pulito e nessuna scrittura resta a metà.
- **SSD non montato = errore esplicito, non danno silenzioso.** Se l'SSD non c'è, il
  percorso `/Volumes/ExtremeSSD/engram-brain` non esiste e il server fallisce all'avvio
  invece di creare di nascosto un brain vuoto in home. È il comportamento voluto:
  meglio un errore chiaro che dati persi. (Se vuoi un fallback più gentile, vedi lo
  script `with-venv.sh` che controlla il mount prima di partire.)
- **WAL (opzionale, consigliato).** Per maggiore resilienza alle interruzioni puoi
  abilitare il journaling WAL sul database una volta sola:
  ```bash
  sqlite3 /Volumes/ExtremeSSD/engram-brain/brain.db 'PRAGMA journal_mode=WAL;'
  ```

---

## 7 · Backup e versionamento

Il brain ha due nature: **markdown leggibili** (il contenuto) + **`brain.db`**
(metadati + cache embeddings). Strategia robusta:

1. **Versiona i markdown con git** dentro `BRAIN_DIR` — diff leggibili, storia, recupero:
   ```bash
   cd /Volumes/ExtremeSSD/engram-brain
   git init
   printf 'brain.db\nbrain.db-wal\nbrain.db-shm\n' > .gitignore
   git add . && git commit -m "snapshot brain"
   ```
   (Il `.db` è ricostruibile/è cache: lo si esclude per evitare conflitti binari.)
2. **Backup periodico di `brain.db`** — è la fonte dei metadati e degli embedding:
   ```bash
   cp /Volumes/ExtremeSSD/engram-brain/brain.db \
      /Volumes/ExtremeSSD/engram-brain/backups/brain-$(date +%Y%m%d).db
   ```
   Automatizzabile con un hook di Claude Code o un `launchd`/cron.

> Nota: i markdown sono la fonte *umana*; gli embedding nel DB sono *cache* rigenerabile
> al `recall`. Quindi anche perdendo il `.db`, il contenuto vive nei markdown.

---

## 8 · Verifica e diagnostica

In una sessione Claude Code (dopo il riavvio), i tool MCP rispondono a:

- `brain_status` → stato, statistiche, percorso del brain in uso;
- `list_projects` → deve mostrare i progetti migrati dal Mini;
- `recall "..."` → ricerca semantica.

Da terminale, controllo rapido senza Claude:

```bash
BRAIN_DIR=/Volumes/ExtremeSSD/engram-brain ~/.local/share/engram/venv/bin/python - <<'PY'
from engram.store import MemoryStore
s = MemoryStore()
print("brain_dir:", s.brain_dir)
print("progetti :", [p["name"] for p in s.list_projects()])
print("memorie  :", len(s.list_memories()))
PY
```

Se `brain_dir` **non** è il percorso sull'SSD → `BRAIN_DIR` non è arrivato al processo
(controlla la config MCP con `claude mcp get engram`).

---

## 9 · Troubleshooting

| Sintomo | Causa | Rimedio |
|---|---|---|
| `bad interpreter: .../python3.14` | venv vecchio non portabile | ricrea il venv con `setup-device.sh` |
| Brain vuoto su una macchina | `BRAIN_DIR` non impostato → usa `~/.engram` locale | verifica `claude mcp get engram`, reimposta `--env BRAIN_DIR=...` |
| `No module named mcp` / `fastembed` | venv senza dipendenze | `uv pip install -e "/Volumes/ExtremeSSD/engram[semantic]"` |
| Il server MCP non parte | SSD non montato | collega/monta l'SSD, poi riavvia Claude Code |
| `recall` lento la prima volta | download modello embeddings | normale (~200 MB, una volta per Mac) |
| Memorie "sparite" dopo scollegamento | scritte su brain locale, non sull'SSD | controlla `BRAIN_DIR`; non lavorare con SSD assente |

---

## 10 · Evoluzioni avanzate (roadmap infra)

Quando vorrai alzare l'asticella oltre il modello "SSD-carry":

- **Sync senza SSD, peer-to-peer:** [Syncthing](https://syncthing.net) tra i Mac sui
  *soli markdown* + ricostruzione del DB on-demand. Evita i problemi del cloud-sync su
  SQLite perché sincronizzi file di testo, non il database.
- **Brain in git remoto privato:** i markdown come repo; un hook ricostruisce/aggiorna
  `brain.db` dai markdown all'avvio. Versionamento + multi-device "veri".
- **Lock multi-device:** un file di lock (`brain.lock`) con hostname+timestamp per
  impedire scritture concorrenti se un giorno il brain finisse su storage realmente
  condiviso in contemporanea.
- **Cache embeddings centralizzata:** spostare la cache del modello fastembed su un
  percorso noto per non riscaricarlo su ogni nuova macchina.
- **Hook di Claude Code:** `get_context` automatico a inizio sessione + backup di
  `brain.db` allo stop (vedi la roadmap nel README).

---

## 11 · Riferimenti rapidi

| Cosa | Percorso / comando |
|---|---|
| Repo (codice) | `/Volumes/ExtremeSSD/engram` |
| Brain condiviso (dati) | `/Volumes/ExtremeSSD/engram-brain` |
| Venv locale (per-Mac) | `~/.local/share/engram/venv` |
| Server MCP | `engram/server.py` (legge `BRAIN_DIR` da env) |
| Setup macchina | `scripts/setup-device.sh` |
| Wrapper venv+check | `scripts/with-venv.sh` |
| Variabile chiave | `BRAIN_DIR=/Volumes/ExtremeSSD/engram-brain` |
