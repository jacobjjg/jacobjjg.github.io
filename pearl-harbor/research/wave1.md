# Pearl Harbor, 7 December 1941: the first attack wave

Research dossier for the three.js reconstruction. Machine-readable companion: `wave1.json` (same directory).

All times are Hawaii local time on 7 December 1941 (UTC-10:30; Tokyo time minus 19h30m). Positions are decimal degrees WGS84, west longitudes negative. Bearings are degrees true. Names are given name first.

## 1. How far to trust this file

Direct page fetching was blocked on this machine, and the shared web-search quota ran out after about 45 queries. Every fact below was checked against search-result summaries of the sources in section 15, combined with what I already knew of the literature. I did not read any source page in full.

Three kinds of statement appear, and the JSON marks them in each record's `confidence` and `basis`:

- **Documented**: a time, count or name that a cited source states (for example "Tora Tora Tora" at 07:53, 183 aircraft, the 20 nm / 340 degree rendezvous).
- **Reconstructed**: a figure I chose between conflicting sources. The conflict is recorded in section 14.
- **Modelled**: every waypoint between documented anchors. I fitted routes by geometry so that each group reaches its target at the documented minute at a plausible ground speed. These are for animation; they are not historical tracks.

Target coordinates for ships and airfields are approximations built from the Arizona, Missouri and Utah memorial anchors and a 045/225 axis for Battleship Row. Use the project's ship-position dataset where it differs.

## 2. Order of battle

183 aircraft reached Oahu out of 189 planned. Six failed to launch: one Kaga level bomber, one Shokaku and two Zuikaku dive bombers, and two fighters (Soryu and Shokaku per NavWeaps).

| JSON id | Role | Carrier | Unit | Count (planned) | Leader | Weapon | Targets |
|---|---|---|---|---|---|---|---|
| level_akagi | Level bomber, B5N2 | Akagi | 1st Attack Unit | 15 (15) | Cdr Mitsuo Fuchida | 800 kg AP bomb | Battleship Row; Fuchida's chutai dropped on Maryland |
| level_kaga | Level bomber, B5N2 | Kaga | 2nd Attack Unit | 14 (15) | Lt Cdr Takashi Hashiguchi | 800 kg AP bomb | Arizona/Vestal (aft), Tennessee/West Virginia |
| level_soryu | Level bomber, B5N2 | Soryu | 3rd Attack Unit | 10 (10) | Lt Heijiro Abe | 800 kg AP bomb | West Virginia/Tennessee (Kanai diary) |
| level_hiryu | Level bomber, B5N2 | Hiryu | 4th Attack Unit | 10 (10) | Lt Cdr Tadashi Kusumi | 800 kg AP bomb | Arizona (bow): the magazine hit |
| torpedo_akagi | Torpedo, B5N2 | Akagi | 1st Torpedo Attack Unit | 12 (12) | Lt Cdr Shigeharu Murata | Type 91 Mod 2 torpedo | West Virginia, Oklahoma |
| torpedo_kaga | Torpedo, B5N2 | Kaga | 2nd Torpedo Attack Unit | 12 (12) | Lt Kazuyoshi Kitajima | Type 91 Mod 2 torpedo | Oklahoma, West Virginia, Nevada, California; Arizona claimed |
| torpedo_soryu | Torpedo, B5N2 | Soryu | 3rd Torpedo Attack Unit | 8 (8) | Lt Tsuyoshi Nagai | Type 91 Mod 2 torpedo | Utah, Raleigh, Helena, California |
| torpedo_hiryu | Torpedo, B5N2 | Hiryu | 4th Torpedo Attack Unit | 8 (8) | Lt Heita Matsumura | Type 91 Mod 2 torpedo | West Virginia, Oklahoma, Helena/Oglala |
| dive_shokaku | Dive bomber, D3A1 | Shokaku | 15th Attack Unit | 26 (27) | Lt Cdr Kakuichi Takahashi | 250 kg land bomb | Ford Island NAS (9), Hickam Field (17) |
| dive_zuikaku | Dive bomber, D3A1 | Zuikaku | 16th Attack Unit | 25 (27) | Lt Akira Sakamoto | 250 kg land bomb | Wheeler Field |
| fighter_akagi | Fighter, A6M2 | Akagi | 1st Fighter Combat Unit | 9 (9) | Lt Cdr Shigeru Itaya | 2 x 20 mm, 2 x 7.7 mm | Ewa, then Hickam |
| fighter_kaga | Fighter, A6M2 | Kaga | 2nd Fighter Combat Unit | 9 (9) | Lt Yoshio Shiga | same | Ewa, then Hickam and Ford Island |
| fighter_soryu | Fighter, A6M2 | Soryu | 3rd Fighter Combat Unit | 8 (9) | Lt Masaji Suganami | same | Wheeler, then Ewa |
| fighter_hiryu | Fighter, A6M2 | Hiryu | 4th Fighter Combat Unit | 6 (6) | Lt Kiyokuma Okajima | same | Wheeler sweep (unconfirmed), Ewa |
| fighter_shokaku | Fighter, A6M2 | Shokaku | 5th Fighter Combat Unit | 5 (6) | Lt Tadashi Kaneko | same | Kaneohe; possibly Bellows |
| fighter_zuikaku | Fighter, A6M2 | Zuikaku | 6th Fighter Combat Unit | 6 (6) | Lt Masao Sato | same | Kaneohe |

Totals: 49 level bombers, 40 torpedo bombers, 51 dive bombers, 43 fighters.

Fuchida flew as observer and commander in B5N2 AI-301, with Lt Mitsuo Matsuzaki as pilot and PO1c Tokunobu Mizuki as radioman.

## 3. Launch and flight to Oahu

- **Launch.** The six carriers were about 230 nm due north of Oahu. Launch began at about 06:00 (sources give 06:00 to 06:18) and took about 15 minutes. The formation set course south at about 06:20.
- **Launch position.** About 25.45 N, 157.86 W at the 06:20 departure. This is an estimate, obtained by running the Opana radar track backwards; the sibling file `kido_butai.json` reaches the same point independently. Confidence low.
- **Formation.** Fuchida's 49 level bombers led at 3,000 m (9,800 ft). Murata's 40 torpedo planes flew to the right at 2,800 m (9,200 ft). Takahashi's 51 dive bombers flew to the left at 3,500 m (11,000 ft). Itaya's 43 fighters covered from about 4,300 m. The Army Staff Ride Handbook gives the first three altitudes; the fighter altitude is from Fuchida's account as I recall it.
- **Speed.** Fuchida gives 125 kt indicated. The Opana plots (132-136 statute miles at 07:02, about 20 at 07:39) imply a ground speed near 160 kt, which fits 125 kt indicated at 3,000 m plus a tail wind.
- **Weather.** Sunrise was at 06:26. A solid cloud layer lay beneath the formation, base about 1,500 m and tops about 2,000 m, breaking up near Oahu.
- **Radio homing.** Fuchida tuned his direction finder to station KGMB in Honolulu, corrected course by about 5 degrees, and heard the local weather: partly cloudy, mostly over the mountains, base 3,500 ft, visibility good, wind north at 10 kt.
- **Radar.** The Opana station first plotted the wave at 07:02, 132-136 statute miles out, 3 degrees east of north. That places it at about 23.59 N, 157.90 W.

## 4. Deployment at 07:40 and the routes round the island

### The flares

At 07:40, off Kahuku Point, Fuchida fired one "black dragon" smoke flare. One flare meant surprise achieved: torpedo planes first, then level bombers, then dive bombers. Two flares meant surprise lost: dive bombers and fighters first.

The fighters did not react, so Fuchida fired a second. Takahashi read the two together as "surprise lost" and took the dive bombers in at once. Murata saw this and hurried the torpedo planes. The practical result was that bombs fell on Ford Island and Hickam at 07:55, about the same moment as the first torpedoes, instead of after them.

Alan Zimm argues that the interval between the flares was too short for Fuchida's version and that he meant to fire two from the start.

### Where the 07:40 point was

Fuchida says he was "over Kahuku Point". The Opana track lost the echo about 20 statute miles out at 07:39. I put the deployment point at 21.90 N, 157.99 W, about 11 nm north of Kahuku Point, as a compromise. From there every group can reach its target at the documented minute.

### Who went which way

| Group | Route after 07:40 | Evidence |
|---|---|---|
| Kaneohe fighters (Shokaku, Zuikaku; 11) | East, then down the windward coast | Marine Corps history: eleven Zeros left the formation and flew east |
| Dive bombers (51) with Soryu and Hiryu fighters (14) | Across the north shore near Haleiwa and down the central plain. North of Wheeler, Zuikaku's 25 peeled off; Shokaku's 26 went on to Pearl Harbor | Arakaki and Kuborn |
| Level bombers (49) | West along the north shore, south just short of Kaena Point, down the Waianae coast, round Barbers Point, then north-east up Battleship Row | Arakaki and Kuborn; Fuchida ("a circuit toward Barbers Point") |
| Torpedo planes (40) with Akagi and Kaga fighters (18) | West and south with the level bombers but lower and faster, crossing the southern Waianae hills near Nanakuli. At about 07:51 the torpedo force split | Marines at Ewa at 07:53 saw about 18 "torpedo planes" at 1,000 ft heading for Pearl Harbor from the Barbers Point side and about 21 fighters coming over the hills from Nanakuli |

### Level-bomber track (modelled, Akagi times)

| Time | Lat | Lon | Alt m | Note |
|---|---|---|---|---|
| 06:20 | 25.4500 | -157.8500 | climbing | Departure (estimated) |
| 07:02 | 23.5940 | -157.9000 | 3000 | First Opana plot (computed) |
| 07:30 | 22.3600 | -157.9600 | 3000 | Coast sighted through cloud |
| 07:40 | 21.9000 | -157.9900 | 3000 | Flares |
| 07:47 | 21.6600 | -158.1200 | 3000 | Off Waialua Bay |
| 07:49 | 21.6350 | -158.1900 | 3000 | "To-To-To" |
| 07:50:30 | 21.6100 | -158.2500 | 3000 | Short of Kaena Point, turn south |
| 07:53 | 21.4800 | -158.2450 | 3000 | "Tora Tora Tora" |
| 07:57 | 21.3300 | -158.1600 | 3000 | Off Nanakuli |
| 07:59 | 21.2750 | -158.0800 | 3000 | Barbers Point |
| 08:00 | 21.2830 | -158.0380 | 3000 | Initial point off Ewa Beach, turn to 045 |
| 08:02:35 | 21.3580 | -157.9575 | 3000 | South-west end of Battleship Row |
| 08:02:50 | 21.3649 | -157.9500 | 3000 | Over Arizona |

Kaga, Soryu and Hiryu follow the same track about 1.5, 2.5 and 3.5 minutes later.

## 5. The torpedo attack

Forty B5N2s attacked between 07:55 and about 08:06. About 36 torpedoes were released. Nineteen are counted as hits in the reconstruction used here.

### Release

- Level flight at about 160 kt, 10-20 m above the water. The NPS timeline says "just 20 feet"; Wikipedia's Type 91 article quotes 180 kt at 20 m.
- Release range: I use 600 m as nominal within a 400-1,000 m band. Southeast Loch gives roughly 900-1,200 m of water in front of Battleship Row.
- Torpedo: Type 91 Mod 2, about 42 kt, 204 kg warhead, wooden breakaway fins and anti-roll gear for the 12-14 m harbour.
- Depth setting: given as 4 m or 6 m. Not verified. The JSON carries 6 m with a note.

### Two streams

**Western stream: Soryu and Hiryu, 16 aircraft.** They came from the west toward the carrier moorings on the north-west side of Ford Island. No carriers were there. Detroit, Raleigh, Utah and Tangier were.

**Southern stream: Akagi and Kaga, 24 aircraft.** They flew south past Ewa, crossed the harbour entrance, passed over Hickam, turned left at the head of Southeast Loch and ran down the loch at Battleship Row on a heading of about 310 degrees. The row's axis is 045/225, so this is close to a beam attack.

### Order of attack

| # | Time | Carrier | Planes | Target | Hits | Note |
|---|---|---|---|---|---|---|
| 1 | 07:55 | Soryu | 6 | Utah, Raleigh | 3 | First torpedoes of the raid. Utah 2, Raleigh 1. Heading about 125 from over Pearl City |
| 2 | 07:57 | Soryu | 1 | Helena/Oglala at 1010 Dock | 1 | Nagai. Torpedo ran under Oglala and hit Helena |
| 3 | 07:57 | Akagi | 6 | West Virginia, Oklahoma | not established | Murata's first chutai. First hits on both ships |
| 4 | 07:58 | Hiryu | 2 | West Virginia | 2 claimed | Matsumura and Oku, who had swung round over Hickam and cut into Akagi's stream. Oku's hit was photographed |
| 5 | 07:58 | Hiryu | 4 | Helena/Oglala | 0 | Kadono's element. All missed |
| 6 | 07:59 | Hiryu | 2 | Oklahoma | not established | Mixed in with Akagi aircraft |
| 7 | 07:59 | Akagi | 6 | Oklahoma, West Virginia | not established | Second chutai, Lt Jinichi Goto |
| 8 | 08:00 | Kaga | 12 | Oklahoma, West Virginia, Nevada, California | not established | Last in, into alert defences. Five shot down. One hit Nevada at about 08:03 |
| 9 | 08:05 | Soryu | 1 | California | 1 claimed | Juzo Mori, on a second run after breaking off from 1010 Dock |

### Hits per ship

| Ship | Launched at her | Hits used | Range in sources | First hit | Note |
|---|---|---|---|---|---|
| West Virginia | 9 | 7 | 6-9 | 07:57 | Seven confirmed (Zimm). 1942 report: four or five. NHHC: up to nine |
| Oklahoma | 12 | 5 | 3-9 | 07:57 | Capsized about 08:08 |
| California | 3 | 2 | 2 | 08:05 | Port side, about frames 52 and 101 |
| Nevada | 1 | 1 | 1 | 08:03 | Port bow, about frame 41 |
| Arizona | 0 | 0 | 0-1 | none | Claimed by a Kaga crew and by witnesses on Vestal; the wreck shows no torpedo damage |
| Utah | 6 (with Raleigh) | 2 | 2 | 07:56 | Capsized about 08:12 |
| Raleigh | in Utah's 6 | 1 | 1 | 07:56 | Port side, about frame 58 |
| Helena | 5 | 1 | 1 | 07:57 | Oglala capsized from the blast about 10:00 |
| **Total** | **36** | **19** | | | |

The Battleship Row launch counts (12, 9, 3, 1) are Zimm's. The 6 and 5 for the Utah group and 1010 Dock, and so the total of 36, are my reconstruction.

### Kaga's five lost torpedo bombers

All five torpedo bombers lost in the raid were Kaga's.

| # | Where it fell | Lat | Lon | Note |
|---|---|---|---|---|
| 1 | Southeast Loch | 21.3562 | -157.9432 | Reported tail code AII-356; salvaged by crane. A ww2db caption identifies it as Lt Mimori Suzuki's |
| 2 | Naval Hospital grounds, Hospital Point | 21.3465 | -157.9650 | Alleged AII-353 |
| 3 | About 100 yards off Nevada's port quarter | 21.3668 | -157.9472 | Shot down just after torpedoing Nevada. Not recovered |
| 4 | On land north of Fort Weaver, west of the harbour | 21.3330 | -157.9870 | |
| 5 | Not located | | | |

All five coordinates are my estimates from the place descriptions; confidence low. Names on the NavWeaps Kaga casualty list include Mimori Suzuki, Syuzo Kitahara, Kenichi Kumamoto, Izumi Nagai and Narikatsu Ohashi. I could not pair names with aircraft.

In the model, four of the five were hit before release and one after. That reconciles 40 aircraft with about 36 torpedoes.

## 6. Level bombing

Ten chutai of five aircraft (one of four) ran up Battleship Row from the south-west on about 045 degrees at 3,000 m. Each chutai flew a tight V and released together on its lead bombardier.

**Result: 49 bombs, 10 confirmed hits** (Zimm): two each on Arizona, Tennessee, Maryland, West Virginia and Vestal. Six of the ten were duds, broke up, or detonated low-order.

| Time | Ship | Effect | Credited to | Confidence |
|---|---|---|---|---|
| 08:05 | Arizona | Glanced off Turret IV, exploded in the captain's pantry | Kaga | medium |
| 08:05 | Vestal | Two hits: forward starboard (exploded in a storeroom) and aft port (passed out through the bottom) | Kaga and/or Hiryu, collateral | medium |
| 08:06 | Arizona | Struck beside Turret II, reached the forward magazines, which detonated about seven seconds later. 1,177 dead | Hiryu, Kusumi's chutai | medium |
| about 08:08 | Tennessee | Turret II centre gun; fragments mortally wounded West Virginia's Capt Bennion | Kaga or Soryu | low |
| about 08:08 | Tennessee | Turret III roof, low-order | Kaga or Soryu | low |
| about 08:08 | West Virginia | Through the foretop to the second deck, dud | Soryu or Kaga | low |
| about 08:08 | West Virginia | Turret III roof, wrecked the floatplane, dud | Soryu or Kaga | low |
| about 08:14 | Maryland | Forecastle, and port bow below the waterline | Claimed by Fuchida; disputed | low |

**Arizona.** Wikipedia's account has five Kaga aircraft bombing from amidships to the stern, then five Hiryu aircraft hitting the bow. The NHHC credits a Hiryu B5N2. Prange and older accounts credit PO Noboru Kanai of Soryu; Kanai's diary, as reported by the World War II Database, says he attacked West Virginia and Tennessee. I follow the Hiryu attribution. Kusumi was a pilot, so the man who released the bomb is not reliably named.

**Fuchida's own chutai.** It aborted its first run when cloud covered the aim point. It circled right over Honolulu and was starting its second run when Arizona blew up. Smoke hid the northern ships, so Fuchida shifted to Maryland and called two hits. Zimm says those bombs missed: two went into Ford Island and the rest into the water. Maryland did take two AP bomb hits from somebody.

**Repeat runs.** Fuchida says some chutai made three runs. I could not establish which.

## 7. Dive bombers

### Wheeler Field: Zuikaku, 25 D3A1, Lt Sakamoto

- **Time:** first bombs 07:51. Other sources give 07:50, 07:53 and 08:02.
- **Approach:** from the north, splitting into two groups that attacked the hangar line from the east and the west.
- **Result:** direct hits on Hangars 1 and 3 and on barracks; stored ammunition exploded; the fighters parked wingtip to wingtip burned.
- **Passes:** one bombing dive, then repeated strafing with Soryu's Zeros. Some aircraft went on to strafe Ewa.
- **Losses:** none.

### Ford Island NAS: Shokaku, about 9 D3A1, Lt Cdr Takahashi

- **Time:** 07:55, as the "prep" signal for morning colours went up. This was the first bomb on Pearl Harbor.
- **Approach:** from the north-east (CINCPAC report).
- **Result:** seaplane ramp and Hangar 6 at the south end hit; 33 aircraft destroyed or damaged, 19 of them PBYs.
- At 07:58 Lt Cdr Logan Ramsey sent "AIR RAID PEARL HARBOR X THIS IS NOT DRILL".

### Hickam Field: Shokaku, about 17 D3A1

- **Time:** 07:55 documented. My geometry puts the first bombs a minute or so after Ford Island's.
- **Approach:** over Fort Kamehameha, from the south-east.
- **Result:** Hawaiian Air Depot and the hangar line hit; parked bombers burned.
- **Losses:** one Shokaku D3A1 failed to return. Lansdale says it was lost at sea on the way back.

Dive profile used in the JSON: push-over from 3,000-4,000 m, 55 degree dive, release at about 450 m. This is doctrine, not a measurement from the day.

## 8. Fighters

| Field | Unit | Time | Direction | Passes | Note |
|---|---|---|---|---|---|
| Kaneohe NAS | Shokaku and Zuikaku, 11 | 07:48 to about 08:05 | Down the windward coast | about 4 | First shots of the air attack. PBYs at moorings and on the ramp burned. No bombers in this wave |
| Wheeler | Soryu, 8 | 07:53 to about 08:05 | Along the flight line | 3 | After the dive bombers' first bombs |
| Wheeler | Hiryu, 6 | about 07:53 | | | Assigned by the plan; presence not confirmed |
| Ewa | Akagi, 9 | 07:55 to about 08:05 | From the north-west at 1,000 ft, down to 20-25 ft | about 4 | First to strafe Ewa (Marine Corps history) |
| Ewa | Kaga, 9 | 07:56 to about 08:06 | Same | about 3 | "Soon after Itaya" |
| Ewa | Hiryu, 6 | about 08:02 to 08:20 | | about 4 | |
| Ewa | Soryu, 8 | about 08:09 to 08:25 | From Wheeler | about 3 | |
| Hickam | Akagi, 9 | about 08:07 to 08:20 | Across Fort Kamehameha | about 3 | Hirano shot down at 08:10 |
| Hickam, Ford Island | Kaga, 9 | about 08:08 to 08:25 | | about 3 | Two Kaga fighters lost |
| Bellows | one Zero | about 08:30 | | 1 | Tent area strafed. Unit not established |

Zeros near Ewa and Barbers Point also set on Enterprise's incoming SBDs at about 08:20-08:30, and Akagi fighters attacked B-17s arriving from California.

## 9. First-wave losses

Nine aircraft and, by arithmetic, 20 aircrew.

| Aircraft | Carrier | Crew | Time | Where | Cause |
|---|---|---|---|---|---|
| A6M2 AI-154 | Akagi | PO1c Takeshi Hirano | 08:10 | Fort Kamehameha, Building 52 (est. 21.3215, -157.9590) | Ground fire and USS Helm |
| A6M2 | Kaga | PO2c Seinoshin Sano | unknown | unknown | Believed anti-aircraft fire |
| A6M2 | Kaga | PO2c Toru Haneda | unknown | unknown | Believed anti-aircraft fire |
| D3A1 | Shokaku | 2 men (possibly Kunio Iwatsuki and Tetsusaburo Kumazo) | unknown | Possibly at sea on return | Failed to return |
| 5 x B5N2 | Kaga | 15 men | 08:00-08:06 | See section 5 | Anti-aircraft fire |

## 10. Withdrawal and return

- **Rendezvous:** the plan set it 20 nm bearing 340 degrees from Kaena Point at 1,000 m. That computes to 21.8880 N, 158.4038 W. Bombers were to collect the fighters there and lead them home.
- **Timing:** first-wave units began leaving at about 08:25. Rendezvous times in the JSON (08:20 to 08:50) are modelled.
- **Recovery:** the carriers had closed to roughly 190 nm north of Oahu. First landings at about 10:10. I took the position (24.70 N, 157.69 W) and time from the sibling file `kido_butai.json`; both are low-confidence estimates.
- **Fuchida** stayed over Oahu through the second wave, left at about 10:00 and landed on Akagi at about 13:00.

## 11. Signals

| Time | Signal | Meaning |
|---|---|---|
| about 07:00 | Direction finder on KGMB | Course check and Honolulu weather |
| about 07:35 | Chikuma floatplane report | Fleet is in Pearl Harbor; Tone's plane reports Lahaina empty (time unverified) |
| 07:40 | One black dragon flare | Surprise achieved |
| 07:40, seconds later | Second flare | Meant as a repeat; read as "surprise lost" |
| 07:49 | "To-To-To" | Totsugeki seyo: all units attack |
| 07:53 | "Tora Tora Tora" | Surprise attack achieved. Heard on Akagi and on Nagato in Japan |
| 07:58 | "AIR RAID PEARL HARBOR X THIS IS NOT DRILL" | US Navy alarm |

## 12. Master timeline

| Time | Event |
|---|---|
| 06:00 | Launch begins about 230 nm north of Oahu |
| 06:15 | 183 aircraft airborne |
| 06:20 | Formation heads south |
| 06:26 | Sunrise |
| 07:02 | Opana radar picks up the wave |
| 07:30 | Fuchida sights the north shore |
| 07:39 | Opana loses the echo about 20 statute miles out |
| 07:40 | Flares off Kahuku Point; deployment |
| 07:48 | Zeros strafe Kaneohe |
| 07:49 | "To-To-To" |
| 07:51 | Wheeler bombed; torpedo force splits |
| 07:53 | "Tora Tora Tora"; Ewa sights torpedo planes and fighters |
| 07:55 | Ford Island and Hickam bombed; first torpedoes at Utah and Raleigh; Ewa strafed |
| 07:56 | Utah and Raleigh hit |
| 07:57 | Akagi torpedoes hit West Virginia and Oklahoma; Helena hit |
| 07:58 | US air raid broadcast; Hiryu pair hit West Virginia |
| 08:00 | Kaga torpedo planes begin their runs |
| 08:02 | Level bombers begin runs; Fuchida's chutai aborts |
| 08:03 | Nevada torpedoed |
| 08:05 | California torpedoed twice; Arizona hit aft; Vestal hit |
| 08:06 | Arizona's forward magazines explode (traditional time 08:10) |
| 08:08 | Oklahoma capsizes; Tennessee and West Virginia bombed |
| 08:10 | Hirano's Zero crashes at Fort Kamehameha |
| 08:12 | Utah capsizes |
| 08:14 | Fuchida's chutai bombs Maryland |
| 08:25 | First wave begins to withdraw |
| 08:30 | Lone Zero strafes Bellows |
| 08:45 | Units at the rendezvous, heading north |
| 10:10 | First landings on the carriers |
| 13:00 | Fuchida lands |

## 13. Markings

| Carrier | Tail code | Fuselage bands |
|---|---|---|
| Akagi | AI- | one red |
| Kaga | AII- | two red |
| Soryu | BI- | one blue |
| Hiryu | BII- | two blue |
| Shokaku | EI- | one white |
| Zuikaku | EII- | two white |

- **Numbers:** 1xx fighters, 2xx dive bombers, 3xx attack bombers.
- **Tail codes** were red. Fuchida's aircraft was the exception.
- **Command stripes** ran horizontally across the fin: three for an air group leader, two for a division leader, one for a section leader. Colours were not verified. They are usually shown in the division's colour, with Akagi's shown red by some and yellow by others.
- **Known aircraft:** AI-301 Fuchida (usually shown with a red tail and three yellow stripes); AI-311 Murata; AI-155 Itaya; AI-154 Hirano; AII-356, the Kaga torpedo plane salvaged from Southeast Loch. EI-238 (Takahashi), BII-320 (Matsumura) and AII-105 (Shiga) are from memory of standard references and unverified.
- **Paint:** A6M2 and D3A1 overall pale grey-green with black cowlings. B5N2 dark green upper surfaces, field-applied and uneven, over natural metal or light grey.

## 14. Uncertainties and conflicts

1. **Fighter counts for Shokaku and Zuikaku.** NavWeaps puts the two fighter aborts on Soryu and Shokaku, giving Shokaku 5 and Zuikaku 6. Wikipedia's Zuikaku article says five Zuikaku Zeros attacked Kaneohe, which implies Shokaku 6 and Zuikaku 5. I use 5 and 6. Either way the Kaneohe force was 11 and the wave total 43.
2. **Arizona explosion time.** 08:06 in the modern reconstruction; "about 08:10" in ship reports, the NPS lesson plan and older histories. I use 08:06.
3. **Who dropped the Arizona bomb.** Hiryu (NHHC, De Virgilio) against Kanai of Soryu (Prange). I use Hiryu.
4. **Arizona bomb hits.** Four hits and three near misses (Japanese and Bureau of Ships) against two hits and two near misses (De Virgilio). The ten-hit total uses two.
5. **Level-bomber hits by carrier.** Only the Arizona hits have an attribution I could support. The Tennessee, West Virginia and Maryland hits are split between Kaga, Soryu and Akagi by inference. The targets of Akagi's 2nd and 3rd chutai, Soryu's 2nd and Hiryu's 2nd are unknown to me.
6. **Fuchida's Maryland hits.** Claimed by Fuchida, rejected by Zimm.
7. **Torpedo hits.** Oklahoma 3 to 9, West Virginia 4 to 9 depending on the source. One secondary source gives 13 hits from 40; the NHHC gives "up to 21 of 29" on Battleship Row. I use 19 of 36.
8. **Hiryu's split.** Stille: four at 1010 Dock, four on Battleship Row. Zimm, as excerpted: six at 1010 Dock, two on Battleship Row. I use 4 and 4 because it fits Zimm's own per-ship launch totals.
9. **Akagi and Kaga plane-by-plane targets.** Not established. The per-carrier allocation in the JSON is labelled illustrative.
10. **Who torpedoed California.** Mori of Soryu claims one. The other two attackers are assigned to Kaga as a model choice; they may have been Akagi's.
11. **Utah hit time.** Utah's report says 08:01; reconstructions say 07:55-07:56. I use 07:56.
12. **Nevada torpedo time.** 08:02-08:03 or about 08:10. I use 08:03.
13. **Wheeler attack time.** 07:50, 07:51, 07:53 or 08:02. I use 07:51.
14. **Wheeler approach.** "From the north, split east and west", "from the east", and "from two directions" all appear. The JSON carries 270 with 090 as the alternative.
15. **Hickam.** Hangar numbers conflict between sources. The 9 / 17 Shokaku split rests on a secondary timeline plus two US observations.
16. **Akagi fighters' route.** The Marine history has them arriving at Ewa over the Waianae hills. One article has them above Shokaku's dive bombers on the way in. I use the western route.
17. **Hiryu fighters at Wheeler.** Assigned by the plan; I found no confirmation that they strafed it.
18. **Kaga torpedo-plane crash sites and crews.** Four sites come from one researcher's work quoted second-hand; the fifth is unlocated; crew pairings are unverified.
19. **Kaga fighter and Shokaku dive-bomber losses.** No time or place found. The JSON carries null positions.
20. **Deployment point.** Fuchida's "over Kahuku Point" against the radar's 20 miles out. My point is a compromise.
21. **Launch time and position, recovery time and position.** Estimates.
22. **Torpedo depth setting and release range.** Not verified.
23. **Command-stripe colours and several tail codes.** Not verified.
24. **Kitajima's given name** appears as Kazuyoshi and as Ichiryo; **Matsumura's** as Heita and, wrongly, Hirata.
25. **A sixth Kaga torpedo bomber** is said by one summary to have ditched later. Not confirmed and not counted.
26. **Mismatch with the radar file.** `warnings.json` puts the last Opana plot (07:39) at 22.00 N, about 3 nm north of where my track is at that minute. I set the 07:40 point further south so the documented attack times can be met. Moving it north to match the radar delays every arrival by about one minute.
27. **Suganami's given name** is Masaji here and Masaharu in `kido_butai.json`. Both readings are in print.

## 15. Sources

Reached only through search-result summaries unless marked otherwise. Books without a URL are cited from memory.

Official and primary

- CINCPAC report of the Pearl Harbor attack (NHHC): https://www.history.navy.mil/research/library/online-reading-room/title-list-alphabetically/c/cincpac-report.html
- Japanese attack plan, Pearl Harbor Attack hearings part 12: https://www.ibiblio.org/pha/pha/pt_12/x12-008.html
- NHHC, USS Arizona (BB-39): https://www.history.navy.mil/browse-by-topic/ships/modern-ships/uss-arizona.html
- NHHC, Battleship Row during the attack: https://www.history.navy.mil/our-collections/photography/wars-and-events/world-war-ii/pearl-harbor-raid/battleship-row-during-the-pearl-harbor-attack.html
- NHHC, Japanese aircraft during and after the raid: https://history.navy.mil/our-collections/photography/wars-and-events/world-war-ii/pearl-harbor-raid/japanese-forces-in-the-pearl-harbor-attack/japanese-aircraft-during-and-after-the-raid.html
- NHHC, H-Gram 001-2: https://www.history.navy.mil/about-us/leadership/director/directors-corner/h-grams/h-gram-001/h-001-2.html
- NHHC, US Marines at Pearl Harbor: https://www.history.navy.mil/research/library/online-reading-room/title-list-alphabetically/u/us-marines-at-pearl-harbor.html
- NPS, Pearl Harbor timeline: https://www.nps.gov/perl/learn/historyculture/timeline.htm
- NPS, The Pearl Harbor Attack: https://www.nps.gov/articles/pearlattackww2.htm
- NPS, Battlefield O'ahu: https://www.nps.gov/valr/learn/historyculture/oahu.htm
- NPS, USS Arizona submerged cultural resources study: https://www.nps.gov/parkhistory/online_books/usar/scrs/scrs2h.htm
- Arakaki and Kuborn, 7 December 1941: The Air Force Story, chapters 4 and 5: https://www.ibiblio.org/hyperwar/AAF/7Dec41/7Dec41-4.html and https://www.ibiblio.org/hyperwar/AAF/7Dec41/7Dec41-5.html
- Cressman and Wenger, Infamous Day: Marines at Pearl Harbor: https://www.ibiblio.org/hyperwar/USMC/USMC-C-Pearl/
- US Army, Staff Ride Handbook for the Attack on Pearl Harbor: https://www.armyupress.army.mil/Portals/7/educational-services/staff-rides/StaffRideHB_PearlHarbor.pdf
- NavSource, deck-log extracts: https://www.navsource.org/Naval/logs.htm

Participants and scholarship

- Fuchida, "I Led the Air Attack on Pearl Harbor", Proceedings, Sept 1952: https://www.usni.org/magazines/proceedings/1952/september/i-led-air-attack-pearl-harbor
- Zimm, "Commander Fuchida's Decision", Naval History, Dec 2016: https://www.usni.org/magazines/navalhistory/2016-12/commander-fuchidas-decision
- Zimm, "Victory Undermined", Naval History: https://www.usni.org/magazines/naval-history/2026/december/victory-undermined
- De Virgilio, "Japanese Thunderfish", Naval History, Dec 1991: https://www.usni.org/magazines/naval-history-magazine/1991/december/technical-report-japanese-thunderfish
- De Virgilio, "Seven Seconds to Infamy", Proceedings, Dec 1997: https://www.usni.org/magazines/proceedings/1997/december/seven-seconds-infamy
- "The Japanese Perspective", Naval History, Dec 1991: https://www.usni.org/magazines/naval-history-magazine/1991/december/japanese-perspective
- Zimm excerpts, "Execution of the Attack" I and II: https://warhistory.org/article/pearl-harbor-execution-of-the-attack-i and https://warhistory.org/article/pearl-harbor-execution-of-the-attack-ii
- Stille (Osprey) excerpt, "Climb Mount Niitaka": https://theaviationgeekclub.com/climb-mount-niitaka-a-detailed-description-of-the-first-wave-attack-on-pearl-harbor/
- Osprey blog, The Pearl Harbor Attack: https://www.ospreypublishing.com/us/osprey-blog/2021/the-pearl-harbor-attack/
- Juzo Mori memoir excerpt, "The Miraculous Torpedo Squadron": https://www.vintagewings.ca/stories/the-miraculous-torpedo-squadron
- Flight Journal attack timeline, Dec 2021: https://www.pressreader.com/usa/flight-journal/20211201/281625308546646
- Review of Wenger, Cressman and Di Virgilio, A Pitiful, Unholy Mess: https://navyhistory.org/2022/11/a-pitiful-unholy-mess-the-history-of-wheeler-bellows-and-haleiwa-fields-and-the-attacks-of-7-december-1941/
- Books, no URL: Prange, At Dawn We Slept; Lord, Day of Infamy; Zimm, Attack on Pearl Harbor: Strategy, Combat, Myths, Deceptions; Wenger, Cressman and Di Virgilio, Pearl Harbor Tactical Studies series.

Losses and markings

- Lansdale, Japanese Losses at Pearl Harbor: https://j-aircraft.com/research/jimlansdale/japanese_losses_ph/Japanese_losses_Pearl_Harbor.htm
- Lansdale, crash sites: https://j-aircraft.com/research/jimlansdale/ph_crashsite/ph_crash_4.html
- j-aircraft Pearl Harbor FAQ: https://j-aircraft.com/faq/pearl_harbor.htm
- Axis History Forum thread quoting the crash-site list: https://forum.axishistory.com/viewtopic.php?t=82379
- Pacific Wrecks, A6M2 5289 (AI-154): https://pacificwrecks.com/aircraft/a6m2/5289.html
- HistoryNet, Hirano's Pearl Harbor Zero: https://historynet.com/hiranos-pearl-harbor-zero/
- WW2DB, Suzuki's B5N being recovered: https://ww2db.com/image.php?image_id=11648
- WW2DB, attack timetable: https://ww2db.com/timetable_pearl.php
- World War II Database, Arizona attribution: https://www.worldwar2database.com/uss-arizona-bb-39-burns-after-japanese-air-attack/
- NavWeaps order of battle: https://www.navweaps.com/index_oob/OOB_WWII_Pacific/OOB_WWII_Pearl_Harbor.php
- Pearl Harbor Aviation Museum, Thunderfish in the Sky: https://www.pearlharboraviationmuseum.org/blog/pearl-harbor-thunderfish-in-the-sky/
- Inch High Guy, carrier aircraft markings: https://inchhighguy.wordpress.com/2025/04/02/japanese-carrier-aircraft-markings-pearl-harbor-raid/
- Pacific Wrecks, Ewa Field: https://pacificwrecks.com/airfield/usa/ewa/index.html

Starting points only

- Wikipedia: order of battle https://en.wikipedia.org/wiki/Attack_on_Pearl_Harbor_order_of_battle ; Mitsuo Fuchida https://en.wikipedia.org/wiki/Mitsuo_Fuchida ; USS Arizona https://en.wikipedia.org/wiki/USS_Arizona ; Zuikaku https://en.wikipedia.org/wiki/Japanese_aircraft_carrier_Zuikaku ; Type 91 torpedo https://en.wikipedia.org/wiki/Type_91_torpedo
- Combined Fleet, Akagi tabular record of movement (listed, not read): https://www.combinedfleet.com/Akagi.htm

Source reliability notes

- One mirror of Wikipedia's Fuchida article that the search returned carried embedded instructions aimed at AI readers. I ignored them and did not use that page.
- The search tool dated the Zimm "Victory Undermined" article to December 2026, which is after the date of this research. I have kept the URL as returned and treat the date as unverified.
