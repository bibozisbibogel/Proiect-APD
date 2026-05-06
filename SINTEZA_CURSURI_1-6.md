# Sinteză APD — Cursurile 1–6 (Parțial)

---

## CURS 1 — Introducere în APD

### De ce APD?
- Trecere de la **gândirea secvențială** la **gândirea paralelă**
- Calculatoare moderne au chip-uri **multicore**
- Domenii: prognoze meteo, genetică, finanțe, inginerie, spațiu

### Definiții esențiale (le știi pe de rost!)

| Termen | Definiție scurtă |
|--------|-----------------|
| **Paralelism** | Utilizarea *simultană* a mai multor resurse de calcul pentru accelerare |
| **Concurență** | Administrarea *corectă și eficientă* a accesului la resurse |
| **Task/Activitate** | Un calcul care poate rula concurent cu altele (program, proces, fir) |
| **Atomicitate** | Proprietatea unei operații de a fi indivizibilă |
| **Consensus** | Acordul între două sau mai multe activități asupra unui predicat |
| **Consistență** | Reguli convenite despre valorile variabilelor în memoria partajată |
| **Multicast** | Transmiterea unui mesaj către mai mulți destinatari fără constrângeri de ordine |

> **Concurența ≠ Paralelism**: Concurența = logic active simultan; Paralelismul = fizic active simultan.

### Calculator paralel vs. distribuit

| Caracteristică | Paralel | Distribuit |
|---|---|---|
| Scop general | Viteză | Comoditate |
| Interacțiuni | Frecvente | Rare |
| Granularitate | Mare | Mică |
| Siguranță funcționare | Presupusă adevărată | Posibil neadevărată |

- **Sistem paralel** = procesoare *strâns cuplate* pe același sistem, comunică prin memorie partajată
- **Sistem distribuit** = sisteme *autonome* conectate în rețea, comunică prin mesaje

### Avantajele sistemelor distribuite
1. Partajare date și resurse
2. Comunicare (email, chat)
3. Flexibilitate (împărțire sarcini)
4. Cost scăzut vs. mainframe
5. Viteză prin load balancing
6. Distributivitate nativă (magazine, bănci)
7. Siguranță/Toleranță la defecte (redundanță)

### Limitările sistemelor distribuite
- Software greu de dezvoltat
- Rețea: întârzieri, saturație, pierderi
- Securitate
- **Problema consensului**: două noduri trebuie să convină prin canale nesigure

### Problema celor 2 Generali
- Doi generali trebuie să atace simultan, comunică prin mesageri care pot fi uciși
- **Nu are soluție** în prezența eșecurilor arbitrare de comunicare
- **Transmiterea atomică** ≡ **Consensus** (sunt echivalente!)

### Dificultăți în procesarea paralelă
1. **Debugging** — greu de replicat contextul (din cauza *interleaving*)
2. **Corectitudinea** — demonstrarea formală este dificilă
3. **Benchmark** — evaluarea performanței pe input mic poate induce în eroare
4. **Comunicarea** — proiectarea optimă a inter-proceselor

---

## CURS 2 — Tipuri și Nivele de Paralelism + POSIX

### Taxonomia lui Flynn (1972)

| Tip | Instrucțiuni | Date | Descriere |
|-----|-------------|------|-----------|
| **SISD** | 1 flux | 1 flux | Calculator clasic secvențial |
| **SIMD** | 1 flux | Multiple fluxuri | GPU, procesare vectorială |
| **MISD** | Multiple fluxuri | 1 flux | Teoretic, rar întâlnit |
| **MIMD** | Multiple fluxuri | Multiple fluxuri | Cel mai comun: sisteme multiprocesor |

**SIMD** — Toate procesoarele execută *aceeași instrucțiune* pe *date diferite*. Avantaj: control unic, memorie mai puțină. Dezavantaj: rigid, bun doar pentru probleme bine structurate.

**MIMD** — Fiecare procesor execută flux propriu de instrucțiuni pe date proprii. Cel mai flexibil, dar mai complex.

### PRAM (Parallel Random Access Machine)
- Model teoretic cu **memorie partajată** — accesul se face în timp constant (cost 0)
- Omologul modelului von Neumann pentru sisteme paralele
- **Instrucțiune**: `For all x in X do in parallel`

#### Variante PRAM (după accesul la memorie):
- **EREW** — Exclusive Read, Exclusive Write (cel mai realist)
- **CREW** — Concurrent Read, Exclusive Write
- **CRCW** — Concurrent Read, Concurrent Write (cel mai puțin realist)

### Topologii rețele de interconectare

#### Metrici de evaluare:
- **Diametru** (↓ mai bine) — lungimea maximă dintre oricare 2 noduri
- **Conectivitate** (↑ mai bine) — numărul minim de conexiuni de distrus pentru a obține 2 componente
- **Lățimea bisecțiunii** (↑ mai bine) — numărul minim de muchii care taie rețeaua în două jumătăți egale
- **Cost** (↓ mai bine) — numărul total de legături

| Topologie | Diametru | Conectivitate | Lăț. bisecțiune | Cost |
|-----------|----------|--------------|-----------------|------|
| Bus | O(1) | O(1) | O(1) | O(p) |
| Crossbar | O(1) | O(1) | O(p) | O(p²) |
| Hipercub | O(log p) | O(log p) | O(p/2) | O(p log p) |

### Costul comunicării (transmitere mesaje)

```
Tcom = Ts + Tw * m
```
- **Ts** = timpul de inițializare (setup, routing)
- **Tw** = timpul de transfer per cuvânt = 1 / lățimea canalului
- **m** = dimensiunea mesajului (în cuvinte)

> Ts este de obicei **mult mai mare** decât Tw, deci reducerea numărului de mesaje > reducerea dimensiunii lor.

### Accelerarea (Speedup)
```
S(p) = T₁ / Tp
```
- T₁ = cel mai bun timp secvențial (pe 1 procesor)
- Tp = timp paralel pe p procesoare
- **Important**: se folosește cel mai bun algoritm secvențial!

### Pipelining
- Se descompune procesul în **K segmente/stadii** distincte
- Fiecare stadiu e dedicat unui procesor
- **Formula**: `Tk = (K + (N-1)) * T`
  - K = numărul de stadii
  - N = numărul de elemente de procesat
  - T = durata unui ciclu (= cel mai lent stadiu)
- **Speedup**: `S = N*K / (K + N - 1)`
- Pentru **N >> K**: Speedup ≈ K
- Limitare: cel mai lent stadiu determină ritmul întregului pipeline

---

## CURS 3 — Modele de Calcul Paralel + C++ Threads

### Paralelism implicit vs. explicit
- **Implicit**: compilatorul paralelizează automat (ex: `a = 2; b = 3;` — independente)
- **Explicit**: programatorul specifică paralelismul prin directive sau biblioteci

> Atenție: `a = 3; b = a;` — NU poate fi paralelizat!

### Modelele algoritmice

| Model | Principiu |
|-------|-----------|
| **Paralelizarea datelor** | Input împărțit între procesoare; se procesează segmente diferite |
| **Paralelizare cu grafuri** | Algoritmul descompus în secțiuni distincte (fork/join/spawn) |
| **Paralelizare cu pool** | Task-urile asignate dinamic; fiecare task are date puține |

### Graful de dependințe (DAG)
- **DAG** = Graf Direcționat Aciclic
- Noduri = task-uri; Muchii = dependențe
- `A → B` înseamnă: B necesită terminarea lui A
- **Calea critică** = cel mai lung drum în DAG → determină limita inferioară a timpului paralel

### Metode de descompunere

| Metodă | Când se folosește |
|--------|------------------|
| **Descompunerea datelor** | Input/output voluminos; partiționăm datele → task-uri |
| **Descompunerea task-urilor** | Procesări distincte care pot rula independent |
| **Recursivă** | Divide et impera (quicksort, min, max) |
| **Exploratorie** | Spațiu de soluții; poate produce *speedup superliniar* |
| **Speculativă** | Pașii următori depind de rezultatul curent; se execută predicții |
| **Hibridă** | Combinație a metodelor de mai sus |

### Alocarea task-urilor
- **Overhead total**: `To = p * Tp - Ts`
- Surse: dezechilibrul încărcării, comunicarea, sincronizarea
- Strategii:
  1. Alocă task-uri independente pe procesoare **diferite** (↑ concurență)
  2. Alocă task-uri care comunică frecvent pe **același** procesor (↑ localizare)

---

## CURS 4 — Metrici de Performanță + STL Parallel

### Metrici fundamentale

```
Accelerare:    S(p) = T₁ / Tp
Eficiență:     E(p) = S(p) / p = T₁ / (p * Tp)
Cost total:    C = p * Tp
Redundanță:    R = (număr operații paralele) / (număr operații secvențiale)
Overhead:      To = p * Tp - T₁
```

- **Eficiență E ∈ (0, 1]** — cât din timpul total al procesoarelor este util
- Adăugarea de procesoare **↓ eficiența** pentru dimensiune fixă a problemei
- Mărirea problemei **↑ eficiența** pentru număr fix de procesoare

### Legea lui Amdahl
> Limita superioară a accelerării când dimensiunea problemei este **fixă**

```
S(N) = 1 / (σ + (1 - σ) / N)
```
- **σ** = fracția din cod care TREBUIE executată secvențial (0 < σ ≤ 1)
- **N** = numărul de procesoare
- **S(∞) = 1/σ** — limita maximă absolută!

#### Exemple:
| σ (cod serial) | S(∞) | S(100 proc.) |
|---|---|---|
| 10% | 10 | ≈9.17 |
| 30% | 3.33 | ≈3.23 |
| 1% | 100 | ≈50.25 |

**Concluzie**: Chiar și 10% cod serial limitează accelerarea la 10x, indiferent de procesoare!

**Limitări Amdahl**: Nu ia în calcul overhead-ul de comunicare, sincronizare, și nici dimensiunea problemei.

### Legea lui Gustafson (Accelerarea Scalată)
> Relevantă când **dimensiunea problemei crește** odată cu numărul de procesoare

```
S ≤ p + (1 - p) * s
```
- **p** = numărul de procesoare
- **s** = procentul de execuție serială *din aplicația paralelă*

**Exemplu**: 32 procesoare, 1% serial:
- Gustafson: S ≤ 32 + (1 - 32) * 0.01 = 31.69
- Amdahl: S ≤ 24.43 (mai pesimist și nerealist pentru probleme mari)

### STL Parallel (C++17)
- 69 algoritmi paraleli în biblioteca standard
- Paralelizarea = adăugarea unui **singur parametru** (politica de execuție):

```cpp
#include <execution>

// Serial
std::sort(begin(v), end(v));

// Paralel
std::sort(std::execution::par, begin(v), end(v));
```

#### Politici de execuție:
| Politică | Semnificație |
|----------|-------------|
| `std::execution::seq` | Secvențial |
| `std::execution::par` | Paralel (fără vectorizare) |
| `std::execution::par_unseq` | Paralel + vectorizat |
| `std::execution::unseq` | Vectorizat (fără paralelism, C++20) |

> **Atenție**: Politica este un *hint* — biblioteca poate ignora și executa serial. NU rezolvă probleme de concurență globale!

---

## CURS 5 — Arhitecturi de Calcul Paralel/Distribuit + Java Paralel

### Arhitecturi cu memorie partajată

#### UMA (Uniform Memory Access) — SMP
- Toate procesoarele accesează memoria cu **același timp**
- **CC-UMA** = Cache Coherent UMA (coerența cache-ului asigurată HW)
- Limitat la câteva zeci de procesoare
- Exemple: Intel Core i7, mașini SMP clasice

#### NUMA (Non-Uniform Memory Access)
- Obținut prin conectarea mai multor SMP-uri
- Procesoarele accesează memoria altui SMP cu timp **mai mare**
- **CC-NUMA** = Cache Coherent NUMA
- Mai scalabil decât UMA

#### Avantaje memorie partajată: ușor de programat, acces rapid
#### Dezavantaje: scalabilitate limitată, programatorul gestionează sincronizarea

### Arhitecturi cu memorie distribuită
- Fiecare procesor are **memorie proprie**
- Comunicare prin **mesaje** (MPI, PVM)
- Nu există coerență cache globală
- Avantaj: scalabilitate excelentă
- Dezavantaj: programatorul gestionează explicit comunicarea

### Comparație arhitecturi

| | CC-UMA | CC-NUMA | Distribuită |
|--|--------|---------|------------|
| Comunicare | MPI, Threads, OpenMP | MPI, OpenMP | MPI |
| Scalabilitate | x10 proc. | x100 proc. | x1000 proc. |
| Exemple | SMP | SGI Origin | IBM SP2, BlueGene |

### Arhitecturi hibride (HPC modern)
- **Cluster de SMP-uri**: intern memorie partajată, între noduri memorie distribuită
- Combină avantajele ambelor
- Tendința actuală în HPC

### Arhitecturi sisteme distribuite

#### Client-Server
- Clienții cunosc serverele; serverele NU cunosc clienții
- Comunicare: TCP/IP
- **3 nivele**: View (client) → Controller (server aplicație) → Model (baza de date)
- Clase: Host-based, Server-based, Client-based, **Cooperative** (recomandat)

#### Cu obiecte distribuite (CORBA, RMI)
- Fără distincție client/server; orice obiect poate fi client sau server
- **Middleware** = software intermediar (CORBA, Java RMI, SOAP, EJB)

### Fiabilitatea sistemelor distribuite

| | Cu blocare (sincron) | Fără blocare (asincron) |
|--|---------------------|------------------------|
| Comportament | Procesul așteaptă confirmarea | Procesul continuă imediat |
| Avantaje | Consistență garantată | Eficient și flexibil |
| Dezavantaje | Poate bloca mult | Debugging dificil |

### Java Paralel — Fork/Join Framework

```java
// Clase principale:
ForkJoinTask<V>    // clasă abstractă de bază
ForkJoinPool       // administrează și monitorizează task-urile
RecursiveAction    // task fără rezultat (void)
RecursiveTask<V>   // task cu rezultat
```

**Strategie**: Divide and Conquer recursiv — împarte până când task-ul e suficient de mic → executare secvențială.

```java
class MyTask extends RecursiveAction {
    protected void compute() {
        if (dimensiuneMica) {
            // execută secvențial
        } else {
            MyTask left = new MyTask(...);
            MyTask right = new MyTask(...);
            left.fork();   // execuție asincronă
            right.fork();
            left.join();   // așteaptă terminarea
            right.join();
        }
    }
}
```

### Programare concurentă Java

```java
// synchronized asigură că un singur fir execută metoda la un moment dat
public synchronized void metoda() { ... }

// Thread clasic
Thread t = new Thread(() -> { /* cod */ });
t.start();
t.join();

// ExecutorService (nivel înalt)
ExecutorService executor = Executors.newFixedThreadPool(4);
executor.execute(new RunnableTask());
executor.shutdown();

// Fluxuri paralele
list.parallelStream()
    .filter(x -> x > 0)
    .collect(Collectors.toList());
```

---

## CURS 6 — Proiectarea Programelor Paralele + OpenMP

### Metodologia Foster (PCAM)
Cei 4 pași pentru proiectarea unui algoritm paralel:

```
1. Partiționare   → granularitate fină, maxim paralelism potențial
2. Comunicare     → identifică fluxurile de date între task-uri
3. Aglomerare     → grupează task-uri mici → task-uri mai mari
4. Alocare/Mapare → asignează task-uri pe procesoare fizice
```

### Pasul 1: Partiționarea (Descompunerea)
- Scop: identificarea celei mai fine granularități posibile
- **Descompunerea domeniului** (a datelor) — datele → task-uri
- **Descompunerea funcțională** — funcțiile → task-uri
- Sunt **complementare**; se pot aplica la aceeași problemă

**Verificare corectitudine**:
1. Numărul de task-uri >> numărul de procesoare? (cel puțin 10x)
2. Evită procesări/date redundante?
3. Task-urile au dimensiuni comparabile?
4. Numărul de task-uri scalează cu dimensiunea problemei?

### Pasul 2: Comunicarea

#### Tipuri de comunicare:
| Dimensiune | Tipuri |
|-----------|--------|
| Local vs. Global | Vecini imediați vs. toate task-urile |
| Structurată vs. Nestructurată | Grid/arbore vs. graf oarecare |
| Statică vs. Dinamică | Parteneri ficși vs. schimbătoare la runtime |
| Sincronă vs. Asincronă | Coordonat vs. independent |

#### Exemplu comunicare globală — Suma N numere (problemă serializată):
- Naive: O(N) — un singur task primește toate valorile → **RĂU**
- **Divide and Conquer**: O(log N) — fiecare nivel execută N/2 adunări **concurent** → **BUN**

```
Nivel 0: [4] [3] [5] [1] [8] [11] [2] [9]
Nivel 1: [7]     [6]     [19]     [11]
Nivel 2: [13]             [30]
Nivel 3:          [43]
```

**Verificare comunicare**: operațiile comunică în paralel? calculele se desfășoară concurent?

### Pasul 3: Aglomerarea
- Grupăm task-uri mici → task-uri mai mari (↓ comunicare, ↑ granularitate)
- Structura **fluture (butterfly)**: log N nivele, suma în log N pași, fiecare task ajunge la suma completă

### Pasul 4: Alocarea
- Specifică *unde* se execută fiecare task
- **Problemă NP-completă** în cazul general!
- Strategii conflictuale:
  - Task-uri independente → procesoare **diferite** (↑ concurență)
  - Task-uri care comunică frecvent → **același** procesor (↑ localizare)

#### Algoritmi de echilibrare a încărcării:
| Algoritm | Descriere |
|----------|-----------|
| **Bisecțiunea recursivă** | Divide domeniul în subdomenii de cost ≈ egal |
| **Local (Greedy)** | Compară încărcarea cu vecinii, transferă task-uri dacă diferența > prag |
| **Probabilistic** | Alocă task-urile aleator; bun când N_task >> N_proc |
| **Manager/Worker** | Manager distribuie task-uri; Worker-ii execută și cer mai mult |

#### Structura Manager/Worker:
- **Worker**: cere task-uri de la manager, le rezolvă, poate trimite task-uri noi
- **Manager**: gestionează pool-ul de task-uri
- **Ierarhic**: sub-manageri pentru grupuri de worker-i (↓ bottleneck manager)

### Concluzii metodologie:

| Pas | Depinde de arhitectură? | Scop |
|-----|------------------------|------|
| Descompunere | NU | Permite concurența |
| Aglomerare | NU | Echilibrează încărcarea, limitează comunicarea |
| Alocare | **DA** | Exploatează localizarea, reduce comunicarea |

---

## CURS 6 (cont.) — OpenMP

### Ce este OpenMP?
- Set de **directive compilator** + funcții de bibliotecă pentru C/C++/Fortran
- Model: **Fork-Join** cu memorie partajată
- Paralelism adăugat **incremental** la cod secvențial

### Sintaxa de bază

```cpp
#include <omp.h>

#pragma omp parallel num_threads(4)
{
    int id = omp_get_thread_num();    // ID-ul firului curent
    int n  = omp_get_num_threads();   // numărul total de fire
    printf("Thread %d din %d\n", id, n);
}
```

### Model Fork-Join

```
Master Thread
     |
     |---- [#pragma omp parallel] ----> fork: crează N fire
     |     Thread 0 | Thread 1 | ... | Thread N-1
     |          (execuție paralelă)
     |---- [end parallel] -----------> join: toate firele se termină
     |
  continuare serială
```

### Sincronizare în OpenMP

#### 1. Barrier — toate firele așteaptă
```cpp
#pragma omp barrier
```

#### 2. Critical — excludere mutuală (secțiune critică)
```cpp
#pragma omp critical
{
    // un singur fir la un moment dat
    result += local_value;
}
```

#### 3. Atomic — excludere mutuală pt. o singură variabilă (mai rapid decât critical)
```cpp
#pragma omp atomic
X += tmp;   // update atomic al lui X
```

### Paralelizarea buclelor

```cpp
#pragma omp parallel
{
    #pragma omp for
    for (int i = 0; i < N; i++) {
        A[i] = f(i);   // variabila i este implicit "privată"
    }
}
```

#### Opțiuni de planificare (schedule):
```cpp
schedule(static [,chunk])   // blcuri de dimensiune chunk distribuite round-robin
schedule(dynamic [,chunk])  // fiecare fir ia dinamic chunk iterații din coadă
schedule(guided [,chunk])   // blocuri descrescătoare dinamic
schedule(runtime)           // planificarea din variabila OMP_SCHEDULE
schedule(auto)              // la dispoziția compilatorului/runtime-ului
```

### Data race în OpenMP
- Apar când mai multe fire accesează aceeași variabilă și cel puțin unul scrie
- Soluții: `critical`, `atomic`, date private per fir
- **Sincronizarea este costisitoare** — minimizați-o!

### Task-uri în OpenMP
- Alcătuite din: cod + date + variabile de control intern (ICV)
- Runtime-ul decide când se execută
- Pot fi amânate sau executate imediat

---

## Rezumat Formule Esențiale

| Formulă | Semnificație |
|---------|-------------|
| `S(p) = T₁ / Tp` | Accelerarea cu p procesoare |
| `E(p) = S(p) / p` | Eficiența (0 < E ≤ 1) |
| `Tcom = Ts + Tw * m` | Costul comunicării unui mesaj de m cuvinte |
| `Tk = (K + N - 1) * T` | Timp total pipeline (K stadii, N elemente) |
| `S_Amdahl = 1 / (σ + (1-σ)/N)` | Amdahl — dimensiune fixă a problemei |
| `S_Gustafson ≤ p + (1-p)*s` | Gustafson — dimensiunea problemei crește |

---

## Tips pentru examen

1. **Taxonomia Flynn**: știți toate 4 tipuri cu exemple clare (SIMD = GPU/vectorial, MIMD = multiprocesor).
2. **Legea Amdahl**: calculați S(∞) = 1/σ și pentru valori concrete de N.
3. **Metodologia Foster**: cei 4 pași în ordine și ce face fiecare.
4. **UMA vs NUMA vs Distribuită**: știți diferențele de scalabilitate (x10, x100, x1000).
5. **Concurență ≠ Paralelism** — definiție exactă pentru ambele.
6. **Data race**: ce este, cum apare, cum se previne (critical/atomic/barrier).
7. **OpenMP**: știți directivele principale și când se folosesc.
8. **Problema celor 2 generali** — nu are soluție în sisteme cu eșecuri arbitrare.
9. **Calea critică** — limitează accelerarea maximă obtenabilă.
10. **Amdahl vs Gustafson**: Amdahl = pesimist pentru dimensiune fixă; Gustafson = realist când problema crește.
